# Configurare MySQL in locale

MiniPay usa MySQL locale tramite PyMySQL. Il database deve essere già installato e il servizio MySQL deve essere avviato.

## 1. Creare database e utente

Apri MySQL Workbench, collegati al server locale e apri una nuova scheda SQL. Esegui il contenuto di `infra/mysql/crea_database.sql`, sostituendo `SOSTITUISCI_CON_UNA_PASSWORD_SICURA` con una password scelta da te.

In alternativa, esegui lo stesso script dal client MySQL. Se l'utente `minipay_user` esiste già, puoi creare il database e assegnare i permessi con:

```sql
CREATE DATABASE IF NOT EXISTS minipay
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'minipay_user'@'127.0.0.1' IDENTIFIED BY 'LA_TUA_PASSWORD';
GRANT ALL PRIVILEGES ON minipay.* TO 'minipay_user'@'127.0.0.1';
FLUSH PRIVILEGES;
```

## 2. Configurare MiniPay

Nella cartella principale del progetto, copia `.env.example` in un nuovo file chiamato `.env`. Inserisci la stessa password impostata per `minipay_user`. Se MySQL usa una porta diversa da `3306`, modifica `MYSQL_PORT`.

Esempio:

```dotenv
MINIPAY_DB_BACKEND=mysql
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=minipay_user
MYSQL_PASSWORD=la_password_che_hai_scelto
MYSQL_DATABASE=minipay
MINIPAY_SECRET=una_chiave_lunga_e_casuale
BANKING_URL=http://127.0.0.1:8001
```

Non caricare `.env` su GitHub: è già escluso da `.gitignore`.

## 3. Installare dipendenze e avviare

Da PowerShell, nella cartella principale:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Avvia il mock del fornitore bancario nel primo terminale:

```powershell
uvicorn banking_mock:app --reload --port 8001
```

Avvia MiniPay nel secondo terminale:

```powershell
uvicorn app:app --reload --port 8000
```

Al primo avvio MiniPay crea automaticamente le tabelle `users`, `wallets`, `transactions` e `notifications` nel database `minipay`.

Apri http://127.0.0.1:8000.

## 4. Verificare i dati

In MySQL Workbench seleziona lo schema `minipay` e aggiorna la lista delle tabelle. Dopo aver registrato un utente nell'applicazione, puoi controllare i dati con:

```sql
USE minipay;
SELECT * FROM users;
SELECT * FROM wallets;
SELECT * FROM transactions;
SELECT * FROM notifications;
```

Il saldo e i pagamenti sono dimostrativi: MiniPay non movimenta denaro reale.
