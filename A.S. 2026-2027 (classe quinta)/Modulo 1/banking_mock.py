"""Mock HTTP separato che rappresenta il fornitore esterno di core banking."""
from fastapi import FastAPI
from sqlmodel import SQLModel, Field

app = FastAPI(title="MiniPay Core Banking Mock", version="1.1")


class AuthorizationRequest(SQLModel):
    reference: str = Field(min_length=1, max_length=80)
    amount: float = Field(gt=0, allow_inf_nan=False)
    currency: str = "EUR"
    sender_email: str
    recipient_email: str


class AuthorizationResponse(SQLModel):
    approved: bool
    bank_reference: str
    message: str


@app.get("/health")
def health():
    return {"service": "core-banking-mock", "status": "up"}


@app.post("/authorize", response_model=AuthorizationResponse)
def authorize(request: AuthorizationRequest):
    # Regola didattica: il mock rifiuta importi oltre 5.000 EUR.
    # Non è un'autorizzazione bancaria reale.
    if request.amount > 5000:
        return AuthorizationResponse(
            approved=False,
            bank_reference=f"BANK-{request.reference}",
            message="Rifiutato dal core banking demo: limite superato",
        )
    return AuthorizationResponse(
        approved=True,
        bank_reference=f"BANK-{request.reference}",
        message="Operazione approvata dal core banking demo",
    )
