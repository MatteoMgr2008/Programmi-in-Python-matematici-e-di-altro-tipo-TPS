"""Lettura di saldo, movimenti e notifiche dell'utente."""
from ..database import connect
from .notification_service import list_notifications


def money(cents: int) -> float:
    return round(cents / 100, 2)


def get_wallet(user_id: int):
    with connect() as db:
        row = db.execute(
            "SELECT balance_cents FROM wallets WHERE user_id = ?", (user_id,)
        ).fetchone()
    if not row:
        return {"balance": 0.0, "currency": "EUR"}
    return {"balance": money(row["balance_cents"]), "currency": "EUR"}


def list_transactions(user_id: int):
    with connect() as db:
        rows = db.execute("""
            SELECT t.id, t.amount_cents, t.status, t.created_at, t.bank_reference,
                   s.email AS sender_email, r.email AS recipient_email, t.sender_id
            FROM transactions t
            JOIN users s ON s.id=t.sender_id
            JOIN users r ON r.id=t.recipient_id
            WHERE t.sender_id=? OR t.recipient_id=?
            ORDER BY t.created_at DESC LIMIT 50
        """, (user_id, user_id)).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["amount"] = money(item.pop("amount_cents"))
        item["direction"] = "out" if item.pop("sender_id") == user_id else "in"
        result.append(item)
    return result


def get_notifications(user_id: int):
    return list_notifications(user_id)
