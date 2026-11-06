import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv('APP_MODE', 'demo')
    app = create_app(tmp_path)
    # Ensure the default AI-not-configured test never calls an external service.
    from app.modules.agent.provider import GeminiProvider
    app.state.provider = GeminiProvider()
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def actor(identity='teacher-1'):
    return {'X-Demo-User': identity}


def sample_content():
    return {'type': 'doc', 'content': [
        {'type': 'heading', 'attrs': {'level': 2}, 'content': [{'type': 'text', 'text': 'Mục tiêu'}]},
        {'type': 'paragraph', 'content': [{'type': 'text', 'text': 'Học sinh thực hành hoạt động và được đánh giá theo mục tiêu đã chọn.', 'marks': [{'type': 'bold'}]}]},
    ]}


def make_doc(client, identity='teacher-1'):
    result = client.post('/api/v1/documents', headers=actor(identity), json={
        'title': 'Giáo án kiểm thử', 'kind': 'lesson', 'period_id': 'period-demo', 'content': sample_content()})
    assert result.status_code == 201, result.text
    return result.json()


def export_and_submit(client, doc, identity='teacher-1'):
    exported = client.post(f'/api/v1/documents/{doc["id"]}/exports', headers=actor(identity), json={'expected_revision': doc['revision']})
    assert exported.status_code == 200, exported.text
    response = client.post(f'/api/v1/documents/{doc["id"]}/submit', headers=actor(identity), json={'expected_revision': doc['revision']})
    assert response.status_code == 200, response.text
    return response.json()
