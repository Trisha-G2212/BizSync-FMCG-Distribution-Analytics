"""
Auth service.

WHY WE DON'T REVEAL WHETHER THE EMAIL OR PASSWORD WAS WRONG: returning
"email not found" vs "wrong password" as different errors lets an
attacker enumerate which emails have accounts. A single generic
InvalidCredentialsError, mapped to one 401 message by the router, is
standard security practice regardless of which part was actually wrong.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.utils.security import verify_password
from app.utils.jwt import create_access_token


class InvalidCredentialsError(Exception):
    pass


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError()
    return user


def create_token_for_user(user: User) -> str:
    return create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
    })
