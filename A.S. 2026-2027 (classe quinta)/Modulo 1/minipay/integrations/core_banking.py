"""Client HTTP per il servizio esterno che simula il core banking."""
import httpx
from fastapi import HTTPException
from ..config import BANK_URL


async def authorize_payment(*, reference: str, amount_cents: int,
                            sender_email: str, recipient_email: str):
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.post(
                f"{BANK_URL}/authorize",
                json={
                    "reference": reference,
                    "amount": amount_cents / 100,
                    "currency": "EUR",
                    "sender_email": sender_email,
                    "recipient_email": recipient_email,
                },
            )
            response.raise_for_status()
            result = response.json()
    except (httpx.HTTPError, ValueError):
        raise HTTPException(status_code=503, detail="Core banking demo non raggiungibile")
    if not result.get("approved"):
        raise HTTPException(status_code=402, detail=result.get("message", "Pagamento rifiutato"))
    return result
