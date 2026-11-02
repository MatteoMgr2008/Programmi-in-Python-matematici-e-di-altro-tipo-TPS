"""Punto d'ingresso: configura FastAPI e collega i router applicativi."""
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from minipay.config import BASE_DIR
from minipay.database import init_db
from minipay.routers import auth, wallet, payments

app = FastAPI(title="MiniPay API", version="2.0-modulare")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
init_db()

app.include_router(auth.router)
app.include_router(wallet.router)
app.include_router(payments.router)


@app.get("/")
def home():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "minipay-api"}
