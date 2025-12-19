"""
Konfigurations-hantering för Efficra Accounting System
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Ladda .env fil
load_dotenv()


class Config:
    """Centraliserad konfiguration"""

    # Företagsinformation
    COMPANY_NAME = os.getenv("COMPANY_NAME", "Efficra Consulting KB")
    ORG_NUMBER = os.getenv("ORG_NUMBER", "")
    VAT_NUMBER = os.getenv("VAT_NUMBER", "")

    # Ollama AI
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

    # Revolut API
    REVOLUT_BUSINESS_API_KEY = os.getenv("REVOLUT_BUSINESS_API_KEY", "")
    REVOLUT_SANDBOX = os.getenv("REVOLUT_SANDBOX", "false").lower() == "true"
    REVOLUT_SYNC_DAYS = int(os.getenv("REVOLUT_SYNC_DAYS", "7"))
    REVOLUT_AUTO_SYNC = os.getenv("REVOLUT_AUTO_SYNC", "false").lower() == "true"

    # Fava
    FAVA_HOST = os.getenv("FAVA_HOST", "0.0.0.0")
    FAVA_PORT = int(os.getenv("FAVA_PORT", "5000"))

    # Sökvägar
    BASE_DIR = Path(__file__).parent.parent
    DATA_INBOX = BASE_DIR / os.getenv("DATA_INBOX", "data/inbox")
    DATA_PROCESSED = BASE_DIR / os.getenv("DATA_PROCESSED", "data/processed")
    DATA_ARCHIVE = BASE_DIR / os.getenv("DATA_ARCHIVE", "data/archive")
    DATA_LEDGER = BASE_DIR / os.getenv("DATA_LEDGER", "data/ledger")

    # Beancount
    MAIN_LEDGER = BASE_DIR / os.getenv("MAIN_LEDGER", "main.beancount")
    CURRENCY = os.getenv("CURRENCY", "SEK")
    OPENING_DATE = os.getenv("OPENING_DATE", "2024-01-01")

    # OCR
    TESSERACT_LANG = os.getenv("TESSERACT_LANG", "swe+eng")
    OCR_DPI = int(os.getenv("OCR_DPI", "300"))

    # Loggning
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = BASE_DIR / os.getenv("LOG_FILE", "logs/efficra.log")

    @classmethod
    def validate(cls):
        """Validera konfiguration"""
        errors = []

        if not cls.ORG_NUMBER:
            errors.append("ORG_NUMBER saknas i .env")

        if not cls.DATA_INBOX.exists():
            errors.append(f"Inbox-mapp saknas: {cls.DATA_INBOX}")

        if errors:
            raise ValueError(f"Konfigurationsfel:\n" + "\n".join(f"- {e}" for e in errors))

        return True


# Skapa en global config-instans
config = Config()
