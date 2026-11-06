from app.core.clock import utcnow, iso_now
from app.core.errors import DomainError
from app.domain.policies import require_lead, require_revision


def grant_override(db, actor: dict, period_id: str, payload: dict) -> dict:
    from datetime import datetime
    require_lead(actor)
    until = datetime.fromisoformat(payload['allowed_until'])
    if until.tzinfo is None or until <= utcnow():
        raise DomainError('INVALID_DEADLINE', 'Hạn mới phải có múi giờ và nằm trong tương lai.', 422)
    with db.transaction() as tx:
        period = tx.get('periods', period_id)
        if period['team_id'] != actor['team_id']:
            raise DomainError('NOT_FOUND', 'Không tìm thấy đợt.', 404)
        require_revision(period['revision'], payload['expected_revision'])
        if payload['user_id'] not in period['participants']:
            raise DomainError('NOT_PARTICIPANT', 'Người được gia hạn không thuộc đợt.', 422)
        previous = period.get('overrides', {}).get(payload['user_id'])
        period.setdefault('overrides', {})[payload['user_id']] = {
            'allowed_until': until.isoformat(), 'reason': payload['reason'],
            'granted_by': actor['id'], 'granted_at': iso_now(), 'revoked': False}
        period['revision'] += 1
        tx.put('periods', period)
        tx.audit(actor, 'deadline.granted', period_id, previous,
                 period['overrides'][payload['user_id']], payload['reason'])
        return period
