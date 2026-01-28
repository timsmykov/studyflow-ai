"""
Chat service for StudyFlow - Using GLM-4.7 API
"""

import os
import httpx
import json
from typing import AsyncGenerator, Optional
from app.config import settings


class ChatService:
    """Chat service using GLM-4.7 API"""

    def __init__(self):
        self.api_key = settings.GLM_API_KEY
        self.api_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        self.client = httpx.AsyncClient(timeout=60.0)

    async def chat(
        self,
        session_id: int,
        course_id: str,
        message: str,
        complexity: str = "standard"
    ) -> dict:
        """
        Send a chat message and get response (non-streaming).
        """
        prompt = self._build_system_prompt(course_id, complexity)

        try:
            response = await self.client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "glm-4",
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": message},
                    ],
                    "stream": False,
                },
                timeout=30.0,
            )
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            return {
                "session_id": session_id,
                "message": content,
                "tokens": len(content.split()),  # Approximate
            }
        except Exception as e:
            raise Exception(f"Chat API error: {str(e)}")

    async def chat_stream(
        self,
        session_id: int,
        course_id: str,
        message: str,
        complexity: str = "standard",
    ) -> AsyncGenerator[dict, None, None]:
        """
        Send a chat message and stream response (SSE).
        """
        prompt = self._build_system_prompt(course_id, complexity)

        try:
            async with self.client.stream(
                self.api_url,
                method="POST",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "glm-4",
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": message},
                    ],
                    "stream": True,
                },
                timeout=60.0,
            ) as response:
                response.raise_for_status()

                current_content = ""
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            yield {
                                "session_id": session_id,
                                "content": current_content,
                                "delta": "",
                                "finished": True,
                            }
                            break

                        try:
                            data = json.loads(data_str)
                            if (
                                "choices" in data
                                and len(data["choices"]) > 0
                                and "delta" in data["choices"][0]
                            ):
                                delta = data["choices"][0]["delta"]
                                if "content" in delta:
                                    chunk = delta["content"]
                                    current_content += chunk
                                    yield {
                                        "session_id": session_id,
                                        "content": current_content,
                                        "delta": chunk,
                                        "finished": False,
                                    }
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            raise Exception(f"Chat streaming error: {str(e)}")

    def _build_system_prompt(self, course_id: str, complexity: str) -> str:
        """
        Build system prompt based on course and complexity.
        """
        complexity_descriptions = {
            "brief": "Provide concise answers (1-2 sentences). Focus on key points only.",
            "standard": "Provide detailed answers with examples. Explain concepts clearly but concisely.",
            "deep": "Provide comprehensive answers with in-depth explanations, examples, and context.",
        }

        complexity_instruction = complexity_descriptions.get(
            complexity,
            complexity_descriptions["standard"]
        )

        return f"""You are an AI tutor for {course_id or "general"} learning.

{complexity_instruction}

Your role:
- Help students understand concepts
- Guide them through problems step-by-step
- Never give direct answers without explanation
- Encourage critical thinking

Answer in a friendly, supportive tone.
"""


# Singleton instance
chat_service = ChatService()
