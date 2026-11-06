from uuid import uuid4

from app.core.clock import iso_now
from app.core.errors import DomainError
from app.domain.quality import verify_claims
from app.modules.agent.tools import collect_sources


async def draft(db, provider, actor, payload):
    sources = collect_sources(db, actor, payload['source_ids'])
    run = {'id': str(uuid4()), 'owner_id': actor['id'], 'team_id': actor['team_id'],
           'kind': payload['kind'], 'status': 'running', 'created_at': iso_now(),
           'source_ids': [s['id'] for s in sources]}
    with db.transaction() as tx:
        tx.put('agent_runs', run)
        tx.audit(actor, 'agent.started', run['id'], None, {'source_ids': run['source_ids']})
    try:
        result = await provider.draft(payload['kind'], payload['instructions'], sources)
        errors = verify_claims(result.get('claims', []), sources)
        run.update(status='rejected' if errors else 'needs_human_review',
                   completed_at=iso_now(), validation_errors=errors)
        if not errors:
            run['result'] = result
        # A valid quote is not a factual correctness guarantee. No output is auto-applied.
        run['notice'] = 'Bản AI đề xuất, chưa duyệt. Kiểm tra chuyên môn, sự kiện và số liệu trước khi sử dụng.'
    except DomainError as exc:
        run.update(status='failed', completed_at=iso_now(), error_code=exc.code)
        with db.transaction() as tx:
            tx.put('agent_runs', run)
            tx.audit(actor, 'agent.failed', run['id'], None, {'code': exc.code})
        raise
    with db.transaction() as tx:
        tx.put('agent_runs', run)
        tx.audit(actor, f'agent.{run["status"]}', run['id'], None, {'status': run['status']})
    return run
