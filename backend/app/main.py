from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import router
from app.core.config import config
from app.core.errors import DomainError
from app.infrastructure.database import Database
from app.infrastructure.local_storage import LocalStorage
from app.modules.agent.provider import GeminiProvider
from app.seed import seed


def create_app(data_dir: Path | None = None, provider=None) -> FastAPI:
    settings = config()
    if settings['mode'] != 'demo':
        raise RuntimeError('Starter chỉ nối local demo. Hoàn thành Firebase repository/auth trước khi dùng cloud.')
    app = FastAPI(title='EduMate Starter', version='0.1.0',
                  description='Demo cục bộ; chưa phải hệ thống triển khai chính thức.')
    directory = data_dir or settings['data_dir']
    app.state.db = Database(directory)
    app.state.storage = LocalStorage(directory / 'files')
    app.state.provider = provider or GeminiProvider(settings['gemini_key'], settings['gemini_model'])
    seed(app.state.db)
    app.add_middleware(CORSMiddleware, allow_origins=settings['cors'],
                       allow_methods=['GET', 'POST', 'PATCH'], allow_headers=['Content-Type', 'X-Demo-User'])

    @app.exception_handler(DomainError)
    async def domain_error(request: Request, exc: DomainError):
        return JSONResponse(status_code=exc.status, content={'code': exc.code, 'message': exc.message})

    @app.get('/health')
    def health():
        return {'status': 'ok', 'mode': 'local_demo', 'cloud_repository': False,
                'ai_configured': app.state.provider.configured}

    app.include_router(router)
    return app


app = create_app()
