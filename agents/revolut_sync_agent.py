#!/usr/bin/env python3
"""
Revolut Sync Agent
Automatisk synkronisering av Revolut-transaktioner och valutaväxlingar till Beancount
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Lägg till parent directory till path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.config import config
from agents.revolut_integration import RevolutSync

# Konfigurera loggning
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RevolutSyncAgent:
    """Agent för automatisk synkronisering av Revolut-data"""

    def __init__(self):
        self.config = config
        self.sync = None
        self._initialize_sync()

    def _initialize_sync(self):
        """Initialisera Revolut-synkronisering"""
        if not self.config.REVOLUT_BUSINESS_API_KEY:
            logger.error("REVOLUT_BUSINESS_API_KEY saknas i konfigurationen!")
            logger.info("Lägg till din API-nyckel i .env filen")
            return

        logger.info("Initierar Revolut-synkronisering...")
        logger.info(f"Sandbox-läge: {self.config.REVOLUT_SANDBOX}")

        try:
            self.sync = RevolutSync(
                business_api_key=self.config.REVOLUT_BUSINESS_API_KEY,
                exchange_api_key=self.config.REVOLUT_EXCHANGE_API_KEY or None,
                sandbox=self.config.REVOLUT_SANDBOX,
                config=self.config
            )
            logger.info("✓ Revolut-synkronisering initierad")
        except Exception as e:
            logger.error(f"Kunde inte initiera Revolut-synkronisering: {e}")
            raise

    def run_sync(self, days_back: int = None, sync_exchanges: bool = True):
        """
        Kör synkronisering
        
        Args:
            days_back: Antal dagar bakåt (None = använd config)
            sync_exchanges: Synkronisera också valutaväxlingar
        """
        if not self.sync:
            logger.error("Revolut-synkronisering inte initierad!")
            return False

        days = days_back or self.config.REVOLUT_SYNC_DAYS
        logger.info(f"🔄 Startar synkronisering ({days} dagar bakåt)...")

        try:
            # Synka transaktioner
            tx_file = self.sync.sync_transactions(days_back=days)
            logger.info(f"✓ Transaktioner sparade: {tx_file}")
            print(f"\n✅ Transaktioner importerade till: {tx_file}")

            # Synka valutaväxlingar (del av Business API)
            if sync_exchanges:
                ex_file = self.sync.sync_exchanges(days_back=days)
                if ex_file:
                    logger.info(f"✓ Valutaväxlingar sparade: {ex_file}")
                    print(f"\n✅ Valutaväxlingar importerade till: {ex_file}")

            # Visa balanser
            self.show_balances()

            return True

        except Exception as e:
            logger.error(f"Synkronisering misslyckades: {e}")
            print(f"\n❌ Fel vid synkronisering: {e}")
            return False

    def show_balances(self):
        """Visa aktuella balanser"""
        try:
            balances = self.sync.get_balances()
            
            print("\n💰 Aktuella Revolut-balanser:")
            print("=" * 50)
            
            total_sek = 0
            for account_id, info in balances.items():
                status = "✓" if info["state"] == "active" else "⚠"
                print(f"{status} {info['name']:20s}: {info['balance']:>12.2f} {info['currency']}")
                
                # Konvertera till SEK för total (förenklad beräkning)
                if info['currency'] == 'SEK':
                    total_sek += float(info['balance'])
            
            print("=" * 50)
            if total_sek > 0:
                print(f"  {'Total (SEK)':20s}: {total_sek:>12.2f} SEK")
            
        except Exception as e:
            logger.error(f"Kunde inte hämta balanser: {e}")

    def check_api_connection(self):
        """Testa API-anslutning"""
        logger.info("Testar Revolut API-anslutning...")
        print("\n🔌 Testar Revolut API-anslutning...")

        try:
            if not self.sync:
                print("❌ Synkronisering inte initierad - kontrollera API-nyckel")
                return False

            # Testa att hämta konton
            accounts = self.sync.business.get_accounts()
            print(f"✅ Anslutning OK - hittade {len(accounts)} konton")
            
            for acc in accounts:
                print(f"   • {acc.get('name', 'Unknown')} ({acc['currency']})")
            
            # Testa Exchange (del av Business API)
            try:
                rate = self.sync.exchange.get_exchange_rate("EUR", "SEK")
                print(f"✅ Foreign Exchange OK - EUR/SEK: {rate.get('rate', 'N/A')}")
            except Exception as e:
                print(f"⚠️  Foreign Exchange: {e}")
            
            return True

        except Exception as e:
            print(f"❌ Anslutning misslyckades: {e}")
            logger.error(f"API-anslutning misslyckades: {e}")
            return False


def main():
    """Huvudprogram"""
    parser = argparse.ArgumentParser(
        description="Revolut Sync Agent - Synkronisera transaktioner till Beancount"
    )
    parser.add_argument(
        "--days",
        type=int,
        help=f"Antal dagar bakåt att synkronisera (standard: {config.REVOLUT_SYNC_DAYS})"
    )
    parser.add_argument(
        "--no-exchanges",
        action="store_true",
        help="Hoppa över synkronisering av valutaväxlingar"
    )
    parser.add_argument(
        "--test-connection",
        action="store_true",
        help="Testa API-anslutning och avsluta"
    )
    parser.add_argument(
        "--show-balances",
        action="store_true",
        help="Visa balanser och avsluta"
    )

    args = parser.parse_args()

    # Banner
    print("\n" + "=" * 60)
    print("   Revolut Sync Agent - Efficra Accounting System")
    print("=" * 60 + "\n")

    try:
        agent = RevolutSyncAgent()

        # Test-läge
        if args.test_connection:
            agent.check_api_connection()
            return

        # Visa balanser
        if args.show_balances:
            agent.show_balances()
            return

        # Kör synkronisering
        success = agent.run_sync(
            days_back=args.days,
            sync_exchanges=not args.no_exchanges
        )

        if success:
            print("\n✅ Synkronisering klar!")
            print(f"\nNästa steg:")
            print(f"1. Granska importerade transaktioner i data/ledger/")
            print(f"2. Inkludera filen i main.beancount")
            print(f"3. Öppna Fava för att verifiera: fava main.beancount")
        else:
            print("\n❌ Synkronisering misslyckades - se logg för detaljer")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Avbruten av användare")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Oväntat fel: {e}", exc_info=True)
        print(f"\n❌ Oväntat fel: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
