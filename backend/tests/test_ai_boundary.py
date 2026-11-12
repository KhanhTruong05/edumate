import httpx
import pytest

from app.modules.agent.provider import GeminiProvider
from conftest import actor


@pytest.mark.parametrize('status,payload', [
    (429, {'error': {'message': 'private upstream diagnostic'}}),
    (200, {'candidates': []}),
    (200, {'candidates': None}),
    (200, {'candidates': [{'content': {'parts': [None]}}]}),
])
def test_package_failure_preserves_api_error_and_failed_audit(app, client, monkeypatch, status, payload):
    from edumate_ai import provider

    original_client = httpx.AsyncClient
    transport = httpx.MockTransport(lambda request: httpx.Response(status, json=payload))
    monkeypatch.setattr(provider.httpx, 'AsyncClient',
                        lambda **kwargs: original_client(transport=transport, **kwargs))
    app.state.provider = GeminiProvider('private-test-key', 'test-model')

    response = client.post('/api/v1/agent/drafts', headers=actor(), json={
        'kind': 'lesson', 'instructions': 'Soạn bài học theo yêu cầu.', 'source_ids': []})

    assert response.status_code == 502
    assert response.json()['code'] == 'AI_UPSTREAM_ERROR'
    assert 'private' not in response.text
    events = client.get('/api/v1/audit-events', headers=actor()).json()
    failed = [event for event in events if event['action'] == 'agent.failed']
    assert len(failed) == 1
    with app.state.db.transaction() as tx:
        runs = tx.all('agent_runs')
    assert len(runs) == 1
    assert runs[0]['status'] == 'failed'
    assert runs[0]['error_code'] == 'AI_UPSTREAM_ERROR'
