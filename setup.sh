#!/bin/bash

# =============================================================================
# Efficra Consulting KB - System Installer
# Target: Arch Linux / Omarchy 3.2
# =============================================================================

set -e # Avsluta direkt vid fel

# Färger för snygg output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "========================================================"
echo "   Efficra Consulting KB - Accounting System Setup      "
echo "========================================================"
echo -e "${NC}"

# 1. Kontrollera att vi kör Arch
if [ ! -f /etc/arch-release ]; then
    echo -e "${YELLOW}[!] Varning: Detta skript är optimerat för Arch Linux.${NC}"
    read -p "Vill du fortsätta ändå? (j/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Jj]$ ]]; then
        exit 1
    fi
fi

# 2. Systemberoenden (Pacman)
echo -e "${GREEN}[+] Installerar systemberoenden...${NC}"
sudo pacman -S --needed --noconfirm \
    python \
    python-pip \
    git \
    base-devel \
    tesseract \
    tesseract-data-swe \
    tesseract-data-eng \
    imagemagick \
    ghostscript

# 3. Mappstruktur
echo -e "${GREEN}[+] Skapar mappstruktur...${NC}"
mkdir -p agents
mkdir -p data/{inbox,processed,archive,ledger}
mkdir -p logs
mkdir -p templates

# 4. Python Virtual Environment
echo -e "${GREEN}[+] Konfigurerar Python-miljö (venv)...${NC}"
if [ ! -d "venv" ]; then
    python -m venv venv
    echo "    Venv skapat."
else
    echo "    Venv existerar redan."
fi

# Aktivera och installera
source venv/bin/activate
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo -e "${RED}[!] requirements.txt saknas! Skapar en minimal fil.${NC}"
    echo "beancount" > requirements.txt
    echo "fava" >> requirements.txt
    pip install -r requirements.txt
fi

# 5. Konfigurationsfiler
echo -e "${GREEN}[+] Kollar konfigurationsfiler...${NC}"

# Kopiera .env mall om den inte finns
if [ ! -f ".env" ]; then
    if [ -f ".env.template" ]; then
        cp .env.template .env
        echo "    Skapade .env från mall."
    else
        echo -e "${YELLOW}[!] Ingen .env.template hittades. Skapa .env manuellt.${NC}"
    fi
fi

# 6. Git Setup
echo -e "${GREEN}[+] Initierar Git repo...${NC}"
if [ ! -d ".git" ]; then
    git init
    echo "*.pyc" > .gitignore
    echo "__pycache__/" >> .gitignore
    echo "venv/" >> .gitignore
    echo ".env" >> .gitignore
    echo "data/inbox/" >> .gitignore
    echo "logs/" >> .gitignore
    echo "    Git initierat och .gitignore skapad."
else
    echo "    Git repo finns redan."
fi

# 7. Ollama Check (AI)
echo -e "${GREEN}[+] Kollar AI-motor (Ollama)...${NC}"
if command -v ollama &> /dev/null; then
    echo "    Ollama är installerat."
    # Kolla om servern körs, annars varna
    if ! pgrep -x "ollama" > /dev/null; then
        echo -e "${YELLOW}[!] Ollama server verkar inte vara igång. Starta den med 'ollama serve' i en annan terminal.${NC}"
    else
        echo "    Ollama server körs."
        # Valfritt: Pulla Llama 3 om den inte finns (avkommentera om önskat)
        # ollama pull llama3
    fi
else
    echo -e "${YELLOW}[!] Ollama saknas. Installera manuellt via AUR (yay -S ollama-bin) för AI-funktioner.${NC}"
fi

echo -e "${BLUE}"
echo "========================================================"
echo "   Installation Klar! 🚀"
echo "========================================================"
echo -e "${NC}"
echo "Starta systemet så här:"
echo "1. source venv/bin/activate"
echo "2. fava main.beancount"
echo ""
