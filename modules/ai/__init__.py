"""
Package ai - Modules d'intelligence artificielle pour l'OSINT

Ce package contient les modules spécialisés dans l'analyse avancée
utilisant l'intelligence artificielle et le machine learning.

Fonctionnalités:
- Analyse de texte et sentiment
- Reconnaissance d'images et OCR
- Analyse comportementale
- Détection de patterns
"""

import importlib
import numpy as np
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from utils.logger import get_logger

# Configuration du logger
logger = get_logger(__name__)

# Métadonnées du package
__version__ = "1.0.0"
__author__ = "AzouC"
__description__ = "Modules d'intelligence artificielle OSINT"

# Liste des modules disponibles dans ce package
__all__ = ['analyzer', 'image_recognition', 'behavioral']

# Registre des modules AI
_AI_MODULES = {}

class AIManager:
    """
    Gestionnaire central des modules d'intelligence artificielle
    
    Fournit une interface unifiée pour les analyses IA avancées
    et l'orchestration des modèles.
    """
    
    def __init__(self, config_manager):
        """
        Initialise le gestionnaire des modules AI
        
        Args:
            config_manager: Gestionnaire de configuration
        """
        self.config = config_manager
        self.logger = logger
        self.modules = {}
        self.models_loaded = False
        self._initialize_ai_modules()
    
    def _initialize_ai_modules(self):
        """Initialise tous les modules AI disponibles"""
        self.logger.info("🧠 Initialisation des modules d'IA...")
        
        # Modules AI à initialiser
        ai_modules = [
            ('analyzer', 'AIAnalyzer'),
            ('image_recognition', 'ImageRecognition'),
            ('behavioral', 'BehavioralAnalyzer')
        ]
        
        for module_name, class_name in ai_modules:
            self._try_initialize_ai_module(module_name, class_name)
        
        self.logger.info(f"✅ {len(self.modules)} modules IA initialisés")
        self._preload_models()
    
    def _try_initialize_ai_module(self, module_name: str, class_name: str):
        """
        Tente d'initialiser un module AI spécifique
        
        Args:
            module_name: Nom du module (ex: 'analyzer')
            class_name: Nom de la classe à instancier
        """
        try:
            # Import dynamique du module
            module = importlib.import_module(f'.{module_name}', 'modules.ai')
            module_class = getattr(module, class_name)
            
            # Création de l'instance
            instance = module_class(self.config)
            self.modules[module_name] = instance
            _AI_MODULES[module_name] = True
            
            self.logger.debug(f"✅ Module {module_name} initialisé")
            
        except ImportError as e:
            self.logger.warning(f"⚠️ Module {module_name} non disponible: {e}")
            _AI_MODULES[module_name] = False
        except AttributeError as e:
            self.logger.warning(f"⚠️ Classe {class_name} non trouvée: {e}")
            _AI_MODULES[module_name] = False
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation {module_name}: {e}")
            _AI_MODULES[module_name] = False
    
    def _preload_models(self):
        """Précharge les modèles AI pour de meilleures performances"""
        self.logger.info("🔄 Préchargement des modèles IA...")
        
        for module_name, module in self.modules.items():
            try:
                if hasattr(module, 'preload_models'):
                    module.preload_models()
                    self.logger.debug(f"✅ Modèles {module_name} préchargés")
            except Exception as e:
                self.logger.warning(f"⚠️ Erreur préchargement {module_name}: {e}")
        
        self.models_loaded = True
        self.logger.info("✅ Tous les modèles IA sont prêts")
    
    def analyze_text(self, text: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Analyse de texte avancée avec IA
        
        Args:
            text: Texte à analyser
            analysis_type: Type d'analyse ('sentiment', 'entities', 'topics', 'comprehensive')
            
        Returns:
            Résultats de l'analyse textuelle
        """
        if 'analyzer' not in self.modules:
            return {"error": "Module d'analyse textuelle non disponible"}
        
        try:
            analyzer = self.modules['analyzer']
            return analyzer.analyze_text(text, analysis_type)
        except Exception as e:
            return {"error": f"Erreur analyse texte: {str(e)}"}
    
    def analyze_image(self, image_path: Union[str, Path], 
                     features: List[str] = None) -> Dict[str, Any]:
        """
        Analyse d'image avec reconnaissance visuelle
        
        Args:
            image_path: Chemin vers l'image
            features: Fonctionnalités à extraire ('objects', 'faces', 'text', 'all')
            
        Returns:
            Résultats de l'analyse d'image
        """
        if 'image_recognition' not in self.modules:
            return {"error": "Module de reconnaissance d'image non disponible"}
        
        try:
            image_module = self.modules['image_recognition']
            return image_module.analyze_image(image_path, features)
        except Exception as e:
            return {"error": f"Erreur analyse image: {str(e)}"}
    
    def analyze_behavior(self, data: Dict[str, Any], 
                        behavior_type: str = "communication") -> Dict[str, Any]:
        """
        Analyse comportementale avec IA
        
        Args:
            data: Données comportementales à analyser
            behavior_type: Type de comportement ('communication', 'social', 'financial')
            
        Returns:
            Profil comportemental et insights
        """
        if 'behavioral' not in self.modules:
            return {"error": "Module d'analyse comportementale non disponible"}
        
        try:
            behavioral_module = self.modules['behavioral']
            return behavioral_module.analyze_behavior(data, behavior_type)
        except Exception as e:
            return {"error": f"Erreur analyse comportementale: {str(e)}"}
    
    def extract_entities(self, text: str, entity_types: List[str] = None) -> Dict[str, List]:
        """
        Extraction d'entités nommées depuis du texte
        
        Args:
            text: Texte source
            entity_types: Types d'entités à extraire ('person', 'organization', 'location', 'all')
            
        Returns:
            Entités extraites par catégorie
        """
        if 'analyzer' not in self.modules:
            return {"error": "Module d'extraction d'entités non disponible"}
        
        try:
            analyzer = self.modules['analyzer']
            return analyzer.extract_entities(text, entity_types)
        except Exception as e:
            return {"error": f"Erreur extraction entités: {str(e)}"}
    
    def compare_profiles(self, profile1: Dict, profile2: Dict, 
                        comparison_type: str = "similarity") -> Dict[str, Any]:
        """
        Compare deux profils avec analyse IA
        
        Args:
            profile1: Premier profil
            profile2: Second profil
            comparison_type: Type de comparaison ('similarity', 'relationships', 'behavior')
            
        Returns:
            Résultats de la comparaison
        """
        try:
            # Utilise le module behavioral pour la comparaison
            if 'behavioral' in self.modules:
                behavioral_module = self.modules['behavioral']
                return behavioral_module.compare_profiles(profile1, profile2, comparison_type)
            else:
                # Fallback avec analyse textuelle
                analyzer = self.modules.get('analyzer')
                if analyzer and hasattr(analyzer, 'compare_texts'):
                    return analyzer.compare_texts(
                        str(profile1), str(profile2), comparison_type
                    )
                else:
                    return {"error": "Aucun module de comparaison disponible"}
        except Exception as e:
            return {"error": f"Erreur comparaison profils: {str(e)}"}
    
    def generate_report(self, data: Any, report_type: str = "analysis") -> Dict[str, Any]:
        """
        Génère un rapport d'analyse avec IA
        
        Args:
            data: Données à analyser
            report_type: Type de rapport ('analysis', 'summary', 'insights')
            
        Returns:
            Rapport généré
        """
        if 'analyzer' not in self.modules:
            return {"error": "Module de génération de rapports non disponible"}
        
        try:
            analyzer = self.modules['analyzer']
            return analyzer.generate_report(data, report_type)
        except Exception as e:
            return {"error": f"Erreur génération rapport: {str(e)}"}
    
    def get_ai_capabilities(self) -> Dict[str, Any]:
        """
        Retourne les capacités IA disponibles
        
        Returns:
            Détails des fonctionnalités IA supportées
        """
        capabilities = {
            "text_analysis": False,
            "image_analysis": False,
            "behavioral_analysis": False,
            "entity_extraction": False,
            "sentiment_analysis": False,
            "model_loaded": self.models_loaded
        }
        
        # Vérifie les capacités par module
        for module_name, module in self.modules.items():
            if module_name == 'analyzer':
                capabilities.update({
                    "text_analysis": True,
                    "entity_extraction": True,
                    "sentiment_analysis": True
                })
            elif module_name == 'image_recognition':
                capabilities["image_analysis"] = True
            elif module_name == 'behavioral':
                capabilities["behavioral_analysis"] = True
        
        return capabilities
    
    def get_model_status(self) -> Dict[str, Any]:
        """
        Retourne le statut des modèles IA
        
        Returns:
            Statut de chargement et métriques des modèles
        """
        status = {
            "models_loaded": self.models_loaded,
            "available_modules": list(self.modules.keys()),
            "module_details": {}
        }
        
        for module_name, module in self.modules.items():
            try:
                module_status = getattr(module, 'get_model_status', lambda: {})()
                status["module_details"][module_name] = module_status
            except Exception as e:
                status["module_details"][module_name] = {"error": str(e)}
        
        return status

# Fonctions utilitaires pour un usage rapide
def get_ai_manager(config_manager) -> AIManager:
    """
    Récupère une instance du gestionnaire AI
    
    Args:
        config_manager: Gestionnaire de configuration
        
    Returns:
        Instance de AIManager
    """
    return AIManager(config_manager)

def quick_text_analysis(text: str, config_manager, analysis_type: str = "comprehensive") -> Dict[str, Any]:
    """
    Analyse rapide de texte avec IA
    
    Args:
        text: Texte à analyser
        config_manager: Gestionnaire de configuration
        analysis_type: Type d'analyse
        
    Returns:
        Résultats de l'analyse
    """
    manager = get_ai_manager(config_manager)
    return manager.analyze_text(text, analysis_type)

def quick_image_analysis(image_path: str, config_manager) -> Dict[str, Any]:
    """
    Analyse rapide d'image avec IA
    
    Args:
        image_path: Chemin vers l'image
        config_manager: Gestionnaire de configuration
        
    Returns:
        Résultats de l'analyse d'image
    """
    manager = get_ai_manager(config_manager)
    return manager.analyze_image(image_path)

# Initialisation au chargement du package
logger.info(f"🧠 Package AI OSINT v{__version__} chargé")

# Vérification de la disponibilité des modules AI
def _check_ai_modules():
    """Vérifie la disponibilité des modules AI"""
    available = {}
    for module_name in __all__:
        try:
            importlib.import_module(f'.{module_name}', 'modules.ai')
            available[module_name] = True
            logger.debug(f"🧠 Module {module_name} disponible")
        except ImportError as e:
            available[module_name] = False
            logger.warning(f"🧠 Module {module_name} non disponible: {e}")
    
    return available

# Vérification au chargement
_AI_MODULES_AVAILABILITY = _check_ai_modules()

if __name__ == "__main__":
    # Mode démonstration
    print("🧠 Modules IA OSINT - Démonstration")
    print("=" * 45)
    
    from core.config_manager import ConfigManager
    
    config = ConfigManager()
    manager = AIManager(config)
    
    print(f"📊 Modules disponibles: {manager.modules.keys()}")
    print(f"🔧 Capacités IA: {manager.get_ai_capabilities()}")
    print(f"📈 Statut modèles: {manager.get_model_status()}")
    
    # Test avec exemple simple
    if manager.modules:
        test_text = "L'OSINT est une méthode puissante pour l'analyse de renseignement."
        print(f"🧪 Test d'analyse: '{test_text}'")
        
        result = manager.analyze_text(test_text, "sentiment")
        print(f"📝 Résultat: {result}")
    
    print("💡 Prêt pour les analyses IA avancées!")
