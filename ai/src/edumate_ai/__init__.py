"""AI capabilities independent of EduMate's API, authentication and database."""
from .errors import AIError
from .provider import GeminiProvider
from .quality import verify_claims
from .schemas import GeneratedDraft

__all__ = ['AIError', 'GeminiProvider', 'GeneratedDraft', 'verify_claims']
