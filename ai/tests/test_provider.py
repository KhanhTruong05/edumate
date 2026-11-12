"""Exercise the standalone AI contract without backend imports or live Gemini."""
import asyncio
import importlib.util
import json

import httpx
import pytest


def test_ai_can_be_used_without_backend():
    assert importlib.util.find_spec('edumate_ai') is not None, 'Standalone AI package is missing'
    from edumate_ai import GeminiProvider, verify_claims

    assert not GeminiProvider().configured
    assert verify_claims([], []) == []


def test_unconfigured_provider_raises_portable_error():
    from edumate_ai import AIError, GeminiProvider

    with pytest.raises(AIError) as error:
        asyncio.run(GeminiProvider().draft('lesson', 'Soạn bài', []))
    assert error.value.code == 'AI_NOT_CONFIGURED'
    assert error.value.status == 503


def configure_transport(monkeypatch, handler):
    from edumate_ai import provider

    client = httpx.AsyncClient
    monkeypatch.setattr(provider.httpx, 'AsyncClient',
                        lambda **kwargs: client(transport=httpx.MockTransport(handler), **kwargs))


def test_gemini_draft_uses_authorized_sources_and_structured_output(monkeypatch):
    from edumate_ai import GeminiProvider

    sources = [{'id': 'doc:1:b0', 'text': 'Học sinh thực hành.'}]

    def handler(request):
        assert request.url.path == '/v1beta/models/test-model:generateContent'
        assert request.headers['x-goog-api-key'] == 'test-key'
        payload = json.loads(request.content)
        assert json.loads(payload['contents'][0]['parts'][0]['text']) == {
            'kind': 'lesson', 'request': 'Soạn bài', 'sources': sources}
        assert payload['generationConfig']['responseMimeType'] == 'application/json'
        return httpx.Response(200, json={'candidates': [{'content': {'parts': [{'text': json.dumps({
            'sections': [{'title': 'Hoạt động', 'text': 'Thực hành theo nhóm.'}],
            'claims': [], 'warnings': ['Cần giáo viên xem xét.']})}]}}]})

    configure_transport(monkeypatch, handler)
    result = asyncio.run(GeminiProvider('test-key', 'test-model').draft('lesson', 'Soạn bài', sources))
    assert result == {'sections': [{'title': 'Hoạt động', 'text': 'Thực hành theo nhóm.'}],
                      'claims': [], 'warnings': ['Cần giáo viên xem xét.']}


@pytest.mark.parametrize('status,payload', [
    (429, {'error': {'message': 'sensitive upstream detail'}}),
    (200, {'candidates': []}),
    (200, {'candidates': None}),
    (200, {'candidates': [{'content': {'parts': [None]}}]}),
    (200, {'candidates': [{'content': {'parts': [{'text': '{}'}]}}]}),
])
def test_upstream_errors_are_portable_and_hide_details(monkeypatch, status, payload):
    from edumate_ai import AIError, GeminiProvider

    configure_transport(monkeypatch, lambda request: httpx.Response(status, json=payload))
    with pytest.raises(AIError) as error:
        asyncio.run(GeminiProvider('secret-test-key', 'test-model').draft('lesson', 'Soạn bài', []))
    assert error.value.code == 'AI_UPSTREAM_ERROR'
    assert error.value.status == 502
    assert 'secret-test-key' not in str(error.value)
    assert 'sensitive upstream detail' not in str(error.value)


@pytest.mark.parametrize('claim,expected', [
    ({'source_id': 'doc:1:b0', 'quote': 'Học sinh thực hành.'}, []),
    ({'source_id': 'doc:1:b0', 'quote': 'Học sinh   thực hành.'}, []),
    ({'source_id': 'other:1:b0', 'quote': 'Học sinh thực hành.'}, ['INVALID_EVIDENCE']),
    ({'source_id': 'doc:1:b0', 'quote': 'Trích dẫn giả'}, ['INVALID_EVIDENCE']),
    ({'source_id': 'doc:1:b0', 'quote': ''}, ['INVALID_EVIDENCE']),
])
def test_citations_must_match_granted_sources(claim, expected):
    from edumate_ai import verify_claims

    errors = verify_claims([claim], [{'id': 'doc:1:b0', 'text': 'Học sinh thực hành.'}])
    assert [error['code'] for error in errors] == expected
