from fastapi import Request

from app.core.errors import DomainError


def current_user(request: Request) -> dict:
    # No passwords are bypassed in production: the application refuses non-demo mode.
    # This picker is intentionally confined to a loopback demo, not an authentication solution.
    if request.client and request.client.host not in {'127.0.0.1', '::1', 'testclient'}:
        raise DomainError('LOCAL_DEMO_ONLY', 'Demo chỉ nhận kết nối cục bộ.', 403)
    user_id = request.headers.get('X-Demo-User', 'teacher-1')
    with request.app.state.db.transaction() as tx:
        return tx.get('users', user_id)
