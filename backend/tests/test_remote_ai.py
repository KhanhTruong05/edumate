import asyncio
import json

import httpx
import pytest

from app.core.errors import DomainError
from app.main import create_app


def remote_provider(monkeypatch, handler):
    from app.modules.agent import remote
    original = httpx.AsyncClient
    monkeypatch.setattr(remote.httpx, 'AsyncClient',
                        lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs))
    return remote.RemoteAIProvider('http://ai:8001')


def test_remote_draft_forwards_sources_without_token(monkeypatch):
    def handler(request):
        assert str(request.url) == 'http://ai:8001/drafts'
        assert 'X-AI-Service-Token' not in request.headers
        assert json.loads(request.content)['sources'] == [{'id': 'd:1:b0', 'text': 'Nguồn'}]
        return httpx.Response(200, json={'sections': [{'title': 'Đề xuất', 'text': 'Bản nháp'}],
                                        'claims': [], 'warnings': []})
    provider = remote_provider(monkeypatch, handler)
    result = asyncio.run(provider.draft('lesson', 'Soạn theo nguồn', [{'id': 'd:1:b0', 'text': 'Nguồn'}]))
    assert result['sections'][0]['text'] == 'Bản nháp'


@pytest.mark.parametrize('status,payload,code', [
    (503, {'code': 'AI_NOT_CONFIGURED', 'message': 'missing'}, 'AI_NOT_CONFIGURED'),
    (403, {'detail': 'private token'}, 'AI_UPSTREAM_ERROR'),
    (200, {'sections': []}, 'AI_UPSTREAM_ERROR'),
])
def test_remote_errors_are_safe_domain_errors(monkeypatch, status, payload, code):
    provider = remote_provider(monkeypatch, lambda request: httpx.Response(status, json=payload))
    with pytest.raises(DomainError) as error:
        asyncio.run(provider.draft('lesson', 'Soạn theo nguồn', []))
    assert error.value.code == code
    assert 'private' not in str(error.value)


def test_remote_timeout_is_domain_error(monkeypatch):
    def handler(request):
        raise httpx.ReadTimeout('private transport details')
    provider = remote_provider(monkeypatch, handler)
    with pytest.raises(DomainError) as error:
        asyncio.run(provider.draft('lesson', 'Soạn theo nguồn', []))
    assert error.value.code == 'AI_UPSTREAM_ERROR'
    assert 'private' not in str(error.value)


def test_app_uses_remote_ai_when_configured(monkeypatch, tmp_path):
    monkeypatch.setenv('AI_SERVICE_URL', 'http://ai:8001')
    app = create_app(tmp_path)
    assert type(app.state.provider).__name__ == 'RemoteAIProvider'


@pytest.mark.parametrize('supplied,status', [('', 403), ('wrong', 403), ('test-proxy', 200)])
def test_remote_demo_requests_require_proxy_token(monkeypatch, tmp_path, supplied, status):
    from fastapi.testclient import TestClient
    monkeypatch.setenv('DEMO_PROXY_TOKEN', 'test-proxy')
    app = create_app(tmp_path)
    client = TestClient(app, client=('172.20.0.5', 40000))
    response = client.get('/api/v1/me', headers={
        'X-Demo-User': 'teacher-1', 'X-Edumate-Proxy-Token': supplied})
    assert response.status_code == status


@pytest.mark.parametrize('fake_quote,expected', [(False, 'needs_human_review'), (True, 'rejected')])
def test_backend_ai_http_flow_preserves_citations_and_audit(app, client, monkeypatch, fake_quote, expected):
    from edumate_ai.service import create_app as create_ai
    from app.modules.agent import remote
    from conftest import actor, make_doc

    class Generator:
        configured = True

        async def draft(self, kind, instructions, sources):
            return {'sections': [{'title': 'Đề xuất', 'text': 'Hoạt động cần xem xét.'}],
                    'claims': [{'text': 'Tham chiếu', 'source_id': sources[0]['id'],
                                'quote': 'trích dẫn giả' if fake_quote else sources[0]['text']}],
                    'warnings': []}

    ai_app = create_ai(provider=Generator())
    transport = httpx.ASGITransport(app=ai_app)
    original = httpx.AsyncClient
    monkeypatch.setattr(remote.httpx, 'AsyncClient', lambda **kwargs: original(transport=transport, **kwargs))
    app.state.provider = remote.RemoteAIProvider('http://ai:8001')
    doc = make_doc(client)

    response = client.post('/api/v1/agent/drafts', headers=actor(), json={
        'kind': 'lesson', 'instructions': 'Soạn bài theo nguồn được chọn.', 'source_ids': [doc['id']]})
    assert response.status_code == 200
    assert response.json()['status'] == expected
    assert ('result' in response.json()) == (not fake_quote)
    assert client.get(f'/api/v1/documents/{doc["id"]}', headers=actor()).json()['revision'] == 1
    events = client.get('/api/v1/audit-events', headers=actor()).json()
    assert any(event['action'] == f'agent.{expected}' for event in events)


def test_direct_demo_access_when_enabled_for_local_docker(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    monkeypatch.setenv('DEMO_ALLOW_DIRECT_ACCESS', 'true')
    client = TestClient(create_app(tmp_path), client=('172.20.0.1', 40000))
    response = client.get('/api/v1/me', headers={'X-Demo-User': 'teacher-1'})
    assert response.status_code == 200
    assert response.json()['id'] == 'teacher-1'
