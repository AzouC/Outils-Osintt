"""
Module Wayback Machine
Interface avec l'Internet Archive Wayback Machine pour l'historique des sites web
"""

import requests
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from urllib.parse import urlparse, urljoin
import concurrent.futures

from utils.logger import Logger
from utils.helpers import rate_limit, validate_url
from core.security import sanitize_input

class WaybackMachine:
    """
    Classe pour interagir avec l'API Wayback Machine
    """
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.logger = Logger(__name__)
        self.session = requests.Session()
        self.base_url = "https://web.archive.org"
        self.setup_headers()
    
    def setup_headers(self):
        """Configure les en-têtes HTTP"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def get_snapshots_list(self, url: str, limit: int = 100) -> Dict[str, Any]:
        """
        Récupère la liste des snapshots disponibles pour une URL
        
        Args:
            url: URL à investiguer
            limit: Nombre maximum de snapshots à récupérer
            
        Returns:
            Dict contenant la liste des snapshots
        """
        try:
            url = sanitize_input(url)
            if not validate_url(url):
                return {"error": "URL invalide"}
            
            self.logger.info(f"Récupération des snapshots pour: {url}")
            
            # API CDX de Wayback Machine
            cdx_url = f"{self.base_url}/cdx/search/cdx"
            params = {
                'url': url,
                'output': 'json',
                'limit': limit,
                'collapse': 'timestamp:10'  # Regroupe par 10 secondes pour éviter les doublons
            }
            
            response = self.session.get(cdx_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not data or len(data) <= 1:
                return {
                    "url": url,
                    "snapshots_count": 0,
                    "snapshots": [],
                    "message": "Aucun snapshot trouvé"
                }
            
            # Traitement des résultats CDX
            # La première ligne contient les en-têtes
            headers = data[0]
            snapshots_data = data[1:]
            
            snapshots = []
            for snapshot in snapshots_data:
                if len(snapshot) >= 5:
                    snapshot_info = {
                        'timestamp': snapshot[1],
                        'original_url': snapshot[2],
                        'mime_type': snapshot[3],
                        'status_code': snapshot[4],
                        'digest': snapshot[5] if len(snapshot) > 5 else None,
                        'length': snapshot[6] if len(snapshot) > 6 else None,
                        'wayback_url': f"{self.base_url}/web/{snapshot[1]}/{snapshot[2]}",
                        'date_formatted': self._format_timestamp(snapshot[1])
                    }
                    snapshots.append(snapshot_info)
            
            # Tri par date (du plus récent au plus ancien)
            snapshots.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return {
                "url": url,
                "snapshots_count": len(snapshots),
                "snapshots": snapshots,
                "first_snapshot": snapshots[-1]['date_formatted'] if snapshots else None,
                "last_snapshot": snapshots[0]['date_formatted'] if snapshots else None
            }
            
        except requests.RequestException as e:
            error_msg = f"Erreur réseau lors de la récupération des snapshots: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
        except Exception as e:
            error_msg = f"Erreur lors de la récupération des snapshots: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def get_snapshot_content(self, wayback_url: str, max_size: int = 1024 * 1024) -> Dict[str, Any]:
        """
        Récupère le contenu d'un snapshot spécifique
        
        Args:
            wayback_url: URL complète du snapshot Wayback
            max_size: Taille maximale du contenu à récupérer (1MB par défaut)
            
        Returns:
            Dict contenant le contenu et les métadonnées du snapshot
        """
        try:
            wayback_url = sanitize_input(wayback_url)
            
            self.logger.info(f"Récupération du contenu: {wayback_url}")
            
            response = self.session.get(wayback_url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Vérification de la taille
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > max_size:
                return {
                    "error": f"Contenu trop volumineux ({content_length} bytes)",
                    "wayback_url": wayback_url,
                    "content_preview": None
                }
            
            content = response.text
            content_preview = content[:1000] + "..." if len(content) > 1000 else content
            
            return {
                "wayback_url": wayback_url,
                "content_length": len(content),
                "content_type": response.headers.get('content-type', 'inconnu'),
                "content_preview": content_preview,
                "full_content": content if len(content) <= 50000 else None  # Limite pour les gros contenus
            }
            
        except requests.RequestException as e:
            error_msg = f"Erreur réseau lors de la récupération du contenu: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
        except Exception as e:
            error_msg = f"Erreur lors de la récupération du contenu: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def get_oldest_snapshot(self, url: str) -> Dict[str, Any]:
        """
        Récupère le snapshot le plus ancien d'une URL
        
        Args:
            url: URL à investiguer
            
        Returns:
            Dict contenant le snapshot le plus ancien
        """
        try:
            url = sanitize_input(url)
            
            self.logger.info(f"Recherche du snapshot le plus ancien pour: {url}")
            
            # API pour le premier snapshot
            cdx_url = f"{self.base_url}/cdx/search/cdx"
            params = {
                'url': url,
                'output': 'json',
                'limit': 1,
                'from': '1990',  # Début d'Internet
                'to': '2020',    # Jusqu'à 2020 pour les anciens snapshots
                'sort': 'asc'    # Tri ascendant pour le plus ancien
            }
            
            response = self.session.get(cdx_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not data or len(data) <= 1:
                return {"error": "Aucun snapshot ancien trouvé"}
            
            snapshot_data = data[1]
            snapshot_info = {
                'timestamp': snapshot_data[1],
                'original_url': snapshot_data[2],
                'mime_type': snapshot_data[3],
                'status_code': snapshot_data[4],
                'wayback_url': f"{self.base_url}/web/{snapshot_data[1]}/{snapshot_data[2]}",
                'date_formatted': self._format_timestamp(snapshot_data[1]),
                'is_oldest': True
            }
            
            return snapshot_info
            
        except Exception as e:
            error_msg = f"Erreur lors de la recherche du snapshot ancien: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def get_newest_snapshot(self, url: str) -> Dict[str, Any]:
        """
        Récupère le snapshot le plus récent d'une URL
        
        Args:
            url: URL à investiguer
            
        Returns:
            Dict contenant le snapshot le plus récent
        """
        try:
            url = sanitize_input(url)
            
            self.logger.info(f"Recherche du snapshot le plus récent pour: {url}")
            
            # API pour le dernier snapshot
            cdx_url = f"{self.base_url}/cdx/search/cdx"
            params = {
                'url': url,
                'output': 'json',
                'limit': 1,
                'sort': 'desc'  # Tri descendant pour le plus récent
            }
            
            response = self.session.get(cdx_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not data or len(data) <= 1:
                return {"error": "Aucun snapshot récent trouvé"}
            
            snapshot_data = data[1]
            snapshot_info = {
                'timestamp': snapshot_data[1],
                'original_url': snapshot_data[2],
                'mime_type': snapshot_data[3],
                'status_code': snapshot_data[4],
                'wayback_url': f"{self.base_url}/web/{snapshot_data[1]}/{snapshot_data[2]}",
                'date_formatted': self._format_timestamp(snapshot_data[1]),
                'is_newest': True
            }
            
            return snapshot_info
            
        except Exception as e:
            error_msg = f"Erreur lors de la recherche du snapshot récent: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def get_snapshots_by_year(self, url: str, year: int) -> Dict[str, Any]:
        """
        Récupère les snapshots d'une année spécifique
        
        Args:
            url: URL à investiguer
            year: Année de recherche
            
        Returns:
            Dict contenant les snapshots de l'année
        """
        try:
            url = sanitize_input(url)
            
            if year < 1990 or year > datetime.now().year:
                return {"error": "Année invalide"}
            
            self.logger.info(f"Recherche des snapshots de {year} pour: {url}")
            
            cdx_url = f"{self.base_url}/cdx/search/cdx"
            params = {
                'url': url,
                'output': 'json',
                'from': str(year),
                'to': str(year + 1),
                'collapse': 'timestamp:6'  # Regroupe par minute
            }
            
            response = self.session.get(cdx_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not data or len(data) <= 1:
                return {
                    "url": url,
                    "year": year,
                    "snapshots_count": 0,
                    "snapshots": [],
                    "message": f"Aucun snapshot trouvé pour {year}"
                }
            
            snapshots = []
            for snapshot in data[1:]:
                if len(snapshot) >= 5:
                    snapshot_info = {
                        'timestamp': snapshot[1],
                        'original_url': snapshot[2],
                        'mime_type': snapshot[3],
                        'status_code': snapshot[4],
                        'wayback_url': f"{self.base_url}/web/{snapshot[1]}/{snapshot[2]}",
                        'date_formatted': self._format_timestamp(snapshot[1])
                    }
                    snapshots.append(snapshot_info)
            
            return {
                "url": url,
                "year": year,
                "snapshots_count": len(snapshots),
                "snapshots": snapshots,
                "first_snapshot_year": snapshots[0]['date_formatted'] if snapshots else None,
                "last_snapshot_year": snapshots[-1]['date_formatted'] if snapshots else None
            }
            
        except Exception as e:
            error_msg = f"Erreur lors de la recherche par année: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def search_text_in_snapshots(self, url: str, search_text: str, limit: int = 10) -> Dict[str, Any]:
        """
        Recherche du texte dans les snapshots (approche basique)
        
        Args:
            url: URL à investiguer
            search_text: Texte à rechercher
            limit: Nombre maximum de snapshots à analyser
            
        Returns:
            Dict contenant les snapshots où le texte a été trouvé
        """
        try:
            url = sanitize_input(url)
            search_text = sanitize_input(search_text)
            
            self.logger.info(f"Recherche du texte '{search_text}' dans les snapshots de: {url}")
            
            # Récupération des snapshots
            snapshots_data = self.get_snapshots_list(url, limit=limit)
            if 'error' in snapshots_data:
                return snapshots_data
            
            matching_snapshots = []
            
            # Recherche dans les snapshots (en parallèle pour la performance)
            def check_snapshot(snapshot):
                try:
                    content_data = self.get_snapshot_content(snapshot['wayback_url'])
                    if 'error' not in content_data and search_text.lower() in content_data.get('content_preview', '').lower():
                        snapshot['search_match'] = True
                        snapshot['content_preview'] = content_data.get('content_preview')
                        return snapshot
                except:
                    pass
                return None
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(check_snapshot, snapshot) for snapshot in snapshots_data['snapshots'][:limit]]
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result:
                        matching_snapshots.append(result)
            
            return {
                "url": url,
                "search_text": search_text,
                "matching_snapshots_count": len(matching_snapshots),
                "total_snapshots_searched": min(limit, len(snapshots_data['snapshots'])),
                "matching_snapshots": matching_snapshots
            }
            
        except Exception as e:
            error_msg = f"Erreur lors de la recherche de texte: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def get_historical_analysis(self, url: str, years: List[int] = None) -> Dict[str, Any]:
        """
        Analyse historique complète d'une URL
        
        Args:
            url: URL à analyser
            years: Liste des années à analyser (par défaut: 5 dernières années)
            
        Returns:
            Dict contenant l'analyse historique
        """
        try:
            url = sanitize_input(url)
            
            if years is None:
                current_year = datetime.now().year
                years = list(range(current_year - 5, current_year + 1))
            
            self.logger.info(f"Analyse historique pour: {url} sur les années {years}")
            
            analysis = {
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "analysis_years": years,
                "oldest_snapshot": self.get_oldest_snapshot(url),
                "newest_snapshot": self.get_newest_snapshot(url),
                "yearly_analysis": {}
            }
            
            # Analyse par année
            for year in years:
                analysis['yearly_analysis'][str(year)] = self.get_snapshots_by_year(url, year)
                rate_limit(1)  # Pause pour éviter de surcharger l'API
            
            # Statistiques globales
            all_snapshots = self.get_snapshots_list(url, limit=500)
            if 'error' not in all_snapshots:
                analysis['total_snapshots'] = all_snapshots.get('snapshots_count', 0)
                analysis['first_snapshot_date'] = all_snapshots.get('first_snapshot')
                analysis['last_snapshot_date'] = all_snapshots.get('last_snapshot')
            
            return analysis
            
        except Exception as e:
            error_msg = f"Erreur lors de l'analyse historique: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def _format_timestamp(self, timestamp: str) -> str:
        """
        Formate un timestamp Wayback en date lisible
        
        Args:
            timestamp: Timestamp Wayback (YYYYMMDDhhmmss)
            
        Returns:
            Date formatée
        """
        try:
            if len(timestamp) >= 8:
                year = timestamp[0:4]
                month = timestamp[4:6]
                day = timestamp[6:8]
                return f"{day}/{month}/{year}"
        except:
            pass
        return timestamp

def main():
    """Fonction principale pour test du module"""
    from core.config_manager import ConfigManager
    
    config = ConfigManager()
    wayback = WaybackMachine(config)
    
    print("🔍 Wayback Machine Intelligence")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Liste des snapshots")
        print("2. Snapshot le plus ancien")
        print("3. Snapshot le plus récent")
        print("4. Snapshots par année")
        print("5. Recherche de texte")
        print("6. Analyse historique")
        print("7. Quitter")
        
        choice = input("\nChoisissez une option (1-7): ").strip()
        
        if choice == '1':
            url = input("Entrez l'URL: ").strip()
            result = wayback.get_snapshots_list(url, limit=20)
            print(f"\nSnapshots pour {url}:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        elif choice == '2':
            url = input("Entrez l'URL: ").strip()
            result = wayback.get_oldest_snapshot(url)
            print(f"\nSnapshot le plus ancien:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        elif choice == '3':
            url = input("Entrez l'URL: ").strip()
            result = wayback.get_newest_snapshot(url)
            print(f"\nSnapshot le plus récent:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        elif choice == '4':
            url = input("Entrez l'URL: ").strip()
            year = int(input("Entrez l'année: ").strip())
            result = wayback.get_snapshots_by_year(url, year)
            print(f"\nSnapshots de {year}:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        elif choice == '5':
            url = input("Entrez l'URL: ").strip()
            text = input("Entrez le texte à rechercher: ").strip()
            result = wayback.search_text_in_snapshots(url, text, limit=10)
            print(f"\nRésultats de recherche:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        elif choice == '6':
            url = input("Entrez l'URL: ").strip()
            result = wayback.get_historical_analysis(url)
            print(f"\nAnalyse historique:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        elif choice == '7':
            break
        else:
            print("Option invalide")

if __name__ == "__main__":
    main()
