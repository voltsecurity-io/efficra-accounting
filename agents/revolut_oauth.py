"""
Revolut Business API OAuth 2.0 Authentication Handler
Hanterar certifikat, JWT-signering, token-förnyelse och säker lagring
"""

import os
import json
import time
import base64
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import logging
from dataclasses import dataclass, asdict
import requests

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.backends import default_backend
    from cryptography import x509
    from cryptography.x509.oid import NameOID
except ImportError:
    raise ImportError(
        "cryptography library krävs. Installera med: pip install cryptography"
    )

logger = logging.getLogger(__name__)


@dataclass
class TokenData:
    """Dataclass för token-information"""
    access_token: str
    refresh_token: Optional[str]
    token_type: str
    expires_at: float  # Unix timestamp
    created_at: float
    
    def is_expired(self, buffer_seconds: int = 300) -> bool:
        """Kontrollera om token har gått ut (med 5 min buffer)"""
        return time.time() >= (self.expires_at - buffer_seconds)
    
    def time_until_expiry(self) -> int:
        """Returnera sekunder tills token går ut"""
        return max(0, int(self.expires_at - time.time()))


class RevolutOAuth:
    """
    Hanterar OAuth 2.0-flödet för Revolut Business API
    
    Features:
    - Automatisk generering av certifikat
    - JWT-signering med RS256
    - Token-förnyelse med refresh tokens
    - Säker lagring av credentials
    - Automatisk återautentisering vid behov
    """
    
    def __init__(
        self,
        client_id: str,
        redirect_uri: str = "https://localhost:8080/callback",
        sandbox: bool = False,
        cert_dir: Optional[Path] = None,
        token_file: Optional[Path] = None
    ):
        """
        Initierar OAuth-handler
        
        Args:
            client_id: Client ID från Revolut Business API settings
            redirect_uri: OAuth redirect URI (samma som i Revolut settings)
            sandbox: True för sandbox, False för production
            cert_dir: Katalog för certifikat (default: ~/.revolut/certs)
            token_file: Fil för token-lagring (default: ~/.revolut/tokens.json)
        """
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.sandbox = sandbox
        
        # API endpoints
        self.base_url = (
            "https://sandbox-b2b.revolut.com" if sandbox 
            else "https://b2b.revolut.com"
        )
        self.auth_url = f"{self.base_url}/app-confirm"
        self.token_url = f"{self.base_url}/api/1.0/auth/token"
        
        # Paths för certifikat och tokens
        self.cert_dir = cert_dir or Path.home() / ".revolut" / "certs"
        self.cert_dir.mkdir(parents=True, exist_ok=True)
        
        self.private_key_path = self.cert_dir / "privatecert.pem"
        self.public_cert_path = self.cert_dir / "publiccert.cer"
        
        self.token_file = token_file or Path.home() / ".revolut" / "tokens.json"
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Ladda eller generera certifikat
        self._ensure_certificates()
        
        # Ladda sparade tokens
        self.token_data: Optional[TokenData] = self._load_tokens()
    
    def _ensure_certificates(self):
        """Säkerställ att certifikat finns, annars generera nya"""
        if not self.private_key_path.exists() or not self.public_cert_path.exists():
            logger.info("Genererar nya certifikat...")
            self.generate_certificates()
        else:
            logger.debug("Använder befintliga certifikat")
    
    def generate_certificates(
        self,
        country: str = "SE",
        organization: str = "Efficra Consulting KB",
        validity_days: int = 1825
    ) -> Tuple[Path, Path]:
        """
        Generera RSA-certifikat för Revolut API
        
        Args:
            country: Landskod (2 bokstäver)
            organization: Organisationsnamn
            validity_days: Giltighetstid i dagar (default: 5 år)
            
        Returns:
            Tuple med (private_key_path, public_cert_path)
        """
        logger.info("Genererar RSA 2048-bit certifikat...")
        
        # Generera privat nyckel
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Spara privat nyckel
        with open(self.private_key_path, "wb") as f:
            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
            )
        
        # Sätt restriktiva rättigheter på privat nyckel
        os.chmod(self.private_key_path, 0o600)
        
        # Generera självsignerat certifikat
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, country),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
        ])
        
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=validity_days))
            .sign(private_key, hashes.SHA256(), default_backend())
        )
        
        # Spara publikt certifikat
        with open(self.public_cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        logger.info(f"✓ Certifikat genererade i {self.cert_dir}")
        logger.info(f"  - Privat nyckel: {self.private_key_path.name}")
        logger.info(f"  - Publikt certifikat: {self.public_cert_path.name}")
        
        return self.private_key_path, self.public_cert_path
    
    def get_public_certificate(self) -> str:
        """Hämta publikt certifikat som sträng (för upload till Revolut)"""
        with open(self.public_cert_path, "r") as f:
            return f.read()
    
    def generate_jwt(self, expiry_seconds: int = 300) -> str:
        """
        Generera JWT för client assertion
        
        Args:
            expiry_seconds: JWT-giltighetstid i sekunder (default: 5 min)
            
        Returns:
            Signerad JWT-token
        """
        # JWT Header
        header = {
            "alg": "RS256",
            "typ": "JWT"
        }
        
        # JWT Payload
        now = int(time.time())
        # Extrahera domän utan port från redirect_uri
        domain = self.redirect_uri.split("://")[1].split("/")[0].split(":")[0]
        payload = {
            "iss": domain,  # Endast domän, ingen port
            "sub": self.client_id,
            "aud": "https://revolut.com",
            "exp": now + expiry_seconds
        }
        
        # Base64 URL-encode header och payload
        header_b64 = self._base64url_encode(json.dumps(header, separators=(',', ':')))
        payload_b64 = self._base64url_encode(json.dumps(payload, separators=(',', ':')))
        
        # Signera med privat nyckel
        message = f"{header_b64}.{payload_b64}".encode()
        
        with open(self.private_key_path, "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )
        
        signature = private_key.sign(
            message,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        
        signature_b64 = self._base64url_encode(signature)
        
        jwt = f"{header_b64}.{payload_b64}.{signature_b64}"
        logger.debug(f"JWT genererad (exp: {expiry_seconds}s)")
        
        return jwt
    
    @staticmethod
    def _base64url_encode(data) -> str:
        """Base64 URL-safe encoding utan padding"""
        if isinstance(data, str):
            data = data.encode()
        return base64.urlsafe_b64encode(data).decode().rstrip('=')
    
    def get_authorization_url(self, scope: Optional[str] = None) -> str:
        """
        Generera authorization URL för manuell consent
        
        Args:
            scope: Komma-separerad lista av scopes (READ, WRITE, PAY, READ_SENSITIVE_CARD_DATA)
                   Default: None (alla tillgängliga scopes)
        
        Returns:
            URL för att godkänna åtkomst
        """
        url = (
            f"{self.auth_url}"
            f"?client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&response_type=code"
        )
        
        if scope:
            url += f"&scope={scope}"
        
        return url
    
    def exchange_code_for_token(self, authorization_code: str) -> TokenData:
        """
        Byt authorization code mot access token
        
        Args:
            authorization_code: Authorization code från redirect URI
            
        Returns:
            TokenData med access och refresh tokens
        """
        logger.info("Byter authorization code mot access token...")
        
        jwt = self.generate_jwt()
        
        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": jwt
        }
        
        response = requests.post(
            self.token_url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        response.raise_for_status()
        token_response = response.json()
        
        # Skapa TokenData
        now = time.time()
        token_data = TokenData(
            access_token=token_response["access_token"],
            refresh_token=token_response.get("refresh_token"),
            token_type=token_response["token_type"],
            expires_at=now + token_response["expires_in"],
            created_at=now
        )
        
        # Spara tokens
        self._save_tokens(token_data)
        self.token_data = token_data
        
        logger.info("✓ Access token erhållen")
        return token_data
    
    def refresh_access_token(self) -> TokenData:
        """
        Förnya access token med refresh token
        
        Returns:
            Ny TokenData
            
        Raises:
            ValueError: Om ingen refresh token finns
        """
        if not self.token_data or not self.token_data.refresh_token:
            raise ValueError("Ingen refresh token tillgänglig. Kör fullständig autentisering igen.")
        
        logger.info("Förnyar access token...")
        
        jwt = self.generate_jwt()
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.token_data.refresh_token,
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": jwt
        }
        
        response = requests.post(
            self.token_url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        response.raise_for_status()
        token_response = response.json()
        
        # Uppdatera TokenData (behåll gamla refresh token om ingen ny returneras)
        now = time.time()
        token_data = TokenData(
            access_token=token_response["access_token"],
            refresh_token=token_response.get("refresh_token", self.token_data.refresh_token),
            token_type=token_response["token_type"],
            expires_at=now + token_response["expires_in"],
            created_at=now
        )
        
        # Spara uppdaterade tokens
        self._save_tokens(token_data)
        self.token_data = token_data
        
        logger.info(f"✓ Access token förnyad (giltig i {token_data.time_until_expiry()//60} min)")
        return token_data
    
    def get_access_token(self, auto_refresh: bool = True) -> str:
        """
        Hämta giltig access token (förnyar automatiskt vid behov)
        
        Args:
            auto_refresh: Automatiskt förnya token om den gått ut
            
        Returns:
            Giltig access token
            
        Raises:
            ValueError: Om ingen token finns och auto_refresh är False
        """
        if not self.token_data:
            raise ValueError(
                "Ingen access token tillgänglig. Kör authenticate() först."
            )
        
        # Kontrollera om token har gått ut
        if self.token_data.is_expired():
            if not auto_refresh:
                raise ValueError("Access token har gått ut")
            
            logger.info("Access token har gått ut, förnyar...")
            self.refresh_access_token()
        
        return self.token_data.access_token
    
    def _save_tokens(self, token_data: TokenData):
        """Spara tokens till disk (krypterat)"""
        data = asdict(token_data)
        
        # Sätt restriktiva rättigheter före skrivning
        if self.token_file.exists():
            os.chmod(self.token_file, 0o600)
        
        with open(self.token_file, "w") as f:
            json.dump(data, f, indent=2)
        
        os.chmod(self.token_file, 0o600)
        logger.debug(f"Tokens sparade i {self.token_file}")
    
    def _load_tokens(self) -> Optional[TokenData]:
        """Ladda sparade tokens från disk"""
        if not self.token_file.exists():
            return None
        
        try:
            with open(self.token_file, "r") as f:
                data = json.load(f)
            
            token_data = TokenData(**data)
            
            if token_data.is_expired(buffer_seconds=0):
                logger.warning("Sparad access token har gått ut")
            else:
                logger.info(f"Laddat token (giltig i {token_data.time_until_expiry()//60} min)")
            
            return token_data
            
        except Exception as e:
            logger.error(f"Kunde inte ladda tokens: {e}")
            return None
    
    def clear_tokens(self):
        """Rensa sparade tokens"""
        if self.token_file.exists():
            self.token_file.unlink()
            logger.info("Tokens rensade")
        self.token_data = None
    
    def is_authenticated(self) -> bool:
        """Kontrollera om vi har en giltig token"""
        return (
            self.token_data is not None 
            and not self.token_data.is_expired()
        )
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Hämta authorization headers för API-requests"""
        token = self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }


def interactive_setup(
    client_id: str,
    redirect_uri: str = "https://localhost:8080/callback",
    sandbox: bool = False,
    scope: str = "READ"
) -> RevolutOAuth:
    """
    Interaktiv setup-process för Revolut OAuth
    
    Args:
        client_id: Client ID från Revolut
        redirect_uri: OAuth redirect URI
        sandbox: Sandbox eller production
        scope: API scopes (READ, WRITE, PAY)
        
    Returns:
        Konfigurerad RevolutOAuth-instans
    """
    print("\n" + "="*60)
    print("   Revolut Business API - OAuth Setup")
    print("="*60 + "\n")
    
    oauth = RevolutOAuth(
        client_id=client_id,
        redirect_uri=redirect_uri,
        sandbox=sandbox
    )
    
    # Visa publikt certifikat
    print("📜 STEG 1: Ladda upp certifikat till Revolut")
    print("-" * 60)
    print("\n1. Gå till: https://business.revolut.com/settings/api")
    print("2. Klicka 'Add API certificate'")
    print("3. Kopiera och klistra in detta certifikat:\n")
    print(oauth.get_public_certificate())
    print("\n4. Ange OAuth redirect URI:", redirect_uri)
    print("5. Kopiera Client ID och tryck Enter här...")
    input()
    
    # Authorization URL
    print("\n🔐 STEG 2: Godkänn åtkomst")
    print("-" * 60)
    auth_url = oauth.get_authorization_url(scope=scope)
    print("\n1. Öppna denna URL i din webbläsare:")
    print(f"\n{auth_url}\n")
    print("2. Logga in och godkänn åtkomst")
    print("3. Du kommer att omdirigeras till:", redirect_uri)
    print("4. Kopiera 'code' parametern från URL:en")
    print("\nExempel: https://localhost:8080/callback?code=oa_prod_ABC123...")
    print("         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
    
    authorization_code = input("\nKlistra in authorization code: ").strip()
    
    # Byt code mot token
    try:
        token_data = oauth.exchange_code_for_token(authorization_code)
        
        print("\n" + "="*60)
        print("   ✅ Setup Klar!")
        print("="*60)
        print(f"\n✓ Access token erhållen")
        print(f"✓ Giltig i {token_data.time_until_expiry()//60} minuter")
        print(f"✓ Tokens sparade i {oauth.token_file}")
        print(f"\nDu kan nu använda API:et! 🚀")
        
        return oauth
        
    except Exception as e:
        print(f"\n❌ Fel vid token-exchange: {e}")
        raise


if __name__ == "__main__":
    # Exempel på användning
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python revolut_oauth.py <client_id> [redirect_uri] [sandbox]")
        print("\nExempel:")
        print("  python revolut_oauth.py 'your_client_id'")
        print("  python revolut_oauth.py 'your_client_id' 'https://example.com' true")
        sys.exit(1)
    
    client_id = sys.argv[1]
    redirect_uri = sys.argv[2] if len(sys.argv) > 2 else "https://localhost:8080/callback"
    sandbox = sys.argv[3].lower() == "true" if len(sys.argv) > 3 else False
    
    oauth = interactive_setup(client_id, redirect_uri, sandbox)
