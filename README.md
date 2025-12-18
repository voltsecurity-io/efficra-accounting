# Efficra Consulting KB - Redovisningssystem

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
