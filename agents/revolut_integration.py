"""
Revolut Business & Exchange API Integration
Hanterar automatisk synkronisering av transaktioner och valutaväxlingar
"""

import os
import requests
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import List, Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)


class RevolutAPI:
    """Base class för Revolut API-kommunikation med OAuth-stöd"""

    def __init__(self, oauth_handler=None, api_key: str = None, base_url: str = None, sandbox: bool = False):
        """
        Initialisera API med antingen OAuth-handler eller direkt API-nyckel
        
        Args:
            oauth_handler: RevolutOAuth-instans (rekommenderat för production)
            api_key: Direkt Bearer token (deprecated, för bakåtkompatibilitet)
            base_url: API base URL
            sandbox: Sandbox-läge
        """
        self.oauth = oauth_handler
        self.sandbox = sandbox
        self.base_url = base_url or (
            "https://sandbox-b2b.revolut.com/api/1.0"
            if sandbox
            else "https://b2b.revolut.com/api/1.0"
        )
        
        self.session = requests.Session()
        
        # Använd OAuth om tillgängligt, annars fallback till direkt API-nyckel
        if not oauth_handler and api_key:
            logger.warning("Använder direkt API-nyckel. För production, använd OAuth!")
            self.session.headers.update({
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            })

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Gör en API-förfrågan med automatisk token-förnyelse"""
        url = f"{self.base_url}{endpoint}"
        
        # Uppdatera headers med OAuth om tillgängligt
        if self.oauth:
            try:
                headers = self.oauth.get_auth_headers()
                if 'headers' in kwargs:
                    kwargs['headers'].update(headers)
                else:
                    kwargs['headers'] = headers
            except Exception as e:
                logger.error(f"OAuth token-fel: {e}")
                raise ValueError("OAuth-autentisering misslyckades. Kör authenticate() igen.")
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401 and self.oauth:
                # Token kan ha gått ut, försök förnya
                logger.info("401 Unauthorized - försöker förnya token...")
                try:
                    self.oauth.refresh_access_token()
                    # Försök igen med ny token
                    headers = self.oauth.get_auth_headers()
                    if 'headers' in kwargs:
                        kwargs['headers'].update(headers)
                    else:
                        kwargs['headers'] = headers
                    response = self.session.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response.json() if response.content else {}
                except Exception as refresh_error:
                    logger.error(f"Token-förnyelse misslyckades: {refresh_error}")
                    raise
            logger.error(f"Revolut API-fel: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Revolut API-fel: {e}")
            raise


class RevolutBusiness(RevolutAPI):
    """Revolut Business API - hanterar transaktioner och konton"""

    def __init__(self, oauth_handler=None, api_key: str = None, sandbox: bool = False):
        """
        Initialisera Business API
        
        Args:
            oauth_handler: RevolutOAuth-instans (rekommenderat)
            api_key: Direkt Bearer token (deprecated)
            sandbox: Sandbox-läge
        """
        super().__init__(oauth_handler=oauth_handler, api_key=api_key, sandbox=sandbox)

    def get_accounts(self) -> List[Dict]:
        """Hämta alla konton"""
        return self._request("GET", "/accounts")

    def get_account(self, account_id: str) -> Dict:
        """Hämta specifikt konto"""
        return self._request("GET", f"/accounts/{account_id}")

    def get_transactions(
        self,
        account_id: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100,
        transaction_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Hämta transaktioner
        
        Args:
            account_id: Specifikt konto (filtrerar på account_id)
            from_date: Från datum (ISO 8601)
            to_date: Till datum (ISO 8601)
            limit: Max antal transaktioner (max 1000 per request)
            transaction_type: Typ av transaktion (atm, card_payment, card_refund, 
                            card_chargeback, card_credit, exchange, transfer, loan, 
                            fee, refund, topup, topup_return, tax, tax_refund)
        
        Note:
            API returnerar max 1000 transaktioner per request.
            Transaktioner sorteras efter created_at i omvänd kronologisk ordning.
        """
        params = {"count": min(limit, 1000)}  # API max är 1000
        
        if from_date:
            params["from"] = from_date.isoformat()
        if to_date:
            params["to"] = to_date.isoformat()
        if account_id:
            params["account"] = account_id
        if transaction_type:
            params["type"] = transaction_type

        return self._request("GET", "/transactions", params=params)

    def get_counterparties(self) -> List[Dict]:
        """Hämta alla motparter (leverantörer/kunder)"""
        return self._request("GET", "/counterparties")


class RevolutExchange:
    """Revolut Foreign Exchange - hanterar valutaväxlingar via Business API"""

    def __init__(self, business_api: RevolutBusiness):
        self.api = business_api

    def get_exchange_rate(self, from_currency: str, to_currency: str, amount: Optional[Decimal] = None) -> Dict:
        """
        Hämta aktuell växelkurs
        
        Args:
            from_currency: Valuta att växla från (ISO 4217)
            to_currency: Valuta att växla till (ISO 4217)
            amount: Belopp att växla (optional)
            
        Returns:
            Växelkursinformation
        """
        params = {
            "from": from_currency,
            "to": to_currency
        }
        if amount:
            params["amount"] = float(amount)
        
        return self.api._request("GET", "/rate", params=params)

    def create_exchange(
        self,
        from_account: str,
        to_account: str,
        from_currency: str,
        to_currency: str,
        amount: Decimal,
        reference: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict:
        """
        Skapa en valutaväxling
        
        Args:
            from_account: Source account ID
            to_account: Target account ID
            from_currency: Valuta att växla från
            to_currency: Valuta att växla till
            amount: Belopp att växla
            reference: Frivillig referens
            request_id: Idempotency key
        """
        payload = {
            "from": {
                "account_id": from_account,
                "currency": from_currency,
                "amount": float(amount)
            },
            "to": {
                "account_id": to_account,
                "currency": to_currency
            }
        }
        
        if reference:
            payload["reference"] = reference
        if request_id:
            payload["request_id"] = request_id
            
        return self.api._request("POST", "/exchange", json=payload)

    def get_exchanges(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Hämta valutaväxlingar (exchange transactions)
        Använder transactions endpoint med type=exchange filter
        """
        return self.api.get_transactions(
            from_date=from_date,
            to_date=to_date,
            transaction_type="exchange"
        )


class RevolutToBeancount:
    """Konverterar Revolut-transaktioner till Beancount-format"""

    def __init__(self, config):
        self.config = config
        self.currency_map = self._load_currency_mapping()
        self.account_map = self._load_account_mapping()

    def _load_currency_mapping(self) -> Dict[str, str]:
        """Ladda valutamappning för Beancount"""
        # Standard mappning - kan utökas via config
        return {
            "SEK": "SEK",
            "EUR": "EUR",
            "USD": "USD",
            "GBP": "GBP",
            "NOK": "NOK",
            "DKK": "DKK"
        }

    def _load_account_mapping(self) -> Dict[str, str]:
        """Ladda kontomappning till Beancount-konton"""
        # Exempel på mappning - skall konfigureras per användare
        return {
            "business_sek": "Assets:Bank:Revolut:SEK",
            "business_eur": "Assets:Bank:Revolut:EUR",
            "business_usd": "Assets:Bank:Revolut:USD",
            "default": "Assets:Bank:Revolut"
        }

    def transaction_to_beancount(self, transaction: Dict) -> str:
        """
        Konvertera en Revolut-transaktion till Beancount-format
        
        Args:
            transaction: Revolut transaction dict med legs
            
        Returns:
            Beancount transaction string
        """
        # Använd completed_at om finns, annars created_at
        date_str = transaction.get("completed_at") or transaction.get("created_at")
        date = datetime.fromisoformat(
            date_str.replace("Z", "+00:00")
        ).strftime("%Y-%m-%d")
        
        # Hämta description från första leg
        legs = transaction.get("legs", [])
        if not legs:
            logger.warning(f"Transaction {transaction.get('id')} har inga legs")
            return ""
        
        first_leg = legs[0]
        description = first_leg.get("description", "Revolut Transaction")
        
        # Bestäm kontotyp
        tx_type = transaction.get("type", "")
        state = transaction.get("state", "")
        
        # Skippa pending transactions
        if state == "pending":
            logger.debug(f"Skippar pending transaction {transaction.get('id')}")
            return ""
        
        # Bygg Beancount-transaktion
        state_flag = "*" if state == "completed" else "!"
        lines = [
            f'{date} {state_flag} "{description}"',
            f'  revolut_id: "{transaction["id"]}"'
        ]
        
        # Lägg till merchant info om det finns
        if "merchant" in transaction:
            merchant = transaction["merchant"]
            merchant_name = merchant.get("name", "")
            if merchant_name:
                lines.append(f'  merchant: "{merchant_name}"')
        
        # Lägg till reference om det finns
        if transaction.get("reference"):
            lines.append(f'  reference: "{transaction["reference"]}"')
        
        # Lägg till tags baserat på typ
        if tx_type:
            lines[0] += f' #{tx_type.lower().replace("_", "-")}'
        
        # Hantera legs (en transaktion kan ha flera legs för olika konton)
        for leg in legs:
            amount = Decimal(str(leg["amount"]))
            currency = leg["currency"]
            account_id = leg.get("account_id", "")
            
            # Bestäm Beancount-konto baserat på account_id och currency
            beancount_account = self._get_account_for_leg(leg)
            
            lines.append(f"  {beancount_account}  {amount} {currency}")
            
            # Lägg till fee om det finns
            fee = leg.get("fee")
            if fee and float(fee) != 0:
                lines.append(f"  Expenses:Banking:Fees  {fee} {currency}")
        
        # Om endast en leg, lägg till motkonto
        if len(legs) == 1:
            category = self._categorize_transaction(transaction)
            lines.append(f"  {category}")
        
        return "\n".join(lines) + "\n"
    
    def _get_account_for_leg(self, leg: Dict) -> str:
        """Bestäm Beancount-konto för en transaction leg"""
        currency = leg["currency"]
        account_id = leg.get("account_id", "")
        
        # Försök hitta mappat konto
        for key, account in self.account_map.items():
            if account_id in key or currency.lower() in key:
                return account
        
        # Default: Assets:Bank:Revolut:CURRENCY
        return f"Assets:Bank:Revolut:{currency}"

    def exchange_to_beancount(self, exchange: Dict) -> str:
        """
        Konvertera en valutaväxling till Beancount-format
        Exchange transaktioner har type="exchange" och har legs för båda sidor
        
        Args:
            exchange: Revolut exchange transaction dict
            
        Returns:
            Beancount transaction string
        """
        # Exchange är en vanlig transaction med type=exchange
        # Den har redan legs så vi kan använda transaction_to_beancount
        return self.transaction_to_beancount(exchange)

    def _categorize_transaction(self, transaction: Dict) -> str:
        """
        Kategorisera transaktion till rätt Beancount-konto
        Använder AI eller regler för kategorisering
        """
        tx_type = transaction.get("type", "").lower()
        description = transaction.get("description", "").lower()
        
        # Enkla regler (kan utökas med AI)
        if tx_type == "transfer":
            return "Assets:Bank:Other"
        elif "fee" in description or "charge" in description:
            return "Expenses:Banking:Fees"
        elif "salary" in description or "lön" in description:
            return "Income:Salary"
        elif any(word in description for word in ["restaurant", "lunch", "dinner"]):
            return "Expenses:Food:Restaurant"
        elif any(word in description for word in ["hotel", "airbnb", "booking"]):
            return "Expenses:Travel:Accommodation"
        else:
            # Default till Expenses:Unknown för manuell kategorisering
            return "Expenses:Unknown"


class RevolutSync:
    """Huvudklass för synkronisering av Revolut-data till Beancount"""

    def __init__(
        self,
        business_api_key: str,
        exchange_api_key: Optional[str] = None,  # Inte längre använd, behålls för bakåtkompatibilitet
        sandbox: bool = False,
        config=None
    ):
        self.business = RevolutBusiness(business_api_key, sandbox)
        self.exchange = RevolutExchange(self.business)
        self.converter = RevolutToBeancount(config)
        self.config = config
        self.output_dir = Path(config.DATA_LEDGER if config else "data/ledger")

    def sync_transactions(
        self,
        days_back: int = 7,
        output_file: Optional[str] = None
    ) -> str:
        """
        Synkronisera transaktioner från Revolut till Beancount
        
        Args:
            days_back: Antal dagar bakåt att hämta
            output_file: Outputfil (None = auto-genererad)
            
        Returns:
            Path till skapad fil
        """
        logger.info(f"Synkroniserar Revolut-transaktioner ({days_back} dagar bakåt)...")
        
        # Hämta transaktioner
        from_date = datetime.now() - timedelta(days=days_back)
        transactions = self.business.get_transactions(from_date=from_date)
        
        logger.info(f"Hittade {len(transactions)} transaktioner")
        
        # Konvertera till Beancount
        beancount_entries = []
        for tx in transactions:
            try:
                entry = self.converter.transaction_to_beancount(tx)
                beancount_entries.append(entry)
            except Exception as e:
                logger.error(f"Kunde inte konvertera transaktion {tx.get('id')}: {e}")
        
        # Spara till fil
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"revolut_import_{timestamp}.beancount"
        else:
            output_file = Path(output_file)
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"; Revolut Import - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"; Importerade {len(beancount_entries)} transaktioner\n\n")
            f.writelines(beancount_entries)
        
        logger.info(f"Sparade {len(beancount_entries)} transaktioner till {output_file}")
        return str(output_file)

    def sync_exchanges(
        self,
        days_back: int = 30,
        output_file: Optional[str] = None
    ) -> Optional[str]:
        """
        Synkronisera valutaväxlingar (exchange transactions)
        
        Args:
            days_back: Antal dagar bakåt att hämta
            output_file: Outputfil (None = auto-genererad)
            
        Returns:
            Path till skapad fil
        """
        logger.info(f"Synkroniserar valutaväxlingar ({days_back} dagar bakåt)...")
        
        # Hämta exchange transactions
        from_date = datetime.now() - timedelta(days=days_back)
        exchanges = self.exchange.get_exchanges(from_date=from_date)
        
        logger.info(f"Hittade {len(exchanges)} valutaväxlingar")
        
        # Konvertera till Beancount
        beancount_entries = []
        for ex in exchanges:
            try:
                entry = self.converter.exchange_to_beancount(ex)
                beancount_entries.append(entry)
            except Exception as e:
                logger.error(f"Kunde inte konvertera växling {ex.get('id')}: {e}")
        
        # Spara till fil
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"revolut_exchanges_{timestamp}.beancount"
        else:
            output_file = Path(output_file)
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"; Revolut Exchange Import - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"; Importerade {len(beancount_entries)} valutaväxlingar\n\n")
            f.writelines(beancount_entries)
        
        logger.info(f"Sparade {len(beancount_entries)} växlingar till {output_file}")
        return str(output_file)

    def get_balances(self) -> Dict[str, Dict]:
        """
        Hämta aktuella balanser från alla Revolut-konton
        
        Returns:
            Dict med konto-ID som nyckel och balance info som värde
        """
        accounts = self.business.get_accounts()
        balances = {}
        
        for account in accounts:
            account_id = account["id"]
            balances[account_id] = {
                "name": account.get("name", "Unknown"),
                "currency": account["currency"],
                "balance": Decimal(str(account["balance"])),
                "state": account.get("state", "unknown")
            }
        
        return balances


# Convenience function för snabb användning
def quick_sync(
    business_api_key: str,
    exchange_api_key: Optional[str] = None,  # Deprecated, behålls för bakåtkompatibilitet
    days_back: int = 7,
    sandbox: bool = False
):
    """
    Snabb synkronisering av Revolut-data
    
    Usage:
        from agents.revolut_integration import quick_sync
        quick_sync("your_api_key", days_back=30)
    
    Note:
        exchange_api_key är inte längre nödvändig - Foreign Exchange är del av Business API
    """
    from .config import config
    
    sync = RevolutSync(business_api_key, None, sandbox, config)
    
    # Synka transaktioner
    tx_file = sync.sync_transactions(days_back=days_back)
    print(f"✓ Transaktioner sparade: {tx_file}")
    
    # Synka växlingar
    ex_file = sync.sync_exchanges(days_back=days_back)
    if ex_file:
        print(f"✓ Valutaväxlingar sparade: {ex_file}")
    
    # Visa balanser
    balances = sync.get_balances()
    print("\n💰 Aktuella balanser:")
    for account_id, info in balances.items():
        print(f"  {info['name']}: {info['balance']} {info['currency']}")
