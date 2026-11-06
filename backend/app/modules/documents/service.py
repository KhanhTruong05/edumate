from copy import deepcopy
from uuid import uuid4

from app.core.clock import utcnow, iso_now
from app.core.errors import DomainError
from app.domain.policies import (require_access, require_owner, require_revision,
                                 require_window, require_draft, require_lead)
from app.domain.quality import validate_editor, content_hash, rule_checks


def summary(doc):
    return {k: doc.get(k) for k in ('title', 'status', 'revision', 'content_hash', 'version_no')}


def list_documents(db, actor):
    with db.transaction() as tx:
        return [d for d in tx.all('documents') if d['team_id'] == actor['team_id']
                and (actor['role'] == 'team_lead' or d['owner_id'] == actor['id'])]


def get_document(db, actor, identity):
    with db.transaction() as tx:
        doc = tx.get('documents', identity)
        require_access(actor, doc)
        return doc


def create_document(db, actor, payload):
    validate_editor(payload['content'])
    with db.transaction() as tx:
        period = tx.get('periods', payload['period_id'])
        require_window(period, actor, utcnow())
        doc = {**payload, 'id': str(uuid4()), 'owner_id': actor['id'],
               'owner_name': actor['name'], 'team_id': actor['team_id'], 'status': 'draft',
               'revision': 1, 'version_no': 1, 'parent_id': None, 'created_at': iso_now(),
               'content_hash': content_hash(payload['content']), 'export': None}
        tx.put('documents', doc)
        tx.audit(actor, 'document.created', doc['id'], None, summary(doc))
        return doc


def save_document(db, actor, identity, payload):
    validate_editor(payload['content'])
    with db.transaction() as tx:
        doc = tx.get('documents', identity)
        require_owner(actor, doc)
        require_draft(doc)
        require_revision(doc['revision'], payload['expected_revision'])
        require_window(tx.get('periods', doc['period_id']), actor, utcnow())
        before = summary(doc)
        doc.update(title=payload['title'], content=payload['content'],
                   content_hash=content_hash(payload['content']), revision=doc['revision'] + 1,
                   export=None)
        tx.put('documents', doc)
        tx.audit(actor, 'document.saved', identity, before, summary(doc))
        return doc


def submit(db, actor, identity, expected):
    with db.transaction() as tx:
        doc = tx.get('documents', identity)
        require_owner(actor, doc)
        require_draft(doc)
        require_revision(doc['revision'], expected)
        require_window(tx.get('periods', doc['period_id']), actor, utcnow())
        if any(f['blocking'] for f in rule_checks(doc)):
            raise DomainError('RULE_CHECK_FAILED', 'Bổ sung tên và nội dung trước khi nộp.', 422)
        if not doc.get('export') or doc['export']['content_hash'] != doc['content_hash']:
            raise DomainError('PREVIEW_REQUIRED', 'Tạo và xem bản Word của nội dung hiện tại trước khi nộp.', 409)
        before = summary(doc)
        doc.update(status='submitted', submitted_at=iso_now(), revision=doc['revision'] + 1)
        tx.put('documents', doc)
        tx.audit(actor, 'document.submitted', identity, before, summary(doc))
        return doc


def decide(db, actor, identity, payload):
    require_lead(actor)
    with db.transaction() as tx:
        doc = tx.get('documents', identity)
        require_access(actor, doc)
        require_revision(doc['revision'], payload['expected_revision'])
        if doc['owner_id'] == actor['id']:
            raise DomainError('SELF_APPROVAL', 'Không tự duyệt hồ sơ do mình soạn.', 403)
        if doc['status'] != 'submitted':
            raise DomainError('INVALID_STATUS', 'Hồ sơ không ở trạng thái chờ duyệt.', 409)
        before = summary(doc)
        decision = payload['decision']
        doc.update(status='approved' if decision == 'approve' else 'changes_requested',
                   revision=doc['revision'] + 1, review_note=payload['reason'],
                   reviewed_by=actor['id'], reviewed_at=iso_now())
        tx.put('documents', doc)
        tx.audit(actor, f'document.{decision}', identity, before, summary(doc), payload['reason'])
        return doc


def revise(db, actor, identity, expected):
    with db.transaction() as tx:
        old = tx.get('documents', identity)
        require_owner(actor, old)
        require_revision(old['revision'], expected)
        if old['status'] not in {'approved', 'changes_requested'}:
            raise DomainError('INVALID_STATUS', 'Chỉ tạo bản sửa sau góp ý hoặc sau duyệt.', 409)
        require_window(tx.get('periods', old['period_id']), actor, utcnow())
        if any(d.get('parent_id') == identity for d in tx.all('documents')):
            raise DomainError('REVISION_EXISTS', 'Đã có phiên bản tiếp theo; hãy mở bản đó.', 409)
        new = deepcopy(old)
        for key in ('reviewed_by', 'reviewed_at', 'review_note', 'submitted_at'):
            new.pop(key, None)
        new.update(id=str(uuid4()), status='draft', revision=1, parent_id=identity,
                   version_no=old['version_no'] + 1, export=None, created_at=iso_now())
        tx.put('documents', new)
        tx.audit(actor, 'document.revised', new['id'], {'parent_id': identity}, summary(new))
        return new
