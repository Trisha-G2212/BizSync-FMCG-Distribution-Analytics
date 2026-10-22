"""
JWT token utilities.

WHY JWT (JSON Web Tokens) INSTEAD OF SERVER-SIDE SESSIONS: a JWT is a
signed, self-contained token — the server can verify it's authentic
(via the signature) without looking anything up in a database or
session store. This matters for a REST API meant to scale horizontally:
any backend instance can verify any token using just the shared secret
key, with zero shared session state between instances.

WHAT'S INSIDE THE TOKEN: we deliberately keep the payload minimal —
just the user's id, email, and role ("claims"). The frontend decodes
none of this itself; it just stores the token and sends it back on
every request via the Authorization header. Only the backend needs to
understand what's inside.

INTERVIEW ANSWER: "How does authentication work end-to-end?" -> "On
login, the backend verifies the password against the bcrypt hash, then
issues a signed JWT containing the user's id/email/role with an
expiry. The frontend stores this and sends it as a Bearer token on
every request. A FastAPI dependency (get_current_user) decodes and
verifies the signature on each request, rejecting anything expired,
tampered with, or missing entirely — this is what makes protected
routes actually protected, not just hidden."
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError

from app.config import settings


def create_access_token(data: dict, expires_minutes: Optional[int] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.JWT_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Raises jose.JWTError if the token is invalid, tampered with, or expired."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
