"""Hash password, firma dei token e dipendenza per l'utente autenticato."""
import hashlib
import hmac
import secrets
from typing import Optional
from fastapi import Header, HTTPException
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from .config import SECRET_KEY, SESSION_MAX_AGE_SECONDS
from .database import connect

serializer = URLSafeTimedSerializer(SECRET_KEY, salt="minipay-session")


def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return salt.hex() + "$" + digest.hex()


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), 200_000
        ).hex()
        return hmac.compare_digest(candidate, digest_hex)
    except (ValueError, TypeError):
        return False


def create_token(user_id: int) -> str:
    return serializer.dumps({"user_id": user_id})


def current_user(authorization: Optional[str] = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Accedi per continuare")
    try:
        payload = serializer.loads(
            authorization[7:], max_age=SESSION_MAX_AGE_SECONDS
        )
        user_id = int(payload["user_id"])
    except (BadSignature, SignatureExpired, KeyError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Sessione non valida o scaduta")
    with connect() as db:
        user = db.execute(
            "SELECT id, name, email FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="Utente non trovato")
    return dict(user)
