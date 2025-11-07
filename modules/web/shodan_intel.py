"""
Module d'intelligence Shodan
Interface avec l'API Shodan pour la collecte d'informations sur les hôtes
"""

import shodan
import json
import ipaddress
from typing import Dict, List, Any, Optional
from datetime import datetime

from utils.logger import Logger
from utils.helpers import rate_limit, validate_ip
from core.security import sanitize_input, encrypt_api_key

class ShodanIntel:
    """
    Classe pour interagir avec l'API Shodan
    """
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.logger = Logger(__name__)
        self.api_key = self._get_shodan_api_key()
        self.api = None
        self._init_shodan_client()
    
    def _get_shodan_api_key(self) -> Optional[str]:
        """
        Récupère la clé API Shodan depuis la configuration
        
        Returns:
            Clé API Shodan ou None si non configurée
        """
        try:
            api_keys = self.config.get('api_keys', {})
            shodan_key = api_keys.get('shodan')
            
            if not shodan_key or shodan_key == "VOTRE_CLE_API_ICI":
                self.logger.warning("Clé API Shodan non configurée")
                return None
            
            return shodan_key
            
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement de la clé API Shodan: {str(e)}")
            return None
    
    def _init_shodan_client(self):
        """Initialise le client API Shodan"""
        if not self.api_key:
            self.logger.error("Impossible d'initialiser Shodan: clé API manquante")
            return
        
        try:
            self.api = shodan.Shodan(self.api_key)
            self.logger.info("Client Shodan initialisé avec succès")
        except Exception as e:
            self.logger.error(f"Erreur d'initialisation Shodan: {str(e)}")
            self.api = None
    
    def is_configured(self) -> bool:
        """
        Vérifie si le module est correctement configuré
        
        Returns:
            bool: True si configuré, False sinon
        """
        return self.api is not None
    
    def get_host_info(self, ip: str) -> Dict[str, Any]:
        """
        Récupère les informations détaillées sur un hôte
        
        Args:
            ip: Adresse IP à investiguer
            
        Returns:
            Dict contenant les informations de l'hôte
        """
        if not self.is_configured():
            return {"error": "Shodan non configuré"}
        
        try:
            ip = sanitize_input(ip)
            if not validate_ip(ip):
                return {"error": "Adresse IP invalide"}
            
            self.logger.info(f"Recherche Shodan pour l'IP: {ip}")
            
            # Appel API Shodan
            host = self.api.host(ip)
            
            # Formatage des résultats
            result = {
                'ip': host.get('ip_str', ip),
                'country': host.get('country_name', 'Inconnu'),
                'city': host.get('city', 'Inconnu'),
                'organization': host.get('org', 'Inconnu'),
                'operating_system': host.get('os', 'Inconnu'),
                'ports': host.get('ports', []),
                'last_update': host.get('last_update', 'Inconnu'),
                'vulnerabilities': host.get('vulns', []),
                'data': []
            }
            
            # Traitement des données des services
            for service in host.get('data', []):
                service_info = {
                    'port': service.get('port'),
                    'transport': service.get('transport'),
                    'product': service.get('product', 'Inconnu'),
                    'version': service.get('version', 'Inconnu'),
                    'banner': service.get('data', '')[:500]  # Limite la taille du banner
                }
                result['data'].append(service_info)
            
            # Statistiques de sécurité
            result['security_metrics'] = {
                'open_ports_count': len(host.get('ports', [])),
                'vulnerabilities_count': len(host.get('vulns', [])),
                'services_count': len(host.get('data', []))
            }
            
            return result
            
        except shodan.APIError as e:
            error_msg = f"Erreur API Shodan: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
        except Exception as e:
            error_msg = f"Erreur lors de la recherche Shodan: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def search_hosts(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Recherche des hôtes via une requête Shodan
        
        Args:
            query: Requête de recherche Shodan
            limit: Nombre maximum de résultats
            
        Returns:
            Dict contenant les résultats de recherche
        """
        if not self.is_configured():
            return {"error": "Shodan non configuré"}
        
        try:
            query = sanitize_input(query)
            self.logger.info(f"Recherche Shodan avec la requête: {query}")
            
            # Appel API Shodan
            results = self.api.search(query, limit=limit)
            
            # Formatage des résultats
            search_results = {
                'query': query,
                'total_results': results.get('total', 0),
                'results': []
            }
            
            for match in results.get('matches', []):
                host_info = {
                    'ip': match.get('ip_str'),
                    'port': match.get('port'),
                    'product': match.get('product', 'Inconnu'),
                    'version': match.get('version', 'Inconnu'),
                    'organization': match.get('org', 'Inconnu'),
                    'location': f"{match.get('city', 'Inconnu')}, {match.get('country_name', 'Inconnu')}",
                    'banner_preview': match.get('data', '')[:200],
                    'last_update': match.get('timestamp', 'Inconnu')
                }
                search_results['results'].append(host_info)
            
            return search_results
            
        except shodan.APIError as e:
            error_msg = f"Erreur API Shodan: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
        except Exception as e:
            error_msg = f"Erreur lors de la recherche Shodan: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def get_scanning_quota(self) -> Dict[str, Any]:
        """
        Récupère les informations de quota de l'API
        
        Returns:
            Dict contenant les informations de quota
        """
        if not self.is_configured():
            return {"error": "Shodan non configuré"}
        
        try:
            info = self.api.info()
            
            quota_info = {
                'scan_credits': info.get('scan_credits', 0),
                'query_credits': info.get('query_credits', 0),
                'monitored_ips': info.get('monitored_ips', 0),
                'plan': info.get('plan', 'Inconnu'),
                'unlocked': info.get('unlocked', False),
                'telnet': info.get('telnet', False)
            }
            
            return quota_info
            
        except Exception as e:
            error_msg = f"Erreur lors de la récupération du quota: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def scan_ip(self, ip: str) -> Dict[str, Any]:
        """
        Demande un scan Shodan pour une IP (nécessite des crédits scan)
        
        Args:
            ip: Adresse IP à scanner
            
        Returns:
            Dict contenant le résultat de la demande de scan
        """
        if not self.is_configured():
            return {"error": "Shodan non configuré"}
        
        try:
            ip = sanitize_input(ip)
            if not validate_ip(ip):
                return {"error": "Adresse IP invalide"}
            
            self.logger.info(f"Demande de scan Shodan pour l'IP: {ip}")
            
            # Vérification du quota
            quota = self.get_scanning_quota()
            if 'error' in quota:
                return quota
            
            if quota.get('scan_credits', 0) <= 0:
                return {"error": "Crédits de scan insuffisants"}
            
            # Demande de scan
            scan_result = self.api.scan(ip)
            
            return {
                'scan_id': scan_result.get('id'),
                'status': 'demandé',
                'message': 'Scan Shodan demandé avec succès',
                'ip': ip
            }
            
        except shodan.APIError as e:
            error_msg = f"Erreur API Shodan lors du scan: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
        except Exception as e:
            error_msg = f"Erreur lors de la demande de scan: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def get_scan_status(self, scan_id: str) -> Dict[str, Any]:
        """
        Récupère le statut d'un scan Shodan
        
        Args:
            scan_id: ID du scan
            
        Returns:
            Dict contenant le statut du scan
        """
        if not self.is_configured():
            return {"error": "Shodan non configuré"}
        
        try:
            scan_status = self.api.scan_status(scan_id)
            
            return {
                'scan_id': scan_id,
                'status': scan_status,
                'completed': scan_status == 'DONE'
            }
            
        except Exception as e:
            error_msg = f"Erreur lors de la récupération du statut: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def search_vulnerabilities(self, query: str = None, product: str = None) -> Dict[str, Any]:
        """
        Recherche des vulnérabilités dans la base Shodan
        
        Args:
            query: Requête de recherche générale
            product: Produit spécifique à rechercher
            
        Returns:
            Dict contenant les vulnérabilités trouvées
        """
        if not self.is_configured():
            return {"error": "Shodan non configuré"}
        
        try:
            search_query = ""
            if query:
                search_query = query
            elif product:
                search_query = f"product:{product}"
            else:
                return {"error": "Requête ou produit requis"}
            
            self.logger.info(f"Recherche de vulnérabilités: {search_query}")
            
            # Recherche d'hôtes avec vulnérabilités
            results = self.api.search(f"{search_query} vuln:", limit=20)
            
            vulnerabilities = {
                'query': search_query,
                'total_hosts_vulnerable': results.get('total', 0),
                'vulnerable_hosts': []
            }
            
            for match in results.get('matches', []):
                host_vulns = match.get('vulns', {})
                if host_vulns:
                    host_info = {
                        'ip': match.get('ip_str'),
                        'port': match.get('port'),
                        'product': match.get('product', 'Inconnu'),
                        'vulnerabilities': list(host_vulns.keys()),
                        'vulnerability_count': len(host_vulns)
                    }
                    vulnerabilities['vulnerable_hosts'].append(host_info)
            
            return vulnerabilities
            
        except Exception as e:
            error_msg = f"Erreur lors de la recherche de vulnérabilités: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def comprehensive_analysis(self, target: str, analysis_type: str = "auto") -> Dict[str, Any]:
        """
        Analyse complète d'une cible (IP ou domaine)
        
        Args:
            target: Cible à analyser (IP ou domaine)
            analysis_type: Type d'analyse (auto, host, search)
            
        Returns:
            Dict contenant l'analyse complète
        """
        self.logger.info(f"Analyse Shodan complète pour: {target}")
        
        result = {
            'target': target,
            'timestamp': datetime.now().isoformat(),
            'analysis_type': analysis_type,
            'shodan_configured': self.is_configured()
        }
        
        if not self.is_configured():
            result['error'] = "Shodan non configuré"
            return result
        
        try:
            # Détection automatique du type de cible
            if analysis_type == "auto":
                try:
                    ipaddress.ip_address(target)
                    analysis_type = "host"
                except ValueError:
                    analysis_type = "search"
            
            # Exécution de l'analyse
            if analysis_type == "host":
                result['host_info'] = self.get_host_info(target)
                result['scan_request'] = self.scan_ip(target) if validate_ip(target) else {"error": "IP invalide pour scan"}
            elif analysis_type == "search":
                result['search_results'] = self.search_hosts(target)
            
            # Informations de quota
            result['quota_info'] = self.get_scanning_quota()
            
            return result
            
        except Exception as e:
            error_msg = f"Erreur lors de l'analyse complète: {str(e)}"
            self.logger.error(error_msg)
            result['error'] = error_msg
            return result

def main():
    """Fonction principale pour test du module"""
    from core.config_manager import ConfigManager
    
    config = ConfigManager()
    shodan_intel = ShodanIntel(config)
    
    if not shodan_intel.is_configured():
        print("❌ Shodan non configuré. Configurez votre clé API dans config/api_keys.yml")
        return
    
    print("🔍 Module Shodan Intelligence")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Informations sur un hôte (IP)")
        print("2. Recherche par requête")
        print("3. Quota API")
        print("4. Scan d'une IP")
        print("5. Recherche de vulnérabilités")
        print("6. Quitter")
        
        choice = input("\nChoisissez une option (1-6): ").strip()
        
        if choice == '1':
            ip = input("Entrez l'adresse IP: ").strip()
            result = shodan_intel.get_host_info(ip)
            print(f"\nRésultats pour {ip}:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        elif choice == '2':
            query = input("Entrez la requête Shodan: ").strip()
            result = shodan_intel.search_hosts(query, limit=5)
            print(f"\nRésultats de recherche:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        elif choice == '3':
            quota = shodan_intel.get_scanning_quota()
            print(f"\nQuota Shodan:")
            print(json.dumps(quota, indent=2, ensure_ascii=False))
            
        elif choice == '4':
            ip = input("Entrez l'adresse IP à scanner: ").strip()
            result = shodan_intel.scan_ip(ip)
            print(f"\nRésultat du scan:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        elif choice == '5':
            product = input("Entrez le produit à rechercher (ex: Apache, nginx): ").strip()
            result = shodan_intel.search_vulnerabilities(product=product)
            print(f"\nVulnérabilités trouvées:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        elif choice == '6':
            break
        else:
            print("Option invalide")

if __name__ == "__main__":
    main()
