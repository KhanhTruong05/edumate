from fastapi.testclient import TestClient

from edumate_ai import GeminiProvider


def service(provider=None):
    from edumate_ai.service import create_app
    return TestClient(create_app(provider=provider or GeminiProvider()))


def test_health_does_not_require_gemini_configuration():
    response = service().get('/health')
    assert response.json() == {'status': 'ok', 'ai_configured': False}


def test_missing_gemini_key_preserves_ai_error():
    response = service().post('/drafts', json={
        'kind': 'lesson', 'instructions': 'Soạn bài theo yêu cầu.', 'sources': []})
    assert response.status_code == 503
    assert response.json()['code'] == 'AI_NOT_CONFIGURED'


def test_service_returns_structured_draft():
    class DraftProvider:
        configured = True

        async def draft(self, kind, instructions, sources):
            assert kind == 'lesson'
            assert sources == [{'id': 'doc:1:b0', 'text': 'Nội dung nguồn.'}]
            return {'sections': [{'title': 'Đề xuất', 'text': 'Hoạt động cần xem xét.'}],
                    'claims': [], 'warnings': []}

    response = service(DraftProvider()).post('/drafts', json={
        'kind': 'lesson', 'instructions': 'Soạn bài theo yêu cầu.',
        'sources': [{'id': 'doc:1:b0', 'text': 'Nội dung nguồn.'}]})
    assert response.status_code == 200
    assert response.json()['sections'] == [{'title': 'Đề xuất', 'text': 'Hoạt động cần xem xét.'}]


def test_service_starts_without_token(monkeypatch):
    from edumate_ai.service import create_app
    monkeypatch.delenv('AI_SERVICE_TOKEN', raising=False)
    response = TestClient(create_app()).get('/health')
    assert response.status_code == 200


def test_source_budget_applies_across_documents_without_per_document_block_cap():
    class Generator:
        configured = True

        async def draft(self, kind, instructions, sources):
            assert len(sources) == 6003
            return {'sections': [{'title': 'Đề xuất', 'text': 'Bản nháp.'}], 'claims': [], 'warnings': []}

    response = service(Generator()).post('/drafts', json={
        'kind': 'lesson', 'instructions': 'Soạn bài theo nguồn đã chọn.',
        'sources': [{'id': f'doc-{i // 2001}:1:b{i % 2001}', 'text': 'a'} for i in range(6003)]})
    assert response.status_code == 200


def test_source_budget_rejects_over_45000_total_characters():
    response = service().post('/drafts', json={
        'kind': 'lesson', 'instructions': 'Soạn bài theo nguồn đã chọn.',
        'sources': [{'id': 'doc:1:b0', 'text': 'a' * 45000}, {'id': 'doc:1:b1', 'text': 'b'}]})
    assert response.status_code == 422
