"""
Chat API endpoints for StudyFlow (using GLM-4.7).
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.chat_service import chat_service


class ChatRequest(BaseModel):
    """Request model for chat messages."""
    session_id: int | None = None
    course_id: str = "general"
    message: str
    complexity: str = "standard"


class ChatResponse(BaseModel):
    """Response model for chat messages."""
    session_id: int
    message: str
    tokens: int


router = APIRouter()


@router.post("/")
async def chat_message(request: ChatRequest):
    """
    Send a chat message and get response (non-streaming).

    Uses GLM-4.7 API via chat_service.
    """
    try:
        result = await chat_service.chat(
            session_id=request.session_id or 0,
            course_id=request.course_id,
            message=request.message,
            complexity=request.complexity,
        )
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Send a chat message and stream response (SSE).

    Uses GLM-4.7 API via chat_service with streaming.
    """
    try:
        async def event_generator():
            """Generate SSE events from GLM-4.7 stream."""
            async for chunk in chat_service.chat_stream(
                session_id=request.session_id or 0,
                course_id=request.course_id,
                message=request.message,
                complexity=request.complexity,
            ):
                if chunk["finished"]:
                    yield f"data: {json.dumps(chunk)}\n\n"
                    yield "data: [DONE]\n\n"
                else:
                    yield f"data: {json.dumps(chunk)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def get_models():
    """
    Get available AI models.

    Currently using GLM-4.7.
    """
    return {
        "current": "GLM-4.7",
        "provider": "Zhipu AI",
        "api_endpoint": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "complexity_levels": ["brief", "standard", "deep"],
    }
