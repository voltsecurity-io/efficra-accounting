#!/usr/bin/env python3
"""
Faktura Processor - OCR och AI-baserad fakturahantering

Detta script tar fakturor från data/inbox/, läser dem med OCR,
och använder AI för att extrahera relevant information.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import pytesseract
from PIL import Image
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/invoice_processor.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class InvoiceProcessor:
    """Processor för fakturor med OCR och AI-integration"""

    def __init__(self, inbox_path: str = "data/inbox"):
        self.inbox_path = Path(inbox_path)
        self.processed_path = Path("data/processed")
        self.archive_path = Path("data/archive")
        
        # Skapa mappar om de inte finns
        self.processed_path.mkdir(parents=True, exist_ok=True)
        self.archive_path.mkdir(parents=True, exist_ok=True)

    def scan_inbox(self) -> list[Path]:
        """Scanna inbox för nya fakturor"""
        supported_formats = [".pdf", ".png", ".jpg", ".jpeg"]
        files = []
        
        for ext in supported_formats:
            files.extend(self.inbox_path.glob(f"*{ext}"))
        
        logger.info(f"Hittade {len(files)} filer i inbox")
        return files

    def extract_text_from_image(self, image_path: Path) -> str:
        """Extrahera text från bild med OCR"""
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang="swe+eng")
            logger.info(f"OCR lyckades för {image_path.name}")
            return text
        except Exception as e:
            logger.error(f"OCR misslyckades för {image_path.name}: {e}")
            return ""

    def parse_invoice_data(self, text: str) -> Optional[Dict]:
        """
        Parsea fakturatext och extrahera viktig information
        
        TODO: Integrera med Ollama/LLM för smart parsing
        """
        # Enkel parsing - ska förbättras med AI
        invoice_data = {
            "date": None,
            "amount": None,
            "supplier": None,
            "description": None,
            "vat": None,
        }
        
        # Här skulle AI-integration komma in
        # För nu returnerar vi bara rådata
        invoice_data["raw_text"] = text
        
        return invoice_data

    def generate_beancount_entry(self, invoice_data: Dict) -> str:
        """Generera Beancount-transaktion från fakturadat"""
        template = """
{date} * "{supplier}" "{description}"
    Expenses:Okategoriserat           {amount} SEK
    Assets:Bank:Företagskonto        -{amount} SEK
"""
        # Placeholder för nu
        return template.format(
            date=datetime.now().strftime("%Y-%m-%d"),
            supplier="Okänd leverantör",
            description="OCR-behandlad faktura",
            amount="0.00",
        )

    def process_file(self, file_path: Path) -> bool:
        """Bearbeta en enskild fakturfil"""
        logger.info(f"Bearbetar {file_path.name}...")
        
        # OCR
        text = self.extract_text_from_image(file_path)
        if not text:
            logger.warning(f"Ingen text extraherad från {file_path.name}")
            return False
        
        # Parse
        invoice_data = self.parse_invoice_data(text)
        
        # Spara rådata
        output_file = self.processed_path / f"{file_path.stem}.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"=== OCR Text från {file_path.name} ===\n\n")
            f.write(text)
        
        logger.info(f"Sparade bearbetad data till {output_file}")
        
        # Flytta till arkiv
        archive_file = self.archive_path / file_path.name
        file_path.rename(archive_file)
        logger.info(f"Arkiverade original till {archive_file}")
        
        return True

    def run(self):
        """Huvudloop för att bearbeta alla fakturor"""
        logger.info("Startar fakturabearbetning...")
        
        files = self.scan_inbox()
        if not files:
            logger.info("Inga filer att bearbeta")
            return
        
        success_count = 0
        for file_path in files:
            if self.process_file(file_path):
                success_count += 1
        
        logger.info(
            f"Bearbetning klar: {success_count}/{len(files)} filer lyckades"
        )


def main():
    """Entry point"""
    processor = InvoiceProcessor()
    processor.run()


if __name__ == "__main__":
    main()
