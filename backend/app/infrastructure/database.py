import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from app.core.clock import iso_now
from app.core.errors import DomainError


class Transaction:
    def __init__(self, connection):
        self.connection = connection

    def get(self, kind: str, identity: str) -> dict:
        row = self.connection.execute('SELECT payload FROM entities WHERE kind=? AND id=?', (kind, identity)).fetchone()
        if row is None:
            raise DomainError('NOT_FOUND', 'Không tìm thấy dữ liệu.', 404)
        return json.loads(row[0])

    def all(self, kind: str) -> list[dict]:
        return [json.loads(row[0]) for row in self.connection.execute(
            'SELECT payload FROM entities WHERE kind=? ORDER BY rowid DESC', (kind,))]

    def put(self, kind: str, value: dict) -> dict:
        self.connection.execute('INSERT INTO entities(kind,id,payload) VALUES(?,?,?) '
                                'ON CONFLICT(kind,id) DO UPDATE SET payload=excluded.payload',
                                (kind, value['id'], json.dumps(value, ensure_ascii=False)))
        return value

    def audit(self, actor: dict, action: str, object_id: str, before=None, after=None, reason='') -> None:
        event = {'id': str(uuid4()), 'actor_id': actor['id'], 'actor_name': actor['name'],
                 'actor_role': actor['role'], 'team_id': actor['team_id'], 'action': action,
                 'object_id': object_id, 'before': before, 'after': after,
                 'reason': reason, 'occurred_at': iso_now()}
        self.connection.execute('INSERT INTO audit(id,payload) VALUES(?,?)',
                                (event['id'], json.dumps(event, ensure_ascii=False)))


class Database:
    """Local demo repository. Firebase adapters are kept separate, not silently substituted."""
    def __init__(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / 'edumate.sqlite3'
        with self.transaction() as tx:
            tx.connection.executescript('''
                CREATE TABLE IF NOT EXISTS entities(kind TEXT,id TEXT,payload TEXT,PRIMARY KEY(kind,id));
                CREATE TABLE IF NOT EXISTS audit(id TEXT PRIMARY KEY,payload TEXT);
                CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit
                BEGIN SELECT RAISE(ABORT,'Audit is append-only'); END;
                CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit
                BEGIN SELECT RAISE(ABORT,'Audit is append-only'); END;
            ''')

    @contextmanager
    def transaction(self):
        connection = sqlite3.connect(self.path, timeout=10)
        try:
            connection.execute('BEGIN IMMEDIATE')
            yield Transaction(connection)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
