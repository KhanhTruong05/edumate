import io
import json
import sqlite3
from datetime import timedelta
from zipfile import ZipFile

import pytest

from app.core.clock import utcnow
from conftest import actor, make_doc, sample_content, export_and_submit


def expire(app):
    with app.state.db.transaction() as tx:
        period = tx.get('periods', 'period-demo')
        period['due_at'] = (utcnow() - timedelta(seconds=1)).isoformat()
        tx.put('periods', period)


def test_other_teacher_cannot_read_or_download(client):
    doc = make_doc(client)
    assert client.get(f'/api/v1/documents/{doc["id"]}', headers=actor('teacher-2')).status_code == 404
    assert client.get(f'/api/v1/documents/{doc["id"]}/file', headers=actor('teacher-2')).status_code == 404


def test_teacher_cannot_approve(client):
    doc = export_and_submit(client, make_doc(client))
    assert client.post(f'/api/v1/documents/{doc["id"]}/decisions', headers=actor(), json={
        'expected_revision': doc['revision'], 'decision': 'approve', 'reason': 'Tự duyệt'}).status_code == 403


def test_stale_revision_cannot_overwrite(client):
    doc = make_doc(client)
    body = {'title': 'Đã sửa', 'kind': 'lesson', 'period_id': 'period-demo',
            'content': sample_content(), 'expected_revision': 1}
    assert client.patch(f'/api/v1/documents/{doc["id"]}', headers=actor(), json=body).status_code == 200
    assert client.patch(f'/api/v1/documents/{doc["id"]}', headers=actor(), json=body).status_code == 409


def test_deadline_blocks_save_and_submit(app, client):
    doc = make_doc(client)
    expire(app)
    body = {'title': doc['title'], 'kind': 'lesson', 'period_id': 'period-demo',
            'content': sample_content(), 'expected_revision': 1}
    assert client.patch(f'/api/v1/documents/{doc["id"]}', headers=actor(), json=body).status_code == 423
    assert client.post(f'/api/v1/documents/{doc["id"]}/submit', headers=actor(), json={'expected_revision': 1}).status_code == 423


def test_override_reopens_window_with_audit(app, client):
    expire(app)
    payload = {'user_id': 'teacher-1', 'allowed_until': (utcnow() + timedelta(hours=1)).isoformat(),
               'reason': 'Bổ sung theo góp ý', 'expected_revision': 1}
    assert client.post('/api/v1/periods/period-demo/deadline-overrides', headers=actor(), json=payload).status_code == 403
    assert client.post('/api/v1/periods/period-demo/deadline-overrides', headers=actor('lead-1'), json=payload).status_code == 200
    make_doc(client)
    logs = client.get('/api/v1/audit-events', headers=actor('lead-1')).json()
    assert any(e['action'] == 'deadline.granted' and e['reason'] == payload['reason'] for e in logs)


def test_preview_is_required_and_word_has_content(client):
    doc = make_doc(client)
    assert client.post(f'/api/v1/documents/{doc["id"]}/submit', headers=actor(), json={'expected_revision': 1}).status_code == 409
    client.post(f'/api/v1/documents/{doc["id"]}/exports', headers=actor(), json={'expected_revision': 1})
    response = client.get(f'/api/v1/documents/{doc["id"]}/file', headers=actor())
    assert response.status_code == 200
    with ZipFile(io.BytesIO(response.content)) as package:
        xml = package.read('word/document.xml').decode()
        assert 'Mục tiêu' in xml and 'Giáo án kiểm thử' in xml


def test_edit_invalidates_previous_export(client):
    doc = make_doc(client)
    client.post(f'/api/v1/documents/{doc["id"]}/exports', headers=actor(), json={'expected_revision': 1})
    saved = client.patch(f'/api/v1/documents/{doc["id"]}', headers=actor(), json={
        'title': 'Tên mới', 'kind': 'lesson', 'period_id': 'period-demo', 'content': sample_content(), 'expected_revision': 1}).json()
    assert saved['export'] is None
    assert client.get(f'/api/v1/documents/{doc["id"]}/file', headers=actor()).status_code == 404


def test_approved_version_immutable_and_revision_has_no_approval(client):
    doc = export_and_submit(client, make_doc(client))
    approved = client.post(f'/api/v1/documents/{doc["id"]}/decisions', headers=actor('lead-1'), json={
        'expected_revision': doc['revision'], 'decision': 'approve', 'reason': 'Đã kiểm tra'}).json()
    response = client.patch(f'/api/v1/documents/{doc["id"]}', headers=actor(), json={
        'title': 'Ghi đè', 'kind': 'lesson', 'period_id': 'period-demo', 'content': sample_content(), 'expected_revision': approved['revision']})
    assert response.status_code == 409
    revision = client.post(f'/api/v1/documents/{doc["id"]}/revisions', headers=actor(), json={'expected_revision': approved['revision']}).json()
    assert revision['status'] == 'draft' and revision['export'] is None
    assert 'reviewed_by' not in revision and revision['parent_id'] == doc['id']
    assert client.get(f'/api/v1/documents/{doc["id"]}', headers=actor()).json()['status'] == 'approved'


def test_no_self_approval(client):
    doc = export_and_submit(client, make_doc(client, 'lead-1'), 'lead-1')
    body = {'expected_revision': doc['revision'], 'decision': 'approve', 'reason': 'Duyệt'}
    assert client.post(f'/api/v1/documents/{doc["id"]}/decisions', headers=actor('lead-1'), json=body).status_code == 403
    assert client.post(f'/api/v1/documents/{doc["id"]}/decisions', headers=actor('lead-2'), json=body).status_code == 200


def test_approval_allowed_after_teacher_deadline(app, client):
    doc = export_and_submit(client, make_doc(client))
    expire(app)
    assert client.post(f'/api/v1/documents/{doc["id"]}/decisions', headers=actor('lead-1'), json={
        'expected_revision': doc['revision'], 'decision': 'approve', 'reason': 'Xem sau hạn nộp'}).status_code == 200


def test_audit_is_append_only(app, client):
    make_doc(client)
    with pytest.raises(sqlite3.IntegrityError):
        with app.state.db.transaction() as tx:
            tx.connection.execute("UPDATE audit SET payload='{}'")
    assert len(client.get('/api/v1/audit-events', headers=actor()).json()) == 1


def test_aggregate_latest_version_and_shared_activity(client):
    url = '/api/v1/periods/period-demo/reports'
    base = {'assigned': 10, 'completed': 6, 'activity_codes': ['A1']}
    assert client.post(url, headers=actor(), json=base).status_code == 201
    assert client.post(url, headers=actor(), json={**base, 'completed': 9}).status_code == 201
    assert client.post(url, headers=actor('teacher-2'), json={'assigned': 0, 'completed': 0, 'activity_codes': ['A1', 'A2']}).status_code == 201
    summary = client.post('/api/v1/periods/period-demo/aggregates', headers=actor('lead-1')).json()
    assert summary['expected_count'] == 20 and summary['submitted_count'] == 2
    assert summary['metrics']['completed'] == 9 and summary['metrics']['completion_rate'] == .9
    assert summary['metrics']['unique_activity_count'] == 2 and len(summary['source_ids']) == 2
    client.post(url, headers=actor(), json={**base, 'completed': 10})
    assert summary['metrics']['completed'] == 9  # the earlier source snapshot is unchanged


def test_zero_denominator_and_missing_values(client):
    client.post('/api/v1/periods/period-demo/reports', headers=actor(), json={'assigned': None, 'completed': None})
    summary = client.post('/api/v1/periods/period-demo/aggregates', headers=actor('lead-1')).json()
    assert summary['metrics']['completion_rate'] is None
    assert summary['metrics']['eligible_count'] == 0 and summary['submitted_count'] == 1


def test_invalid_report_numbers_rejected(client):
    url = '/api/v1/periods/period-demo/reports'
    assert client.post(url, headers=actor(), json={'assigned': 2, 'completed': 3}).status_code == 422
    assert client.post(url, headers=actor(), json={'assigned': 2, 'completed': None}).status_code == 422


def test_ai_without_credentials_is_explicit_failure(client):
    response = client.post('/api/v1/agent/drafts', headers=actor(), json={
        'kind': 'lesson', 'instructions': 'Soạn bài học theo yêu cầu.', 'source_ids': []})
    assert response.status_code == 503 and response.json()['code'] == 'AI_NOT_CONFIGURED'
    assert any(e['action'] == 'agent.failed' for e in client.get('/api/v1/audit-events', headers=actor()).json())


class ProviderForTests:
    configured = True
    def __init__(self, fake_quote=False):
        self.fake_quote = fake_quote
    async def draft(self, kind, instructions, sources):
        return {'sections': [{'title': 'Đề xuất', 'text': 'Hoạt động cần giáo viên xác nhận.'}],
                'claims': [{'text': 'Nội dung tham chiếu', 'source_id': sources[0]['id'],
                            'quote': 'trích dẫn không tồn tại' if self.fake_quote else sources[0]['text']}],
                'warnings': []}


def test_fake_citation_rejected(app, client):
    doc = make_doc(client)
    app.state.provider = ProviderForTests(fake_quote=True)
    run = client.post('/api/v1/agent/drafts', headers=actor(), json={
        'kind': 'lesson', 'instructions': 'Soạn theo nguồn đã chọn.', 'source_ids': [doc['id']]}).json()
    assert run['status'] == 'rejected' and 'result' not in run


def test_valid_quote_still_requires_human_review(app, client):
    doc = make_doc(client)
    app.state.provider = ProviderForTests()
    run = client.post('/api/v1/agent/drafts', headers=actor(), json={
        'kind': 'lesson', 'instructions': 'Soạn theo nguồn đã chọn.', 'source_ids': [doc['id']]}).json()
    assert run['status'] == 'needs_human_review'
    assert client.get(f'/api/v1/documents/{doc["id"]}', headers=actor()).json()['revision'] == 1


def test_agent_cannot_read_other_teacher_source(client):
    doc = make_doc(client, 'teacher-2')
    response = client.post('/api/v1/agent/drafts', headers=actor(), json={
        'kind': 'lesson', 'instructions': 'Soạn theo nguồn đã chọn.', 'source_ids': [doc['id']]})
    assert response.status_code == 404


def test_no_html_script_editor_node(client):
    response = client.post('/api/v1/documents', headers=actor(), json={
        'title': 'X', 'kind': 'lesson', 'period_id': 'period-demo',
        'content': {'type': 'doc', 'content': [{'type': 'script', 'text': 'alert(1)'}]}})
    assert response.status_code == 422


def test_malformed_editor_marks_return_validation_error(client):
    response = client.post('/api/v1/documents', headers=actor(), json={
        'title': 'X', 'kind': 'lesson', 'period_id': 'period-demo',
        'content': {'type': 'doc', 'content': [{'type': 'text', 'text': 'Nội dung thử', 'marks': ['bold']}]}})
    assert response.status_code == 422
