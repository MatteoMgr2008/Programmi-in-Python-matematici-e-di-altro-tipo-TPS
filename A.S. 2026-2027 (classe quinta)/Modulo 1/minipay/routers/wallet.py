from fastapi import APIRouter, Depends
from ..security import current_user
from ..services.wallet_service import get_wallet, list_transactions, get_notifications

router = APIRouter(prefix="/api", tags=["Portafoglio e attività"])


@router.get("/wallet")
def wallet(user=Depends(current_user)):
    return get_wallet(user["id"])


@router.get("/transactions")
def transactions(user=Depends(current_user)):
    return list_transactions(user["id"])


@router.get("/notifications")
def notifications(user=Depends(current_user)):
    return get_notifications(user["id"])
