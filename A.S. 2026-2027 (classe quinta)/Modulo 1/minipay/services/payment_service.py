"""Orchestrazione applicativa dei trasferimenti tra utenti."""
import secrets
from fastapi import HTTPException
from ..database import connect, now_iso, is_integrity_error
from ..integrations.core_banking import authorize_payment
from .notification_service import create_notification
from .wallet_service import money


async def create_payment(data, user):
    recipient_email = data.recipient_email.strip().lower()
    if recipient_email == user["email"].lower():
        raise HTTPException(status_code=400, detail="Non puoi inviare denaro a te stesso")
    amount_cents = int(round(data.amount * 100))
    if amount_cents <= 0:
        raise HTTPException(status_code=400, detail="Importo non valido")
    reference = data.reference or secrets.token_hex(12)

    with connect() as db:
        if db.execute("SELECT id FROM transactions WHERE id=?", (reference,)).fetchone():
            raise HTTPException(status_code=409, detail="Riferimento già utilizzato")
        recipient = db.execute(
            "SELECT id,email,name FROM users WHERE email=?", (recipient_email,)
        ).fetchone()
        if not recipient:
            raise HTTPException(status_code=404, detail="Destinatario non trovato")
        sender_wallet = db.execute(
            "SELECT balance_cents FROM wallets WHERE user_id=?", (user["id"],)
        ).fetchone()
        if not sender_wallet or sender_wallet["balance_cents"] < amount_cents:
            raise HTTPException(status_code=400, detail="Saldo insufficiente")

    # La chiamata al sistema bancario è isolata nel client integrations/core_banking.py.
    bank = await authorize_payment(
        reference=reference,
        amount_cents=amount_cents,
        sender_email=user["email"],
        recipient_email=recipient_email,
    )

    # Aggiornamento atomico dei due wallet e registrazione del movimento.
    try:
        with connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT id FROM transactions WHERE id=?", (reference,)).fetchone():
                raise HTTPException(status_code=409, detail="Riferimento già utilizzato")
            sender_wallet = db.execute(
                "SELECT balance_cents FROM wallets WHERE user_id=?", (user["id"],)
            ).fetchone()
            if not sender_wallet or sender_wallet["balance_cents"] < amount_cents:
                raise HTTPException(status_code=400, detail="Saldo insufficiente")
            db.execute("UPDATE wallets SET balance_cents=balance_cents-? WHERE user_id=?",
                       (amount_cents, user["id"]))
            db.execute("UPDATE wallets SET balance_cents=balance_cents+? WHERE user_id=?",
                       (amount_cents, recipient["id"]))
            db.execute(
                "INSERT INTO transactions(id,sender_id,recipient_id,amount_cents,status,bank_reference,created_at) "
                "VALUES(?,?,?,?,?,?,?)",
                (reference, user["id"], recipient["id"], amount_cents, "COMPLETATO",
                 bank.get("bank_reference"), now_iso()),
            )
            db.execute(
                "INSERT INTO notifications(user_id,message,created_at) VALUES(?,?,?)",
                (user["id"], f"Pagamento di {money(amount_cents):.2f} € inviato a {recipient_email}.", now_iso()),
            )
            db.execute(
                "INSERT INTO notifications(user_id,message,created_at) VALUES(?,?,?)",
                (recipient["id"], f"Hai ricevuto {money(amount_cents):.2f} € da {user['email']}.", now_iso()),
            )
    except Exception as exc:
        if is_integrity_error(exc):
            raise HTTPException(status_code=409, detail="Impossibile registrare la transazione") from exc
        raise

    return {
        "id": reference, "status": "COMPLETATO", "amount": money(amount_cents),
        "recipient": recipient_email, "bank_reference": bank.get("bank_reference"),
        "message": "Pagamento completato",
    }
