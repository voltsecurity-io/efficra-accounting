# Bidra till Efficra Accounting System

Tack för att du vill bidra till projektet!

## Utvecklingsmiljö

### Förutsättningar
- Python 3.11+
- Git
- Arch Linux (rekommenderat) eller liknande

### Setup
```bash
# Klona repot
git clone https://github.com/voltsecurity-io/efficra-accounting.git
cd efficra-accounting

# Kör setup-skriptet
chmod +x setup.sh
./setup.sh

# Aktivera virtual environment
source venv/bin/activate
```

## Kodstandarder

### Python
- Använd **Black** för formattering (88 tecken per rad)
- Följ **PEP 8**
- Typ-hints är obligatoriska för publika funktioner
- Docstrings för alla moduler, klasser och publika funktioner

### Git Commit Messages
Följ Conventional Commits:
```
feat: lägg till OCR-stöd för PDF-fakturor
fix: rätta momsberäkning för EU-transaktioner
docs: uppdatera README med installation
chore: uppdatera dependencies
```

### Branch Naming
- `feature/beskrivning` - nya funktioner
- `fix/beskrivning` - buggfixar
- `docs/beskrivning` - dokumentation
- `refactor/beskrivning` - kodförbättringar

## Pull Request Process

1. Skapa en ny branch från `develop`
2. Implementera dina ändringar
3. Testa lokalt
4. Kör linters och formattering:
   ```bash
   black agents/ tests/
   flake8 agents/ tests/
   ```
5. Commit och push
6. Skapa PR mot `develop`
7. Vänta på code review

## Testing

```bash
# Kör alla tester
pytest tests/ -v

# Med coverage
pytest --cov=agents tests/
```

## Dokumentation

- Uppdatera README.md om du ändrar API eller användning
- Lägg till docstrings för nya funktioner
- Inkludera exempel i docstrings där det är användbart

## Frågor?

Öppna en issue eller kontakta maintainers.

## Licens

Genom att bidra accepterar du att ditt bidrag licensieras under samma licens som projektet.
