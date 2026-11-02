"""Gestione delle notifiche persistite nel database (non invia email/SMS)."""
from ..database import connect, now_iso


def create_notification(user_id: int, message: str) -> None:
    with connect() as db:
        db.execute(
            "INSERT INTO notifications(user_id,message,created_at) VALUES(?,?,?)",
            (user_id, message, now_iso()),
        )


def list_notifications(user_id: int):
    with connect() as db:
        rows = db.execute(
            "SELECT id,message,created_at,is_read FROM notifications "
            "WHERE user_id=? ORDER BY id DESC LIMIT 30", (user_id,)
        ).fetchall()
    return [dict(row) for row in rows]
