"""HTTP adapter for the separately deployed AI service."""
import httpx
from edumate_ai import GeneratedDraft

from app.core.errors import DomainError


class RemoteAIProvider:
    # Key/model live in the AI service; backend health cannot infer their state.
    configured = None

    def __init__(self, url: str, token: str):
        self.url = url.rstrip('/')
        self.token = token

    async def draft(self, kind, instructions, sources) -> dict:
        if not self.token:
            raise DomainError('AI_NOT_CONFIGURED', 'Chưa cấu hình token kết nối AI service.', 503)
        try:
            async with httpx.AsyncClient(timeout=55) as client:
                response = await client.post(f'{self.url}/drafts',
                    headers={'X-AI-Service-Token': self.token},
                    json={'kind': kind, 'instructions': instructions, 'sources': sources})
            if response.status_code == 503 and response.json().get('code') == 'AI_NOT_CONFIGURED':
                raise DomainError('AI_NOT_CONFIGURED', 'Chưa cấu hình Gemini ở AI service.', 503)
            response.raise_for_status()
            return GeneratedDraft.model_validate_json(response.content).model_dump()
        except (httpx.HTTPError, ValueError, TypeError, AttributeError) as exc:
            raise DomainError('AI_UPSTREAM_ERROR', 'Không gọi được AI service hoặc kết quả không hợp lệ.', 502) from exc
