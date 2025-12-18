#!/bin/bash

# =============================================================================
# Efficra Consulting - Development Helper Script
# =============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Aktivera venv
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo -e "${RED}[!] Virtual environment saknas. Kör ./setup.sh först.${NC}"
    exit 1
fi

# Meny
echo -e "${BLUE}==============================${NC}"
echo -e "${BLUE}  Efficra Dev Helper${NC}"
echo -e "${BLUE}==============================${NC}"
echo ""
echo "1. Starta Fava (Web UI)"
echo "2. Kör tester"
echo "3. Formatera kod (Black)"
echo "4. Lint kod (Flake8)"
echo "5. Uppdatera dependencies"
echo "6. Backup bokföring"
echo "7. Process fakturor (WIP)"
echo "0. Avsluta"
echo ""
read -p "Välj alternativ: " choice

case $choice in
    1)
        echo -e "${GREEN}[+] Startar Fava...${NC}"
        fava main.beancount
        ;;
    2)
        echo -e "${GREEN}[+] Kör tester...${NC}"
        pytest tests/ -v --cov=agents
        ;;
    3)
        echo -e "${GREEN}[+] Formaterar kod...${NC}"
        black agents/ tests/
        ;;
    4)
        echo -e "${GREEN}[+] Lintar kod...${NC}"
        flake8 agents/ tests/
        ;;
    5)
        echo -e "${GREEN}[+] Uppdaterar dependencies...${NC}"
        pip install --upgrade pip
        pip install -r requirements.txt --upgrade
        ;;
    6)
        echo -e "${GREEN}[+] Skapar backup...${NC}"
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        tar -czf "backups/efficra_backup_${TIMESTAMP}.tar.gz" main.beancount data/ledger/
        echo -e "${GREEN}    Backup skapad: backups/efficra_backup_${TIMESTAMP}.tar.gz${NC}"
        ;;
    7)
        echo -e "${YELLOW}[!] Funktionen är under utveckling...${NC}"
        ;;
    0)
        echo "Hejdå!"
        exit 0
        ;;
    *)
        echo -e "${RED}[!] Ogiltigt val.${NC}"
        exit 1
        ;;
esac
