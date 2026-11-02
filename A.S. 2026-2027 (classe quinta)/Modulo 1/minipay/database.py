"""Accesso dati MiniPay tramite MySQL locale (PyMySQL)."""
import re
import sqlite3
from pathlib import Path
from datetime import datetime, timezone


from .config import DB_BACKEND, DB_PATH, MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE


class MySQLConnection:
    """Adatta PyMySQL all'interfaccia execute usata dai servizi MiniPay."""
    def __init__(self, connection):
        self._connection = connection

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type is None:
                self._connection.commit()
            else:
                self._connection.rollback()
        finally:
            self._connection.close()
        return False

    def execute(self, sql, params=()):
        sql = sql.strip()
        if sql.upper() == "BEGIN IMMEDIATE":
            self._connection.begin()
            return self._connection.cursor()
        # I servizi usano ? come segnaposto; PyMySQL usa %s.
        sql = re.sub(r"\?", "%s", sql)
        cursor = self._connection.cursor()
        cursor.execute(sql, tuple(params) if params else ())
        return cursor


def connect():
    if DB_BACKEND == "sqlite":
        connection = sqlite3.connect(DB_PATH, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    try:
        import pymysql
    except ImportError as exc:
        raise RuntimeError(
            "Driver MySQL mancante. Esegui `pip install -r requirements.txt`."
        ) from exc

    missing = [name for name, value in {
        "MYSQL_USER": MYSQL_USER,
        "MYSQL_PASSWORD": MYSQL_PASSWORD,
        "MYSQL_DATABASE": MYSQL_DATABASE,
    }.items() if not value]
    if missing:
        raise RuntimeError(
            "Configurazione MySQL incompleta nel file .env: " + ", ".join(missing)
        )

    connection = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        connect_timeout=10,
    )
    return MySQLConnection(connection)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def create_user_record(db, name, email, password_hash, created_at):
    cursor = db.execute(
        "INSERT INTO users(name,email,password_hash,created_at) VALUES(?,?,?,?)",
        (name, email, password_hash, created_at),
    )
    return cursor.lastrowid


def is_integrity_error(exc):
    if isinstance(exc, sqlite3.IntegrityError):
        return True
    try:
        import pymysql
        if isinstance(exc, pymysql.IntegrityError):
            return True
    except ImportError:
        pass
    # Codici MySQL: duplicato, vincolo FK e CHECK.
    error_code = exc.args[0] if getattr(exc, "args", None) else None
    return error_code in {1062, 1451, 1452, 3819}


def init_db():
    """Crea le tabelle MiniPay; SQLite resta disponibile per i test automatici."""
    if DB_BACKEND == "sqlite":
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        with connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS wallets (
                user_id INTEGER PRIMARY KEY REFERENCES users(id),
                balance_cents INTEGER NOT NULL DEFAULT 10000 CHECK(balance_cents >= 0)
            );
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                sender_id INTEGER NOT NULL REFERENCES users(id),
                recipient_id INTEGER NOT NULL REFERENCES users(id),
                amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
                status TEXT NOT NULL,
                bank_reference TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                message TEXT NOT NULL,
                created_at TEXT NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0
            );
            """)
        return

    statements = [
        """CREATE TABLE IF NOT EXISTS users (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(120) NOT NULL,
            email VARCHAR(254) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            created_at VARCHAR(40) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
        """CREATE TABLE IF NOT EXISTS wallets (
            user_id BIGINT UNSIGNED NOT NULL PRIMARY KEY,
            balance_cents BIGINT NOT NULL DEFAULT 10000,
            CONSTRAINT fk_wallet_user FOREIGN KEY (user_id) REFERENCES users(id),
            CONSTRAINT chk_wallet_balance CHECK (balance_cents >= 0)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
        """CREATE TABLE IF NOT EXISTS transactions (
            id VARCHAR(64) NOT NULL PRIMARY KEY,
            sender_id BIGINT UNSIGNED NOT NULL,
            recipient_id BIGINT UNSIGNED NOT NULL,
            amount_cents BIGINT NOT NULL,
            status VARCHAR(30) NOT NULL,
            bank_reference VARCHAR(120),
            created_at VARCHAR(40) NOT NULL,
            CONSTRAINT fk_transaction_sender FOREIGN KEY (sender_id) REFERENCES users(id),
            CONSTRAINT fk_transaction_recipient FOREIGN KEY (recipient_id) REFERENCES users(id),
            CONSTRAINT chk_transaction_amount CHECK (amount_cents > 0)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
        """CREATE TABLE IF NOT EXISTS notifications (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT UNSIGNED NOT NULL,
            message TEXT NOT NULL,
            created_at VARCHAR(40) NOT NULL,
            is_read TINYINT(1) NOT NULL DEFAULT 0,
            CONSTRAINT fk_notification_user FOREIGN KEY (user_id) REFERENCES users(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    ]
    with connect() as db:
        for statement in statements:
            db.execute(statement)
