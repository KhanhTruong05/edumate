from datetime import timedelta

from app.core.clock import utcnow


def seed(db):
    with db.transaction() as tx:
        if tx.all('users'):
            return
        for i in range(1, 21):
            tx.put('users', {'id': f'teacher-{i}', 'name': f'Giáo viên {i}',
                             'role': 'teacher', 'team_id': 'team-demo'})
        for i, name in [(1, 'Tổ trưởng'), (2, 'Người duyệt thay')]:
            tx.put('users', {'id': f'lead-{i}', 'name': name, 'role': 'team_lead', 'team_id': 'team-demo'})
        tx.put('periods', {'id': 'period-demo', 'name': 'Đợt dùng thử — một tổ chuyên môn',
                           'team_id': 'team-demo', 'revision': 1, 'closed': False,
                           'due_at': (utcnow() + timedelta(days=7)).isoformat(),
                           'participants': [f'teacher-{i}' for i in range(1, 21)] + ['lead-1', 'lead-2'],
                           'report_participants': [f'teacher-{i}' for i in range(1, 21)],
                           'overrides': {}})
