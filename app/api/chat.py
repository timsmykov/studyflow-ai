from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session
from typing import AsyncGenerator, Optional
from pydantic import BaseModel
import json

from app.database import get_session
from app.utils.clerk_auth import get_current_clerk_user
from app.services.ai_chat import ai_chat_service
from app.models import Student, Session


router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    session_id: Optional[int] = None
    content: str
    course_id: str
    complexity: str = "standard"  # Options: "brief", "standard", "deep"

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": 1,
                "content": "Explain the concept of photosynthesis",
                "course_id": "BIO101",
                "complexity": "standard"
            }
        }


class ChatError(BaseModel):
    error: str
    detail: str


async def get_or_create_student(
    clerk_id: str, db_session: Session
) -> Student:
    """
    Get existing student or create a new one based on clerk_id.
    """
    from app.models import Student
    from sqlmodel import select

    statement = select(Student).where(Student.clerk_id == clerk_id)
    result = db_session.exec(statement)
    student = result.first()

    if not student:
        student = Student(clerk_id=clerk_id)
        db_session.add(student)
        db_session.flush()
        db_session.refresh(student)

    return student


async def stream_response(content: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
    """
    SSE (Server-Sent Events) streaming wrapper.
    """
    try:
        async for chunk in content:
            # Format as SSE event
            data = json.dumps({"content": chunk}, ensure_ascii=False)
            yield f"data: {data}\n\n"

        # Send completion event
        done_event = json.dumps({"done": True}, ensure_ascii=False)
        yield f"data: {done_event}\n\n"

    except Exception as e:
        # Send error event
        error_event = json.dumps(
            {"error": True, "message": str(e)}, ensure_ascii=False
        )
        yield f"data: {error_event}\n\n"


@router.post(
    "/",
    responses={
        200: {
            "description": "Streaming chat response (SSE)",
            "content": {
                "text/event-stream": {
                    "example": "data: {\"content\": \"Hello\"}\n\ndata: {\"done\": true}\n\n"
                }
            },
        },
        400: {"model": ChatError, "description": "Bad request"},
        401: {"model": ChatError, "description": "Unauthorized"},
        500: {"model": ChatError, "description": "Internal server error"},
    },
    summary="Send a chat message and receive a streaming response",
)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_clerk_user),
    db_session: Session = Depends(get_session),
):
    """
    Send a chat message and receive a streaming AI response.

    **Authentication:** Required (Clerk JWT)

    **Request Body:**
    - `session_id` (optional): Existing session ID. If not provided, a new session will be created.
    - `content`: The user's message to the AI.
    - `course_id`: Course identifier for context.
    - `complexity` (optional): Response complexity level. Options:
      - `brief`: Concise, to-the-point answers
      - `standard` (default): Detailed explanations
      - `deep`: Extensive explanations with examples

    **Response:** Server-Sent Events (SSE) stream
    - Each event contains a JSON object with `content` field
    - Final event contains `done: true`
    - Errors are sent as events with `error: true`

    **Example:**
    ```bash
    curl -X POST "https://api.studyflow.com/chat/" \\
      -H "Authorization: Bearer <clerk_jwt>" \\
      -H "Content-Type: application/json" \\
      -d '{
        "session_id": 1,
        "content": "Explain the concept of photosynthesis",
        "course_id": "BIO101",
        "complexity": "standard"
      }'
    ```
    """
    try:
        # Validate complexity
        if request.complexity not in ["brief", "standard", "deep"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid complexity. Must be one of: brief, standard, deep"
            )

        # Validate content
        if not request.content or not request.content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message content cannot be empty"
            )

        # Get or create student
        clerk_id = current_user.get("user_id")
        student = await get_or_create_student(clerk_id, db_session)

        # Get or create session
        session = await ai_chat_service.get_session_or_create(
            session_id=request.session_id,
            course_id=request.course_id,
            student_id=student.id,
            db_session=db_session,
        )

        # Stream the response
        async def generate() -> AsyncGenerator[str, None]:
            try:
                chat_stream = ai_chat_service.chat(
                    session_id=session.id,
                    user_message=request.content,
                    course_id=request.course_id,
                    complexity=request.complexity,
                    db_session=db_session,
                )
                async for chunk in stream_response(chat_stream):
                    yield chunk
            except Exception as e:
                # Send error event
                error_event = json.dumps(
                    {"error": True, "message": str(e)}, ensure_ascii=False
                )
                yield f"data: {error_event}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/sessions/{session_id}",
    response_model=dict,
    summary="Get session information",
)
async def get_session(
    session_id: int,
    current_user: dict = Depends(get_current_clerk_user),
    db_session: Session = Depends(get_session),
):
    """
    Get information about a specific chat session and its messages.
    """
    try:
        # Verify student
        clerk_id = current_user.get("user_id")
        statement = (
            select(Session, Student)
            .join(Student, Session.student_id == Student.id)
            .where(Session.id == session_id, Student.clerk_id == clerk_id)
        )
        result = await db_session.exec(statement)
        data = result.first()

        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session, student = data

        # Get messages
        from app.models import Message
        from sqlmodel import select

        message_statement = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at)
        )
        messages_result = await db_session.exec(message_statement)
        messages = messages_result.all()

        return {
            "session": {
                "id": session.id,
                "course_id": session.course_id,
                "created_at": session.created_at.isoformat(),
            },
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role.value,
                    "content": msg.content,
                    "tokens": msg.tokens,
                    "latency_ms": msg.latency_ms,
                    "created_at": msg.created_at.isoformat(),
                }
                for msg in messages
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
