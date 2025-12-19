# Efficra Consulting KB - Redovisningssystem

[![CI/CD](https://github.com/voltsecurity-io/efficra-accounting/actions/workflows/ci.yml/badge.svg)](https://github.com/voltsecurity-io/efficra-accounting/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Ett automatiserat bokföringssystem byggt på Beancount med AI-stöd för fakturahantering och OCR.

## 🚀 Snabbstart

### Installation

```bash
chmod +x setup.sh
./setup.sh
```

### Starta systemet

```bash
# Aktivera Python-miljön
source venv/bin/activate

# Starta Fava webgränssnitt
fava main.beancount

# Öppna webbläsaren på http://localhost:5000
```

## 📁 Projektstruktur

```
efficra-accounting/
├── agents/                 # AI-agenter för automatisering
├── data/
│   ├── inbox/             # Inkommande fakturor (PDF, bilder)
│   ├── processed/         # Bearbetade dokument
│   ├── archive/           # Arkiverade dokument
│   └── ledger/            # Beancount-filer per period
├── logs/                  # Systemloggar
├── templates/             # Mallar för dokument
├── venv/                  # Python virtual environment
├── main.beancount        # Huvudbokföringsfil
├── requirements.txt      # Python-beroenden
├── setup.sh              # Installationsskript
└── .env                  # Konfiguration (kopia från .env.template)
```

## 🔧 Konfiguration

Redigera `.env` med dina företagsuppgifter:
- Företagsnamn och organisationsnummer
- Ollama AI-inställningar
- Sökvägar och preferenser

## 📊 Användning

### Manuell bokföring
Redigera `main.beancount` direkt med valfri textredigerare.

### Automatisk fakturahantering
1. Lägg fakturor i `data/inbox/`
2. Kör AI-agenten (kommer i framtida version)
3. Granska föreslagna transaktioner i Fava

## 🧰 Verktyg

- **Beancount**: Dubbel bokföring i textformat
- **Fava**: Webbaserat gränssnitt
- **Tesseract**: OCR för fakturor
- **Ollama**: Lokal AI för kategorisering

## 📝 Kontoplan

Systemet använder en förenklad BAS-kontoplan:
- **1xxx**: Tillgångar
- **2xxx**: Skulder och Eget Kapital
- **3xxx**: Intäkter
- **4-8xxx**: Kostnader

## 🏦 Revolut Integration (OAuth 2.0 - Production Ready)

Systemet använder **OAuth 2.0** för säker integration med Revolut Business API.

### 🚀 Quick Start (5 minuter)

```bash
# 1. Installera cryptography-bibliotek
source venv/bin/activate
pip install cryptography

# 2. Kör interaktiv OAuth-setup
python setup_revolut_oauth.py
```

Scriptet guidar dig genom:
- Generering av SSL-certifikat
- Upload till Revolut Business
- OAuth authorization flow
- Automatisk token-hantering

### 📋 Detaljerad Guide

Se [ARCHITECTURE.md](ARCHITECTURE.md) för komplett dokumentation om:
- OAuth 2.0-arkitektur
- Säkerhets best practices
- Production deployment
- AI-Team setup
- Trading integration (Revolut X)

### 💻 Användning

```bash
# Testa anslutning
python agents/revolut_sync_agent.py --test-connection

# Visa balanser
python agents/revolut_sync_agent.py --show-balances

# Synkronisera transaktioner (senaste 7 dagarna)
python agents/revolut_sync_agent.py

# Synkronisera 30 dagar bakåt
python agents/revolut_sync_agent.py --days 30

# Endast transaktioner (hoppa över växlingar)
python agents/revolut_sync_agent.py --no-exchanges
```

### Funktioner

- ✅ Automatisk import av transaktioner
- ✅ Import av valutaväxlingar från Exchange
- ✅ Visa aktuella balanser i alla valutor
- ✅ Automatisk kategorisering med AI
- ✅ Stöd för multi-valuta bokföring
- ✅ Sandbox-läge för testning

## 🤖 AI-funktioner (planerade)

- Automatisk OCR av fakturor
- Smart kategorisering av transaktioner
- Momsberäkning och rapportering
- Påminnelser om skattedeklarationer

## 📖 Dokumentation

- [Beancount Documentation](https://beancount.github.io/docs/)
- [Fava Documentation](https://beancount.github.io/fava/)
- [Svensk Bokföring](https://www.verksamt.se)

## 🔒 Säkerhet

- `.env` innehåller känslig information - aldrig committa till Git
- `data/inbox/` ignoreras av Git
- Säkerhetskopiera regelbundet `main.beancount`

## 📞 Support

För frågor om systemet, kontakta Efficra Consulting KB.

---
**Version**: 1.0  
**Målplattform**: Arch Linux / Omarchy 3.2  
**Licens**: Proprietär
