from __future__ import annotations
import hmac

def admin_credentials(streamlit_secrets) -> tuple[str|None, str|None]:
    try:
        admin = streamlit_secrets["admin"]
        return str(admin.get("username", "")), str(admin.get("password", ""))
    except Exception:
        return None, None

def authenticate(username: str, password: str, expected_user: str|None, expected_password: str|None) -> bool:
    if not expected_user or not expected_password:
        return False
    return hmac.compare_digest(username, expected_user) and hmac.compare_digest(password, expected_password)
