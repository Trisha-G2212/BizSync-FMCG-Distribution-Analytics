"""
Authentication & authorization dependencies.

WHY THIS LIVES SEPARATELY FROM auth_service.py: auth_service handles
LOGIN (verifying credentials, issuing a token). This file handles
PROTECTING ROUTES — reading a token FROM an already-authenticated
request and deciding whether that request is allowed to proceed. They
run at completely different times: auth_service runs once at login;
get_current_user/require_role run on EVERY request to a protected
endpoint.

HOW get_current_user WORKS: OAuth2PasswordBearer tells FastAPI to look
for `Authorization: Bearer <token>` on incoming requests and extracts
just the token part. We decode it, verify the signature/expiry, and
look up the user it refers to. Any protected route just adds
`current_user: CurrentUser = Depends(get_current_user)` as a parameter
— FastAPI runs this dependency before the route body executes, so an
invalid token never reaches business logic at all.

HOW require_role WORKS: it's a dependency FACTORY — calling
require_role(UserRole.ADMIN) returns a new dependency function
tailored to that specific role check, which the route function then
depends on. This is what makes "ADMIN: full access, ANALYST: read-only"
(spec section 26) an enforced rule rather than a paper policy.
"""
from typing import Iterable
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.enums import UserRole
from app.utils.jwt import decode_access_token
from app.schemas.auth import CurrentUser

# WHY HTTPBearer INSTEAD OF OAuth2PasswordBearer: OAuth2PasswordBearer
# makes Swagger render an OAuth2-style username/password form that
# submits as x-www-form-urlencoded — but our /auth/login endpoint takes
# JSON (email/password), matching the spec's LoginRequest schema. That
# mismatch would make Swagger's built-in "Authorize" form submit
# incorrectly against our real endpoint. HTTPBearer instead makes
# Swagger show one plain "paste your token" field, matching the actual
# flow: call /auth/login separately, copy the returned token, paste it
# into Authorize.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise credentials_error
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise credentials_error

    user = db.get(User, user_id)
    if user is None:
        raise credentials_error

    return CurrentUser.model_validate(user)


def require_role(*allowed_roles: Iterable[UserRole]):
    """Usage: Depends(require_role(UserRole.ADMIN, UserRole.SALES_MANAGER))"""
    def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role.value}' is not permitted to perform this action",
            )
        return current_user
    return dependency
