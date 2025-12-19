#!/usr/bin/env python3
"""
Revolut OAuth Setup Script
Interaktiv konfiguration av Revolut Business API OAuth 2.0
"""

import sys
import os
from pathlib import Path

# Lägg till parent directory till path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.revolut_oauth import RevolutOAuth, interactive_setup
from agents.config import config
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)


def main():
    print("\n" + "="*70)
    print("   Revolut Business API - OAuth 2.0 Setup")
    print("   Efficra Consulting KB")
    print("="*70 + "\n")
    
    print("Detta script guidar dig genom OAuth-setup för Revolut Business API.")
    print("Du behöver:")
    print("  1. Ett Revolut Business-konto")
    print("  2. Tillgång till Business API settings\n")
    
    # Kontrollera om redan konfigurerat
    token_file = Path.home() / ".revolut" / "tokens.json"
    if token_file.exists():
        print(f"⚠️  Hittar befintlig konfiguration i {token_file}")
        response = input("Vill du konfigurera om? (y/N): ").strip().lower()
        if response != 'y':
            print("\nAvbryter. Använd befintlig konfiguration.")
            return
    
    # Välj miljö
    print("\n📍 MILJÖ")
    print("-" * 70)
    print("1. Production (riktiga transaktioner)")
    print("2. Sandbox (testmiljö)")
    
    env_choice = input("\nVälj miljö (1 eller 2): ").strip()
    sandbox = env_choice == "2"
    
    env_name = "Sandbox" if sandbox else "Production"
    api_url = "https://sandbox-business.revolut.com" if sandbox else "https://business.revolut.com"
    
    print(f"\n✓ Vald miljö: {env_name}")
    
    # Client ID
    print("\n🔑 CLIENT ID")
    print("-" * 70)
    print(f"1. Gå till: {api_url}/settings/api")
    print("2. Klicka 'Add API certificate' eller använd befintligt")
    
    client_id = input("\nAnge Client ID: ").strip()
    
    if not client_id:
        print("❌ Client ID krävs!")
        sys.exit(1)
    
    # Redirect URI
    print("\n🔗 REDIRECT URI")
    print("-" * 70)
    print("Detta är URL:en där du omdirigeras efter godkännande.")
    print("För lokal testning kan du använda: https://localhost:8080/callback")
    
    redirect_uri = input("\nRedirect URI [https://localhost:8080/callback]: ").strip()
    if not redirect_uri:
        redirect_uri = "https://localhost:8080/callback"
    
    # Scope
    print("\n🔐 API SCOPE")
    print("-" * 70)
    print("Välj vilka rättigheter som behövs:")
    print("  READ  - Läsa konton och transaktioner (rekommenderat)")
    print("  WRITE - Uppdatera counterparties och webhooks")
    print("  PAY   - Genomföra betalningar och växlingar")
    print("\nKomma-separera flera, t.ex: READ,WRITE")
    
    scope = input("\nScope [READ]: ").strip().upper()
    if not scope:
        scope = "READ"
    
    print(f"\n✓ Scope: {scope}")
    
    # Kör interactive setup
    try:
        oauth = interactive_setup(
            client_id=client_id,
            redirect_uri=redirect_uri,
            sandbox=sandbox,
            scope=scope
        )
        
        # Spara konfiguration till .env
        env_file = Path.cwd() / ".env"
        print(f"\n💾 SPARA KONFIGURATION")
        print("-" * 70)
        
        if env_file.exists():
            response = input(f"{env_file} finns redan. Uppdatera? (y/N): ").strip().lower()
            if response != 'y':
                print("\n✓ OAuth-setup klar! Tokens sparade.")
                print(f"  Token-fil: {oauth.token_file}")
                print(f"  Certifikat: {oauth.cert_dir}")
                return
        
        # Läs befintlig .env eller skapa ny
        env_content = {}
        if env_file.exists():
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_content[key.strip()] = value.strip()
        
        # Uppdatera Revolut-konfiguration
        env_content["REVOLUT_CLIENT_ID"] = f'"{client_id}"'
        env_content["REVOLUT_REDIRECT_URI"] = f'"{redirect_uri}"'
        env_content["REVOLUT_SANDBOX"] = f'"{str(sandbox).lower()}"'
        env_content["REVOLUT_OAUTH_ENABLED"] = '"true"'
        
        # Skriv tillbaka
        with open(env_file, "w") as f:
            f.write("# Efficra Consulting KB - Miljövariabler\n")
            f.write("# OAuth-konfiguration för Revolut Business API\n\n")
            for key, value in env_content.items():
                f.write(f"{key}={value}\n")
        
        print(f"\n✓ Konfiguration sparad i {env_file}")
        print(f"✓ Tokens sparade i {oauth.token_file}")
        print(f"✓ Certifikat i {oauth.cert_dir}")
        
        print("\n" + "="*70)
        print("   🎉 Setup Klar!")
        print("="*70)
        print("\nNästa steg:")
        print("  1. Testa anslutningen:")
        print("     python agents/revolut_sync_agent.py --test-connection")
        print("\n  2. Importera transaktioner:")
        print("     python agents/revolut_sync_agent.py --days 30")
        print("\n  3. Starta Fava:")
        print("     fava main.beancount\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup avbruten")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Setup misslyckades: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
