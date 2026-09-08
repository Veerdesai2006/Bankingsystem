from datetime import datetime, timedelta, UTC
from typing import Any

from jose import JWTError, jwt
from pwdlib import PasswordHash

from app.core.config import settings


# ─── Password Hashing ─────────────────────────────────────────────────────────
#
# We use Argon2 — the winner of the 2015 Password Hashing Competition.
# It is the recommended algorithm for hashing passwords today.
# PasswordHash.recommended() automatically selects the best available algorithm.
#
_password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Convert a plain-text password into a secure, one-way hash.

    WHAT IS A HASH?
    ────────────────
    A hash is a transformation that:
      - Always produces the same output for the same input
      - Cannot be reversed (you cannot get the password back from the hash)
      - Changes completely if even one character of the input changes

    Example:
        "mysecret123"  →  "$argon2id$v=19$m=65536,t=3,p=4$abc123..."

    We ALWAYS store the hash, NEVER the original password.
    Even if the database is stolen, attackers only see useless hashes.
    """
    return _password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check whether a plain-text password matches a stored hash.

    HOW LOGIN WORKS:
    ─────────────────
    1. User types password → "mysecret123"
    2. We hash it again    → "$argon2id$..."
    3. Compare to stored   → match? → logged in ✓
    4.                     → no match? → wrong password ✗

    We NEVER unhash. We re-hash and compare.
    """
    return _password_hasher.verify(plain_password, hashed_password)


# ─── JSON Web Tokens (JWT) ────────────────────────────────────────────────────
#
# WHAT IS A JWT?
# ───────────────
# HTTP is "stateless" — the server forgets you between requests.
# JWTs solve this: after login, the server gives you a signed "passport."
# You present this passport with every request to prove who you are.
#
# A JWT looks like this:
#   eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.abc123
#   ─────────────────────.───────────────.──────
#        Header              Payload       Signature
#
# The PAYLOAD contains: { "sub": "1", "exp": 1234567890, "iat": ... }
# The SIGNATURE is: HMAC-SHA256(Header + Payload, SECRET_KEY)
#
# Anyone can READ the payload (it's just Base64 encoded, not encrypted).
# But only our server can CREATE a valid signature (because only we know SECRET_KEY).
# If someone tampers with the payload, the signature becomes invalid.
#


def create_access_token(subject: Any, expires_delta: timedelta | None = None) -> str:
    """
    Create a signed JWT that identifies a logged-in user.

    Args:
        subject:       Typically the user's database ID (e.g., 1, 2, 3...)
        expires_delta: How long the token is valid (defaults to settings value)

    Returns:
        A JWT string like "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

    PAYLOAD FIELDS:
    ────────────────
        sub: "subject" — who the token is FOR (the user's ID as a string)
        exp: "expiry"  — Unix timestamp when the token stops being valid
        iat: "issued at" — when the token was created
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    expire = datetime.now(UTC) + expires_delta

    payload = {
        "sub": str(subject),       # Always convert to string for JWT compatibility
        "exp": expire,
        "iat": datetime.now(UTC),
    }

    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict | None:
    """
    Verify and decode a JWT. Returns the payload dict if valid, None if not.

    This is called on EVERY protected request.
    It checks:
      1. Has the token been tampered with? (signature validation)
      2. Has the token expired? (exp field)

    If either check fails, the user is treated as unauthenticated.
    We return None (not raise) so callers can decide what to do.
    """
    try:
        payload: dict = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        return payload
    except JWTError:
        return None
