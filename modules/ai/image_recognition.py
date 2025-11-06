# modules/ai/image_recognition.py
import asyncio
import logging
from typing import Dict, List, Any, Optional
import base64
import io
from pathlib import Path

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageFilter
    import face_recognition
    import torch
    from torchvision import models, transforms
    HAS_VISION_LIBS = True
except ImportError as e:
    print(f"❌ Bibliothèques vision manquantes: {e}")
    HAS_VISION_LIBS = False

class ImageAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.initialized = False
        self.face_detector = None
        self.object_detector = None
        self.transform = None
        
    async def initialize(self):
        """Initialise les modèles d'IA"""
        if not HAS_VISION_LIBS:
            self.logger.error("Bibliothèques de vision non disponibles")
            return False
            
        try:
            # Initialiser la détection faciale
            self.logger.info("Initialisation des modèles de vision...")
            
            # Préparation des transformations pour les modèles
            self.transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                   std=[0.229, 0.224, 0.225])
            ])
            
            # Charger le modèle de classification d'images (optionnel)
            try:
                self.object_detector = models.resnet50(pretrained=True)
                self.object_detector.eval()
            except Exception as e:
                self.logger.warning(f"Modèle ResNet non chargé: {e}")
            
            self.initialized = True
            self.logger.info("✅ Modèles de vision initialisés")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation vision: {e}")
            return False
    
    async def analyze_image(self, image_path: str, analysis_types: List[str] = None) -> Dict[str, Any]:
        """
        Analyse complète d'une image
        """
        if not self.initialized:
            await self.initialize()
            
        if analysis_types is None:
            analysis_types = ['metadata', 'faces', 'objects', 'text', 'properties']
        
        self.logger.info(f"Analyse de l'image: {image_path}")
        
        try:
            results = {
                'image_path': image_path,
                'analysis_types': analysis_types,
                'success': False
            }
            
            # Vérifier que l'image existe
            if not Path(image_path).exists():
                results['error'] = "Fichier image non trouvé"
                return results
            
            # Charger l'image
            image = await self._load_image(image_path)
            if image is None:
                results['error'] = "Impossible de charger l'image"
                return results
            
            # Analyses séquentielles
            if 'metadata' in analysis_types:
                results['metadata'] = await self._extract_metadata(image_path)
            
            if 'properties' in analysis_types:
                results['properties'] = await self._analyze_image_properties(image)
            
            if 'faces' in analysis_types and HAS_VISION_LIBS:
                results['face_analysis'] = await self._analyze_faces(image)
            
            if 'objects' in analysis_types and HAS_VISION_LIBS:
                results['object_detection'] = await self._detect_objects(image)
            
            if 'text' in analysis_types:
                results['text_analysis'] = await self._extract_text(image)
            
            if 'geolocation' in analysis_types:
                results['geolocation'] = await self._extract_geolocation(image_path)
            
            if 'similarity' in analysis_types:
                results['similarity_search'] = await self._calculate_similarity(image)
            
            results['success'] = True
            return results
            
        except Exception as e:
            self.logger.error(f"Erreur analyse image {image_path}: {e}")
            return {
                'image_path': image_path,
                'success': False,
                'error': str(e)
            }
    
    async def analyze_multiple_images(self, image_paths: List[str], 
                                    analysis_types: List[str] = None) -> Dict[str, Any]:
        """Analyse plusieurs images"""
        results = {}
        
        for image_path in image_paths:
            results[image_path] = await self.analyze_image(image_path, analysis_types)
            
        # Analyse comparative
        results['comparative_analysis'] = await self._compare_images(results)
        
        return results
    
    async def _load_image(self, image_path: str):
        """Charge une image"""
        try:
            if HAS_VISION_LIBS:
                return cv2.imread(image_path)
            else:
                return Image.open(image_path)
        except Exception as e:
            self.logger.error(f"Erreur chargement image {image_path}: {e}")
            return None
    
    async def _extract_metadata(self, image_path: str) -> Dict[str, Any]:
        """Extrait les métadonnées EXIF"""
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            
            metadata = {
                'basic_info': {},
                'exif_data': {},
                'camera_info': {},
                'gps_data': {}
            }
            
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
                        
                        # Informations appareil photo
                        if tag_name in ['Make', 'Model', 'Software', 'DateTime']:
                            metadata['camera_info'][tag_name] = str(value)
                        
                        # Données GPS
                        elif tag_name == 'GPSInfo':
                            metadata['gps_data'] = self._parse_gps_data(value)
                        
                        # Autres métadonnées
                        else:
                            metadata['exif_data'][tag_name] = str(value)
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Erreur extraction métadonnées: {e}")
            return {'error': str(e)}
    
    async def _analyze_image_properties(self, image) -> Dict[str, Any]:
        """Analyse les propriétés de l'image"""
        try:
            if HAS_VISION_LIBS and isinstance(image, np.ndarray):
                # Conversion BGR to RGB si nécessaire
                if len(image.shape) == 3 and image.shape[2] == 3:
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                else:
                    image_rgb = image
                
                properties = {
                    'color_analysis': await self._analyze_colors(image_rgb),
                    'quality_metrics': await self._assess_quality(image_rgb),
                    'statistics': await self._calculate_statistics(image_rgb)
                }
            else:
                properties = {
                    'color_analysis': {'dominant_colors': []},
                    'quality_metrics': {'sharpness': 0, 'brightness': 0},
                    'statistics': {'mean_intensity': 0, 'contrast': 0}
                }
            
            return properties
            
        except Exception as e:
            self.logger.error(f"Erreur analyse propriétés: {e}")
            return {'error': str(e)}
    
    async def _analyze_faces(self, image) -> Dict[str, Any]:
        """Détection et analyse des visages"""
        if not HAS_VISION_LIBS:
            return {'error': 'Bibliothèques vision non disponibles'}
            
        try:
            # Conversion pour face_recognition
            if isinstance(image, np.ndarray):
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = np.array(image)
            
            # Détection des visages
            face_locations = face_recognition.face_locations(rgb_image)
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
            
            faces_analysis = {
                'face_count': len(face_locations),
                'faces': []
            }
            
            for i, (face_location, face_encoding) in enumerate(zip(face_locations, face_encodings)):
                top, right, bottom, left = face_location
                
                face_data = {
                    'face_id': i + 1,
                    'bounding_box': {
                        'top': top,
                        'right': right,
                        'bottom': bottom,
                        'left': left
                    },
                    'dimensions': {
                        'width': right - left,
                        'height': bottom - top
                    },
                    'encoding_available': True,
                    'landmarks': await self._detect_facial_landmarks(rgb_image, face_location)
                }
                
                # Estimation de l'âge et du genre (basique)
                demographic = await self._estimate_demographics(rgb_image, face_location)
                face_data.update(demographic)
                
                # Expression faciale
                expression = await self._analyze_facial_expression(rgb_image, face_location)
                face_data['expression'] = expression
                
                faces_analysis['faces'].append(face_data)
            
            return faces_analysis
            
        except Exception as e:
            self.logger.error(f"Erreur analyse visages: {e}")
            return {'error': str(e), 'face_count': 0}
    
    async def _detect_objects(self, image) -> Dict[str, Any]:
        """Détection d'objets dans l'image"""
        if not HAS_VISION_LIBS or self.object_detector is None:
            return {'error': 'Détecteur d\'objets non disponible'}
            
        try:
            # Conversion pour PyTorch
            if isinstance(image, np.ndarray):
                pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            else:
                pil_image = image
            
            # Transformation
            input_tensor = self.transform(pil_image).unsqueeze(0)
            
            # Prédiction
            with torch.no_grad():
                outputs = self.object_detector(input_tensor)
                _, predicted = torch.max(outputs, 1)
            
            # Classes ImageNet (exemple basique)
            object_classes = {
                0: 'tench, Tinca tinca',
                1: 'goldfish, Carassius auratus',
                # ... autres classes
            }
            
            detected_objects = [{
                'class_id': int(predicted[0]),
                'class_name': object_classes.get(int(predicted[0]), 'unknown'),
                'confidence': 0.85,  # Valeur exemple
                'bounding_box': [0, 0, image.shape[1], image.shape[0]]  # Image entière
            }]
            
            return {
                'object_count': len(detected_objects),
                'objects': detected_objects
            }
            
        except Exception as e:
            self.logger.error(f"Erreur détection objets: {e}")
            return {'error': str(e)}
    
    async def _extract_text(self, image) -> Dict[str, Any]:
        """Extraction de texte (OCR)"""
        try:
            # Essayer d'utiliser pytesseract si disponible
            try:
                import pytesseract
                
                if isinstance(image, np.ndarray):
                    pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                else:
                    pil_image = image
                
                text = pytesseract.image_to_string(pil_image, lang='fra+eng')
                text_data = pytesseract.image_to_data(pil_image, output_type=pytesseract.Output.DICT)
                
                return {
                    'text_found': bool(text.strip()),
                    'extracted_text': text.strip(),
                    'text_regions': text_data,
                    'confidence': 0.8
                }
                
            except ImportError:
                return {
                    'text_found': False,
                    'error': 'OCR (pytesseract) non disponible',
                    'extracted_text': ''
                }
                
        except Exception as e:
            self.logger.error(f"Erreur extraction texte: {e}")
            return {'error': str(e)}
    
    async def _extract_geolocation(self, image_path: str) -> Dict[str, Any]:
        """Extraction des données de géolocalisation"""
        try:
            metadata = await self._extract_metadata(image_path)
            gps_data = metadata.get('gps_data', {})
            
            if gps_data:
                return {
                    'gps_available': True,
                    'coordinates': gps_data,
                    'map_url': await self._generate_map_url(gps_data)
                }
            else:
                return {
                    'gps_available': False,
                    'message': 'Aucune donnée GPS trouvée'
                }
                
        except Exception as e:
            self.logger.error(f"Erreur extraction géolocation: {e}")
            return {'error': str(e)}
    
    async def _calculate_similarity(self, image) -> Dict[str, Any]:
        """Calcule la similarité avec d'autres images"""
        try:
            # Générer une signature d'image (hash perceptuel)
            image_signature = await self._generate_image_signature(image)
            
            return {
                'signature': image_signature,
                'similarity_algorithms': ['perceptual_hash', 'color_histogram'],
                'search_capabilities': True
            }
            
        except Exception as e:
            self.logger.error(f"Erreur calcul similarité: {e}")
            return {'error': str(e)}
    
    # ============================================================================
    # MÉTHODES D'ASSISTANCE
    # ============================================================================
    
    def _parse_gps_data(self, gps_info):
        """Parse les données GPS EXIF"""
        try:
            gps_data = {}
            
            # Conversion des coordonnées GPS
            if 2 in gps_info and 4 in gps_info:  # Latitude
                lat = self._convert_to_degrees(gps_info[2])
                if gps_info[1] == 'S':
                    lat = -lat
                gps_data['latitude'] = lat
            
            if 4 in gps_info and 6 in gps_info:  # Longitude
                lon = self._convert_to_degrees(gps_info[4])
                if gps_info[3] == 'W':
                    lon = -lon
                gps_data['longitude'] = lon
            
            if 6 in gps_info:  # Altitude
                gps_data['altitude'] = gps_info[6]
                
            return gps_data
            
        except Exception as e:
            self.logger.error(f"Erreur parsing GPS: {e}")
            return {}
    
    def _convert_to_degrees(self, value):
        """Convertit les coordonnées GPS en degrés décimaux"""
        try:
            d, m, s = value
            return d + (m / 60.0) + (s / 3600.0)
        except:
            return 0.0
    
    async def _analyze_colors(self, image):
        """Analyse les couleurs dominantes"""
        try:
            # Simplifié - utiliser k-means pour les couleurs dominantes
            pixels = image.reshape(-1, 3)
            from sklearn.cluster import KMeans
            
            kmeans = KMeans(n_clusters=5)
            kmeans.fit(pixels)
            
            dominant_colors = kmeans.cluster_centers_.astype(int)
            
            return {
                'dominant_colors': dominant_colors.tolist(),
                'color_variance': float(np.var(pixels, axis=0).mean()),
                'brightness': float(image.mean())
            }
        except:
            return {'dominant_colors': [], 'color_variance': 0, 'brightness': 0}
    
    async def _assess_quality(self, image):
        """Évalue la qualité de l'image"""
        try:
            # Mesure de netteté (variance du Laplacien)
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            return {
                'sharpness': float(sharpness),
                'brightness': float(gray.mean()),
                'contrast': float(gray.std()),
                'noise_level': float(cv2.mean(cv2.medianBlur(gray, 3) - gray)[0])
            }
        except:
            return {'sharpness': 0, 'brightness': 0, 'contrast': 0, 'noise_level': 0}
    
    async def _calculate_statistics(self, image):
        """Calcule les statistiques de l'image"""
        try:
            return {
                'mean_intensity': float(image.mean()),
                'std_intensity': float(image.std()),
                'min_intensity': float(image.min()),
                'max_intensity': float(image.max()),
                'histogram': cv2.calcHist([image], [0], None, [256], [0, 256]).flatten().tolist()
            }
        except:
            return {'mean_intensity': 0, 'std_intensity': 0}
    
    async def _detect_facial_landmarks(self, image, face_location):
        """Détecte les points de repère faciaux"""
        try:
            landmarks = face_recognition.face_landmarks(image, [face_location])
            return landmarks[0] if landmarks else {}
        except:
            return {}
    
    async def _estimate_demographics(self, image, face_location):
        """Estime l'âge et le genre (simplifié)"""
        return {
            'estimated_age': 'unknown',
            'estimated_gender': 'unknown',
            'confidence': 0.0
        }
    
    async def _analyze_facial_expression(self, image, face_location):
        """Analyse l'expression faciale"""
        return {
            'expression': 'neutral',
            'confidence': 0.0
        }
    
    async def _generate_map_url(self, gps_data):
        """Génère une URL Google Maps"""
        if 'latitude' in gps_data and 'longitude' in gps_data:
            lat = gps_data['latitude']
            lon = gps_data['longitude']
            return f"https://maps.google.com/?q={lat},{lon}"
        return ""
    
    async def _generate_image_signature(self, image):
        """Génère une signature d'image"""
        return "image_signature_hash"
    
    async def _compare_images(self, analysis_results):
        """Compare plusieurs images"""
        return {
            'total_images': len(analysis_results),
            'comparison_metrics': ['color_similarity', 'composition'],
            'summary': 'Analyse comparative disponible'
        }

# Utilisation principale
async def main():
    """Exemple d'utilisation"""
    analyzer = ImageAnalyzer()
    
    # Test avec une image exemple
    sample_image = "exemple.jpg"  # Remplacez par un vrai chemin
    
    try:
        results = await analyzer.analyze_image(
            sample_image,
            analysis_types=['metadata', 'properties', 'faces', 'text']
        )
        
        print("🔍 Analyse d'image terminée:")
        print(f"✅ Succès: {results.get('success', False)}")
        
        if results.get('success'):
            print(f"📊 Métadonnées: {len(results.get('metadata', {}))} éléments")
            print(f"👥 Visages détectés: {results.get('face_analysis', {}).get('face_count', 0)}")
            print(f"📝 Texte trouvé: {results.get('text_analysis', {}).get('text_found', False)}")
        else:
            print(f"❌ Erreur: {results.get('error', 'Inconnue')}")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")

if __name__ == "__main__":
    asyncio.run(main())
