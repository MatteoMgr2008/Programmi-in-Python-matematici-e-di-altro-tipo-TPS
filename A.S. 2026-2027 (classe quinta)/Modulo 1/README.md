# MiniPay — versione modulare

MiniPay è una demo didattica full-stack per simulare alcuni flussi di un servizio di pagamenti digitali. Questa versione mantiene la stessa interfaccia web e le stesse funzioni della versione iniziale, ma separa il backend in moduli Python con responsabilità distinte.

## Struttura del progetto

```text
MiniPay/
├── app.py                         # Punto d'ingresso: crea FastAPI e collega i router
├── banking_mock.py                # Processo separato che simula il fornitore di core banking
├── minipay/
│   ├── config.py                  # Configurazione e variabili d'ambiente
│   ├── database.py                # Accesso dati MySQL tramite PyMySQL
│   ├── schemas.py                 # Validazione dei dati ricevuti dalle API
│   ├── security.py                # Hash password, token e utente autenticato
│   ├── routers/
│   │   ├── auth.py                # API registrazione, login e profilo
│   │   ├── wallet.py              # API saldo, movimenti e notifiche
│   │   └── payments.py            # API di invio pagamento
│   ├── services/
│   │   ├── auth_service.py        # Regole di registrazione e login
│   │   ├── wallet_service.py      # Lettura del saldo e dello storico
│   │   ├── payment_service.py     # Regole e transazione del pagamento
│   │   └── notification_service.py# Creazione e lettura delle notifiche
│   └── integrations/
│       └── core_banking.py        # Client HTTP verso il core banking esterno
├── static/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── test_app.py
└── requirements.txt
```

## Perché la separazione è migliore

- **Router**: definiscono gli endpoint HTTP e collegano richieste e servizi.
- **Services**: contengono le regole applicative, evitando di concentrare tutto in `app.py`.
- **Integrations**: isolano la comunicazione HTTP con il fornitore esterno.
- **Database e security**: centralizzano accesso ai dati, hashing e verifica della sessione.
- **Schemas**: i modelli SQLModel validano i dati in ingresso e riducono la duplicazione dei modelli Pydantic.
- **SQLModel**: viene usato per i modelli delle richieste HTTP. L’accesso ai dati MySQL resta isolato in `database.py` e usa PyMySQL.

Questa è una separazione modulare del codice. Non tutti i moduli sono microservizi autonomi: i router e i servizi girano nello stesso processo MiniPay. `banking_mock.py`, invece, è un processo separato che rappresenta il sistema esterno.

## Requisiti

Python 3.11 o superiore e un server MySQL locale (ad esempio MySQL Server con MySQL Workbench). Il codice dell’applicazione si collega a MySQL tramite PyMySQL. Oracle resta indicato nell’architettura teorica della consegna, ma non viene usato da questa versione eseguibile.

## Avvio su Windows

1. Verifica che il servizio MySQL Server sia avviato. In MySQL Workbench collegati al server locale, apri una scheda SQL ed esegui `infra/mysql/crea_database.sql`, dopo aver sostituito la password segnaposto con una password scelta da te.
2. Copia `.env.example` in `.env` e inserisci la stessa password nel campo `MYSQL_PASSWORD`.
3. Apri un terminale nella cartella `MiniPay` ed esegui:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Avvia il servizio bancario simulato nel **primo terminale**:

```powershell
uvicorn banking_mock:app --reload --port 8001
```

Avvia MiniPay nel **secondo terminale**, con lo stesso ambiente virtuale attivo:

```powershell
uvicorn app:app --reload --port 8000
```

Apri http://127.0.0.1:8000 nel browser.

## Avvio su macOS/Linux

Crea e attiva l'ambiente (`python3 -m venv .venv`, `source .venv/bin/activate`), installa le dipendenze e usa i due comandi `uvicorn` descritti sopra.

## Come provarlo

1. Registra due utenti con indirizzi email diversi.
2. Accedi con il primo utente.
3. Inserisci l'email del secondo come destinatario.
4. Invia un pagamento e verifica saldo, storico e notifiche.
5. Prova un importo superiore al saldo o un importo oltre il limite del core banking demo (5.000 €).

Ogni nuovo utente riceve 100,00 € virtuali demo. Non è denaro reale.

## Test

Con l'ambiente virtuale attivo:

```powershell
pytest -q
```

I test inclusi verificano stato API, registrazione, saldo iniziale, email duplicata e rifiuto di una password errata. Non sostituiscono una suite completa di test di integrazione dei pagamenti.

## Corrispondenza con la consegna

- **Browser**: frontend web statico.
- **Servizi applicativi**: separati in moduli Python, ma eseguiti dentro la stessa API.
- **Core banking esterno**: rappresentato da `banking_mock.py`, raggiunto tramite chiamata HTTP dall'adattatore in `minipay/integrations/core_banking.py`.
- **Database nell’implementazione demo**: MySQL locale. SQLite viene usato solo dai test automatici.
- **Database nell’architettura teorica della consegna**: Oracle, come indicato dal testo dell’esercizio. MySQL è la scelta pratica per eseguire la demo sul PC e non sostituisce Oracle nello schema architetturale.
- **AWS**: non configurato; la distribuzione AWS è un possibile passo successivo e va rappresentata nello schema architetturale.

## Limiti e sicurezza

Questo progetto è solo didattico e **non è adatto a gestire denaro reale**. Non integra banche, carte o circuiti di pagamento. La chiave di sessione predefinita è solo per la demo e va sostituita tramite `MINIPAY_SECRET` in un ambiente non locale. Prima di un uso reale servirebbero, tra le altre cose, controlli di sicurezza, idempotenza robusta, audit, cifratura, monitoraggio e una progettazione transazionale più rigorosa.

## Parte architetturale della consegna

Per la proposta AWS, il diagramma a blocchi e il piano d'integrazione Oracle, consulta:

- [`docs/architettura.md`](docs/architettura.md): componenti, collocazione AWS e flusso di un pagamento;
- [`docs/architettura.mmd`](docs/architettura.mmd): diagramma Mermaid separato, utilizzabile anche in editor compatibili;
- [`docs/mysql-locale.md`](docs/mysql-locale.md): configurazione del database MySQL locale;
- [`infra/mysql/crea_database.sql`](infra/mysql/crea_database.sql): creazione del database e dell’utente MySQL;
- [`infra/oracle/schema_demo.sql`](infra/oracle/schema_demo.sql): schema di riferimento Oracle per l’architettura della consegna;
- [`infra/aws/README.md`](infra/aws/README.md): traccia semplificata di deployment AWS;
- [`.env.example`](.env.example): esempio di variabili locali.

### Database usato da questa versione

Questa versione eseguibile usa MySQL locale. Segui [`docs/mysql-locale.md`](docs/mysql-locale.md) per creare database e utente, configurare `.env` e avviare i due servizi. Oracle rimane nel disegno architetturale richiesto dalla traccia, ma non viene contattato dal codice di questa versione.


I test automatici usano un database temporaneo SQLite impostato esclusivamente in `test_app.py`; l’applicazione avviata normalmente usa MySQL. AWS non è stato configurato: la distribuzione cloud resta una proposta architetturale.
