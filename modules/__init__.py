"""
Package modules - Système modulaire d'intelligence OSINT

Ce package contient tous les modules spécialisés pour la collecte et l'analyse de données OSINT.
Chaque sous-module est conçu pour être autonome et réutilisable.

Version: 1.0.0
Auteur: AzouC
"""

import importlib
import sys
from typing import Dict, List, Any, Optional, Type

# Import des utilitaires
try:
    from utils.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    # Fallback basique si le logger n'est pas disponible
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Déclaration des sous-packages disponibles
__all__ = [
    'phone_intel',
    'email_intel', 
    'social',
    'web',
    'blockchain',
    'ai',
    'geolocation'
]

# Métadonnées du package
__version__ = "1.0.0"
__author__ = "AzouC"
__description__ = "Système modulaire d'intelligence OSINT"

# Registre des modules chargés
_MODULE_REGISTRY = {}
_MODULE_AVAILABILITY = {}

class ModuleManager:
    """
    Gestionnaire central des modules OSINT
    
    Fournit une interface unifiée pour accéder à tous les modules
    et gérer leur cycle de vie.
    """
    
    def __init__(self, config_manager=None):
        """
        Initialise le gestionnaire de modules
        
        Args:
            config_manager: Gestionnaire de configuration (optionnel)
        """
        self.config = config_manager
        self.logger = logger
        self.modules = {}
        self._initialize_modules()
    
    def _initialize_modules(self):
        """Initialise tous les modules disponibles"""
        self.logger.info("🔧 Initialisation des modules OSINT...")
        
        # Test et initialisation de chaque module
        modules_to_init = [
            ('phone_intel', 'PhoneIntel'),
            ('email_intel', 'EmailIntel'),
            ('social.instagram', 'InstagramIntel'),
            ('social.twitter', 'TwitterIntel'), 
            ('social.telegram', 'TelegramIntel'),
            ('social.facebook', 'FacebookIntel'),
            ('social.linkedin', 'LinkedInIntel'),
            ('web.domain_intel', 'DomainIntel'),
            ('web.shodan_intel', 'ShodanIntel'),
            ('web.wayback', 'WaybackMachine'),
            ('web.darkweb', 'DarkWebIntel'),
            ('blockchain.bitcoin', 'BitcoinIntel'),
            ('blockchain.ethereum', 'EthereumIntel'),
            ('blockchain.crypto_tracker', 'CryptoTracker'),
            ('ai.analyzer', 'AIAnalyzer'),
            ('ai.image_recognition', 'ImageRecognition'),
            ('ai.behavioral', 'BehavioralAnalyzer'),
            ('geolocation.wifi_analyzer', 'WifiAnalyzer'),
            ('geolocation.geotag', 'GeotagAnalyzer'),
            ('geolocation.cell_tower', 'CellTowerAnalyzer')
        ]
        
        for module_path, class_name in modules_to_init:
            self._try_initialize_module(module_path, class_name)
        
        self.logger.info(f"✅ {len(self.modules)} modules initialisés sur {len(modules_to_init)} possibles")
    
    def _try_initialize_module(self, module_path: str, class_name: str):
        """
        Tente d'initialiser un module spécifique
        
        Args:
            module_path: Chemin du module (ex: 'web.domain_intel')
            class_name: Nom de la classe à instancier
        """
        try:
            module = importlib.import_module(f'.{module_path}', 'modules')
            module_class = getattr(module, class_name)
            module_key = module_path.split('.')[-1]  # 'domain_intel' -> 'domain'
            
            # Création de l'instance
            if self.config:
                instance = module_class(self.config)
            else:
                instance = module_class()
            
            self.modules[module_key] = instance
            _MODULE_AVAILABILITY[module_key] = True
            
            self.logger.debug(f"✅ Module {module_key} initialisé")
            
        except ImportError as e:
            self.logger.warning(f"⚠️ Module {module_path} non disponible: {e}")
            _MODULE_AVAILABILITY[module_key] = False
        except AttributeError as e:
            self.logger.warning(f"⚠️ Classe {class_name} non trouvée dans {module_path}: {e}")
            _MODULE_AVAILABILITY[module_key] = False
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation {module_path}: {e}")
            _MODULE_AVAILABILITY[module_key] = False
    
    def get_module(self, module_name: str):
        """
        Récupère un module par son nom
        
        Args:
            module_name: Nom du module (ex: 'domain', 'email')
            
        Returns:
            Instance du module ou None
        """
        return self.modules.get(module_name)
    
    def list_available_modules(self) -> List[str]:
        """
        Liste tous les modules disponibles
        
        Returns:
            Liste des noms de modules disponibles
        """
        return list(self.modules.keys())
    
    def is_module_available(self, module_name: str) -> bool:
        """
        Vérifie si un module est disponible
        
        Args:
            module_name: Nom du module
            
        Returns:
            True si le module est disponible
        """
        return module_name in self.modules
    
    def get_module_status(self) -> Dict[str, bool]:
        """
        Retourne le statut de tous les modules
        
        Returns:
            Dict avec le statut de chaque module
        """
        return _MODULE_AVAILABILITY.copy()
    
    def execute_analysis(self, module_name: str, target: str, **kwargs) -> Any:
        """
        Exécute une analyse avec un module spécifique
        
        Args:
            module_name: Nom du module à utiliser
            target: Cible de l'analyse
            **kwargs: Arguments supplémentaires
            
        Returns:
            Résultat de l'analyse
            
        Raises:
            ValueError: Si le module n'est pas disponible
        """
        if module_name not in self.modules:
            raise ValueError(f"Module '{module_name}' non disponible")
        
        module = self.modules[module_name]
        
        # Essaye d'appeler comprehensive_analysis, sinon utilise la méthode appropriée
        if hasattr(module, 'comprehensive_analysis'):
            return module.comprehensive_analysis(target, **kwargs)
        elif hasattr(module, 'analyze'):
            return module.analyze(target, **kwargs)
        else:
            # Fallback générique
            return getattr(module, f'get_{module_name}_info', lambda x: {})(target)

# Fonctions utilitaires pour un usage rapide
def get_module_manager(config_manager=None) -> ModuleManager:
    """
    Récupère une instance du gestionnaire de modules
    
    Args:
        config_manager: Gestionnaire de configuration
        
    Returns:
        Instance de ModuleManager
    """
    return ModuleManager(config_manager)

def quick_analysis(module_name: str, target: str, config_manager=None, **kwargs) -> Any:
    """
    Exécute une analyse rapide avec un module
    
    Args:
        module_name: Nom du module
        target: Cible de l'analyse
        config_manager: Gestionnaire de configuration
        **kwargs: Arguments supplémentaires
        
    Returns:
        Résultat de l'analyse
    """
    manager = get_module_manager(config_manager)
    return manager.execute_analysis(module_name, target, **kwargs)

def list_modules() -> List[str]:
    """
    Liste tous les modules disponibles (sans initialisation)
    
    Returns:
        Liste des noms de modules
    """
    return [
        'phone', 'email', 'instagram', 'twitter', 'telegram', 
        'facebook', 'linkedin', 'domain', 'shodan', 'wayback',
        'darkweb', 'bitcoin', 'ethereum', 'crypto', 'ai_analyzer',
        'image_recognition', 'behavioral', 'wifi', 'geotag', 'cell_tower'
    ]

# Initialisation au chargement du package
logger.info(f"📦 Package modules OSINT v{__version__} chargé")

# Test rapide de disponibilité des sous-packages
def _check_subpackages():
    """Vérifie la disponibilité des sous-packages"""
    available = {}
    for subpackage in __all__:
        try:
            importlib.import_module(f'.{subpackage}', 'modules')
            available[subpackage] = True
            logger.debug(f"📁 Sous-package {subpackage} disponible")
        except ImportError as e:
            available[subpackage] = False
            logger.warning(f"📁 Sous-package {subpackage} non disponible: {e}")
    
    return available

# Vérification au chargement
_SUBPACKAGE_AVAILABILITY = _check_subpackages()

if __name__ == "__main__":
    # Mode démonstration
    print("🔍 Modules OSINT - Démonstration")
    print("=" * 40)
    
    manager = ModuleManager()
    print(f"📊 Modules disponibles: {manager.list_available_modules()}")
    print(f"📈 Statut des modules: {manager.get_module_status()}")
    
    # Test d'analyse rapide (si des modules sont disponibles)
    available_modules = manager.list_available_modules()
    if available_modules:
        test_module = available_modules[0]
        print(f"🧪 Test du module: {test_module}")
        # Note: Les appels réels dépendent de la configuration API
        print("💡 Prêt pour les analyses OSINT!")
