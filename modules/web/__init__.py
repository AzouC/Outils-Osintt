"""
Package web - Modules d'intelligence web et investigation en ligne

Ce package contient les modules spécialisés dans l'analyse web,
la collecte d'informations en ligne et l'investigation numérique.

Fonctionnalités:
- Analyse de domaines et DNS
- Investigation via Shodan
- Archivage web avec Wayback Machine
- Exploration du dark web
"""

import importlib
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urlparse
from utils.logger import get_logger

# Configuration du logger
logger = get_logger(__name__)

# Métadonnées du package
__version__ = "1.0.0"
__author__ = "AzouC"
__description__ = "Modules d'intelligence web OSINT"

# Liste des modules disponibles dans ce package
__all__ = ['darkweb', 'shodan_intel', 'wayback', 'domain_intel']

# Registre des modules web
_WEB_MODULES = {}

class WebIntelManager:
    """
    Gestionnaire central des modules d'intelligence web
    
    Fournit une interface unifiée pour l'analyse web,
    la collecte d'informations et l'investigation en ligne.
    """
    
    def __init__(self, config_manager):
        """
        Initialise le gestionnaire des modules web
        
        Args:
            config_manager: Gestionnaire de configuration
        """
        self.config = config_manager
        self.logger = logger
        self.modules = {}
        self._initialize_web_modules()
    
    def _initialize_web_modules(self):
        """Initialise tous les modules web disponibles"""
        self.logger.info("🌐 Initialisation des modules web...")
        
        # Modules web à initialiser
        web_modules = [
            ('darkweb', 'DarkWebIntel'),
            ('shodan_intel', 'ShodanIntel'),
            ('wayback', 'WaybackMachine'),
            ('domain_intel', 'DomainIntel')
        ]
        
        for module_name, class_name in web_modules:
            self._try_initialize_web_module(module_name, class_name)
        
        self.logger.info(f"✅ {len(self.modules)} modules web initialisés")
    
    def _try_initialize_web_module(self, module_name: str, class_name: str):
        """
        Tente d'initialiser un module web spécifique
        
        Args:
            module_name: Nom du module (ex: 'domain_intel')
            class_name: Nom de la classe à instancier
        """
        try:
            # Import dynamique du module
            module = importlib.import_module(f'.{module_name}', 'modules.web')
            module_class = getattr(module, class_name)
            
            # Création de l'instance
            instance = module_class(self.config)
            self.modules[module_name] = instance
            _WEB_MODULES[module_name] = True
            
            self.logger.debug(f"✅ Module {module_name} initialisé")
            
        except ImportError as e:
            self.logger.warning(f"⚠️ Module {module_name} non disponible: {e}")
            _WEB_MODULES[module_name] = False
        except AttributeError as e:
            self.logger.warning(f"⚠️ Classe {class_name} non trouvée: {e}")
            _WEB_MODULES[module_name] = False
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation {module_name}: {e}")
            _WEB_MODULES[module_name] = False
    
    def analyze_domain(self, domain: str) -> Dict[str, Any]:
        """
        Analyse complète d'un domaine
        
        Args:
            domain: Nom de domaine à analyser
            
        Returns:
            Analyse détaillée du domaine
        """
        if 'domain_intel' not in self.modules:
            return {"error": "Module d'analyse de domaine non disponible"}
        
        try:
            domain_module = self.modules['domain_intel']
            return domain_module.comprehensive_analysis(domain)
        except Exception as e:
            return {"error": f"Erreur analyse domaine: {str(e)}"}
    
    def get_whois_info(self, domain: str) -> Dict[str, Any]:
        """
        Récupère les informations WHOIS d'un domaine
        
        Args:
            domain: Nom de domaine
            
        Returns:
            Informations WHOIS
        """
        if 'domain_intel' not in self.modules:
            return {"error": "Module d'analyse de domaine non disponible"}
        
        try:
            domain_module = self.modules['domain_intel']
            return domain_module.get_whois_info(domain)
        except Exception as e:
            return {"error": f"Erreur WHOIS: {str(e)}"}
    
    def get_dns_records(self, domain: str) -> Dict[str, Any]:
        """
        Récupère les enregistrements DNS d'un domaine
        
        Args:
            domain: Nom de domaine
            
        Returns:
            Enregistrements DNS
        """
        if 'domain_intel' not in self.modules:
            return {"error": "Module d'analyse de domaine non disponible"}
        
        try:
            domain_module = self.modules['domain_intel']
            return domain_module.get_dns_records(domain)
        except Exception as e:
            return {"error": f"Erreur DNS: {str(e)}"}
    
    def shodan_host_lookup(self, ip: str) -> Dict[str, Any]:
        """
        Recherche d'informations sur un hôte via Shodan
        
        Args:
            ip: Adresse IP à investiguer
            
        Returns:
            Informations Shodan sur l'hôte
        """
        if 'shodan_intel' not in self.modules:
            return {"error": "Module Shodan non disponible"}
        
        try:
            shodan_module = self.modules['shodan_intel']
            if not shodan_module.is_configured():
                return {"error": "Shodan non configuré - clé API manquante"}
            
            return shodan_module.get_host_info(ip)
        except Exception as e:
            return {"error": f"Erreur Shodan: {str(e)}"}
    
    def shodan_search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Recherche Shodan avec une requête personnalisée
        
        Args:
            query: Requête de recherche Shodan
            limit: Nombre maximum de résultats
            
        Returns:
            Résultats de la recherche
        """
        if 'shodan_intel' not in self.modules:
            return {"error": "Module Shodan non disponible"}
        
        try:
            shodan_module = self.modules['shodan_intel']
            if not shodan_module.is_configured():
                return {"error": "Shodan non configuré - clé API manquante"}
            
            return shodan_module.search_hosts(query, limit)
        except Exception as e:
            return {"error": f"Erreur recherche Shodan: {str(e)}"}
    
    def get_wayback_snapshots(self, url: str, limit: int = 50) -> Dict[str, Any]:
        """
        Récupère les snapshots Wayback Machine d'une URL
        
        Args:
            url: URL à investiguer
            limit: Nombre maximum de snapshots
            
        Returns:
            Liste des snapshots disponibles
        """
        if 'wayback' not in self.modules:
            return {"error": "Module Wayback Machine non disponible"}
        
        try:
            wayback_module = self.modules['wayback']
            return wayback_module.get_snapshots_list(url, limit)
        except Exception as e:
            return {"error": f"Erreur Wayback: {str(e)}"}
    
    def get_wayback_content(self, wayback_url: str) -> Dict[str, Any]:
        """
        Récupère le contenu d'un snapshot Wayback spécifique
        
        Args:
            wayback_url: URL complète du snapshot Wayback
            
        Returns:
            Contenu du snapshot
        """
        if 'wayback' not in self.modules:
            return {"error": "Module Wayback Machine non disponible"}
        
        try:
            wayback_module = self.modules['wayback']
            return wayback_module.get_snapshot_content(wayback_url)
        except Exception as e:
            return {"error": f"Erreur contenu Wayback: {str(e)}"}
    
    def search_wayback_text(self, url: str, search_text: str, 
                           limit: int = 10) -> Dict[str, Any]:
        """
        Recherche du texte dans les snapshots Wayback
        
        Args:
            url: URL de base
            search_text: Texte à rechercher
            limit: Nombre maximum de snapshots à analyser
            
        Returns:
            Snapshots contenant le texte recherché
        """
        if 'wayback' not in self.modules:
            return {"error": "Module Wayback Machine non disponible"}
        
        try:
            wayback_module = self.modules['wayback']
            return wayback_module.search_text_in_snapshots(url, search_text, limit)
        except Exception as e:
            return {"error": f"Erreur recherche texte Wayback: {str(e)}"}
    
    def darkweb_search(self, query: str, engine: str = "ahmia") -> Dict[str, Any]:
        """
        Recherche sur le dark web (si configuré et autorisé)
        
        Args:
            query: Termes de recherche
            engine: Moteur de recherche dark web
            
        Returns:
            Résultats de la recherche
        """
        if 'darkweb' not in self.modules:
            return {"error": "Module dark web non disponible"}
        
        try:
            darkweb_module = self.modules['darkweb']
            return darkweb_module.search(query, engine)
        except Exception as e:
            return {"error": f"Erreur recherche dark web: {str(e)}"}
    
    def comprehensive_web_analysis(self, target: str, 
                                 analysis_type: str = "auto") -> Dict[str, Any]:
        """
        Analyse web complète d'une cible (domaine, IP ou URL)
        
        Args:
            target: Cible à analyser
            analysis_type: Type d'analyse ('auto', 'domain', 'ip', 'url')
            
        Returns:
            Analyse web complète consolidée
        """
        results = {
            "target": target,
            "analysis_type": analysis_type,
            "timestamp": self._get_timestamp(),
            "modules_used": [],
            "results": {}
        }
        
        # Détection automatique du type
        if analysis_type == "auto":
            analysis_type = self._detect_target_type(target)
            results["analysis_type"] = analysis_type
        
        # Analyse selon le type détecté
        if analysis_type == "domain":
            # Analyse de domaine
            if 'domain_intel' in self.modules:
                results["modules_used"].append("domain_intel")
                results["results"]["domain_analysis"] = self.analyze_domain(target)
            
            # Recherche Wayback
            if 'wayback' in self.modules:
                results["modules_used"].append("wayback")
                results["results"]["wayback_snapshots"] = self.get_wayback_snapshots(f"http://{target}")
        
        elif analysis_type == "ip":
            # Recherche Shodan
            if 'shodan_intel' in self.modules:
                results["modules_used"].append("shodan_intel")
                results["results"]["shodan_analysis"] = self.shodan_host_lookup(target)
        
        elif analysis_type == "url":
            parsed_url = urlparse(target)
            domain = parsed_url.netloc
            
            # Analyse du domaine sous-jacent
            if 'domain_intel' in self.modules:
                results["modules_used"].append("domain_intel")
                results["results"]["domain_analysis"] = self.analyze_domain(domain)
            
            # Recherche Wayback
            if 'wayback' in self.modules:
                results["modules_used"].append("wayback")
                results["results"]["wayback_analysis"] = self.get_wayback_snapshots(target)
        
        # Ajoute les métriques de l'analyse
        results["analysis_metrics"] = self._calculate_analysis_metrics(results)
        
        return results
    
    def _detect_target_type(self, target: str) -> str:
        """
        Détecte automatiquement le type de cible
        
        Args:
            target: Cible à analyser
            
        Returns:
            Type détecté ('domain', 'ip', 'url')
        """
        # Vérifie si c'est une IP
        try:
            import ipaddress
            ipaddress.ip_address(target)
            return "ip"
        except ValueError:
            pass
        
        # Vérifie si c'est une URL
        if target.startswith(('http://', 'https://', 'www.')):
            return "url"
        
        # Suppose que c'est un domaine par défaut
        return "domain"
    
    def _get_timestamp(self) -> str:
        """Retourne un timestamp formaté"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _calculate_analysis_metrics(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcule les métriques de l'analyse web
        
        Args:
            analysis_results: Résultats de l'analyse
            
        Returns:
            Métriques calculées
        """
        metrics = {
            "modules_used_count": len(analysis_results.get("modules_used", [])),
            "data_points": 0,
            "success_rate": 0.0
        }
        
        # Compte les points de données réussis
        successful_analyses = 0
        total_analyses = 0
        
        for module_result in analysis_results.get("results", {}).values():
            total_analyses += 1
            if "error" not in module_result:
                successful_analyses += 1
                # Estime le nombre de points de données
                metrics["data_points"] += self._estimate_data_points(module_result)
        
        # Calcule le taux de succès
        if total_analyses > 0:
            metrics["success_rate"] = successful_analyses / total_analyses
        
        return metrics
    
    def _estimate_data_points(self, data: Any) -> int:
        """
        Estime le nombre de points de données dans un résultat
        
        Args:
            data: Données à analyser
            
        Returns:
            Estimation du nombre de points de données
        """
        if isinstance(data, dict):
            return len(data)
        elif isinstance(data, list):
            return len(data)
        else:
            return 1
    
    def get_shodan_quota(self) -> Dict[str, Any]:
        """
        Récupère le quota d'API Shodan
        
        Returns:
            Informations de quota
        """
        if 'shodan_intel' not in self.modules:
            return {"error": "Module Shodan non disponible"}
        
        try:
            shodan_module = self.modules['shodan_intel']
            if not shodan_module.is_configured():
                return {"error": "Shodan non configuré"}
            
            return shodan_module.get_scanning_quota()
        except Exception as e:
            return {"error": f"Erreur quota Shodan: {str(e)}"}
    
    def validate_target(self, target: str, target_type: str = None) -> Dict[str, Any]:
        """
        Valide une cible web pour l'analyse
        
        Args:
            target: Cible à valider
            target_type: Type de cible (optionnel)
            
        Returns:
            Résultat de la validation
        """
        validation_result = {
            "target": target,
            "is_valid": False,
            "detected_type": target_type or self._detect_target_type(target),
            "issues": []
        }
        
        if not target or not isinstance(target, str):
            validation_result["issues"].append("Cible vide ou invalide")
            return validation_result
        
        target = target.strip()
        
        if validation_result["detected_type"] == "ip":
            try:
                import ipaddress
                ipaddress.ip_address(target)
                validation_result["is_valid"] = True
            except ValueError:
                validation_result["issues"].append("Adresse IP invalide")
        
        elif validation_result["detected_type"] == "domain":
            # Validation basique de domaine
            if len(target) < 3 or len(target) > 253:
                validation_result["issues"].append("Longueur de domaine invalide")
            elif '.' not in target:
                validation_result["issues"].append("Domaine sans extension")
            else:
                validation_result["is_valid"] = True
        
        elif validation_result["detected_type"] == "url":
            try:
                parsed = urlparse(target)
                if not parsed.scheme or not parsed.netloc:
                    validation_result["issues"].append("URL mal formée")
                else:
                    validation_result["is_valid"] = True
            except Exception:
                validation_result["issues"].append("Erreur parsing URL")
        
        return validation_result
    
    def get_module_status(self) -> Dict[str, Any]:
        """
        Retourne le statut de tous les modules web
        
        Returns:
            Statut et configuration des modules
        """
        status = {
            "available_modules": list(self.modules.keys()),
            "module_details": {}
        }
        
        for module_name, module in self.modules.items():
            module_status = {
                "initialized": True,
                "configured": False
            }
            
            # Vérification spécifique par module
            if module_name == 'shodan_intel':
                module_status["configured"] = getattr(module, 'is_configured', lambda: False)()
            elif module_name == 'domain_intel':
                module_status["configured"] = True  # Toujours disponible
            elif module_name == 'wayback':
                module_status["configured"] = True  # API publique
            elif module_name == 'darkweb':
                module_status["configured"] = getattr(module, 'is_configured', lambda: True)()
            
            status["module_details"][module_name] = module_status
        
        return status

# Fonctions utilitaires pour un usage rapide
def get_web_manager(config_manager) -> WebIntelManager:
    """
    Récupère une instance du gestionnaire web
    
    Args:
        config_manager: Gestionnaire de configuration
        
    Returns:
        Instance de WebIntelManager
    """
    return WebIntelManager(config_manager)

def quick_domain_analysis(domain: str, config_manager) -> Dict[str, Any]:
    """
    Analyse rapide d'un domaine
    
    Args:
        domain: Domaine à analyser
        config_manager: Gestionnaire de configuration
        
    Returns:
        Résultats de l'analyse
    """
    manager = get_web_manager(config_manager)
    return manager.analyze_domain(domain)

def quick_shodan_lookup(ip: str, config_manager) -> Dict[str, Any]:
    """
    Recherche rapide Shodan
    
    Args:
        ip: Adresse IP à rechercher
        config_manager: Gestionnaire de configuration
        
    Returns:
        Résultats Shodan
    """
    manager = get_web_manager(config_manager)
    return manager.shodan_host_lookup(ip)

# Initialisation au chargement du package
logger.info(f"🌐 Package web OSINT v{__version__} chargé")

# Vérification de la disponibilité des modules web
def _check_web_modules():
    """Vérifie la disponibilité des modules web"""
    available = {}
    for module_name in __all__:
        try:
            importlib.import_module(f'.{module_name}', 'modules.web')
            available[module_name] = True
            logger.debug(f"🌐 Module {module_name} disponible")
        except ImportError as e:
            available[module_name] = False
            logger.warning(f"🌐 Module {module_name} non disponible: {e}")
    
    return available

# Vérification au chargement
_WEB_MODULES_AVAILABILITY = _check_web_modules()

if __name__ == "__main__":
    # Mode démonstration
    print("🌐 Modules Web OSINT - Démonstration")
    print("=" * 45)
    
    from core.config_manager import ConfigManager
    
    config = ConfigManager()
    manager = WebIntelManager(config)
    
    print(f"📊 Modules disponibles: {manager.modules.keys()}")
    print(f"🔧 Statut modules: {manager.get_module_status()}")
    
    # Test de validation
    test_targets = [
        "example.com",
        "192.168.1.1", 
        "https://www.example.com",
        "invalid-target"
    ]
    
    print("\n🧪 Tests de validation:")
    for target in test_targets:
        validation = manager.validate_target(target)
        status = "✅" if validation["is_valid"] else "❌"
        print(f"  {status} {target} -> {validation['detected_type']}")
    
    print("💡 Prêt pour les investigations web!")

