# core/security.py
import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector
import random
import stem.process
from stem.control import Controller
import cryptography.fernet
from typing import List, Optional

class SecurityManager:
    def __init__(self):
        self.tor_process = None
        self.fernet = cryptography.fernet.Fernet(
            cryptography.fernet.Fernet.generate_key()
        )
        self.user_agents = self._load_user_agents()
        self.proxies = self._load_proxies()
        
    def _load_user_agents(self) -> List[str]:
        """Charge une liste de User-Agents variés"""
        return [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        ]
    
    def _load_proxies(self) -> List[str]:
        """Charge la liste des proxies"""
        # Peut être étendu avec des proxies premium
        return [
            'socks5://127.0.0.1:9050'  # Tor par défaut
        ]
    
    async def start_tor(self):
        """Démarre le service Tor"""
        try:
            self.tor_process = stem.process.launch_tor_with_config(
                config={
                    'SocksPort': '9050',
                    'ControlPort': '9051',
                    'DataDirectory': '/tmp/tor-osint'
                }
            )
        except Exception as e:
            print(f"Tor start failed: {e}")
    
    async def get_secure_session(self, use_tor: bool = True) -> aiohttp.ClientSession:
        """Crée une session HTTP sécurisée"""
        connector = None
        
        if use_tor:
            connector = ProxyConnector.from_url(
                random.choice(self.proxies)
            )
        
        timeout = aiohttp.ClientTimeout(total=30)
        session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': random.choice(self.user_agents)
            }
        )
        
        return session
    
    def encrypt_data(self, data: str) -> bytes:
        """Chiffre les données sensibles"""
        return self.fernet.encrypt(data.encode())
    
    def decrypt_data(self, encrypted_data: bytes) -> str:
        """Déchiffre les données"""
        return self.fernet.decrypt(encrypted_data).decode()
    
    async def rotate_identity(self):
        """Change l'identité Tor"""
        with Controller.from_port(port=9051) as controller:
            controller.authenticate()
            controller.signal('NEWNYM')
