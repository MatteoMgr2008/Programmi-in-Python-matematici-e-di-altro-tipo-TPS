from fastapi import APIRouter, Depends
from ..schemas import RegisterRequest, LoginRequest
from ..security import current_user
from ..services.auth_service import register_user, login_user

router = APIRouter(prefix="/api", tags=["Autenticazione"])


@router.post("/register", status_code=201)
def register(data: RegisterRequest):
    return register_user(data)


@router.post("/login")
def login(data: LoginRequest):
    return login_user(data)


@router.get("/me")
def me(user=Depends(current_user)):
    return user
