"""
Package geolocation - Modules de géolocalisation et analyse spatiale

Ce package contient les modules spécialisés dans la localisation,
l'analyse géospatiale et l'intelligence basée sur la position.

Fonctionnalités:
- Analyse des réseaux WiFi et triangulation
- Extraction et analyse des métadonnées géographiques
- Localisation via tours cellulaires
- Cartographie et heatmaps
"""

import importlib
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json
from utils.logger import get_logger

# Configuration du logger
logger = get_logger(__name__)

# Métadonnées du package
__version__ = "1.0.0"
__author__ = "AzouC"
__description__ = "Modules de géolocalisation OSINT"

# Liste des modules disponibles dans ce package
__all__ = ['wifi_analyzer', 'geotag', 'cell_tower']

# Registre des modules géolocation
_GEOLOCATION_MODULES = {}

class GeolocationManager:
    """
    Gestionnaire central des modules de géolocalisation
    
    Fournit une interface unifiée pour l'analyse géospatiale,
    la localisation et la cartographie des données OSINT.
    """
    
    def __init__(self, config_manager):
        """
        Initialise le gestionnaire des modules géolocation
        
        Args:
            config_manager: Gestionnaire de configuration
        """
        self.config = config_manager
        self.logger = logger
        self.modules = {}
        self._initialize_geolocation_modules()
    
    def _initialize_geolocation_modules(self):
        """Initialise tous les modules géolocation disponibles"""
        self.logger.info("📍 Initialisation des modules de géolocalisation...")
        
        # Modules géolocation à initialiser
        geolocation_modules = [
            ('wifi_analyzer', 'WifiAnalyzer'),
            ('geotag', 'GeotagAnalyzer'),
            ('cell_tower', 'CellTowerAnalyzer')
        ]
        
        for module_name, class_name in geolocation_modules:
            self._try_initialize_geolocation_module(module_name, class_name)
        
        self.logger.info(f"✅ {len(self.modules)} modules géolocalisation initialisés")
    
    def _try_initialize_geolocation_module(self, module_name: str, class_name: str):
        """
        Tente d'initialiser un module géolocation spécifique
        
        Args:
            module_name: Nom du module (ex: 'wifi_analyzer')
            class_name: Nom de la classe à instancier
        """
        try:
            # Import dynamique du module
            module = importlib.import_module(f'.{module_name}', 'modules.geolocation')
            module_class = getattr(module, class_name)
            
            # Création de l'instance
            instance = module_class(self.config)
            self.modules[module_name] = instance
            _GEOLOCATION_MODULES[module_name] = True
            
            self.logger.debug(f"✅ Module {module_name} initialisé")
            
        except ImportError as e:
            self.logger.warning(f"⚠️ Module {module_name} non disponible: {e}")
            _GEOLOCATION_MODULES[module_name] = False
        except AttributeError as e:
            self.logger.warning(f"⚠️ Classe {class_name} non trouvée: {e}")
            _GEOLOCATION_MODULES[module_name] = False
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation {module_name}: {e}")
            _GEOLOCATION_MODULES[module_name] = False
    
    def scan_wifi_networks(self, interface: str = None, duration: int = 10) -> Dict[str, Any]:
        """
        Scan les réseaux WiFi environnants
        
        Args:
            interface: Interface WiFi à utiliser
            duration: Durée du scan en secondes
            
        Returns:
            Liste des réseaux détectés avec informations
        """
        if 'wifi_analyzer' not in self.modules:
            return {"error": "Module d'analyse WiFi non disponible"}
        
        try:
            wifi_module = self.modules['wifi_analyzer']
            return wifi_module.scan_networks(interface, duration)
        except Exception as e:
            return {"error": f"Erreur scan WiFi: {str(e)}"}
    
    def locate_from_wifi(self, networks_data: List[Dict]) -> Dict[str, Any]:
        """
        Estime la position basée sur les réseaux WiFi
        
        Args:
            networks_data: Données des réseaux WiFi détectés
            
        Returns:
            Position estimée et précision
        """
        if 'wifi_analyzer' not in self.modules:
            return {"error": "Module d'analyse WiFi non disponible"}
        
        try:
            wifi_module = self.modules['wifi_analyzer']
            return wifi_module.estimate_location(networks_data)
        except Exception as e:
            return {"error": f"Erreur localisation WiFi: {str(e)}"}
    
    def extract_geotags(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Extrait les métadonnées géographiques d'un fichier
        
        Args:
            file_path: Chemin vers le fichier (image, vidéo, document)
            
        Returns:
            Métadonnées géographiques extraites
        """
        if 'geotag' not in self.modules:
            return {"error": "Module d'extraction géotags non disponible"}
        
        try:
            geotag_module = self.modules['geotag']
            return geotag_module.extract_geotags(file_path)
        except Exception as e:
            return {"error": f"Erreur extraction géotags: {str(e)}"}
    
    def analyze_geotag_patterns(self, files_list: List[str]) -> Dict[str, Any]:
        """
        Analyse les patterns géographiques depuis multiple fichiers
        
        Args:
            files_list: Liste des chemins de fichiers à analyser
            
        Returns:
            Patterns géographiques détectés
        """
        if 'geotag' not in self.modules:
            return {"error": "Module d'analyse géotags non disponible"}
        
        try:
            geotag_module = self.modules['geotag']
            return geotag_module.analyze_patterns(files_list)
        except Exception as e:
            return {"error": f"Erreur analyse patterns: {str(e)}"}
    
    def locate_from_cell_towers(self, cell_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estime la position basée sur les tours cellulaires
        
        Args:
            cell_data: Données des tours cellulaires
                      (cell_id, lac, mcc, mnc, signal_strength)
            
        Returns:
            Position estimée et précision
        """
        if 'cell_tower' not in self.modules:
            return {"error": "Module d'analyse cellulaire non disponible"}
        
        try:
            cell_module = self.modules['cell_tower']
            return cell_module.estimate_location(cell_data)
        except Exception as e:
            return {"error": f"Erreur localisation cellulaire: {str(e)}"}
    
    def get_cell_tower_info(self, cell_id: int, lac: int, mcc: int, mnc: int) -> Dict[str, Any]:
        """
        Récupère les informations d'une tour cellulaire spécifique
        
        Args:
            cell_id: Identifiant de la cellule
            lac: Location Area Code
            mcc: Mobile Country Code
            mnc: Mobile Network Code
            
        Returns:
            Informations de la tour cellulaire
        """
        if 'cell_tower' not in self.modules:
            return {"error": "Module d'analyse cellulaire non disponible"}
        
        try:
            cell_module = self.modules['cell_tower']
            return cell_module.get_tower_info(cell_id, lac, mcc, mnc)
        except Exception as e:
            return {"error": f"Erreur info tour cellulaire: {str(e)}"}
    
    def reverse_geocode(self, lat: float, lon: float, 
                       language: str = "fr") -> Dict[str, Any]:
        """
        Convertit des coordonnées en adresse lisible
        
        Args:
            lat: Latitude
            lon: Longitude
            language: Langue pour les résultats
            
        Returns:
            Informations d'adresse
        """
        # Essaye d'abord le module geotag
        if 'geotag' in self.modules:
            try:
                geotag_module = self.modules['geotag']
                if hasattr(geotag_module, 'reverse_geocode'):
                    return geotag_module.reverse_geocode(lat, lon, language)
            except Exception as e:
                self.logger.warning(f"Reverse geocode geotag échoué: {e}")
        
        # Fallback vers une implémentation basique
        try:
            import requests
            url = f"https://nominatim.openstreetmap.org/reverse"
            params = {
                'lat': lat,
                'lon': lon,
                'format': 'json',
                'accept-language': language,
                'zoom': 18
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "address": data.get('address', {}),
                    "display_name": data.get('display_name', ''),
                    "source": "openstreetmap"
                }
            else:
                return {"error": "Erreur API géocodage"}
                
        except Exception as e:
            return {"error": f"Erreur reverse geocode: {str(e)}"}
    
    def calculate_distance(self, point1: Tuple[float, float], 
                          point2: Tuple[float, float], 
                          unit: str = "km") -> float:
        """
        Calcule la distance entre deux points géographiques
        
        Args:
            point1: Tuple (lat, lon) du premier point
            point2: Tuple (lat, lon) du second point
            unit: Unité de distance ('km', 'miles', 'meters')
            
        Returns:
            Distance dans l'unité spécifiée
        """
        try:
            from math import radians, sin, cos, sqrt, atan2
            
            lat1, lon1 = map(radians, point1)
            lat2, lon2 = map(radians, point2)
            
            # Formule de Haversine
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            
            # Rayon de la Terre en kilomètres
            R = 6371.0
            distance_km = R * c
            
            # Conversion d'unité
            if unit == "miles":
                return distance_km * 0.621371
            elif unit == "meters":
                return distance_km * 1000
            else:  # km par défaut
                return distance_km
                
        except Exception as e:
            self.logger.error(f"Erreur calcul distance: {e}")
            return 0.0
    
    def create_heatmap(self, points: List[Tuple[float, float]], 
                      output_path: str = None) -> Dict[str, Any]:
        """
        Crée une heatmap à partir de points géographiques
        
        Args:
            points: Liste de tuples (lat, lon)
            output_path: Chemin de sauvegarde (optionnel)
            
        Returns:
            Données et métriques de la heatmap
        """
        try:
            # Utilise le visualizer pour créer la heatmap
            from utils.visualizer import DataVisualizer
            visualizer = DataVisualizer(self.config)
            
            locations = [{"latitude": lat, "longitude": lon, "intensity": 1} 
                        for lat, lon in points]
            
            if output_path is None:
                output_path = "heatmap_analysis"
            
            result = visualizer.create_geographic_map(locations, output_path)
            
            # Ajoute des métriques supplémentaires
            if result.get('success'):
                result['heatmap_metrics'] = {
                    "points_count": len(points),
                    "area_covered": self._calculate_coverage_area(points),
                    "density": len(points) / max(1, self._calculate_coverage_area(points))
                }
            
            return result
            
        except Exception as e:
            return {"error": f"Erreur création heatmap: {str(e)}"}
    
    def _calculate_coverage_area(self, points: List[Tuple[float, float]]) -> float:
        """
        Calcule la zone couverte par les points (km² approximatif)
        
        Args:
            points: Liste de points (lat, lon)
            
        Returns:
            Superficie en km²
        """
        if len(points) < 2:
            return 0.0
        
        try:
            # Calcule la bounding box
            lats = [p[0] for p in points]
            lons = [p[1] for p in points]
            
            lat_range = max(lats) - min(lats)
            lon_range = max(lons) - min(lons)
            
            # Approximation de la superficie
            # (très basique, ne tient pas compte de la courbure terrestre)
            avg_lat = sum(lats) / len(lats)
            km_per_degree_lat = 111.0
            km_per_degree_lon = 111.0 * abs(cos(radians(avg_lat)))
            
            area = (lat_range * km_per_degree_lat) * (lon_range * km_per_degree_lon)
            return max(area, 0.1)  # Minimum 0.1 km²
            
        except Exception:
            return 0.0
    
    def multi_source_locate(self, wifi_data: List[Dict] = None,
                           cell_data: Dict = None,
                           geotags: List[Dict] = None) -> Dict[str, Any]:
        """
        Localisation utilisant multiples sources de données
        
        Args:
            wifi_data: Données réseaux WiFi
            cell_data: Données tours cellulaires
            geotags: Géotags extraits
            
        Returns:
            Position consolidée et confiance
        """
        locations = []
        confidence_scores = []
        
        # Localisation WiFi
        if wifi_data and 'wifi_analyzer' in self.modules:
            try:
                wifi_location = self.locate_from_wifi(wifi_data)
                if 'error' not in wifi_location:
                    locations.append(wifi_location)
                    confidence_scores.append(0.7)  # Confiance moyenne pour WiFi
            except Exception as e:
                self.logger.warning(f"Localisation WiFi échouée: {e}")
        
        # Localisation cellulaire
        if cell_data and 'cell_tower' in self.modules:
            try:
                cell_location = self.locate_from_cell_towers(cell_data)
                if 'error' not in cell_location:
                    locations.append(cell_location)
                    confidence_scores.append(0.8)  # Bonne confiance pour cellulaire
            except Exception as e:
                self.logger.warning(f"Localisation cellulaire échouée: {e}")
        
        # Géotags
        if geotags and 'geotag' in self.modules:
            for geotag in geotags:
                if 'latitude' in geotag and 'longitude' in geotag:
                    locations.append({
                        'latitude': geotag['latitude'],
                        'longitude': geotag['longitude'],
                        'accuracy': geotag.get('accuracy', 50),
                        'source': 'geotag'
                    })
                    confidence_scores.append(0.9)  # Haute confiance pour géotags
        
        # Fusion des positions
        if not locations:
            return {"error": "Aucune donnée de localisation valide"}
        
        # Moyenne pondérée par la confiance
        total_weight = sum(confidence_scores)
        if total_weight == 0:
            return {"error": "Aucune confiance dans les données"}
        
        avg_lat = sum(loc.get('latitude', 0) * conf 
                     for loc, conf in zip(locations, confidence_scores)) / total_weight
        avg_lon = sum(loc.get('longitude', 0) * conf 
                     for loc, conf in zip(locations, confidence_scores)) / total_weight
        
        # Précision moyenne
        avg_accuracy = sum(loc.get('accuracy', 100) * conf 
                          for loc, conf in zip(locations, confidence_scores)) / total_weight
        
        return {
            "latitude": avg_lat,
            "longitude": avg_lon,
            "accuracy": avg_accuracy,
            "confidence": total_weight / len(confidence_scores),
            "sources_used": len(locations),
            "method": "multi_source_fusion"
        }
    
    def get_module_capabilities(self) -> Dict[str, Any]:
        """
        Retourne les capacités des modules géolocation
        
        Returns:
            Détails des fonctionnalités supportées
        """
        capabilities = {}
        
        for module_name, module in self.modules.items():
            module_caps = {
                "wifi_scanning": hasattr(module, 'scan_networks'),
                "wifi_location": hasattr(module, 'estimate_location'),
                "geotag_extraction": hasattr(module, 'extract_geotags'),
                "pattern_analysis": hasattr(module, 'analyze_patterns'),
                "cell_location": hasattr(module, 'estimate_location'),
                "tower_info": hasattr(module, 'get_tower_info')
            }
            capabilities[module_name] = module_caps
        
        return capabilities

# Fonctions utilitaires pour un usage rapide
def get_geolocation_manager(config_manager) -> GeolocationManager:
    """
    Récupère une instance du gestionnaire géolocation
    
    Args:
        config_manager: Gestionnaire de configuration
        
    Returns:
        Instance de GeolocationManager
    """
    return GeolocationManager(config_manager)

def quick_geotag_extraction(file_path: str, config_manager) -> Dict[str, Any]:
    """
    Extraction rapide de géotags
    
    Args:
        file_path: Chemin du fichier
        config_manager: Gestionnaire de configuration
        
    Returns:
        Géotags extraits
    """
    manager = get_geolocation_manager(config_manager)
    return manager.extract_geotags(file_path)

def quick_wifi_scan(config_manager, interface: str = None) -> Dict[str, Any]:
    """
    Scan rapide des réseaux WiFi
    
    Args:
        config_manager: Gestionnaire de configuration
        interface: Interface WiFi
        
    Returns:
        Réseaux détectés
    """
    manager = get_geolocation_manager(config_manager)
    return manager.scan_wifi_networks(interface)

# Initialisation au chargement du package
logger.info(f"📍 Package géolocalisation OSINT v{__version__} chargé")

# Vérification de la disponibilité des modules géolocation
def _check_geolocation_modules():
    """Vérifie la disponibilité des modules géolocation"""
    available = {}
    for module_name in __all__:
        try:
            importlib.import_module(f'.{module_name}', 'modules.geolocation')
            available[module_name] = True
            logger.debug(f"📍 Module {module_name} disponible")
        except ImportError as e:
            available[module_name] = False
            logger.warning(f"📍 Module {module_name} non disponible: {e}")
    
    return available

# Vérification au chargement
_GEOLOCATION_MODULES_AVAILABILITY = _check_geolocation_modules()

if __name__ == "__main__":
    # Mode démonstration
    print("📍 Modules Géolocalisation OSINT - Démonstration")
    print("=" * 55)
    
    from core.config_manager import ConfigManager
    
    config = ConfigManager()
    manager = GeolocationManager(config)
    
    print(f"📊 Modules disponibles: {list(manager.modules.keys())}")
    print(f"🔧 Capacités: {manager.get_module_capabilities()}")
    
    # Démonstration des calculs
    point1 = (48.8566, 2.3522)  # Paris
    point2 = (45.7640, 4.8357)  # Lyon
    distance = manager.calculate_distance(point1, point2, "km")
    print(f"📏 Distance Paris-Lyon: {distance:.1f} km")
    
    print("💡 Prêt pour les analyses géospatiales!")
