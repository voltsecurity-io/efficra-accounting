# Makefile för Efficra Accounting System

.PHONY: help install dev test lint format clean run backup

help: ## Visa detta hjälpmeddelande
	@echo "Tillgängliga kommandon:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Installera systemet
	./setup.sh

dev: ## Aktivera utvecklingsmiljö
	@echo "Kör: source venv/bin/activate"

run: ## Starta Fava web UI
	venv/bin/fava main.beancount

test: ## Kör alla tester
	venv/bin/pytest tests/ -v

test-cov: ## Kör tester med coverage
	venv/bin/pytest tests/ -v --cov=agents --cov-report=html

lint: ## Kontrollera kod med flake8
	venv/bin/flake8 agents/ tests/

format: ## Formatera kod med black
	venv/bin/black agents/ tests/

format-check: ## Kontrollera formatering
	venv/bin/black --check agents/ tests/

backup: ## Skapa backup av bokföring
	@mkdir -p backups
	@tar -czf backups/efficra_backup_$$(date +%Y%m%d_%H%M%S).tar.gz main.beancount data/ledger/
	@echo "Backup skapad i backups/"

clean: ## Rensa temporära filer
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage

update: ## Uppdatera dependencies
	venv/bin/pip install --upgrade pip
	venv/bin/pip install -r requirements.txt --upgrade

.DEFAULT_GOAL := help
