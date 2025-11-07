"""
Package social - Modules de renseignement sur les réseaux sociaux

Ce package contient les modules spécialisés dans la collecte d'informations
depuis les plateformes sociales majeures.

⚠️ IMPORTANT: Respectez toujours les conditions d'utilisation des plateformes
et les lois locales sur la protection des données.
"""

import importlib
from typing import Dict, List, Any, Optional
from utils.logger import get_logger

# Configuration du logger
logger = get_logger(__name__)

# Métadonnées du package
__version__ = "1.0.0"
__author__ = "AzouC"
__description__ = "Modules d'intelligence sociale OSINT"

# Liste des modules disponibles dans ce package
__all__ = ['instagram', 'twitter', 'telegram', 'facebook', 'linkedin']

# Registre des modules sociaux
_SOCIAL_MODULES = {}

class SocialIntelManager:
    """
    Gestionnaire central des modules de renseignement social
    
    Fournit une interface unifiée pour accéder aux différentes plateformes
    sociales et gérer les quotas d'API.
    """
    
    def __init__(self, config_manager):
        """
        Initialise le gestionnaire des modules sociaux
        
        Args:
            config_manager: Gestionnaire de configuration
        """
        self.config = config_manager
        self.logger = logger
        self.modules = {}
        self._initialize_social_modules()
    
    def _initialize_social_modules(self):
        """Initialise tous les modules sociaux disponibles"""
        self.logger.info("📱 Initialisation des modules sociaux...")
        
        # Modules sociaux à initialiser
        social_modules = [
            ('instagram', 'InstagramIntel'),
            ('twitter', 'TwitterIntel'),
            ('telegram', 'TelegramIntel'),
            ('facebook', 'FacebookIntel'),
            ('linkedin', 'LinkedInIntel')
        ]
        
        for module_name, class_name in social_modules:
            self._try_initialize_social_module(module_name, class_name)
        
        self.logger.info(f"✅ {len(self.modules)} modules sociaux initialisés")
    
    def _try_initialize_social_module(self, module_name: str, class_name: str):
        """
        Tente d'initialiser un module social spécifique
        
        Args:
            module_name: Nom du module (ex: 'instagram')
            class_name: Nom de la classe à instancier
        """
        try:
            # Import dynamique du module
            module = importlib.import_module(f'.{module_name}', 'modules.social')
            module_class = getattr(module, class_name)
            
            # Création de l'instance
            instance = module_class(self.config)
            self.modules[module_name] = instance
            _SOCIAL_MODULES[module_name] = True
            
            self.logger.debug(f"✅ Module {module_name} initialisé")
            
        except ImportError as e:
            self.logger.warning(f"⚠️ Module {module_name} non disponible: {e}")
            _SOCIAL_MODULES[module_name] = False
        except AttributeError as e:
            self.logger.warning(f"⚠️ Classe {class_name} non trouvée: {e}")
            _SOCIAL_MODULES[module_name] = False
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation {module_name}: {e}")
            _SOCIAL_MODULES[module_name] = False
    
    def get_platform_module(self, platform: str):
        """
        Récupère le module d'une plateforme spécifique
        
        Args:
            platform: Nom de la plateforme ('instagram', 'twitter', etc.)
            
        Returns:
            Instance du module ou None
        """
        return self.modules.get(platform)
    
    def analyze_username(self, username: str, platforms: List[str] = None) -> Dict[str, Any]:
        """
        Analyse un nom d'utilisateur sur plusieurs plateformes
        
        Args:
            username: Nom d'utilisateur à rechercher
            platforms: Liste des plateformes à analyser (toutes par défaut)
            
        Returns:
            Résultats de l'analyse par plateforme
        """
        if platforms is None:
            platforms = list(self.modules.keys())
        
        results = {}
        
        for platform in platforms:
            if platform in self.modules:
                try:
                    module = self.modules[platform]
                    if hasattr(module, 'get_user_info'):
                        results[platform] = module.get_user_info(username)
                    else:
                        results[platform] = {"error": f"Méthode non disponible pour {platform}"}
                except Exception as e:
                    results[platform] = {"error": f"Erreur {platform}: {str(e)}"}
            else:
                results[platform] = {"error": f"Module {platform} non disponible"}
        
        return results
    
    def search_content(self, query: str, platform: str, content_type: str = "posts") -> Dict[str, Any]:
        """
        Recherche du contenu sur une plateforme spécifique
        
        Args:
            query: Terme de recherche
            platform: Plateforme cible
            content_type: Type de contenu ('posts', 'users', 'hashtags')
            
        Returns:
            Résultats de la recherche
        """
        if platform not in self.modules:
            return {"error": f"Plateforme {platform} non disponible"}
        
        try:
            module = self.modules[platform]
            
            # Mapping des méthodes de recherche par type de contenu
            search_methods = {
                'posts': getattr(module, 'search_posts', None),
                'users': getattr(module, 'search_users', None),
                'hashtags': getattr(module, 'search_hashtags', None)
            }
            
            method = search_methods.get(content_type)
            if method:
                return method(query)
            else:
                return {"error": f"Type de contenu '{content_type}' non supporté"}
                
        except Exception as e:
            return {"error": f"Erreur recherche {platform}: {str(e)}"}
    
    def get_platform_metrics(self) -> Dict[str, Any]:
        """
        Retourne les métriques de disponibilité des plateformes
        
        Returns:
            Statut et métriques de chaque plateforme
        """
        metrics = {}
        
        for platform, module in self.modules.items():
            try:
                # Vérifie si le module est configuré
                is_configured = getattr(module, 'is_configured', lambda: True)()
                api_quota = getattr(module, 'get_api_quota', lambda: {})()
                
                metrics[platform] = {
                    'available': True,
                    'configured': is_configured,
                    'api_quota': api_quota
                }
            except Exception as e:
                metrics[platform] = {
                    'available': False,
                    'error': str(e)
                }
        
        return metrics
    
    def list_available_platforms(self) -> List[str]:
        """
        Liste toutes les plateformes disponibles
        
        Returns:
            Liste des noms de plateformes
        """
        return list(self.modules.keys())
    
    def is_platform_available(self, platform: str) -> bool:
        """
        Vérifie si une plateforme est disponible
        
        Args:
            platform: Nom de la plateforme
            
        Returns:
            True si la plateforme est disponible
        """
        return platform in self.modules

# Fonctions utilitaires pour un usage rapide
def get_social_manager(config_manager) -> SocialIntelManager:
    """
    Récupère une instance du gestionnaire social
    
    Args:
        config_manager: Gestionnaire de configuration
        
    Returns:
        Instance de SocialIntelManager
    """
    return SocialIntelManager(config_manager)

def quick_social_search(username: str, config_manager, platforms: List[str] = None) -> Dict[str, Any]:
    """
    Recherche rapide d'un utilisateur sur les réseaux sociaux
    
    Args:
        username: Nom d'utilisateur à rechercher
        config_manager: Gestionnaire de configuration
        platforms: Plateformes spécifiques (toutes par défaut)
        
    Returns:
        Résultats de la recherche
    """
    manager = get_social_manager(config_manager)
    return manager.analyze_username(username, platforms)

# Initialisation au chargement du package
logger.info(f"📱 Package social OSINT v{__version__} chargé")

# Vérification de la disponibilité des modules sociaux
def _check_social_modules():
    """Vérifie la disponibilité des modules sociaux"""
    available = {}
    for module_name in __all__:
        try:
            importlib.import_module(f'.{module_name}', 'modules.social')
            available[module_name] = True
            logger.debug(f"📱 Module {module_name} disponible")
        except ImportError as e:
            available[module_name] = False
            logger.warning(f"📱 Module {module_name} non disponible: {e}")
    
    return available

# Vérification au chargement
_SOCIAL_MODULES_AVAILABILITY = _check_social_modules()

if __name__ == "__main__":
    # Mode démonstration
    print("📱 Modules Sociaux OSINT - Démonstration")
    print("=" * 45)
    
    from core.config_manager import ConfigManager
    
    config = ConfigManager()
    manager = SocialIntelManager(config)
    
    print(f"📊 Plateformes disponibles: {manager.list_available_platforms()}")
    print(f"📈 Métriques: {manager.get_platform_metrics()}")
    
    # Exemple d'utilisation
    if manager.list_available_platforms():
        print("💡 Prêt pour les analyses sociales!")
        print("💡 Exemple: manager.analyze_username('nom_utilisateur')")
