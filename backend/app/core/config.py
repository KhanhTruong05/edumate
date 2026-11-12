import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / '.env')


def config() -> dict:
    return {
        'mode': os.getenv('APP_MODE', 'demo'),
        'data_dir': Path(os.getenv('EDUMATE_DATA_DIR', str(BACKEND_DIR / '.data'))),
        'cors': [s.strip() for s in os.getenv(
            'CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173'
        ).split(',') if s.strip()],
        'gemini_key': os.getenv('GEMINI_API_KEY', ''),
        'gemini_model': os.getenv('GEMINI_MODEL', ''),
        'ai_service_url': os.getenv('AI_SERVICE_URL', ''),
        'ai_service_token': os.getenv('AI_SERVICE_TOKEN', ''),
        'demo_proxy_token': os.getenv('DEMO_PROXY_TOKEN', ''),
    }
