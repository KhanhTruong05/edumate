from uuid import uuid4

from app.core.clock import utcnow, iso_now
from app.core.errors import DomainError
from app.domain.policies import require_window, require_lead


def submit_report(db, actor, period_id, payload):
    with db.transaction() as tx:
        period = tx.get('periods', period_id)
        require_window(period, actor, utcnow())
        if actor['id'] not in period.get('report_participants', period['participants']):
            raise DomainError('NOT_REPORT_PARTICIPANT', 'Tài khoản này không được giao nộp báo cáo trong kỳ.', 403)
        previous = [r for r in tx.all('reports') if r['period_id'] == period_id and r['owner_id'] == actor['id']]
        report = {**payload, 'id': str(uuid4()), 'period_id': period_id,
                  'owner_id': actor['id'], 'owner_name': actor['name'], 'team_id': actor['team_id'],
                  'version_no': 1 + max((r['version_no'] for r in previous), default=0),
                  'submitted_at': iso_now()}
        tx.put('reports', report)
        tx.audit(actor, 'report.submitted', report['id'],
                 {'previous_version': previous[0]['id']} if previous else None,
                 {'version_no': report['version_no'], 'assigned': report['assigned'], 'completed': report['completed']})
        return report


def aggregate(db, actor, period_id):
    require_lead(actor)
    with db.transaction() as tx:
        period = tx.get('periods', period_id)
        if period['team_id'] != actor['team_id']:
            raise DomainError('NOT_FOUND', 'Không tìm thấy kỳ.', 404)
        # Sources are immutable report versions; select one latest version per participant.
        participants = period.get('report_participants', period['participants'])
        selected = {}
        for report in tx.all('reports'):
            if report['period_id'] != period_id or report['owner_id'] not in participants:
                continue
            prior = selected.get(report['owner_id'])
            if prior is None or report['version_no'] > prior['version_no']:
                selected[report['owner_id']] = report
        sources = list(selected.values())
        eligible = [r for r in sources if r['assigned'] is not None and r['completed'] is not None]
        assigned = sum(r['assigned'] for r in eligible)
        completed = sum(r['completed'] for r in eligible)
        result = {'id': str(uuid4()), 'period_id': period_id, 'created_at': iso_now(),
                  'team_id': actor['team_id'], 'owner_id': actor['id'],
                  'source_ids': [r['id'] for r in sources], 'submitted_count': len(sources),
                  'expected_count': len(participants),
                  'missing_user_ids': [u for u in participants if u not in selected],
                  'metrics': {'assigned': assigned, 'completed': completed,
                              'completion_rate': completed / assigned if assigned else None,
                              'eligible_count': len(eligible),
                              'unique_activity_count': len({code for r in sources for code in r['activity_codes']})},
                  'narrative_status': 'not_generated',
                  'note': 'Số liệu được tính bằng mã. Chưa có nhận xét AI hoặc bước duyệt báo cáo tổ.'}
        tx.put('aggregates', result)
        tx.audit(actor, 'report.aggregated', result['id'], None,
                 {'source_ids': result['source_ids'], 'metrics': result['metrics']})
        return result
