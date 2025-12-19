# Revolut Integration - Snabbguide

## 🎯 Översikt

Efficra Accounting System stödjer nu automatisk integration med:
- **Revolut Business API** - För transaktioner och kontosaldon
- **Revolut Exchange API** - För valutaväxlingar

## 📋 Steg-för-steg installation

### 1. Skaffa API-nyckel

#### Revolut Business API
1. Logga in på https://business.revolut.com
2. Gå till **Settings** → **API**
3. Klicka på **Create API key** eller **Generate certificate**
4. Välj scope (permissions):
   - `READ` - För att läsa accounts, transactions, counterparties
   - `WRITE` - För att uppdatera counterparties och webhooks (valfritt)
   - `PAY` - För att genomföra betalningar och valutaväxlingar (valfritt)
5. Ladda ner private key och certificate
6. Spara API-nyckeln säkert (visas bara en gång!)

**Viktigt:** Business API inkluderar redan Foreign Exchange - ingen separat Exchange API-nyckel behövs!

### 2. Konfigurera systemet

Skapa eller redigera `.env` filen i projektroten:

```bash
# Kopiera template om du inte har en .env fil
cp .env.template .env

# Redigera filen
nano .env
```

Lägg till din API-nyckel:

```bash
# === Revolut API Konfiguration ===
REVOLUT_BUSINESS_API_KEY="your_access_token_here"
REVOLUT_SANDBOX="false"  # true för testmiljö
REVOLUT_SYNC_DAYS="7"
REVOLUT_AUTO_SYNC="false"
```

**OBS:** Om du använder OAuth-baserad autentisering behöver du följa [Revoluts guide](https://developer.revolut.com/docs/guides/manage-accounts/get-started/make-your-first-api-request) för att generera access tokens.

⚠️ **VIKTIGT:** Håll `.env` filen privat - den är redan i `.gitignore`

### 3. Testa anslutningen

```bash
# Aktivera Python-miljön
source venv/bin/activate

# Testa API-anslutning
python agents/revolut_sync_agent.py --test-connection
```

Förväntat resultat:
```
🔌 Testar Revolut API-anslutning...
✅ Anslutning OK - hittade 3 konton
   • Business SEK (SEK)
   • Business EUR (EUR)
   • Business USD (USD)
✅ Foreign Exchange OK - EUR/SEK: 11.23
```

### 4. Visa aktuella balanser

```bash
python agents/revolut_sync_agent.py --show-balances
```

### 5. Synkronisera transaktioner

```bash
# Synkronisera senaste 7 dagarna (standard)
python agents/revolut_sync_agent.py

# Synkronisera 30 dagar bakåt
python agents/revolut_sync_agent.py --days 30

# Endast transaktioner (ingen exchange)
python agents/revolut_sync_agent.py --no-exchanges
```

### 6. Inkludera i Beancount

Efter synkronisering hittar du importerade filer i `data/ledger/`:
- `revolut_import_YYYYMMDD_HHMMSS.beancount`
- `revolut_exchanges_YYYYMMDD_HHMMSS.beancount`

Lägg till i din `main.beancount`:

```beancount
; Inkludera Revolut-transaktioner
include "data/ledger/revolut_import_20251218_143022.beancount"
include "data/ledger/revolut_exchanges_20251218_143022.beancount"
```

### 7. Verifiera i Fava

```bash
fava main.beancount
```

Öppna http://localhost:5000 och kontrollera:
- Alla transaktioner importerades korrekt
- Balanser stämmer överens med Revolut
- Kategoriseringen är rimlig

## 🔧 Avancerad användning

### Programmatisk användning

```python
from agents.revolut_integration import quick_sync

# Snabb synkronisering
quick_sync(
    business_api_key="your_key",
    exchange_api_key="your_exchange_key",
    days_back=30
)
```

### Anpassad kategorisering

Redigera `agents/revolut_integration.py` och uppdatera metoden `_categorize_transaction()`:

```python
def _categorize_transaction(self, transaction: Dict) -> str:
    description = transaction.get("description", "").lower()
    
    # Dina egna kategoriseringsregler
    if "aws" in description:
        return "Expenses:IT:Cloud"
    elif "github" in description:
        return "Expenses:IT:Software"
    # ... osv
```

### Kontomappning

Anpassa kontomappningen i `RevolutToBeancount._load_account_mapping()`:

```python
return {
    "business_sek": "Assets:Bank:Revolut:SEK",
    "business_eur": "Assets:Bank:Revolut:EUR",
    "savings_sek": "Assets:Savings:Revolut:SEK",
    # ... dina egna konton
}
```

## 🔐 Säkerhet

### Best Practices

1. **Använd Read-Only scope** när det är möjligt
2. **Rotera API-nycklar** regelbundet (var 90:e dag)
3. **Använd Sandbox** för testning innan production
4. **Säkerhetskopiera** `.env` säkert (inte i Git!)
5. **Begränsa access** till `.env` filen:
   ```bash
   chmod 600 .env
   ```

### Sandbox-testning

För att testa utan att påverka riktiga transaktioner:

1. Skapa Sandbox API-nyckel på Revolut
2. Sätt i `.env`:
   ```bash
   REVOLUT_SANDBOX="true"
   ```
3. Testa funktionalitet
4. Byt tillbaka till `false` för production

## 🆘 Felsökning

### "API key invalid"
- Kontrollera att nyckeln är korrekt kopierad (inga mellanslag)
- Verifiera att nyckeln är aktiverad i Revolut
- Kontrollera att rätt sandbox/production nyckel används

### "Permission denied"
- Kontrollera API-nyckelns scope/permissions
- Vissa funktioner kräver specifika rättigheter

### "No transactions found"
- Kontrollera datumintervallet (`--days`)
- Verifiera att det finns transaktioner i Revolut för perioden
- Testa med `--test-connection` först

### Loggfiler

Kontrollera `logs/efficra.log` för detaljerad information:
```bash
tail -f logs/efficra.log
```

## 📞 Support

- **Revolut API Docs:** https://developer.revolut.com/docs/business-api
- **Beancount Docs:** https://beancount.github.io/docs/
- **GitHub Issues:** [Skapa ett issue](https://github.com/voltsecurity-io/efficra-accounting/issues)

## 🚀 Nästa steg

- [ ] Konfigurera automatisk schemalagd synkronisering (cron)
- [ ] Anpassa kategoriseringsregler för ditt företag
- [ ] Utforska AI-kategorisering med Ollama
- [ ] Sätt upp automatiska backups
