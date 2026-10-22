"""
Password hashing.

WHY BCRYPT DIRECTLY (not via passlib): bcrypt is a deliberately slow,
salted hashing algorithm designed for passwords — unlike a fast hash
(MD5, SHA256), it's computationally expensive to brute-force, and the
salt is stored inside the hash string itself, so no separate salt
column is needed.

We call the `bcrypt` library directly rather than through passlib's
CryptContext wrapper: passlib's bcrypt backend detection has a known
incompatibility with recent bcrypt releases (it looks for an internal
`__about__.__version__` attribute that newer bcrypt versions removed).
Calling bcrypt's `hashpw`/`checkpw` directly avoids that entirely and
is only a few lines of code either way.

This file is used by seed_data.py now (Phase 3, so seeded users have
real credentials) and will be reused unchanged by the login/register
endpoints in Phase 5.
"""
import bcrypt


def hash_password(plain_password: str) -> str:
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
