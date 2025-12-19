# Efficra Accounting System - Arkitektur & AI-Team

## 🏗️ Systemöversikt

Detta är ett **helautomatiserat bokföringssystem** med AI-agents för Efficra Consulting KB, integrerat med Revolut Business och Revolut X (trading).

### Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     EFFICRA ACCOUNTING SYSTEM                    │
│                                                                  │
│  ┌────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Beancount     │  │  Revolut OAuth  │  │   AI Agents     │ │
│  │  (Ledger)      │◄─┤  Integration    │◄─┤   (Trading +    │ │
│  │                │  │                 │  │    Accounting)   │ │
│  └────────────────┘  └─────────────────┘  └─────────────────┘ │
│          │                    │                     │           │
│          │                    │                     │           │
│  ┌───────▼────────────────────▼─────────────────────▼────────┐ │
│  │              Fava Web Interface + Reports                 │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │
                ┌──────────────┴──────────────┐
                │                             │
         ┌──────▼────────┐           ┌───────▼────────┐
         │  Revolut      │           │  Revolut X     │
         │  Business API │           │  Trading API   │
         │  (Banking)    │           │  (Crypto)      │
         └───────────────┘           └────────────────┘
```

## 🔐 OAuth 2.0 Arkitektur (Production-Ready)

### Säkerhetsflöde

1. **Certifikat-generering** (Engångs-setup)
   - RSA 2048-bit key pair
   - X.509 självsignerat certifikat
   - Privat nyckel: `~/.revolut/certs/privatecert.pem` (600 permissions)
   - Publikt cert: `~/.revolut/certs/publiccert.cer`

2. **JWT Client Assertion**
   - RS256-signerad JWT
   - 5 minuters giltighet
   - Header: `{"alg": "RS256", "typ": "JWT"}`
   - Payload: `{iss, sub (client_id), aud, exp}`

3. **Authorization Code Flow**
   - User consent via Revolut Business web app
   - Authorization code (2 min giltighet)
   - Exchange för access + refresh tokens

4. **Token Management**
   - Access token: 40 minuter giltighet
   - Refresh token: 90 dagar (Freelancer plan)
   - Automatisk förnyelse 5 min före expiry
   - Säker lagring: `~/.revolut/tokens.json` (600 permissions)

5. **Auto-Recovery**
   - Automatisk token-förnyelse vid 401 Unauthorized
   - JWT regenerering vid behov
   - Graceful degradation

### Säkerhetsrekommendationer

- ✅ **Privata nycklar**: Endast läsbara för owner (chmod 600)
- ✅ **Token-rotation**: Automatisk vid varje refresh
- ✅ **Minimal expiry**: JWT endast 5 min giltighet
- ✅ **Scope limitation**: Endast READ för bokföring
- ✅ **IP Whitelisting**: Konfigurera i Revolut settings (optional)
- ✅ **Audit logging**: All API-access loggad
- ✅ **Secrets management**: Aldrig committa tokens/certs till Git

## 🤖 AI-Team Arkitektur

### Agent Roles

#### 1. **Accounting Agent** (Befintlig)
```python
agents/revolut_sync_agent.py
```
- Synkroniserar transaktioner från Revolut Business
- Kategoriserar utgifter med Ollama AI
- Genererar Beancount-entries
- Momsberäkning och rapportering

#### 2. **Trading Agent** (Planerad - Revolut X)
```python
agents/trading_agent.py
```
- Övervakar Revolut X trading-konto
- Spårar crypto-transaktioner
- Beräknar kapitalvinster/förluster
- Cost-basis tracking
- Tax lot management

#### 3. **Invoice Agent** (Under utveckling)
```python
agents/invoice_processor.py
```
- OCR-scanning av fakturor (Tesseract)
- AI-extraktion av leverantörsinfo
- Automatisk bokföring
- Due date tracking
- Payment automation via Revolut

#### 4. **Tax Agent** (Planerad)
```python
agents/tax_agent.py
```
- Momsrapportering (månatlig/kvartalsvis)
- Preliminärskatt-beräkning
- Skattedeklaration (K10/INK2)
- Deadline-påminnelser

#### 5. **Analytics Agent** (Planerad)
```python
agents/analytics_agent.py
```
- Cashflow-analys
- Trend-detection
- Anomaly detection
- Budget forecasting
- Custom reporting

### AI Stack

```
┌─────────────────────────────────────────┐
│          Ollama (Local LLM)             │
│     - llama3 (default model)            │
│     - Offline operation                 │
│     - Privacy-first                     │
└─────────────────────────────────────────┘
                 │
                 │
┌────────────────┴──────────────────┐
│      LangChain Framework          │
│  - Agent orchestration            │
│  - Tool management                │
│  - Prompt engineering             │
└───────────────────────────────────┘
                 │
      ┌──────────┴───────────┐
      │                      │
┌─────▼──────┐      ┌───────▼────────┐
│  Tesseract │      │   Beancount    │
│  OCR       │      │   Parser       │
└────────────┘      └────────────────┘
```

## 📊 Data Flow

### 1. Transaction Import

```
Revolut API ──OAuth──► RevolutBusiness.get_transactions()
                               │
                               │ Parse legs, merchant data
                               ▼
                    RevolutToBeancount.transaction_to_beancount()
                               │
                               │ AI Categorization (Ollama)
                               ▼
                       Beancount file (.beancount)
                               │
                               │ Auto-include
                               ▼
                          main.beancount
                               │
                               │
                               ▼
                        Fava Web Interface
```

### 2. Invoice Processing

```
PDF/Image ──► Tesseract OCR ──► Text Extraction
                                      │
                                      │
                                      ▼
                               Ollama AI Analysis
                               (Supplier, Amount,
                                VAT, Due Date)
                                      │
                                      │
                                      ▼
                            Generate Beancount Entry
                                      │
                                      │
                                      ▼
                            Optional: Auto-pay via
                            Revolut API (PAY scope)
```

### 3. Trading Integration (Revolut X)

```
Revolut X API ──► Fetch Crypto Trades
                         │
                         │
                         ▼
                  Calculate Cost Basis
                  (FIFO/LIFO/Specific ID)
                         │
                         │
                         ▼
              Generate Multi-Currency Entries
              with Exchange Rates
                         │
                         │
                         ▼
                    Beancount Commodities
```

## 🔧 Configuration Management

### Environment Variables (.env)

```bash
# === Företagsinformation ===
COMPANY_NAME="Efficra Consulting KB"
ORG_NUMBER="XXXXXX-XXXX"
VAT_NUMBER="SEXXXXXXXXXXXXXX"

# === Revolut OAuth (Production-Ready) ===
REVOLUT_CLIENT_ID="your_client_id"
REVOLUT_REDIRECT_URI="https://localhost:8080/callback"
REVOLUT_SANDBOX="false"
REVOLUT_OAUTH_ENABLED="true"
REVOLUT_SYNC_DAYS="7"

# === Revolut X Trading (Planerad) ===
REVOLUT_X_API_KEY=""
REVOLUT_X_ENABLED="false"

# === Ollama AI ===
OLLAMA_HOST="http://localhost:11434"
OLLAMA_MODEL="llama3"

# === Fava ===
FAVA_HOST="0.0.0.0"
FAVA_PORT="5000"
```

### Token Storage

```
~/.revolut/
├── certs/
│   ├── privatecert.pem  (600 - ENDAST OWNER)
│   └── publiccert.cer   (644)
└── tokens.json          (600 - ENDAST OWNER)
    ├── access_token
    ├── refresh_token
    ├── expires_at
    └── created_at
```

## 🚀 Production Deployment

### Systemkrav

- **OS**: Linux (Ubuntu/Debian recommended)
- **Python**: 3.11+
- **Tesseract**: 5.x (Svenska + Engelska)
- **Ollama**: Latest (för AI)
- **SSL/TLS**: För OAuth redirect (Let's Encrypt)

### Deployment Steps

```bash
# 1. Clone repository
git clone <your-repo>
cd efficra-accounting

# 2. Setup
./setup.sh

# 3. Install cryptography dependency
source venv/bin/activate
pip install cryptography

# 4. OAuth Setup (Interactive)
python setup_revolut_oauth.py

# 5. Test Connection
python agents/revolut_sync_agent.py --test-connection

# 6. Initial Import (30 dagar)
python agents/revolut_sync_agent.py --days 30

# 7. Start Fava
fava main.beancount

# 8. Schedule cron jobs
crontab -e
```

### Cron Jobs för Automation

```cron
# Synkronisera transaktioner dagligen kl 02:00
0 2 * * * cd /path/to/efficra-accounting && ./venv/bin/python agents/revolut_sync_agent.py --days 7 >> logs/cron.log 2>&1

# Förnya token proaktivt var 30:e minut
*/30 * * * * cd /path/to/efficra-accounting && ./venv/bin/python agents/token_refresh.py >> logs/token_refresh.log 2>&1

# Backup dagligen kl 03:00
0 3 * * * cd /path/to/efficra-accounting && ./scripts/backup.sh >> logs/backup.log 2>&1

# Momsrapport sista dagen i månaden
0 9 28-31 * * cd /path/to/efficra-accounting && ./venv/bin/python agents/vat_report.py >> logs/vat.log 2>&1
```

### Docker Deployment (Recommended)

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-swe \
    tesseract-ocr-eng \
    imagemagick \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set restrictive permissions
RUN chmod 600 .env

# Run as non-root
RUN useradd -m efficra
USER efficra

# Expose Fava port
EXPOSE 5000

CMD ["fava", "main.beancount", "--host", "0.0.0.0"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  fava:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ~/.revolut:/home/efficra/.revolut:ro  # Read-only OAuth certs
    environment:
      - REVOLUT_OAUTH_ENABLED=true
    restart: unless-stopped

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped

  sync-agent:
    build: .
    command: python agents/revolut_sync_agent.py --days 7
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ~/.revolut:/home/efficra/.revolut:ro
    environment:
      - REVOLUT_OAUTH_ENABLED=true
    restart: "no"  # Run via cron/scheduler

volumes:
  ollama_data:
```

## 📈 Revolut X Trading Integration (Roadmap)

### Trading Agent Architecture

```python
# agents/revolut_x_agent.py

class RevolutXTrading:
    """
    Revolut X Trading Integration
    Hanterar crypto trades, cost basis, tax reporting
    """
    
    def __init__(self, oauth_handler, config):
        self.oauth = oauth_handler
        self.config = config
        self.base_url = "https://api.revolut.com/trading/1.0"
    
    def get_trades(self, from_date, to_date):
        """Hämta crypto trades"""
        pass
    
    def calculate_cost_basis(self, trades, method='FIFO'):
        """Beräkna cost basis (FIFO/LIFO/Specific ID)"""
        pass
    
    def generate_capital_gains_report(self, tax_year):
        """Generera kapitalvinstrapport för K4"""
        pass
    
    def to_beancount(self, trade):
        """Konvertera trade till Beancount commodity transaction"""
        # Multi-currency med exchange rates
        pass
```

### Example Beancount Output

```beancount
; Crypto Trading - Revolut X

2024-12-01 * "Bought Bitcoin"
  revolut_x_id: "trade_abc123"
  Assets:Crypto:BTC                 0.05 BTC @ 450000.00 SEK
  Assets:Bank:Revolut:SEK      -22500.00 SEK

2024-12-15 * "Sold Bitcoin"
  revolut_x_id: "trade_def456"
  Assets:Crypto:BTC                -0.05 BTC @ 480000.00 SEK
  Assets:Bank:Revolut:SEK       24000.00 SEK
  Income:CapitalGains:Crypto     1500.00 SEK  ; Realiserad vinst
```

## 🔍 Monitoring & Alerts

### Logging Strategy

```python
# logs/
├── efficra.log          # Main application log
├── revolut_api.log      # API calls & responses
├── oauth.log            # Authentication events
├── trading.log          # Trading operations
├── errors.log           # Error tracking
└── audit.log            # Security & compliance audit trail
```

### Alert System (Planned)

- **Email alerts**: För kritiska fel, token expiry warnings
- **Slack/Discord**: Dagliga sammanfattningar
- **Dashboard**: Real-time monitoring via Fava

## 🛡️ Security Best Practices

1. **Secrets Management**
   - Använd `python-dotenv` för env vars
   - Aldrig commita `.env` till Git
   - Rotera API-nycklar var 90:e dag
   - Använd `keyring` för extra säkerhet

2. **Access Control**
   - Minimal OAuth scopes (READ endast för bokföring)
   - IP whitelisting i Revolut settings
   - 2FA aktiverat på alla konton

3. **Backup Strategy**
   - Daglig backup av `main.beancount`
   - Backup av OAuth tokens (krypterat)
   - Off-site backup (encrypted)
   - Retention: 7 dagliga, 4 veckovisa, 12 månadsvisa

4. **Audit Trail**
   - Alla API-calls loggade
   - Timestamp + request/response
   - User actions tracked
   - Compliance med GDPR

## 📚 Resources

- **Revolut Business API**: https://developer.revolut.com/docs/business/business-api
- **Beancount Docs**: https://beancount.github.io/docs/
- **LangChain**: https://python.langchain.com/docs/
- **Ollama**: https://ollama.ai/

## 🎯 Next Steps

1. ✅ **OAuth Implementation** - KLART!
2. ⏳ **Production Testing** - Kör setup_revolut_oauth.py
3. ⏳ **Trading Agent** - Integrera Revolut X API
4. ⏳ **Invoice Processor** - Färdigställ OCR + AI
5. ⏳ **Tax Agent** - Automatiska momsrapporter
6. ⏳ **Docker Deployment** - Containerisering
7. ⏳ **Monitoring** - Alerting & dashboards

---

**Status**: 🟢 **Production-Ready OAuth Implementation**

Systemet är nu redo för produktionsmiljö med robust OAuth 2.0-autentisering!
