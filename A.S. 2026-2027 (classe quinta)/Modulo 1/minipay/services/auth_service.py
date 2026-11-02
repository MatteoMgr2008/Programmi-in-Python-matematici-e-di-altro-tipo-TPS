"""Regole applicative per registrazione e login."""
from fastapi import HTTPException
from ..database import connect, now_iso, create_user_record, is_integrity_error
from ..security import hash_password, verify_password, create_token
from .notification_service import create_notification


def register_user(data):
    name = data.name.strip()
    email = data.email.strip().lower()
    if not name:
        raise HTTPException(status_code=422, detail="Inserisci un nome valido")
    try:
        with connect() as db:
            user_id = create_user_record(
                db, name, email, hash_password(data.password), now_iso()
            )
            db.execute(
                "INSERT INTO wallets(user_id,balance_cents) VALUES(?,10000)",
                (user_id,),
            )
            db.execute(
                "INSERT INTO notifications(user_id,message,created_at) VALUES(?,?,?)",
                (user_id, "Benvenuto su MiniPay! Hai ricevuto 100,00 € virtuali demo.", now_iso()),
            )
    except Exception as exc:
        if is_integrity_error(exc):
            raise HTTPException(status_code=409, detail="Questa email è già registrata") from exc
        raise
    return {"token": create_token(user_id), "user": {"id": user_id, "name": name, "email": email}}


def login_user(data):
    with connect() as db:
        user = db.execute(
            "SELECT * FROM users WHERE email = ?", (data.email.strip().lower(),)
        ).fetchone()
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email o password non corretti")
    return {
        "token": create_token(user["id"]),
        "user": {"id": user["id"], "name": user["name"], "email": user["email"]},
    }
