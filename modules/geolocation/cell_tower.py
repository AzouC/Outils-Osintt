# modules/geolocation/cell_tower.py
import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import math
import json

class CellTowerAnalyzer:
    def __init__(self, config_manager=None):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        self.api_endpoints = self._setup_endpoints()
        
    def _setup_endpoints(self) -> Dict[str, str]:
        """Configure les endpoints API pour les antennes relais"""
        return {
            'openbmap': 'https://www.openbmap.org/api',
            'opencellid': 'https://opencellid.org/api',
            'mylnikov': 'https://api.mylnikov.org/geolocation',
            'google_geolocation': 'https://www.googleapis.com/geolocation/v1/geolocate',
            'unwiredlabs': 'https://eu1.unwiredlabs.com/api'
        }
    
    async def investigate(self, cell_data: Dict, depth: int = 2) -> Dict[str, Any]:
        """
        Investigation des antennes relais pour géolocalisation
        """
        self.logger.info("Début de l'analyse des antennes relais")
        
        results = {
            'cell_data_provided': cell_data,
            'investigation_timestamp': datetime.now().isoformat(),
            'tower_analysis': {},
            'geolocation_results': {},
            'coverage_analysis': {},
            'network_analysis': {},
            'accuracy_assessment': {}
        }
        
        if depth >= 1:
            results['tower_analysis'] = await self._analyze_cell_towers(cell_data)
            results['geolocation_results'] = await self._perform_geolocation(cell_data)
        
        if depth >= 2:
            results['coverage_analysis'] = await self._analyze_coverage_area(results)
            results['network_analysis'] = await self._analyze_network_info(cell_data)
        
        if depth >= 3:
            results['accuracy_assessment'] = await self._assess_accuracy(results)
            results['historical_analysis'] = await self._historical_analysis(cell_data)
            results['predictive_analysis'] = await self._predictive_analysis(results)
        
        return {'cell_tower_analysis': results}
    
    async def _analyze_cell_towers(self, cell_data: Dict) -> Dict[str, Any]:
        """Analyse détaillée des antennes relais fournies"""
        analysis = {
            'towers_identified': 0,
            'towers_details': [],
            'operators_detected': [],
            'technologies_found': [],
            'signal_analysis': {}
        }
        
        try:
            # Extraire les données des cellules
            cells = self._extract_cell_data(cell_data)
            analysis['towers_identified'] = len(cells)
            
            for cell in cells:
                tower_info = await self._get_tower_info(cell)
                if tower_info:
                    analysis['towers_details'].append(tower_info)
                    
                    # Opérateurs
                    operator = tower_info.get('operator', 'Unknown')
                    if operator not in analysis['operators_detected']:
                        analysis['operators_detected'].append(operator)
                    
                    # Technologies
                    technology = tower_info.get('technology', 'Unknown')
                    if technology not in analysis['technologies_found']:
                        analysis['technologies_found'].append(technology)
            
            # Analyse des signaux
            analysis['signal_analysis'] = await self._analyze_signal_strength(cells)
            
        except Exception as e:
            self.logger.error(f"Erreur analyse tours: {e}")
            analysis['error'] = str(e)
        
        return analysis
    
    def _extract_cell_data(self, cell_data: Dict) -> List[Dict]:
        """Extrait et normalise les données de cellules"""
        cells = []
        
        # Format Android
        if 'cellTowers' in cell_data:
            cells.extend(cell_data['cellTowers'])
        
        # Format iOS
        if 'cells' in cell_data:
            cells.extend(cell_data['cells'])
        
        # Format brut
        if 'cells' not in cell_data and 'cellTowers' not in cell_data:
            # Essayer d'extraire depuis les clés racines
            potential_cells = []
            for key, value in cell_data.items():
                if isinstance(value, dict) and any(field in value for field in ['mcc', 'mnc', 'lac', 'cid']):
                    potential_cells.append(value)
            cells.extend(potential_cells)
        
        return cells
    
    async def _get_tower_info(self, cell: Dict) -> Dict[str, Any]:
        """Récupère les informations détaillées d'une antenne"""
        tower_info = {
            'cell_id': cell.get('cid') or cell.get('cellId'),
            'location_area_code': cell.get('lac') or cell.get('locationAreaCode'),
            'mobile_country_code': cell.get('mcc'),
            'mobile_network_code': cell.get('mnc'),
            'signal_strength': cell.get('signalStrength') or cell.get('dbm'),
            'technology': cell.get('technology') or self._detect_technology(cell),
            'operator': await self._identify_operator(cell.get('mcc'), cell.get('mnc'))
        }
        
        # Géolocalisation de l'antenne
        location = await self._locate_tower(cell)
        if location:
            tower_info['location'] = location
            tower_info['coordinates'] = {
                'lat': location.get('lat'),
                'lon': location.get('lon'),
                'accuracy': location.get('accuracy', 0)
            }
        
        return tower_info
    
    def _detect_technology(self, cell: Dict) -> str:
        """Détecte la technologie cellulaire"""
        # Basé sur les champs disponibles
        if 'psc' in cell or 'primaryScramblingCode' in cell:
            return 'UMTS'
        elif 'pci' in cell or 'physicalCellId' in cell:
            return 'LTE'
        elif 'tac' in cell or 'trackingAreaCode' in cell:
            return 'LTE'
        elif 'nr' in cell:
            return '5G'
        else:
            return 'GSM'
    
    async def _identify_operator(self, mcc: int, mnc: int) -> str:
        """Identifie l'opérateur via MCC/MNC"""
        operators = {
            (208, 1): 'Orange France',
            (208, 2): 'Orange France',
            (208, 10): 'SFR',
            (208, 11): 'SFR', 
            (208, 13): 'SFR',
            (208, 15): 'Free Mobile',
            (208, 16): 'Free Mobile',
            (208, 20): 'Bouygues Telecom',
            (208, 21): 'Bouygues Telecom',
            (208, 88): 'Bouygues Telecom',
            (208, 9): 'SFR',
            (208, 91): 'Orange France'
        }
        
        return operators.get((mcc, mnc), f'Unknown ({mcc}-{mnc})')
    
    async def _locate_tower(self, cell: Dict) -> Optional[Dict[str, float]]:
        """Localise une antenne spécifique"""
        try:
            # Essayer OpenCellID
            location = await self._query_opencellid(cell)
            if location:
                return location
            
            # Essayer OpenBMap
            location = await self._query_openbmap(cell)
            if location:
                return location
            
            # Fallback: Estimation basée sur LAC
            return await self._estimate_from_lac(cell)
            
        except Exception as e:
            self.logger.error(f"Erreur localisation tour: {e}")
            return None
    
    async def _query_opencellid(self, cell: Dict) -> Optional[Dict[str, float]]:
        """Interroge l'API OpenCellID"""
        try:
            api_key = self.config.get_api_key('geolocation', 'opencellid_key') if self.config else None
            if not api_key:
                return None
            
            url = f"{self.api_endpoints['opencellid']}/cell"
            params = {
                'mcc': cell.get('mcc'),
                'mnc': cell.get('mnc'), 
                'lac': cell.get('lac'),
                'cellid': cell.get('cid'),
                'format': 'json',
                'key': api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('lat') and data.get('lon'):
                            return {
                                'lat': data['lat'],
                                'lon': data['lon'],
                                'accuracy': data.get('range', 1000),
                                'source': 'opencellid'
                            }
            return None
            
        except Exception as e:
            self.logger.debug(f"OpenCellID non disponible: {e}")
            return None
    
    async def _query_openbmap(self, cell: Dict) -> Optional[Dict[str, float]]:
        """Interroge l'API OpenBMap"""
        try:
            url = f"{self.api_endpoints['openbmap']}/cell"
            params = {
                'mcc': cell.get('mcc'),
                'mnc': cell.get('mnc'),
                'lac': cell.get('lac'),
                'cid': cell.get('cid'),
                'format': 'json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('lat') and data.get('lon'):
                            return {
                                'lat': data['lat'],
                                'lon': data['lon'],
                                'accuracy': 500,
                                'source': 'openbmap'
                            }
            return None
            
        except Exception as e:
            self.logger.debug(f"OpenBMap non disponible: {e}")
            return None
    
    async def _estimate_from_lac(self, cell: Dict) -> Optional[Dict[str, float]]:
        """Estime la position basée sur le LAC"""
        try:
            # Cette méthode fournit une estimation grossière basée sur le LAC
            # En pratique, vous auriez besoin d'une base de données LAC->position
            return {
                'lat': 48.8566,  # Paris par défaut
                'lon': 2.3522,
                'accuracy': 50000,  # Très faible précision
                'source': 'lac_estimation',
                'note': 'Estimation basée sur LAC - précision très faible'
            }
        except:
            return None
    
    async def _perform_geolocation(self, cell_data: Dict) -> Dict[str, Any]:
        """Effectue la géolocalisation basée sur les cellules"""
        geolocation = {
            'estimated_location': {},
            'method_used': 'unknown',
            'confidence_level': 'low',
            'possible_locations': []
        }
        
        try:
            # Essayer Google Geolocation API
            google_location = await self._google_geolocation(cell_data)
            if google_location:
                geolocation['estimated_location'] = google_location
                geolocation['method_used'] = 'google_geolocation'
                geolocation['confidence_level'] = 'high'
            
            # Essayer UnwiredLabs
            elif await self._unwiredlabs_geolocation(cell_data):
                unwired_location = await self._unwiredlabs_geolocation(cell_data)
                geolocation['estimated_location'] = unwired_location
                geolocation['method_used'] = 'unwiredlabs'
                geolocation['confidence_level'] = 'medium'
            
            # Fallback: Triangulation basique
            else:
                basic_location = await self._basic_triangulation(cell_data)
                geolocation['estimated_location'] = basic_location
                geolocation['method_used'] = 'basic_triangulation'
                geolocation['confidence_level'] = 'low'
            
            # Générer des localisations alternatives
            geolocation['possible_locations'] = await self._generate_alternative_locations(geolocation['estimated_location'])
            
        except Exception as e:
            self.logger.error(f"Erreur géolocalisation: {e}")
            geolocation['error'] = str(e)
        
        return geolocation
    
    async def _google_geolocation(self, cell_data: Dict) -> Optional[Dict[str, Any]]:
        """Utilise l'API Google Geolocation"""
        try:
            api_key = self.config.get_api_key('google', 'api_key') if self.config else None
            if not api_key:
                return None
            
            payload = {
                'cellTowers': self._extract_cell_data(cell_data),
                'considerIp': False
            }
            
            url = f"{self.api_endpoints['google_geolocation']}?key={api_key}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        location = data.get('location', {})
                        return {
                            'lat': location.get('lat'),
                            'lon': location.get('lng'),
                            'accuracy': data.get('accuracy', 0),
                            'source': 'google_geolocation'
                        }
            return None
            
        except Exception as e:
            self.logger.debug(f"Google Geolocation non disponible: {e}")
            return None
    
    async def _unwiredlabs_geolocation(self, cell_data: Dict) -> Optional[Dict[str, Any]]:
        """Utilise l'API UnwiredLabs"""
        try:
            api_key = self.config.get_api_key('geolocation', 'unwiredlabs_key') if self.config else None
            if not api_key:
                return None
            
            payload = {
                'token': api_key,
                'radio': 'gsm',
                'mcc': cell_data.get('mcc'),
                'mnc': cell_data.get('mnc'),
                'cells': [{
                    'lac': cell.get('lac'),
                    'cid': cell.get('cid'),
                    'psc': cell.get('psc'),
                    'signal': cell.get('signalStrength')
                } for cell in self._extract_cell_data(cell_data)]
            }
            
            url = f"{self.api_endpoints['unwiredlabs']}/v2/process.php"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == 'ok':
                            return {
                                'lat': data.get('lat'),
                                'lon': data.get('lon'),
                                'accuracy': data.get('accuracy', 0),
                                'source': 'unwiredlabs'
                            }
            return None
            
        except Exception as e:
            self.logger.debug(f"UnwiredLabs non disponible: {e}")
            return None
    
    async def _basic_triangulation(self, cell_data: Dict) -> Dict[str, Any]:
        """Effectue une triangulation basique"""
        try:
            cells = self._extract_cell_data(cell_data)
            tower_locations = []
            
            for cell in cells:
                location = await self._locate_tower(cell)
                if location and location.get('accuracy', 0) < 10000:  # Filtrer les estimations trop imprécises
                    tower_locations.append(location)
            
            if tower_locations:
                # Moyenne des positions avec pondération par précision
                total_weight = 0
                weighted_lat = 0
                weighted_lon = 0
                
                for loc in tower_locations:
                    weight = 1 / (loc.get('accuracy', 1000) + 1)
                    weighted_lat += loc['lat'] * weight
                    weighted_lon += loc['lon'] * weight
                    total_weight += weight
                
                if total_weight > 0:
                    return {
                        'lat': weighted_lat / total_weight,
                        'lon': weighted_lon / total_weight,
                        'accuracy': self._calculate_triangulation_accuracy(tower_locations),
                        'source': 'basic_triangulation',
                        'towers_used': len(tower_locations)
                    }
            
            # Fallback: Première tour avec meilleur signal
            best_signal_cell = max(cells, key=lambda x: x.get('signalStrength', -120))
            best_location = await self._locate_tower(best_signal_cell)
            
            return best_location or {
                'lat': 0,
                'lon': 0,
                'accuracy': 100000,
                'source': 'fallback',
                'note': 'Localisation non déterminée'
            }
            
        except Exception as e:
            self.logger.error(f"Erreur triangulation: {e}")
            return {
                'lat': 0,
                'lon': 0,
                'accuracy': 0,
                'source': 'error',
                'error': str(e)
            }
    
    def _calculate_triangulation_accuracy(self, tower_locations: List[Dict]) -> float:
        """Calcule la précision de la triangulation"""
        if len(tower_locations) < 2:
            return 5000  # Précision faible pour une seule tour
        
        # Calcul de l'étendue géographique
        lats = [loc['lat'] for loc in tower_locations]
        lons = [loc['lon'] for loc in tower_locations]
        
        lat_range = max(lats) - min(lats)
        lon_range = max(lons) - min(lons)
        
        # Conversion en mètres (approximative)
        accuracy_km = math.sqrt(lat_range**2 + lon_range**2) * 111  # 1 degré ≈ 111 km
        accuracy_m = accuracy_km * 1000
        
        return min(accuracy_m, 5000)  # Limiter à 5km max
    
    async def _analyze_coverage_area(self, analysis_results: Dict) -> Dict[str, Any]:
        """Analyse la zone de couverture"""
        coverage = {
            'estimated_radius': 0,
            'coverage_area_km2': 0,
            'population_density': 'unknown',
            'environment_type': 'unknown',
            'nearby_landmarks': []
        }
        
        try:
            location = analysis_results.get('geolocation_results', {}).get('estimated_location', {})
            if location and location.get('lat'):
                # Estimation basique du rayon de couverture
                towers_count = analysis_results.get('tower_analysis', {}).get('towers_identified', 0)
                coverage['estimated_radius'] = max(1000, 5000 / towers_count)  # En mètres
                coverage['coverage_area_km2'] = 3.14 * (coverage['estimated_radius'] / 1000) ** 2
                
                # Type d'environnement basé sur la densité de tours
                if towers_count > 5:
                    coverage['environment_type'] = 'urban'
                    coverage['population_density'] = 'high'
                elif towers_count > 2:
                    coverage['environment_type'] = 'suburban' 
                    coverage['population_density'] = 'medium'
                else:
                    coverage['environment_type'] = 'rural'
                    coverage['population_density'] = 'low'
            
        except Exception as e:
            self.logger.error(f"Erreur analyse couverture: {e}")
            coverage['error'] = str(e)
        
        return coverage
    
    async def _analyze_network_info(self, cell_data: Dict) -> Dict[str, Any]:
        """Analyse les informations réseau"""
        network_info = {
            'network_quality': 'unknown',
            'data_speed_estimate': 'unknown',
            'roaming_status': 'unknown',
            'network_reliability': 'unknown'
        }
        
        try:
            cells = self._extract_cell_data(cell_data)
            technologies = []
            signal_strengths = []
            
            for cell in cells:
                tech = self._detect_technology(cell)
                if tech not in technologies:
                    technologies.append(tech)
                
                signal = cell.get('signalStrength')
                if signal:
                    signal_strengths.append(signal)
            
            # Qualité réseau basée sur la technologie et le signal
            if '5G' in technologies:
                network_info['network_quality'] = 'excellent'
                network_info['data_speed_estimate'] = 'high'
            elif 'LTE' in technologies:
                network_info['network_quality'] = 'good'
                network_info['data_speed_estimate'] = 'medium'
            else:
                network_info['network_quality'] = 'basic'
                network_info['data_speed_estimate'] = 'low'
            
            # Fiabilité basée sur le nombre de tours
            if len(cells) >= 3:
                network_info['network_reliability'] = 'high'
            elif len(cells) >= 2:
                network_info['network_reliability'] = 'medium'
            else:
                network_info['network_reliability'] = 'low'
            
        except Exception as e:
            self.logger.error(f"Erreur analyse réseau: {e}")
            network_info['error'] = str(e)
        
        return network_info
    
    async def _analyze_signal_strength(self, cells: List[Dict]) -> Dict[str, Any]:
        """Analyse la force du signal"""
        signal_analysis = {
            'average_strength': 0,
            'strongest_signal': -120,
            'weakest_signal': -50,
            'signal_quality': 'poor'
        }
        
        try:
            signals = [cell.get('signalStrength', -120) for cell in cells if cell.get('signalStrength')]
            if signals:
                signal_analysis['average_strength'] = sum(signals) / len(signals)
                signal_analysis['strongest_signal'] = max(signals)
                signal_analysis['weakest_signal'] = min(signals)
                
                # Qualité du signal
                avg = signal_analysis['average_strength']
                if avg >= -70:
                    signal_analysis['signal_quality'] = 'excellent'
                elif avg >= -85:
                    signal_analysis['signal_quality'] = 'good'
                elif avg >= -100:
                    signal_analysis['signal_quality'] = 'fair'
                else:
                    signal_analysis['signal_quality'] = 'poor'
            
        except Exception as e:
            self.logger.error(f"Erreur analyse signal: {e}")
            signal_analysis['error'] = str(e)
        
        return signal_analysis
    
    async def _assess_accuracy(self, analysis_results: Dict) -> Dict[str, Any]:
        """Évalue la précision de la géolocalisation"""
        accuracy = {
            'overall_confidence': 'low',
            'factors_considered': [],
            'estimated_error_meters': 0,
            'recommendations': []
        }
        
        try:
            towers_count = analysis_results.get('tower_analysis', {}).get('towers_identified', 0)
            location_data = analysis_results.get('geolocation_results', {}).get('estimated_location', {})
            
            accuracy['estimated_error_meters'] = location_data.get('accuracy', 5000)
            
            # Facteurs influençant la précision
            if towers_count >= 3:
                accuracy['factors_considered'].append('multiple_towers_triangulation')
                accuracy['overall_confidence'] = 'high'
            elif towers_count == 2:
                accuracy['factors_considered'].append('two_towers_estimation') 
                accuracy['overall_confidence'] = 'medium'
            else:
                accuracy['factors_considered'].append('single_tower_estimation')
                accuracy['overall_confidence'] = 'low'
            
            # Recommandations
            if accuracy['overall_confidence'] == 'low':
                accuracy['recommendations'].append('Collecter plus de données cellulaires')
                accuracy['recommendations'].append('Utiliser WiFi ou GPS si disponible')
            
        except Exception as e:
            self.logger.error(f"Erreur évaluation précision: {e}")
            accuracy['error'] = str(e)
        
        return accuracy
    
    async def _historical_analysis(self, cell_data: Dict) -> Dict[str, Any]:
        """Analyse historique des positions"""
        return {
            'historical_data_available': False,
            'movement_patterns': [],
            'frequent_locations': []
        }
    
    async def _predictive_analysis(self, analysis_results: Dict) -> Dict[str, Any]:
        """Analyse prédictive"""
        return {
            'likely_environment': analysis_results.get('coverage_analysis', {}).get('environment_type', 'unknown'),
            'movement_prediction': 'stationary',
            'confidence': 0.5
        }
    
    async def _generate_alternative_locations(self, main_location: Dict) -> List[Dict]:
        """Génère des localisations alternatives"""
        alternatives = []
        
        try:
            if main_location and main_location.get('lat'):
                accuracy = main_location.get('accuracy', 1000)
                
                # Générer des points autour de la localisation principale
                for i in range(3):
                    import random
                    offset_lat = random.uniform(-0.01, 0.01)  # ~1km
                    offset_lon = random.uniform(-0.01, 0.01)
                    
                    alternatives.append({
                        'lat': main_location['lat'] + offset_lat,
                        'lon': main_location['lon'] + offset_lon,
                        'accuracy': accuracy * 1.5,
                        'probability': 0.7 - (i * 0.2)
                    })
            
        except Exception as e:
            self.logger.error(f"Erreur génération alternatives: {e}")
        
        return alternatives

# Exemple d'utilisation
async def main():
    """Exemple d'utilisation du analyseur d'antennes"""
    analyzer = CellTowerAnalyzer()
    
    # Données cellulaires exemple (format Android)
    sample_cell_data = {
        "cellTowers": [
            {
                "cellId": 12345678,
                "locationAreaCode": 5678,
                "mobileCountryCode": 208,
                "mobileNetworkCode": 1,
                "signalStrength": -75
            },
            {
                "cellId": 87654321,
                "locationAreaCode": 5678,
                "mobileCountryCode": 208,
                "mobileNetworkCode": 1,
                "signalStrength": -82
            }
        ]
    }
    
    try:
        results = await analyzer.investigate(sample_cell_data, depth=2)
        
        print("📡 Analyse des antennes relais terminée:")
        cell_data = results.get('cell_tower_analysis', {})
        
        print(f"🗼 Tours identifiées: {cell_data.get('tower_analysis', {}).get('towers_identified', 0)}")
        print(f"📍 Localisation estimée: {cell_data.get('geolocation_results', {}).get('estimated_location', {})}")
        print(f"📶 Qualité signal: {cell_data.get('tower_analysis', {}).get('signal_analysis', {}).get('signal_quality', 'unknown')}")
        print(f"🎯 Confiance: {cell_data.get('accuracy_assessment', {}).get('overall_confidence', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Erreur analyse: {e}")

if __name__ == "__main__":
    asyncio.run(main())
