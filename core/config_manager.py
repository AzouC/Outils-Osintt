# core/config_manager.py
import yaml
import os
import logging
from typing import Dict, Any, Optional

class ConfigManager:
    def __init__(self):
        self.settings = {}
        self.api_keys = {}
        self.proxies = []
        self.logger = logging.getLogger(__name__)
        self.load_all_configs()
    
    def load_all_configs(self):
        """Charge toutes les configurations"""
        self.settings = self._load_settings()
        self.api_keys = self._load_api_keys()
        self.proxies = self._load_proxies()
        
    def _load_settings(self) -> Dict[str, Any]:
        """Charge la configuration principale"""
        settings_path = 'config/settings.yaml'
        
        if not os.path.exists(settings_path):
            self.logger.warning("settings.yaml non trouvé, utilisation des valeurs par défaut")
            return self._get_default_settings()
        
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = yaml.safe_load(f) or {}
                return {**self._get_default_settings(), **settings}
        except Exception as e:
            self.logger.error(f"Erreur chargement settings.yaml: {e}")
            return self._get_default_settings()
    
    def _load_api_keys(self) -> Dict[str, Any]:
        """Charge les clés API"""
        api_keys_path = 'config/api_keys.yaml'
        
        if not os.path.exists(api_keys_path):
            self.logger.warning("api_keys.yaml non trouvé")
            return {}
        
        try:
            with open(api_keys_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            self.logger.error(f"Erreur chargement api_keys.yaml: {e}")
            return {}
    
    def _load_proxies(self) -> list:
        """Charge la configuration des proxies"""
        proxies_path = 'config/proxies.yaml'
        
        if not os.path.exists(proxies_path):
            self.logger.info("proxies.yaml non trouvé, utilisation de Tor par défaut")
            return ['socks5://127.0.0.1:9050']  # Tor par défaut
        
        try:
            with open(proxies_path, 'r', encoding='utf-8') as f:
                proxies_config = yaml.safe_load(f) or {}
                
                # Essayer différents formats de configuration
                if 'proxies' in proxies_config:
                    return proxies_config['proxies']
                elif 'tor_proxies' in proxies_config:
                    return proxies_config['tor_proxies']
                elif 'free_proxies' in proxies_config:
                    return proxies_config['free_proxies']
                else:
                    return ['socks5://127.0.0.1:9050']
                    
        except Exception as e:
            self.logger.error(f"Erreur chargement proxies.yaml: {e}")
            return ['socks5://127.0.0.1:9050']
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Retourne les paramètres par défaut"""
        return {
            'app': {
                'name': 'OSINT Framework Pro',
                'version': '1.0.0',
                'debug': False,
                'secret_key': 'default-secret-key-change-in-production'
            },
            'investigation': {
                'default_depth': 2,
                'max_concurrent_requests': 10,
                'request_timeout': 30,
                'rate_limit_delay': 1
            },
            'security': {
                'use_tor': True,
                'proxy_rotation': True,
                'user_agent_rotation': True,
                'encrypt_local_data': False
            },
            'ai': {
                'enabled': True,
                'sentiment_analysis': True,
                'entity_recognition': True,
                'risk_assessment': True
            },
            'export': {
                'default_formats': ['json', 'html'],
                'include_timestamps': True,
                'compress_exports': False
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/osint.log',
                'max_size': '10MB',
                'backup_count': 5
            },
            'database': {
                'enabled': True,
                'type': 'json',
                'path': 'data/databases/'
            },
            'monitoring': {
                'enabled': False,
                'check_interval': 3600,
                'alert_webhook': ''
            }
        }
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Récupère un paramètre de configuration"""
        keys = key.split('.')
        value = self.settings
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_api_key(self, service: str, key_name: str = None) -> Optional[str]:
        """Récupère une clé API"""
        try:
            if key_name:
                return self.api_keys.get(service, {}).get(key_name)
            else:
                return self.api_keys.get(service, {}).get('api_key')
        except (KeyError, TypeError):
            return None
    
    def get_proxies(self) -> list:
        """Récupère la liste des proxies"""
        return self.proxies
    
    def is_tor_enabled(self) -> bool:
        """Vérifie si Tor est activé"""
        return self.get_setting('security.use_tor', True)
    
    def reload_configs(self):
        """Recharge toutes les configurations"""
        self.load_all_configs()
        self.logger.info("Configurations rechargées")
    
    def save_settings(self, new_settings: Dict[str, Any]):
        """Sauvegarde les paramètres (pour l'interface web)"""
        try:
            with open('config/settings.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(new_settings, f, default_flow_style=False, allow_unicode=True)
            self.reload_configs()
            return True
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde settings: {e}")
            return False
