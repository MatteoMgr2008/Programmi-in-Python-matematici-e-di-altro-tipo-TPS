"""Configurazione MiniPay."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
DB_BACKEND = os.getenv("MINIPAY_DB_BACKEND", "mysql").strip().lower()
DB_PATH = os.getenv("MINIPAY_DB", str(BASE_DIR / "minipay_test.db"))
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "minipay_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "minipay")
BANK_URL = os.getenv("BANKING_URL", "http://127.0.0.1:8001").rstrip("/")
SECRET_KEY = os.getenv("MINIPAY_SECRET", "solo-per-demo-cambiare-in-produzione")
SESSION_MAX_AGE_SECONDS = 60 * 60 * 8

if DB_BACKEND not in {"mysql", "sqlite"}:
    raise ValueError("MINIPAY_DB_BACKEND deve essere 'mysql' oppure 'sqlite'")
