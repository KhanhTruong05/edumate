"""Adapt the standalone AI package's failures to the backend API contract."""
from edumate_ai import AIError, GeminiProvider as AIGeminiProvider

from app.core.errors import DomainError


class GeminiProvider(AIGeminiProvider):
    async def draft(self, kind, instructions, sources) -> dict:
        try:
            return await super().draft(kind, instructions, sources)
        except AIError as exc:
            raise DomainError(exc.code, exc.message, exc.status) from exc
