# modules/geolocation/wifi_analyzer.py
import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import math
import json

class WifiAnalyzer:
    def __init__(self, config_manager=None):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        self.api_endpoints = self._setup_endpoints()
        
    def _setup_endpoints(self) -> Dict[str, str]:
        """Configure les endpoints API pour l'analyse WiFi"""
        return {
            'google_geolocation': 'https://www.googleapis.com/geolocation/v1/geolocate',
            'mozilla_geolocation': 'https://location.services.mozilla.com/v1/geolocate',
            'unwiredlabs': 'https://eu1.unwiredlabs.com/api',
            'wigle': 'https://api.wigle.net/api/v2',
            'openwifi': 'https://api.openwifi.io/v1'
        }
    
    async def investigate(self, wifi_data: Dict, depth: int = 2) -> Dict[str, Any]:
        """
        Investigation des réseaux WiFi pour géolocalisation
        """
        self.logger.info("Début de l'analyse des réseaux WiFi")
        
        results = {
            'wifi_data_provided': wifi_data,
            'investigation_timestamp': datetime.now().isoformat(),
            'network_analysis': {},
            'geolocation_results': {},
            'security_assessment': {},
            'coverage_analysis': {},
            'privacy_risks': {}
        }
        
        if depth >= 1:
            results['network_analysis'] = await self._analyze_networks(wifi_data)
            results['geolocation_results'] = await self._perform_wifi_geolocation(wifi_data)
        
        if depth >= 2:
            results['security_assessment'] = await self._assess_security(results['network_analysis'])
            results['coverage_analysis'] = await self._analyze_coverage(results)
        
        if depth >= 3:
            results['privacy_risks'] = await self._assess_privacy_risks(results)
            results['network_fingerprinting'] = await self._analyze_network_fingerprint(results)
            results['predictive_analysis'] = await self._predictive_analysis(results)
        
        return {'wifi_analysis': results}
    
    async def _analyze_networks(self, wifi_data: Dict) -> Dict[str, Any]:
        """Analyse détaillée des réseaux WiFi détectés"""
        analysis = {
            'networks_detected': 0,
            'networks_details': [],
            'ssid_analysis': {},
            'signal_analysis': {},
            'encryption_types': [],
            'vendors_identified': []
        }
        
        try:
            # Extraire les données WiFi
            networks = self._extract_wifi_data(wifi_data)
            analysis['networks_detected'] = len(networks)
            
            for network in networks:
                network_info = await self._get_network_info(network)
                if network_info:
                    analysis['networks_details'].append(network_info)
                    
                    # Types de chiffrement
                    encryption = network_info.get('encryption', 'Unknown')
                    if encryption not in analysis['encryption_types']:
                        analysis['encryption_types'].append(encryption)
                    
                    # Fabricants identifiés
                    vendor = network_info.get('vendor', 'Unknown')
                    if vendor not in analysis['vendors_identified']:
                        analysis['vendors_identified'].append(vendor)
            
            # Analyse des SSID
            analysis['ssid_analysis'] = await self._analyze_ssids(networks)
            
            # Analyse des signaux
            analysis['signal_analysis'] = await self._analyze_wifi_signals(networks)
            
        except Exception as e:
            self.logger.error(f"Erreur analyse réseaux: {e}")
            analysis['error'] = str(e)
        
        return analysis
    
    def _extract_wifi_data(self, wifi_data: Dict) -> List[Dict]:
        """Extrait et normalise les données WiFi"""
        networks = []
        
        # Format standard (Google Geolocation)
        if 'wifiAccessPoints' in wifi_data:
            networks.extend(wifi_data['wifiAccessPoints'])
        
        # Format alternatif
        if 'networks' in wifi_data:
            networks.extend(wifi_data['networks'])
        
        # Format brut
        if 'wifiAccessPoints' not in wifi_data and 'networks' not in wifi_data:
            # Essayer d'extraire depuis les clés racines
            potential_networks = []
            for key, value in wifi_data.items():
                if isinstance(value, dict) and any(field in value for field in ['macAddress', 'bssid', 'ssid']):
                    potential_networks.append(value)
            networks.extend(potential_networks)
        
        return networks
    
    async def _get_network_info(self, network: Dict) -> Dict[str, Any]:
        """Récupère les informations détaillées d'un réseau WiFi"""
        network_info = {
            'bssid': network.get('macAddress') or network.get('bssid'),
            'ssid': network.get('ssid'),
            'signal_strength': network.get('signalStrength') or network.get('rssi'),
            'channel': network.get('channel'),
            'frequency': network.get('frequency'),
            'encryption': await self._detect_encryption(network),
            'vendor': await self._identify_vendor(network.get('macAddress') or network.get('bssid')),
            'first_seen': network.get('firstSeen'),
            'last_seen': network.get('lastSeen')
        }
        
        # Informations de géolocalisation
        location = await self._locate_network(network_info['bssid'])
        if location:
            network_info['location'] = location
            network_info['coordinates'] = {
                'lat': location.get('lat'),
                'lon': location.get('lon'),
                'accuracy': location.get('accuracy', 0)
            }
        
        # Sécurité
        network_info['security_assessment'] = await self._assess_network_security(network_info)
        
        return network_info
    
    async def _detect_encryption(self, network: Dict) -> str:
        """Détecte le type de chiffrement"""
        # Basé sur les champs disponibles et les patterns courants
        capabilities = network.get('capabilities', '')
        ssid = network.get('ssid', '')
        
        if 'WPA3' in capabilities:
            return 'WPA3'
        elif 'WPA2' in capabilities:
            return 'WPA2'
        elif 'WPA' in capabilities:
            return 'WPA'
        elif 'WEP' in capabilities:
            return 'WEP'
        elif 'PSK' in capabilities:
            return 'WPA-PSK'
        elif 'EAP' in capabilities:
            return 'WPA-Enterprise'
        else:
            return 'Open'
    
    async def _identify_vendor(self, mac_address: str) -> str:
        """Identifie le fabricant via l'adresse MAC"""
        if not mac_address:
            return 'Unknown'
        
        # Extraire l'OUI (premiers 3 octets)
        try:
            oui = mac_address.replace(':', '').upper()[:6]
            
            # Base de données OUI basique
            oui_database = {
                '000C29': 'VMware',
                '001C14': 'Cisco',
                '0021E9': 'Samsung',
                '0050F1': 'Cisco',
                '080027': 'PCS Systemtechnik',
                '0C5B8F': 'TP-Link',
                '1062EB': 'D-Link',
                '14CC20': 'TP-Link',
                '185E0F': 'Samsung',
                '1C3BF3': 'TP-Link',
                '1C5C60': 'Samsung',
                '202BC1': 'Huawei',
                '2462AB': 'Huawei',
                '286ED4': 'Huawei',
                '2C3996': 'Samsung',
                '2C5A0F': 'Cisco',
                '34159E': 'Ubiquiti',
                '3C8BFE': 'Samsung',
                '40F407': 'Huawei',
                '485A3F': 'Samsung',
                '4C09D4': 'Huawei',
                '54724F': 'Samsung',
                '5C353B': 'Samsung',
                '60A37D': 'Apple',
                '6C2E85': 'Samsung',
                '705812': 'TP-Link',
                '748D08': 'Apple',
                '78A106': 'Apple',
                '7C6D62': 'Apple',
                '885395': 'Apple',
                '8C8590': 'Apple',
                '9C207B': 'Apple',
                'A020A6': 'Samsung',
                'A4C361': 'Apple',
                'ACBC32': 'Apple',
                'B065BD': 'Apple',
                'B8E856': 'Apple',
                'BC5436': 'Apple',
                'C82A14': 'Apple',
                'CC25EF': 'Apple',
                'D0A637': 'Apple',
                'D8BB2C': 'Apple',
                'DC2B2A': 'Apple',
                'E0C767': 'Apple',
                'F0D1A9': 'Apple',
                'F4F5D8': 'Google',
                'FCFC48': 'Apple'
            }
            
            return oui_database.get(oui, 'Unknown')
            
        except:
            return 'Unknown'
    
    async def _locate_network(self, bssid: str) -> Optional[Dict[str, float]]:
        """Localise un réseau WiFi spécifique"""
        try:
            # Essayer Wigle API
            location = await self._query_wigle(bssid)
            if location:
                return location
            
            # Essayer OpenWiFi
            location = await self._query_openwifi(bssid)
            if location:
                return location
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erreur localisation réseau: {e}")
            return None
    
    async def _query_wigle(self, bssid: str) -> Optional[Dict[str, float]]:
        """Interroge l'API Wigle"""
        try:
            api_key = self.config.get_api_key('geolocation', 'wigle_key') if self.config else None
            if not api_key:
                return None
            
            url = f"{self.api_endpoints['wigle']}/network/detail"
            params = {
                'netid': bssid
            }
            headers = {
                'Authorization': f'Basic {api_key}'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('results'):
                            result = data['results'][0]
                            return {
                                'lat': result.get('trilat'),
                                'lon': result.get('trilong'),
                                'accuracy': 50,  # Estimation
                                'source': 'wigle'
                            }
            return None
            
        except Exception as e:
            self.logger.debug(f"Wigle non disponible: {e}")
            return None
    
    async def _query_openwifi(self, bssid: str) -> Optional[Dict[str, float]]:
        """Interroge l'API OpenWiFi"""
        try:
            url = f"{self.api_endpoints['openwifi']}/search"
            params = {
                'bssid': bssid
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('lat') and data.get('lon'):
                            return {
                                'lat': data['lat'],
                                'lon': data['lon'],
                                'accuracy': data.get('accuracy', 100),
                                'source': 'openwifi'
                            }
            return None
            
        except Exception as e:
            self.logger.debug(f"OpenWiFi non disponible: {e}")
            return None
    
    async def _perform_wifi_geolocation(self, wifi_data: Dict) -> Dict[str, Any]:
        """Effectue la géolocalisation basée sur les réseaux WiFi"""
        geolocation = {
            'estimated_location': {},
            'method_used': 'unknown',
            'confidence_level': 'low',
            'networks_used': 0,
            'possible_locations': []
        }
        
        try:
            # Essayer Google Geolocation API
            google_location = await self._google_wifi_geolocation(wifi_data)
            if google_location:
                geolocation['estimated_location'] = google_location
                geolocation['method_used'] = 'google_geolocation'
                geolocation['confidence_level'] = 'high'
                geolocation['networks_used'] = len(self._extract_wifi_data(wifi_data))
            
            # Essayer Mozilla Geolocation
            elif await self._mozilla_geolocation(wifi_data):
                mozilla_location = await self._mozilla_geolocation(wifi_data)
                geolocation['estimated_location'] = mozilla_location
                geolocation['method_used'] = 'mozilla_geolocation'
                geolocation['confidence_level'] = 'medium'
            
            # Essayer UnwiredLabs
            elif await self._unwiredlabs_wifi_geolocation(wifi_data):
                unwired_location = await self._unwiredlabs_wifi_geolocation(wifi_data)
                geolocation['estimated_location'] = unwired_location
                geolocation['method_used'] = 'unwiredlabs'
                geolocation['confidence_level'] = 'medium'
            
            # Fallback: Triangulation basique
            else:
                basic_location = await self._basic_wifi_triangulation(wifi_data)
                geolocation['estimated_location'] = basic_location
                geolocation['method_used'] = 'basic_triangulation'
                geolocation['confidence_level'] = 'low'
            
            # Générer des localisations alternatives
            geolocation['possible_locations'] = await self._generate_wifi_alternative_locations(geolocation['estimated_location'])
            
        except Exception as e:
            self.logger.error(f"Erreur géolocalisation WiFi: {e}")
            geolocation['error'] = str(e)
        
        return geolocation
    
    async def _google_wifi_geolocation(self, wifi_data: Dict) -> Optional[Dict[str, Any]]:
        """Utilise l'API Google Geolocation pour WiFi"""
        try:
            api_key = self.config.get_api_key('google', 'api_key') if self.config else None
            if not api_key:
                return None
            
            payload = {
                'wifiAccessPoints': self._extract_wifi_data(wifi_data),
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
                            'source': 'google_wifi_geolocation'
                        }
            return None
            
        except Exception as e:
            self.logger.debug(f"Google WiFi Geolocation non disponible: {e}")
            return None
    
    async def _mozilla_geolocation(self, wifi_data: Dict) -> Optional[Dict[str, Any]]:
        """Utilise l'API Mozilla Geolocation"""
        try:
            payload = {
                'wifiAccessPoints': self._extract_wifi_data(wifi_data),
                'fallbacks': {'ipf': False}
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_endpoints['mozilla_geolocation'], json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        location = data.get('location', {})
                        return {
                            'lat': location.get('lat'),
                            'lon': location.get('lng'),
                            'accuracy': data.get('accuracy', 0),
                            'source': 'mozilla_geolocation'
                        }
            return None
            
        except Exception as e:
            self.logger.debug(f"Mozilla Geolocation non disponible: {e}")
            return None
    
    async def _unwiredlabs_wifi_geolocation(self, wifi_data: Dict) -> Optional[Dict[str, Any]]:
        """Utilise l'API UnwiredLabs pour WiFi"""
        try:
            api_key = self.config.get_api_key('geolocation', 'unwiredlabs_key') if self.config else None
            if not api_key:
                return None
            
            networks = self._extract_wifi_data(wifi_data)
            payload = {
                'token': api_key,
                'wifi': [{
                    'bssid': net.get('macAddress') or net.get('bssid'),
                    'signal': net.get('signalStrength') or net.get('rssi'),
                    'channel': net.get('channel')
                } for net in networks]
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
                                'source': 'unwiredlabs_wifi'
                            }
            return None
            
        except Exception as e:
            self.logger.debug(f"UnwiredLabs WiFi non disponible: {e}")
            return None
    
    async def _basic_wifi_triangulation(self, wifi_data: Dict) -> Dict[str, Any]:
        """Effectue une triangulation WiFi basique"""
        try:
            networks = self._extract_wifi_data(wifi_data)
            network_locations = []
            
            for network in networks:
                bssid = network.get('macAddress') or network.get('bssid')
                if bssid:
                    location = await self._locate_network(bssid)
                    if location and location.get('accuracy', 0) < 1000:  # Filtrer les estimations imprécises
                        network_locations.append(location)
            
            if network_locations:
                # Moyenne des positions avec pondération par précision
                total_weight = 0
                weighted_lat = 0
                weighted_lon = 0
                
                for loc in network_locations:
                    weight = 1 / (loc.get('accuracy', 100) + 1)
                    weighted_lat += loc['lat'] * weight
                    weighted_lon += loc['lon'] * weight
                    total_weight += weight
                
                if total_weight > 0:
                    return {
                        'lat': weighted_lat / total_weight,
                        'lon': weighted_lon / total_weight,
                        'accuracy': self._calculate_wifi_triangulation_accuracy(network_locations),
                        'source': 'basic_wifi_triangulation',
                        'networks_used': len(network_locations)
                    }
            
            # Fallback: Réseau avec meilleur signal
            best_signal_network = max(networks, key=lambda x: x.get('signalStrength', -100))
            best_bssid = best_signal_network.get('macAddress') or best_signal_network.get('bssid')
            best_location = await self._locate_network(best_bssid)
            
            return best_location or {
                'lat': 0,
                'lon': 0,
                'accuracy': 10000,
                'source': 'fallback',
                'note': 'Localisation non déterminée'
            }
            
        except Exception as e:
            self.logger.error(f"Erreur triangulation WiFi: {e}")
            return {
                'lat': 0,
                'lon': 0,
                'accuracy': 0,
                'source': 'error',
                'error': str(e)
            }
    
    async def _analyze_ssids(self, networks: List[Dict]) -> Dict[str, Any]:
        """Analyse les SSID des réseaux"""
        ssid_analysis = {
            'common_patterns': [],
            'hidden_networks': 0,
            'enterprise_networks': 0,
            'default_ssids': 0,
            'suspicious_ssids': []
        }
        
        try:
            default_ssids = ['default', 'linksys', 'netgear', 'dlink', 'tp-link', 'home', 'wireless']
            enterprise_keywords = ['corp', 'enterprise', 'company', 'office', 'business']
            suspicious_keywords = ['attwifi', 'xfinitywifi', 'googlewifi', 'fbwifi']
            
            for network in networks:
                ssid = (network.get('ssid') or '').lower()
                
                # Réseaux cachés
                if not ssid or ssid == '':
                    ssid_analysis['hidden_networks'] += 1
                    continue
                
                # SSID par défaut
                if any(default in ssid for default in default_ssids):
                    ssid_analysis['default_ssids'] += 1
                
                # Réseaux d'entreprise
                if any(keyword in ssid for keyword in enterprise_keywords):
                    ssid_analysis['enterprise_networks'] += 1
                
                # SSID suspects
                if any(suspicious in ssid for suspicious in suspicious_keywords):
                    ssid_analysis['suspicious_ssids'].append(ssid)
            
        except Exception as e:
            self.logger.error(f"Erreur analyse SSID: {e}")
            ssid_analysis['error'] = str(e)
        
        return ssid_analysis
    
    async def _analyze_wifi_signals(self, networks: List[Dict]) -> Dict[str, Any]:
        """Analyse la force des signaux WiFi"""
        signal_analysis = {
            'average_strength': -100,
            'strongest_signal': -100,
            'weakest_signal': -30,
            'signal_quality': 'poor',
            'coverage_density': 'low'
        }
        
        try:
            signals = [net.get('signalStrength', -100) for net in networks if net.get('signalStrength')]
            if signals:
                signal_analysis['average_strength'] = sum(signals) / len(signals)
                signal_analysis['strongest_signal'] = max(signals)
                signal_analysis['weakest_signal'] = min(signals)
                
                # Qualité du signal
                avg = signal_analysis['average_strength']
                if avg >= -50:
                    signal_analysis['signal_quality'] = 'excellent'
                elif avg >= -65:
                    signal_analysis['signal_quality'] = 'good'
                elif avg >= -75:
                    signal_analysis['signal_quality'] = 'fair'
                else:
                    signal_analysis['signal_quality'] = 'poor'
                
                # Densité de couverture
                if len(signals) >= 10:
                    signal_analysis['coverage_density'] = 'high'
                elif len(signals) >= 5:
                    signal_analysis['coverage_density'] = 'medium'
                else:
                    signal_analysis['coverage_density'] = 'low'
            
        except Exception as e:
            self.logger.error(f"Erreur analyse signaux: {e}")
            signal_analysis['error'] = str(e)
        
        return signal_analysis
    
    async def _assess_security(self, network_analysis: Dict) -> Dict[str, Any]:
        """Évalue la sécurité des réseaux détectés"""
        security = {
            'overall_security': 'unknown',
            'encryption_breakdown': {},
            'security_risks': [],
            'recommendations': []
        }
        
        try:
            networks = network_analysis.get('networks_details', [])
            encryption_types = network_analysis.get('encryption_types', [])
            
            # Analyse par type de chiffrement
            encryption_counts = {}
            for net in networks:
                enc = net.get('encryption', 'Unknown')
                encryption_counts[enc] = encryption_counts.get(enc, 0) + 1
            
            security['encryption_breakdown'] = encryption_counts
            
            # Évaluation globale
            if 'Open' in encryption_types:
                security['overall_security'] = 'poor'
                security['security_risks'].append('Réseaux ouverts détectés')
            elif 'WEP' in encryption_types:
                security['overall_security'] = 'weak'
                security['security_risks'].append('Chiffrement WEP vulnérable détecté')
            elif 'WPA' in encryption_types and 'WPA2' not in encryption_types:
                security['overall_security'] = 'fair'
                security['security_risks'].append('Ancien chiffrement WPA détecté')
            elif 'WPA3' in encryption_types:
                security['overall_security'] = 'excellent'
            else:
                security['overall_security'] = 'good'
            
            # Recommandations
            if security['overall_security'] in ['poor', 'weak']:
                security['recommendations'].append('Éviter les réseaux ouverts et WEP')
                security['recommendations'].append('Utiliser un VPN sur les réseaux publics')
            
        except Exception as e:
            self.logger.error(f"Erreur évaluation sécurité: {e}")
            security['error'] = str(e)
        
        return security
    
    async def _analyze_coverage(self, analysis_results: Dict) -> Dict[str, Any]:
        """Analyse la zone de couverture WiFi"""
        coverage = {
            'estimated_radius': 0,
            'coverage_area_km2': 0,
            'environment_type': 'unknown',
            'network_density': 'low',
            'likely_venue': 'unknown'
        }
        
        try:
            networks_count = analysis_results.get('network_analysis', {}).get('networks_detected', 0)
            signal_analysis = analysis_results.get('network_analysis', {}).get('signal_analysis', {})
            
            # Estimation du rayon basée sur la densité
            if networks_count >= 15:
                coverage['estimated_radius'] = 50  # mètres
                coverage['network_density'] = 'very_high'
                coverage['environment_type'] = 'dense_urban'
                coverage['likely_venue'] = 'shopping_mall'
            elif networks_count >= 8:
                coverage['estimated_radius'] = 100
                coverage['network_density'] = 'high'
                coverage['environment_type'] = 'urban'
                coverage['likely_venue'] = 'office_building'
            elif networks_count >= 3:
                coverage['estimated_radius'] = 200
                coverage['network_density'] = 'medium'
                coverage['environment_type'] = 'suburban'
                coverage['likely_venue'] = 'residential_area'
            else:
                coverage['estimated_radius'] = 500
                coverage['network_density'] = 'low'
                coverage['environment_type'] = 'rural'
                coverage['likely_venue'] = 'open_area'
            
            coverage['coverage_area_km2'] = 3.14 * (coverage['estimated_radius'] / 1000) ** 2
            
        except Exception as e:
            self.logger.error(f"Erreur analyse couverture: {e}")
            coverage['error'] = str(e)
        
        return coverage
    
    async def _assess_privacy_risks(self, analysis_results: Dict) -> Dict[str, Any]:
        """Évalue les risques pour la vie privée"""
        risks = {
            'tracking_risk': 'low',
            'identified_risks': [],
            'privacy_recommendations': []
        }
        
        try:
            network_analysis = analysis_results.get('network_analysis', {})
            geolocation = analysis_results.get('geolocation_results', {})
            
            # Risque de tracking
            if geolocation.get('confidence_level') in ['high', 'medium']:
                risks['tracking_risk'] = 'high'
                risks['identified_risks'].append('Géolocalisation précise possible via WiFi')
            
            # Réseaux d'entreprise
            enterprise_nets = network_analysis.get('ssid_analysis', {}).get('enterprise_networks', 0)
            if enterprise_nets > 0:
                risks['identified_risks'].append(f'{enterprise_nets} réseaux d\'entreprise détectés')
                risks['tracking_risk'] = max(risks['tracking_risk'], 'medium')
            
            # Recommandations
            if risks['tracking_risk'] in ['high', 'medium']:
                risks['privacy_recommendations'].append('Désactiver le WiFi quand non utilisé')
                risks['privacy_recommendations'].append('Utiliser des réseaux privés virtuels (VPN)')
                risks['privacy_recommendations'].append('Éviter la connexion automatique aux réseaux')
            
        except Exception as e:
            self.logger.error(f"Erreur évaluation risques: {e}")
            risks['error'] = str(e)
        
        return risks
    
    async def _analyze_network_fingerprint(self, analysis_results: Dict) -> Dict[str, Any]:
        """Analyse l'empreinte réseau unique"""
        fingerprint = {
            'environment_signature': 'unknown',
            'unique_characteristics': [],
            'stability_score': 0,
            'fingerprint_confidence': 'low'
        }
        
        try:
            network_analysis = analysis_results.get('network_analysis', {})
            networks_count = network_analysis.get('networks_detected', 0)
            vendors = network_analysis.get('vendors_identified', [])
            
            # Caractéristiques uniques
            if 'Apple' in vendors and networks_count > 5:
                fingerprint['unique_characteristics'].append('Environnement riche en appareils Apple')
            
            if network_analysis.get('ssid_analysis', {}).get('enterprise_networks', 0) > 2:
                fingerprint['unique_characteristics'].append('Présence entreprise significative')
            
            # Score de stabilité
            if networks_count >= 5:
                fingerprint['stability_score'] = 80
                fingerprint['fingerprint_confidence'] = 'high'
            elif networks_count >= 2:
                fingerprint['stability_score'] = 60
                fingerprint['fingerprint_confidence'] = 'medium'
            else:
                fingerprint['stability_score'] = 30
                fingerprint['fingerprint_confidence'] = 'low'
            
        except Exception as e:
            self.logger.error(f"Erreur empreinte réseau: {e}")
            fingerprint['error'] = str(e)
        
        return fingerprint
    
    async def _predictive_analysis(self, analysis_results: Dict) -> Dict[str, Any]:
        """Analyse prédictive"""
        predictive = {
            'likely_environment': analysis_results.get('coverage_analysis', {}).get('likely_venue', 'unknown'),
            'movement_prediction': 'stationary',
            'user_behavior': 'unknown',
            'confidence': 0.5
        }
        
        try:
            networks_count = analysis_results.get('network_analysis', {}).get('networks_detected', 0)
            
            if networks_count > 10:
                predictive['user_behavior'] = 'indoor_urban'
                predictive['movement_prediction'] = 'limited_mobility'
            elif networks_count > 3:
                predictive['user_behavior'] = 'mixed_environment'
                predictive['movement_prediction'] = 'local_movement'
            else:
                predictive['user_behavior'] = 'outdoor_rural'
                predictive['movement_prediction'] = 'mobile'
            
        except Exception as e:
            self.logger.error(f"Erreur analyse prédictive: {e}")
            predictive['error'] = str(e)
        
        return predictive
    
    def _calculate_wifi_triangulation_accuracy(self, network_locations: List[Dict]) -> float:
        """Calcule la précision de la triangulation WiFi"""
        if len(network_locations) < 2:
            return 1000  # Précision faible pour un seul réseau
        
        # Calcul de l'étendue géographique
        lats = [loc['lat'] for loc in network_locations]
        lons = [loc['lon'] for loc in network_locations]
        
        lat_range = max(lats) - min(lats)
        lon_range = max(lons) - min(lons)
        
        # Conversion en mètres (approximative)
        accuracy_km = math.sqrt(lat_range**2 + lon_range**2) * 111
        accuracy_m = accuracy_km * 1000
        
        return min(accuracy_m, 500)  # WiFi est généralement plus précis que cellulaire
    
    async def _generate_wifi_alternative_locations(self, main_location: Dict) -> List[Dict]:
        """Génère des localisations alternatives pour WiFi"""
        alternatives = []
        
        try:
            if main_location and main_location.get('lat'):
                accuracy = main_location.get('accuracy', 100)
                
                # Générer des points autour de la localisation principale
                for i in range(3):
                    import random
                    offset_lat = random.uniform(-0.001, 0.001)  # ~100m
                    offset_lon = random.uniform(-0.001, 0.001)
                    
                    alternatives.append({
                        'lat': main_location['lat'] + offset_lat,
                        'lon': main_location['lon'] + offset_lon,
                        'accuracy': accuracy * 1.2,
                        'probability': 0.8 - (i * 0.2)
                    })
            
        except Exception as e:
            self.logger.error(f"Erreur génération alternatives WiFi: {e}")
        
        return alternatives

# Utilisation principale
async def main():
    """Exemple d'utilisation du analyseur WiFi"""
    analyzer = WifiAnalyzer()
    
    # Données WiFi exemple (format Google Geolocation)
    sample_wifi_data = {
        "wifiAccessPoints": [
            {
                "macAddress": "00:11:22:33:44:55",
                "signalStrength": -45,
                "ssid": "MyHomeWiFi",
                "channel": 6
            },
            {
                "macAddress": "AA:BB:CC:DD:EE:FF", 
                "signalStrength": -62,
                "ssid": "NeighborWiFi",
                "channel": 11
            },
            {
                "macAddress": "11:22:33:44:55:66",
                "signalStrength": -75,
                "ssid": "FreeWifi",
                "channel": 1
            }
        ]
    }
    
    try:
        results = await analyzer.investigate(sample_wifi_data, depth=2)
        
        print("📶 Analyse WiFi terminée:")
        wifi_data = results.get('wifi_analysis', {})
        
        print(f"📡 Réseaux détectés: {wifi_data.get('network_analysis', {}).get('networks_detected', 0)}")
        print(f"📍 Localisation: {wifi_data.get('geolocation_results', {}).get('estimated_location', {})}")
        print(f"🛡️ Sécurité: {wifi_data.get('security_assessment', {}).get('overall_security', 'unknown')}")
        print(f"📊 Environnement: {wifi_data.get('coverage_analysis', {}).get('environment_type', 'unknown')}")
        print(f"⚠️ Risque tracking: {wifi_data.get('privacy_risks', {}).get('tracking_risk', 'unknown')}")

except Exception as e:
    print(f"❌ Erreur analyse: {e}")

if __name__ == "__main__":
    asyncio.run(main())
