from openai import AsyncOpenAI
from typing import Optional, List, AsyncGenerator, Dict, Any
import time
from app.config import settings
from app.models import Message, MessageRole, Session
from sqlmodel import Session as SQLSession, select


class AIChatService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.context_window = 20  # Number of messages to keep in context
        self._last_stream_metrics = {}

        # Initialize tiktoken for accurate token counting
        try:
            import tiktoken
            self.encoding = tiktoken.encoding_for_model(self.model)
        except Exception:
            self.encoding = None

    async def count_tokens(self, text: str) -> int:
        """
        Count tokens for a text string using tiktoken if available,
        otherwise fall back to simple approximation.
        """
        if self.encoding:
            try:
                tokens = self.encoding.encode(text)
                return len(tokens)
            except Exception:
                pass

        # Fallback to approximation: ~4 characters per token
        return max(1, len(text) // 4)

    async def get_message_history(
        self, session_id: int, db_session: SQLSession
    ) -> List[Dict[str, str]]:
        """
        Retrieve the last N messages from the session history.
        """
        statement = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at)
            .limit(self.context_window)
        )
        results = await db_session.exec(statement)
        messages = results.all()

        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]

    def build_system_prompt(
        self, course_name: str, complexity: str = "standard"
    ) -> str:
        """
        Build the system prompt based on course and complexity.
        """
        complexity_description = {
            "brief": "concise answers, keep explanations short and to the point",
            "standard": "detailed explanations, provide clear and thorough answers",
            "deep": "extensive explanations with examples, analogies, and in-depth analysis"
        }.get(complexity, "standard")

        return (
            f"You are an AI tutor for {course_name}. "
            f"Complexity: {complexity} ({complexity_description}). "
            f"Help students understand concepts, guide them through problems, "
            f"never give direct answers without explanation."
        )

    async def stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion from OpenAI.
        Yields chunks of the response as they arrive.
        """
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        start_time = time.time()
        first_chunk_time = None
        token_count = 0

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                stream=True,
                temperature=0.7,
                max_tokens=2000,
            )

            async for chunk in stream:
                if first_chunk_time is None:
                    first_chunk_time = time.time()

                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    token_count += await self.count_tokens(content)
                    yield content

        except Exception as e:
            raise RuntimeError(f"OpenAI streaming error: {str(e)}")

        # Track latency and store for later access
        end_time = time.time()
        total_latency = (end_time - start_time) * 1000  # Convert to ms
        first_chunk_latency = (
            (first_chunk_time - start_time) * 1000 if first_chunk_time else 0
        )

        # Store metrics as instance variables for later access
        self._last_stream_metrics = {
            "total_latency_ms": total_latency,
            "first_chunk_latency_ms": first_chunk_latency,
            "token_count": token_count,
        }

    async def chat(
        self,
        session_id: int,
        user_message: str,
        course_id: str,
        complexity: str = "standard",
        db_session: Optional[SQLSession] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Main chat function that handles streaming and context management.
        """
        if not db_session:
            raise ValueError("Database session is required")

        # Get course name (simplified - in production, fetch from courses table)
        course_name = f"Course {course_id}"

        # Get message history
        message_history = await self.get_message_history(session_id, db_session)

        # Build system prompt
        system_prompt = self.build_system_prompt(course_name, complexity)

        # Add user message to history
        user_tokens = await self.count_tokens(user_message)
        user_tokens_saved = user_tokens  # Will be saved to DB

        # Stream the response
        full_response = ""
        start_time = time.time()

        try:
            async for chunk in self.stream_chat_completion(
                message_history, system_prompt
            ):
                full_response += chunk
                yield chunk

        except Exception as e:
            raise RuntimeError(f"Chat streaming error: {str(e)}")

        # Calculate latency
        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)

        # Count assistant tokens
        assistant_tokens = await self.count_tokens(full_response)

        # Save messages to database
        try:
            # Save user message
            user_message_db = Message(
                session_id=session_id,
                role=MessageRole.USER,
                content=user_message,
                tokens=user_tokens_saved,
                latency_ms=0,  # User messages don't have latency
            )
            db_session.add(user_message_db)
            await db_session.flush()

            # Save assistant message
            assistant_message_db = Message(
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=full_response,
                tokens=assistant_tokens,
                latency_ms=latency_ms,
            )
            db_session.add(assistant_message_db)
            await db_session.commit()

        except Exception as e:
            await db_session.rollback()
            raise RuntimeError(f"Failed to save messages to database: {str(e)}")

    async def get_session_or_create(
        self, session_id: Optional[int], course_id: str, student_id: int, db_session: SQLSession
    ) -> Session:
        """
        Get existing session or create a new one.
        """
        if session_id:
            statement = select(Session).where(Session.id == session_id)
            result = await db_session.exec(statement)
            session = result.first()
            if session:
                return session

        # Create new session
        new_session = Session(
            student_id=student_id,
            course_id=course_id,
        )
        db_session.add(new_session)
        await db_session.flush()
        await db_session.refresh(new_session)
        return new_session


# Singleton instance
ai_chat_service = AIChatService()
