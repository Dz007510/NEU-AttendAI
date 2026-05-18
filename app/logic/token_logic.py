import secrets
from datetime import datetime, timedelta
from typing import Optional

_active: dict = {}
TTL = 120  # 2 minutes


def generate_token(course_id: str) -> dict:
    token  = secrets.token_hex(16)
    expiry = datetime.now() + timedelta(seconds=TTL)
    _active[course_id] = {"token": token, "expires_at": expiry}
    return {
        "token":      token,
        "expires_at": expiry.isoformat(),
        "qr_data":    f"neu://attend?course={course_id}&token={token}",
    }


def verify_token(course_id: str, token: str) -> bool:
    entry = _active.get(course_id)
    if not entry:
        return False
    if datetime.now() > entry["expires_at"]:
        _active.pop(course_id, None)
        return False
    return entry["token"] == token


def get_active_token(course_id: str) -> Optional[str]:
    entry = _active.get(course_id)
    if entry and datetime.now() <= entry["expires_at"]:
        return entry["token"]
    return None
