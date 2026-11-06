from datetime import datetime, timezone

from app.core.errors import DomainError


def require_lead(actor: dict) -> None:
    if actor['role'] != 'team_lead':
        raise DomainError('FORBIDDEN', 'Chỉ tổ trưởng được thực hiện.', 403)


def require_access(actor: dict, document: dict) -> None:
    if document['team_id'] != actor['team_id'] or (
        actor['role'] != 'team_lead' and document['owner_id'] != actor['id']
    ):
        raise DomainError('NOT_FOUND', 'Không tìm thấy hồ sơ trong phạm vi quyền.', 404)


def require_owner(actor: dict, document: dict) -> None:
    require_access(actor, document)
    if document['owner_id'] != actor['id']:
        raise DomainError('FORBIDDEN', 'Chỉ người soạn được sửa nội dung.', 403)


def require_revision(actual: int, expected: int) -> None:
    if actual != expected:
        raise DomainError('REVISION_CONFLICT', 'Có bản mới hơn. Hãy tải lại trước khi sửa.', 409)


def require_window(period: dict, actor: dict, now: datetime) -> None:
    if period['team_id'] != actor['team_id'] or actor['id'] not in period['participants']:
        raise DomainError('FORBIDDEN', 'Bạn không được phân công trong đợt này.', 403)
    override = period.get('overrides', {}).get(actor['id'])
    deadline = (override['allowed_until'] if override and not override.get('revoked')
                else period['due_at'])
    if now.tzinfo is None:
        raise ValueError('Clock must be timezone-aware')
    if period.get('closed') or now.astimezone(timezone.utc) >= datetime.fromisoformat(deadline):
        raise DomainError('DEADLINE_LOCKED', 'Đã khóa theo hạn. Xin tổ trưởng mở cửa sổ sửa.', 423)


def require_draft(document: dict) -> None:
    if document['status'] != 'draft':
        raise DomainError('IMMUTABLE_VERSION', 'Bản đã nộp không sửa tại chỗ. Tạo phiên bản mới.', 409)
