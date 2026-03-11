from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.exceptions import AppException

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash of *plain_password*."""
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if *plain_password* matches *hashed_password*."""
    return _pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT tokens
# ---------------------------------------------------------------------------

_TOKEN_TYPE_ACCESS = "access"
_TOKEN_TYPE_REFRESH = "refresh"


def create_access_token(
    subject: str,
    *,
    algorithm: str,
    secret_key: str,
    expires_minutes: int,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a signed JWT access token for *subject* (typically the user UUID)."""
    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
        "type": _TOKEN_TYPE_ACCESS,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def create_refresh_token(
    subject: str,
    *,
    algorithm: str,
    secret_key: str,
    expires_days: int,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a signed JWT refresh token for *subject*."""
    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": now + timedelta(days=expires_days),
        "type": _TOKEN_TYPE_REFRESH,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def verify_token(
    token: str,
    *,
    algorithm: str,
    secret_key: str,
    expected_type: str = _TOKEN_TYPE_ACCESS,
) -> dict[str, Any]:
    """Decode and validate *token*; raise AppException on failure.

    Returns the decoded payload dict.
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
    except JWTError as exc:
        raise AppException(f"Invalid or expired token: {exc}") from exc

    if payload.get("type") != expected_type:
        raise AppException(
            f"Token type mismatch: expected '{expected_type}', got '{payload.get('type')}'"
        )

    sub = payload.get("sub")
    if not sub:
        raise AppException("Token is missing 'sub' claim")

    return payload


# ---------------------------------------------------------------------------
# Fernet encryption for OAuth tokens stored at rest
# ---------------------------------------------------------------------------


def _get_fernet(key: str) -> Fernet:
    """Return a Fernet instance from a base64-url-encoded 32-byte *key*."""
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_token(plain_token: str, *, encryption_key: str) -> str:
    """Encrypt *plain_token* with Fernet symmetric encryption.

    Returns a URL-safe base64-encoded ciphertext string.
    """
    fernet = _get_fernet(encryption_key)
    return fernet.encrypt(plain_token.encode()).decode()


def decrypt_token(encrypted_token: str, *, encryption_key: str) -> str:
    """Decrypt a Fernet-encrypted *encrypted_token*.

    Raises AppException if decryption fails (e.g. wrong key or tampered data).
    """
    fernet = _get_fernet(encryption_key)
    try:
        return fernet.decrypt(encrypted_token.encode()).decode()
    except Exception as exc:
        raise AppException(f"Failed to decrypt token: {exc}") from exc
