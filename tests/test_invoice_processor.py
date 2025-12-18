"""
Tester för invoice_processor
"""

import pytest
from pathlib import Path
from agents.invoice_processor import InvoiceProcessor


def test_invoice_processor_init():
    """Test att InvoiceProcessor initialiseras korrekt"""
    processor = InvoiceProcessor()
    assert processor.inbox_path.exists()


def test_scan_inbox_empty(tmp_path):
    """Test scan av tom inbox"""
    processor = InvoiceProcessor(inbox_path=str(tmp_path))
    files = processor.scan_inbox()
    assert len(files) == 0


def test_parse_invoice_data():
    """Test parsing av fakturatext"""
    processor = InvoiceProcessor()
    test_text = "Faktura 123\nBelopp: 1000 SEK\nDatum: 2025-12-18"
    
    result = processor.parse_invoice_data(test_text)
    assert result is not None
    assert "raw_text" in result
    assert result["raw_text"] == test_text
