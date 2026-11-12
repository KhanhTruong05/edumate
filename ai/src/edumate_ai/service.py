"""Optional HTTP entry point. Core provider/schema code remains usable without FastAPI."""
import hmac
import os
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .errors import AIError
from .provider import GeminiProvider
from .schemas import GeneratedDraft


class Source(BaseModel):
    model_config = ConfigDict(extra='allow')
    id: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=45000)


class DraftInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    kind: Literal['lesson', 'plan', 'personal_report']
    instructions: str = Field(min_length=10, max_length=6000)
    # Each non-empty source uses at least one character of the aggregate budget.
    sources: list[Source] = Field(default_factory=list, max_length=45000)

    @model_validator(mode='after')
    def source_budget(self):
        if sum(len(source.text) for source in self.sources) > 45000:
            raise ValueError('Tập nguồn vượt 45000 ký tự.')
        return self


def create_app(provider=None, token: str | None = None) -> FastAPI:
    service_token = token if token is not None else os.getenv('AI_SERVICE_TOKEN', '')
    if not service_token:
        raise RuntimeError('Cần AI_SERVICE_TOKEN để chạy AI HTTP service.')
    generator = provider or GeminiProvider(os.getenv('GEMINI_API_KEY', ''), os.getenv('GEMINI_MODEL', ''))
    app = FastAPI(title='EduMate AI', docs_url=None, redoc_url=None, openapi_url=None)

    def authorize(x_ai_service_token: str = Header(default='')):
        if not hmac.compare_digest(x_ai_service_token.encode(), service_token.encode()):
            raise HTTPException(status_code=403, detail='Invalid service token')

    @app.exception_handler(AIError)
    async def ai_error(request: Request, exc: AIError):
        return JSONResponse(status_code=exc.status, content={'code': exc.code, 'message': exc.message})

    @app.get('/health')
    def health():
        return {'status': 'ok', 'ai_configured': generator.configured}

    @app.post('/drafts', response_model=GeneratedDraft, dependencies=[Depends(authorize)])
    async def draft(body: DraftInput):
        return await generator.draft(body.kind, body.instructions, [s.model_dump() for s in body.sources])

    return app
