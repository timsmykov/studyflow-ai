from typing import AsyncGenerator, Optional
from datetime import datetime
import time
from openai import AsyncOpenAI
from app.models import Session, Message, Student
from app.database import get_db
from app.config import settings


class ChatService:
    """OpenAI chat service with streaming support."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def create_session(
        self,
        db,
        student_id: int,
        course_id: str
    ) -> Session:
        """Create a new chat session."""
        session = Session(
            student_id=student_id,
            course_id=course_id
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    async def save_message(
        self,
        db,
        session_id: int,
        role: str,
        content: str,
        tokens: int = 0,
        latency_ms: int = 0
    ) -> Message:
        """Save a message to the database."""
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            tokens=tokens,
            latency_ms=latency_ms
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    async def get_session_history(
        self,
        db,
        session_id: int,
        limit: int = 10
    ) -> list[dict]:
        """Get chat session history."""
        messages = db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at).limit(limit).all()

        return [
            {
                "role": msg.role,
                "content": msg.content
            }
            for msg in messages
        ]

    async def chat_stream(
        self,
        db,
        student_id: int,
        course_id: str,
        session_id: Optional[int],
        user_message: str
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response from OpenAI.

        Yields chunks of the response as they arrive.
        """
        start_time = time.time()

        # Create or get session
        if not session_id:
            session = await self.create_session(db, student_id, course_id)
            session_id = session.id
        else:
            session = db.get(Session, session_id)

        # Save user message
        await self.save_message(
            db,
            session_id,
            "user",
            user_message
        )

        # Build system prompt based on course
        system_prompt = self._build_system_prompt(course_id)

        # Get session history for context
        history = await self.get_session_history(db, session_id)

        # Build messages for OpenAI
        messages = [
            {"role": "system", "content": system_prompt},
            *history
        ]

        # Stream response from OpenAI
        response_content = ""
        total_tokens = 0

        try:
            stream = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                stream=True,
                temperature=0.7,
                max_tokens=2000
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    response_content += content
                    total_tokens += len(content.split())

                    # Emit SSE format
                    yield f"data: {json.dumps({'content': content})}\n\n"

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # Save assistant message
            await self.save_message(
                db,
                session_id,
                "assistant",
                response_content,
                tokens=total_tokens,
                latency_ms=latency_ms
            )

            # Update student's last_active timestamp
            student = db.get(Student, student_id)
            if student:
                student.last_active = datetime.utcnow()
                db.commit()

            # Send done signal
            yield f"data: {json.dumps({'done': True, 'session_id': session_id, 'tokens': total_tokens, 'latency_ms': latency_ms})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    async def chat_non_stream(
        self,
        db,
        student_id: int,
        course_id: str,
        session_id: Optional[int],
        user_message: str
    ) -> dict:
        """
        Non-streaming chat response from OpenAI.

        Returns complete response with metadata.
        """
        start_time = time.time()

        # Create or get session
        if not session_id:
            session = await self.create_session(db, student_id, course_id)
            session_id = session.id
        else:
            session = db.get(Session, session_id)

        # Save user message
        await self.save_message(
            db,
            session_id,
            "user",
            user_message
        )

        # Build system prompt based on course
        system_prompt = self._build_system_prompt(course_id)

        # Get session history for context
        history = await self.get_session_history(db, session_id)

        # Build messages for OpenAI
        messages = [
            {"role": "system", "content": system_prompt},
            *history
        ]

        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                stream=False,
                temperature=0.7,
                max_tokens=2000
            )

            response_content = response.choices[0].message.content
            total_tokens = response.usage.total_tokens

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # Save assistant message
            message = await self.save_message(
                db,
                session_id,
                "assistant",
                response_content,
                tokens=total_tokens,
                latency_ms=latency_ms
            )

            # Update student's last_active timestamp
            student = db.get(Student, student_id)
            if student:
                student.last_active = datetime.utcnow()
                db.commit()

            return {
                "session_id": session_id,
                "message_id": message.id,
                "content": response_content,
                "tokens": total_tokens,
                "latency_ms": latency_ms
            }

        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

    def _build_system_prompt(self, course_id: str) -> str:
        """Build system prompt based on course context."""
        return f"""You are a helpful AI tutor for StudyFlow AI.

You are helping a student learn in course: {course_id}

Your role is to:
1. Provide clear, accurate explanations
2. Ask follow-up questions to check understanding
3. Adapt your teaching style to the student's progress
4. Encourage critical thinking
5. Be patient and supportive

Keep responses concise and focused. Use examples when helpful.
"""


# Global service instance
import json
chat_service = ChatService()
