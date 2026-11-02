from fastapi import APIRouter, Depends
from ..schemas import PaymentRequest
from ..security import current_user
from ..services.payment_service import create_payment

router = APIRouter(prefix="/api", tags=["Pagamenti"])


@router.post("/payments")
async def payments(data: PaymentRequest, user=Depends(current_user)):
    return await create_payment(data, user)
