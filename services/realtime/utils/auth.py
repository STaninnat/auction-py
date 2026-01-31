from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import jwt
from decouple import config
from fastapi import Query, WebSocket, status

SECRET_DIR = Path("/app/secrets")
PUBLIC_KEY_PATH = SECRET_DIR / "public_key.pem"


def get_public_key():
    try:
        with open(PUBLIC_KEY_PATH, "rb") as f:
            return f.read()
    except FileNotFoundError:
        print(f"CRITICAL: Public key not found at {PUBLIC_KEY_PATH}")
        return b""


VERIFY_KEY = get_public_key()

JWT_AUDIENCE = config("JWT_AUDIENCE", default="auction:realtime")
JWT_ISSUER = config("JWT_ISSUER", default="auction:core")


@dataclass
class AuthenticatedUser:
    id: str
    username: str = ""


async def get_current_user(websocket: WebSocket, token: Optional[str] = Query(None)) -> Optional[AuthenticatedUser]:
    """
    Dependency for authentication before accepting a WebSocket connection.
    """
    if token is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    try:
        payload = jwt.decode(
            token,
            VERIFY_KEY,
            algorithms=["RS256"],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
        )

        user_id = payload.get("user_id")
        username = payload.get("username", "")

        if user_id is None:
            raise Exception("Invalid authentication token")

        return AuthenticatedUser(id=user_id, username=username)

    except Exception as e:
        print(f"CRITICAL: Failed to authenticate WebSocket connection: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
