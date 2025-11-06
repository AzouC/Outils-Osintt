# modules/geolocation/geotag.py
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import struct
from pathlib import Path

try:
    from PIL import Image, ExifTags
    from PIL.ExifTags import TAGS, GPSTAGS
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import exifread
    HAS_EXIFREAD = True
except ImportError:
    HAS_EXIFREAD = False

class GeotagExtractor:
    def __init__(self, config_manager=None):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        
    async def investigate(self, image_path: str, depth: int = 2) -> Dict[str, Any]:
        """
        Extraction et analyse des géotags d'une image
        """
        self.logger.info(f"Extraction des géotags pour: {image_path}")
        
        results = {
            'image_path': image_path,
            'investigation_timestamp': datetime.now().isoformat(),
            'file_info': {},
            'exif_metadata': {},
            'gps_data': {},
            'location_analysis': {},
            'privacy_risks': {},
            'reverse_geocoding': {}
        }
        
        if not Path(image_path).exists():
            return {'error': f"Fichier non trouvé: {image_path}"}
        
        if depth >= 1:
            results['file_info'] = await self._get_file_info(image_path)
            results['exif_metadata'] = await self._extract_exif_metadata(image_path)
            results['gps_data'] = await self._extract_gps_data(image_path)
        
        if depth >= 2:
            results['location_analysis'] = await self._analyze_location(results['gps_data'])
            results['privacy_risks'] = await self._assess_privacy_risks(results)
        
        if depth >= 3:
            results['reverse_geocoding'] = await self._reverse_geocode(results['gps_data'])
            results['temporal_analysis'] = await self._analyze_temporal_data(results)
            results['device_fingerprinting'] = await self._analyze_device_info(results)
        
        return {'geotag_analysis': results}
    
    async def _get_file_info(self, image_path: str) -> Dict[str, Any]:
        """Récupère les informations basiques du fichier"""
        try:
            path = Path(image_path)
            stat = path.stat()
            
            return {
                'filename': path.name,
                'file_size': stat.st_size,
                'file_extension': path.suffix.lower(),
                'creation_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modification_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'file_path': str(path.absolute())
            }
        except Exception as e:
            self.logger.error(f"Erreur info fichier {image_path}: {e}")
            return {'error': str(e)}
    
    async def _extract_exif_metadata(self, image_path: str) -> Dict[str, Any]:
        """Extrait toutes les métadonnées EXIF"""
        metadata = {
            'basic_info': {},
            'camera_info': {},
            'shooting_info': {},
            'software_info': {},
            'all_exif_data': {}
        }
        
        try:
            if HAS_PIL:
                with Image.open(image_path) as img:
                    # Informations basiques
                    metadata['basic_info'] = {
                        'format': img.format,
                        'mode': img.mode,
                        'size': img.size,
                        'width': img.width,
                        'height': img.height
                    }
                    
                    # Données EXIF
                    exif_data = img._getexif()
                    if exif_data:
                        for tag_id, value in exif_data.items():
                            tag_name = TAGS.get(tag_id, tag_id)
                            
                            # Informations appareil
                            if tag_name in ['Make', 'Model', 'LensModel', 'SerialNumber']:
                                metadata['camera_info'][tag_name] = str(value)
                            
                            # Informations prise de vue
                            elif tag_name in ['DateTime', 'DateTimeOriginal', 'ExposureTime', 'FNumber', 'ISOSpeedRatings', 'FocalLength']:
                                metadata['shooting_info'][tag_name] = str(value)
                            
                            # Logiciel
                            elif tag_name in ['Software', 'ProcessingSoftware']:
                                metadata['software_info'][tag_name] = str(value)
                            
                            # Toutes les données
                            metadata['all_exif_data'][tag_name] = str(value)
            
            # Alternative avec exifread
            elif HAS_EXIFREAD:
                with open(image_path, 'rb') as f:
                    tags = exifread.process_file(f)
                    for tag, value in tags.items():
                        metadata['all_exif_data'][tag] = str(value)
            
            else:
                metadata['error'] = "Aucune bibliothèque EXIF disponible"
                
        except Exception as e:
            self.logger.error(f"Erreur extraction EXIF {image_path}: {e}")
            metadata['error'] = str(e)
        
        return metadata
    
    async def _extract_gps_data(self, image_path: str) -> Dict[str, Any]:
        """Extrait spécifiquement les données GPS"""
        gps_data = {
            'gps_available': False,
            'coordinates': {},
            'altitude': {},
            'timestamp': {},
            'gps_info': {}
        }
        
        try:
            if HAS_PIL:
                with Image.open(image_path) as img:
                    exif_data = img._getexif()
                    
                    if not exif_data:
                        return gps_data
                    
                    # Trouver le tag GPSInfo
                    gps_info = None
                    for tag_id, value in exif_data.items():
                        tag_name = TAGS.get(tag_id, tag_id)
                        if tag_name == 'GPSInfo':
                            gps_info = value
                            break
                    
                    if gps_info:
                        gps_data['gps_available'] = True
                        
                        # Extraire les données GPS
                        for key, value in gps_info.items():
                            tag_name = GPSTAGS.get(key, key)
                            
                            if tag_name == 'GPSLatitude':
                                gps_data['coordinates']['latitude'] = self._convert_to_degrees(value)
                                gps_data['coordinates']['latitude_ref'] = gps_info.get(
                                    GPSTAGS.get(1), 'N'
                                )
                            
                            elif tag_name == 'GPSLongitude':
                                gps_data['coordinates']['longitude'] = self._convert_to_degrees(value)
                                gps_data['coordinates']['longitude_ref'] = gps_info.get(
                                    GPSTAGS.get(3), 'E'
                                )
                            
                            elif tag_name == 'GPSAltitude':
                                gps_data['altitude']['value'] = float(value[0]) / float(value[1])
                                gps_data['altitude']['ref'] = gps_info.get(GPSTAGS.get(5), 0)
                            
                            elif tag_name == 'GPSTimeStamp':
                                gps_data['timestamp']['time'] = self._convert_gps_time(value)
                            
                            elif tag_name == 'GPSDateStamp':
                                gps_data['timestamp']['date'] = str(value)
                            
                            # Stocker toutes les infos GPS
                            gps_data['gps_info'][tag_name] = str(value)
                        
                        # Ajuster les coordonnées selon la référence
                        if 'latitude' in gps_data['coordinates']:
                            lat_ref = gps_data['coordinates'].get('latitude_ref', 'N')
                            if lat_ref == 'S':
                                gps_data['coordinates']['latitude'] = -gps_data['coordinates']['latitude']
                        
                        if 'longitude' in gps_data['coordinates']:
                            lon_ref = gps_data['coordinates'].get('longitude_ref', 'E')
                            if lon_ref == 'W':
                                gps_data['coordinates']['longitude'] = -gps_data['coordinates']['longitude']
            
            # Alternative avec exifread
            elif HAS_EXIFREAD:
                with open(image_path, 'rb') as f:
                    tags = exifread.process_file(f)
                    
                    gps_tags = {tag: value for tag, value in tags.items() if tag.startswith('GPS')}
                    if gps_tags:
                        gps_data['gps_available'] = True
                        gps_data['gps_info'] = {tag: str(value) for tag, value in gps_tags.items()}
                        
                        # Extraire coordonnées si disponibles
                        if 'GPS GPSLatitude' in gps_tags and 'GPS GPSLatitudeRef' in gps_tags:
                            lat = self._exifread_to_decimal(gps_tags['GPS GPSLatitude'])
                            lat_ref = str(gps_tags['GPS GPSLatitudeRef'])
                            gps_data['coordinates']['latitude'] = -lat if lat_ref == 'S' else lat
                        
                        if 'GPS GPSLongitude' in gps_tags and 'GPS GPSLongitudeRef' in gps_tags:
                            lon = self._exifread_to_decimal(gps_tags['GPS GPSLongitude'])
                            lon_ref = str(gps_tags['GPS GPSLongitudeRef'])
                            gps_data['coordinates']['longitude'] = -lon if lon_ref == 'W' else lon
            
            # Générer une URL Google Maps si coordonnées disponibles
            if gps_data['gps_available'] and 'latitude' in gps_data['coordinates']:
                lat = gps_data['coordinates']['latitude']
                lon = gps_data['coordinates']['longitude']
                gps_data['maps_url'] = f"https://maps.google.com/?q={lat},{lon}"
                gps_data['openstreetmap_url'] = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}"
        
        except Exception as e:
            self.logger.error(f"Erreur extraction GPS {image_path}: {e}")
            gps_data['error'] = str(e)
        
        return gps_data
    
    async def _analyze_location(self, gps_data: Dict) -> Dict[str, Any]:
        """Analyse la localisation GPS"""
        analysis = {
            'location_accuracy': 'unknown',
            'environment_type': 'unknown',
            'privacy_implications': [],
            'location_confidence': 'low'
        }
        
        try:
            if not gps_data.get('gps_available', False):
                analysis['location_accuracy'] = 'no_gps_data'
                return analysis
            
            coordinates = gps_data.get('coordinates', {})
            lat = coordinates.get('latitude')
            lon = coordinates.get('longitude')
            
            if lat is None or lon is None:
                analysis['location_accuracy'] = 'incomplete_coordinates'
                return analysis
            
            # Estimation de la précision basée sur les données disponibles
            if gps_data.get('altitude'):
                analysis['location_accuracy'] = 'high'
                analysis['location_confidence'] = 'high'
            else:
                analysis['location_accuracy'] = 'medium'
                analysis['location_confidence'] = 'medium'
            
            # Type d'environnement basé sur les coordonnées
            analysis['environment_type'] = await self._estimate_environment_type(lat, lon)
            
            # Implications vie privée
            analysis['privacy_implications'] = await self._assess_location_privacy(lat, lon)
            
        except Exception as e:
            self.logger.error(f"Erreur analyse localisation: {e}")
            analysis['error'] = str(e)
        
        return analysis
    
    async def _assess_privacy_risks(self, analysis_results: Dict) -> Dict[str, Any]:
        """Évalue les risques pour la vie privée"""
        risks = {
            'privacy_risk_level': 'low',
            'identified_risks': [],
            'recommendations': [],
            'sensitive_locations': []
        }
        
        try:
            gps_data = analysis_results.get('gps_data', {})
            exif_data = analysis_results.get('exif_metadata', {})
            
            # Risque 1: Données GPS présentes
            if gps_data.get('gps_available', False):
                risks['identified_risks'].append({
                    'type': 'gps_location',
                    'severity': 'high',
                    'description': 'Localisation exacte disponible dans les métadonnées',
                    'mitigation': 'Supprimer les données GPS avant partage'
                })
                risks['privacy_risk_level'] = 'high'
            
            # Risque 2: Informations appareil
            camera_info = exif_data.get('camera_info', {})
            if camera_info.get('SerialNumber'):
                risks['identified_risks'].append({
                    'type': 'device_identification',
                    'severity': 'medium',
                    'description': 'Numéro de série de l\'appareil présent',
                    'mitigation': 'Supprimer les métadonnées d\'identification'
                })
                risks['privacy_risk_level'] = max(risks['privacy_risk_level'], 'medium')
            
            # Risque 3: Date et heure exactes
            shooting_info = exif_data.get('shooting_info', {})
            if any(key in shooting_info for key in ['DateTime', 'DateTimeOriginal']):
                risks['identified_risks'].append({
                    'type': 'temporal_tracking',
                    'severity': 'medium',
                    'description': 'Date et heure exactes de prise de vue',
                    'mitigation': 'Supprimer les timestamps EXIF'
                })
            
            # Générer des recommandations
            if risks['privacy_risk_level'] in ['high', 'medium']:
                risks['recommendations'].append("Utiliser un outil de suppression EXIF avant partage")
                risks['recommendations'].append("Désactiver la géolocalisation dans l'appareil photo")
                risks['recommendations'].append("Éviter de partager des photos de lieux sensibles")
            
            # Détection de lieux sensibles
            if gps_data.get('gps_available', False):
                sensitive_locs = await self._detect_sensitive_locations(gps_data)
                risks['sensitive_locations'] = sensitive_locs
        
        except Exception as e:
            self.logger.error(f"Erreur évaluation risques: {e}")
            risks['error'] = str(e)
        
        return risks
    
    async def _reverse_geocode(self, gps_data: Dict) -> Dict[str, Any]:
        """Effectue un reverse geocoding des coordonnées"""
        geocoding = {
            'address_components': {},
            'location_type': 'unknown',
            'geocoding_service': 'none'
        }
        
        try:
            if not gps_data.get('gps_available', False):
                return geocoding
            
            coordinates = gps_data.get('coordinates', {})
            lat = coordinates.get('latitude')
            lon = coordinates.get('longitude')
            
            if lat is None or lon is None:
                return geocoding
            
            # Essayer différents services de géocodage
            nominatim_result = await self._nominatim_reverse_geocode(lat, lon)
            if nominatim_result:
                geocoding.update(nominatim_result)
                geocoding['geocoding_service'] = 'nominatim'
            
            # Fallback: Estimation basique
            else:
                geocoding['address_components'] = {
                    'estimated_country': await self._estimate_country(lat, lon),
                    'estimation_confidence': 'low'
                }
                geocoding['location_type'] = 'estimated'
        
        except Exception as e:
            self.logger.error(f"Erreur reverse geocoding: {e}")
            geocoding['error'] = str(e)
        
        return geocoding
    
    async def _analyze_temporal_data(self, analysis_results: Dict) -> Dict[str, Any]:
        """Analyse les données temporelles"""
        temporal = {
            'timeline_analysis': {},
            'temporal_patterns': [],
            'timezone_inference': 'unknown'
        }
        
        try:
            exif_data = analysis_results.get('exif_metadata', {})
            shooting_info = exif_data.get('shooting_info', {})
            gps_data = analysis_results.get('gps_data', {})
            
            # Extraction du timestamp
            datetime_str = shooting_info.get('DateTimeOriginal') or shooting_info.get('DateTime')
            if datetime_str:
                try:
                    # Essayer différents formats de date
                    dt = datetime.strptime(datetime_str, '%Y:%m:%d %H:%M:%S')
                    temporal['timeline_analysis'] = {
                        'capture_datetime': dt.isoformat(),
                        'day_of_week': dt.strftime('%A'),
                        'time_of_day': self._classify_time_of_day(dt),
                        'season': self._determine_season(dt)
                    }
                except:
                    pass
            
            # Inférence du fuseau horaire
            if gps_data.get('gps_available', False):
                temporal['timezone_inference'] = await self._infer_timezone(
                    gps_data['coordinates'].get('latitude'),
                    gps_data['coordinates'].get('longitude')
                )
        
        except Exception as e:
            self.logger.error(f"Erreur analyse temporelle: {e}")
            temporal['error'] = str(e)
        
        return temporal
    
    async def _analyze_device_info(self, analysis_results: Dict) -> Dict[str, Any]:
        """Analyse les informations de l'appareil"""
        device_info = {
            'camera_fingerprint': {},
            'software_identification': {},
            'device_characteristics': []
        }
        
        try:
            exif_data = analysis_results.get('exif_metadata', {})
            camera_info = exif_data.get('camera_info', {})
            software_info = exif_data.get('software_info', {})
            
            # Empreinte de l'appareil
            if camera_info:
                device_info['camera_fingerprint'] = {
                    'make': camera_info.get('Make'),
                    'model': camera_info.get('Model'),
                    'lens': camera_info.get('LensModel'),
                    'serial_number': camera_info.get('SerialNumber')
                }
            
            # Identification logicielle
            if software_info:
                device_info['software_identification'] = {
                    'software': software_info.get('Software'),
                    'processing_software': software_info.get('ProcessingSoftware')
                }
            
            # Caractéristiques uniques
            shooting_info = exif_data.get('shooting_info', {})
            unique_characteristics = []
            
            if shooting_info.get('SerialNumber'):
                unique_characteristics.append('serial_number_present')
            if any('Phone' in str(val) for val in camera_info.values()):
                unique_characteristics.append('likely_mobile_device')
            
            device_info['device_characteristics'] = unique_characteristics
        
        except Exception as e:
            self.logger.error(f"Erreur analyse appareil: {e}")
            device_info['error'] = str(e)
        
        return device_info
    
    # ============================================================================
    # MÉTHODES D'ASSISTANCE
    # ============================================================================
    
    def _convert_to_degrees(self, value: Tuple) -> float:
        """Convertit les coordonnées GPS en degrés décimaux"""
        try:
            if isinstance(value, tuple) and len(value) == 3:
                d, m, s = value
                return d + (m / 60.0) + (s / 3600.0)
            elif isinstance(value, (int, float)):
                return float(value)
            else:
                return 0.0
        except:
            return 0.0
    
    def _convert_gps_time(self, time_tuple: Tuple) -> str:
        """Convertit le temps GPS en format lisible"""
        try:
            if isinstance(time_tuple, tuple) and len(time_tuple) == 3:
                h, m, s = time_tuple
                return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
            return "00:00:00"
        except:
            return "00:00:00"
    
    def _exifread_to_decimal(self, value) -> float:
        """Convertit les valeurs EXIFread en décimal"""
        try:
            if hasattr(value, 'values'):
                values = list(value.values)
                if len(values) == 3:
                    return float(values[0]) + float(values[1])/60 + float(values[2])/3600
            return 0.0
        except:
            return 0.0
    
    async def _estimate_environment_type(self, lat: float, lon: float) -> str:
        """Estime le type d'environnement basé sur les coordonnées"""
        # Implémentation basique - en pratique, utiliserait des APIs de cartographie
        return "urban"  # Placeholder
    
    async def _assess_location_privacy(self, lat: float, lon: float) -> List[str]:
        """Évalue les implications vie privée de la localisation"""
        implications = []
        
        # Vérifications basiques
        implications.append("Localisation exacte exposée")
        implications.append("Possibilité de tracking géographique")
        
        return implications
    
    async def _detect_sensitive_locations(self, gps_data: Dict) -> List[Dict]:
        """Détecte les localisations sensibles"""
        sensitive_locations = []
        
        try:
            coordinates = gps_data.get('coordinates', {})
            lat = coordinates.get('latitude')
            lon = coordinates.get('longitude')
            
            if lat and lon:
                # Vérifications basiques de sensibilité
                if await self._is_residential_area(lat, lon):
                    sensitive_locations.append({
                        'type': 'residential_area',
                        'risk_level': 'high',
                        'description': 'Zone résidentielle - vie privée compromise'
                    })
                
                if await self._is_workplace(lat, lon):
                    sensitive_locations.append({
                        'type': 'workplace',
                        'risk_level': 'medium',
                        'description': 'Lieu de travail potentiel'
                    })
        
        except Exception as e:
            self.logger.error(f"Erreur détection lieux sensibles: {e}")
        
        return sensitive_locations
    
    async def _nominatim_reverse_geocode(self, lat: float, lon: float) -> Optional[Dict]:
        """Utilise Nominatim pour le reverse geocoding"""
        try:
            import aiohttp
            
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                'lat': lat,
                'lon': lon,
                'format': 'json',
                'zoom': 18,
                'addressdetails': 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        return {
                            'address_components': data.get('address', {}),
                            'display_name': data.get('display_name', ''),
                            'location_type': data.get('type', 'unknown'),
                            'osm_id': data.get('osm_id'),
                            'licence': data.get('licence')
                        }
            return None
            
        except Exception as e:
            self.logger.debug(f"Nominatim non disponible: {e}")
            return None
    
    async def _estimate_country(self, lat: float, lon: float) -> str:
        """Estime le pays basé sur les coordonnées"""
        # Implémentation basique - en pratique, utiliserait une base de données géographique
        if 41.0 <= lat <= 51.0 and -5.0 <= lon <= 10.0:
            return "France"
        elif 24.0 <= lat <= 50.0 and -125.0 <= lon <= -65.0:
            return "United States"
        elif 35.0 <= lat <= 72.0 and -10.0 <= lon <= 40.0:
            return "Europe"
        else:
            return "Unknown"
    
    def _classify_time_of_day(self, dt: datetime) -> str:
        """Classifie l'heure de la journée"""
        hour = dt.hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"
    
    def _determine_season(self, dt: datetime) -> str:
        """Détermine la saison"""
        month = dt.month
        if 3 <= month <= 5:
            return "spring"
        elif 6 <= month <= 8:
            return "summer"
        elif 9 <= month <= 11:
            return "autumn"
        else:
            return "winter"
    
    async def _infer_timezone(self, lat: float, lon: float) -> str:
        """Infère le fuseau horaire"""
        # Implémentation basique
        return "UTC+1"  # Placeholder
    
    async def _is_residential_area(self, lat: float, lon: float) -> bool:
        """Vérifie si c'est une zone résidentielle"""
        return False  # Placeholder
    
    async def _is_workplace(self, lat: float, lon: float) -> bool:
        """Vérifie si c'est un lieu de travail"""
        return False  # Placeholder

# Utilisation principale
async def main():
    """Exemple d'utilisation du extracteur de géotags"""
    extractor = GeotagExtractor()
    
    # Test avec une image exemple (remplacer par un vrai chemin)
    sample_image = "test_image.jpg"
    
    try:
        results = await extractor.investigate(sample_image, depth=2)
        
        print("📍 Analyse des géotags terminée:")
        geotag_data = results.get('geotag_analysis', {})
        
        print(f"📁 Fichier: {geotag_data.get('file_info', {}).get('filename')}")
        print(f"📊 GPS disponible: {geotag_data.get('gps_data', {}).get('gps_available', False)}")
        
        if geotag_data.get('gps_data', {}).get('gps_available'):
            coords = geotag_data['gps_data']['coordinates']
            print(f"🗺️ Coordonnées: {coords.get('latitude')}, {coords.get('longitude')}")
            print(f"🔗 Carte: {geotag_data['gps_data'].get('maps_url')}")
        
        print(f"⚠️ Risque vie privée: {geotag_data.get('privacy_risks', {}).get('privacy_risk_level', 'unknown')}")
        print(f"📷 Appareil: {geotag_data.get('exif_metadata', {}).get('camera_info', {}).get('Model', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Erreur analyse: {e}")

if __name__ == "__main__":
    asyncio.run(main())
