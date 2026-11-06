import json


def events(db, actor, object_id=None):
    with db.transaction() as tx:
        rows = tx.connection.execute('SELECT payload FROM audit ORDER BY rowid DESC').fetchall()
        result = []
        for row in rows:
            event = json.loads(row[0])
            if event['team_id'] != actor['team_id']:
                continue
            if actor['role'] != 'team_lead' and event['actor_id'] != actor['id']:
                # Basic starter scope: teachers see their own actions, not other teachers' activity.
                continue
            if object_id and event['object_id'] != object_id:
                continue
            result.append(event)
        return result[:200]
