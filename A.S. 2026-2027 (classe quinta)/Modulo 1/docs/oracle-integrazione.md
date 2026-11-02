# Collegare MiniPay a Oracle Autonomous AI Database (Always Free)

Questa guida configura MiniPay per collegarsi a un database Oracle ospitato su Oracle Cloud, senza installare Oracle Database sul PC e senza installare Oracle Instant Client. Il database rimane Oracle: SQLite è disponibile esclusivamente per test locali.

## 1. Creare il database su Oracle Cloud

1. Accedi a [Oracle Cloud](https://cloud.oracle.com/).
2. Crea un'istanza **Autonomous AI Database** e seleziona l'opzione **Always Free**, se disponibile nella tua tenancy e nella tua regione. Evita di creare una risorsa a pagamento.
3. Scegli un carico di lavoro adatto, ad esempio **Transaction Processing**.
4. Imposta la password amministrativa e attendi che il database sia disponibile.
5. Nella configurazione di rete abilita l'accesso dalla rete da cui eseguirai MiniPay. Per una prova puoi usare una regola di accesso IP; non lasciare il database aperto a tutto Internet. Se MiniPay verrà eseguito su AWS, consenti l'IP pubblico statico o l'egress previsto dal servizio AWS, oppure configura una rete privata secondo l'architettura scelta.

La disponibilità dell'opzione Always Free, le quote e le risorse dipendono dalla regione e dalla tenancy. La registrazione Oracle Cloud può richiedere una carta per la verifica. Controlla sempre il riepilogo dei costi prima di creare risorse.

## 2. Creare un utente dedicato a MiniPay

Apri **Database Actions** dalla pagina del database (è utilizzabile dal browser). Accedi come ADMIN e apri SQL. Crea un utente applicativo dedicato; sostituisci la password con una tua password robusta:

```sql
CREATE USER MINIPAY_USER IDENTIFIED BY "ScegliUnaPasswordForte";
GRANT CREATE SESSION, CREATE TABLE TO MINIPAY_USER;
ALTER USER MINIPAY_USER QUOTA UNLIMITED ON DATA;
```

Se il tablespace predefinito della tua istanza non si chiama `DATA`, verifica il nome corretto in Database Actions e adegua il comando QUOTA. Non usare l'utente ADMIN nell'applicazione.

Esci dalla sessione ADMIN e accedi a Database Actions con `MINIPAY_USER`. Esegui il contenuto del file `infra/oracle/schema_demo.sql` per creare le tabelle `USERS`, `WALLETS`, `TRANSACTIONS` e `NOTIFICATIONS`.

## 3. Copiare il connect string TLS (senza wallet)

1. Nella pagina del database Autonomous, apri **Database connection**.
2. Seleziona il tipo di connessione **TLS** / **TLS authentication** (non mTLS e non un alias che richiede wallet).
3. Copia il connect string completo fornito da Oracle. È normalmente un descrittore che usa `PROTOCOL=TCPS`, host, porta e nome del servizio. Non inventare o modificare host e servizio.

Con `python-oracledb` in Thin mode, il collegamento TLS può essere effettuato senza wallet e senza Oracle Instant Client. La libreria Python `oracledb` deve comunque essere installata con le dipendenze del progetto.

## 4. Configurare MiniPay

Nella cartella principale del progetto, copia `.env.example` in `.env`. Inserisci le credenziali dell'utente applicativo e incolla il connect string TLS copiato da OCI come valore di `ORACLE_DSN`. Mantienilo su un'unica riga. Esempio illustrativo (non utilizzare questi dati):

```dotenv
MINIPAY_DB_BACKEND=oracle
ORACLE_USER=MINIPAY_USER
ORACLE_PASSWORD=la_tua_password
ORACLE_DSN=(description=(retry_count=...)(address=(protocol=tcps)(host=...)(port=...))(connect_data=(service_name=...))(security=(ssl_server_dn_match=yes)))
ORACLE_CONNECT_TIMEOUT=15
MINIPAY_SECRET=una_chiave_casuale_lunga
BANKING_URL=http://127.0.0.1:8001
```

Non copiare l'esempio del DSN: usa esattamente il descrittore mostrato nella console OCI. Non inserire `.env` in Git e non condividere password o connect string con credenziali.

## 5. Installare e avviare MiniPay

Su Windows PowerShell, dalla cartella del progetto:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Avvia il mock del servizio bancario in un primo terminale:

```powershell
uvicorn banking_mock:app --reload --port 8001
```

Avvia MiniPay in un secondo terminale:

```powershell
uvicorn app:app --reload --port 8000
```

Apri <http://127.0.0.1:8000>. All'avvio MiniPay verifica la connessione Oracle e la presenza delle quattro tabelle. Se fallisce, controlla che l'IP del PC sia autorizzato nell'ACL di rete OCI, che il database sia disponibile, che il DSN TLS sia stato copiato integralmente e che utente/password siano corretti.

## 6. Cosa viene installato sul PC

- Python e le dipendenze del progetto, inclusa `oracledb`.
- **Non** viene installato Oracle Database.
- **Non** è necessario installare Oracle Instant Client per questa connessione TLS in Thin mode.
- Database Actions consente di gestire ed eseguire SQL dal browser.

## 7. Modalità SQLite per i soli test locali

Per testare senza collegarsi al database cloud, imposta temporaneamente in `.env`:

```dotenv
MINIPAY_DB_BACKEND=sqlite
MINIPAY_DB=./minipay.db
```

Riporta `MINIPAY_DB_BACKEND=oracle` per l'utilizzo con il database Oracle online. I dati SQLite e Oracle sono separati e non vengono sincronizzati.

## Limiti della versione didattica

Il progetto è una demo: non gestisce denaro reale e non è adatto alla produzione. Il mock bancario non è un istituto di credito. Prima di un impiego reale servirebbero revisione di sicurezza, gestione delle transazioni concorrenti, idempotenza, audit, monitoraggio, gestione dei segreti e test di integrazione approfonditi.
