import hmac

from fastapi import Request

from app.core.errors import DomainError


def current_user(request: Request) -> dict:
    # No passwords are bypassed in production: the application refuses non-demo mode.
    # Only local clients or the configured internal demo proxy may use this picker.
    if request.client and request.client.host not in {'127.0.0.1', '::1', 'testclient'}:
        expected = request.app.state.demo_proxy_token
        supplied = request.headers.get('X-Edumate-Proxy-Token', '')
        if not expected or not hmac.compare_digest(supplied.encode(), expected.encode()):
            raise DomainError('LOCAL_DEMO_ONLY', 'Demo chỉ nhận kết nối cục bộ hoặc proxy nội bộ.', 403)
    user_id = request.headers.get('X-Demo-User', 'teacher-1')
    with request.app.state.db.transaction() as tx:
        return tx.get('users', user_id)
