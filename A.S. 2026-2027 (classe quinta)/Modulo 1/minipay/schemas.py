"""Modelli SQLModel condivisi per validare i payload delle API."""

from typing import Optional
import math

from sqlmodel import SQLModel, Field
from pydantic import EmailStr, field_validator

class RegisterRequest(SQLModel):
    name: str = Field(min_length=2, max_length=60)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(SQLModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class PaymentRequest(SQLModel):
    recipient_email: EmailStr
    amount: float = Field(gt=0, le=50000)
    reference: Optional[str] = Field(
        default=None,
        min_length=8,
        max_length=80
    )

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("L'importo deve essere un numero finito")
        return value
