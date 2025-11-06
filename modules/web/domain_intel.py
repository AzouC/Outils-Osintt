"""
Module d'intelligence sur les domaines
Fournit des informations détaillées sur les noms de domaine
"""

import whois
import dns.resolver
import requests
import socket
import ssl
import json
from datetime import datetime
from urllib.parse import urlparse
import concurrent.futures
from typing import Dict, List, Any, Optional

from utils.logger import Logger
from utils.helpers import rate_limit, validate_domain
from core.security import sanitize_input

class DomainIntel:
    """
    Classe principale pour l'analyse des domaines
    """
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.logger = Logger(__name__)
        self.session = requests.Session()
        self.setup_headers()
    
    def setup_headers(self):
        """Configure les en-têtes HTTP"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def get_whois_info(self, domain: str) -> Dict[str, Any]:
        """
        Récupère les informations WHOIS d'un domaine
        
        Args:
            domain: Nom de domaine à analyser
            
        Returns:
            Dict contenant les informations WHOIS
        """
        try:
            domain = sanitize_input(domain)
            if not validate_domain(domain):
                return {"error": "Domaine invalide"}
            
            self.logger.info(f"Récupération WHOIS pour: {domain}")
            whois_data = whois.whois(domain)
            
            # Conversion des données WHOIS en dict serializable
            result = {}
            for key, value in whois_data.items():
                if isinstance(value, list):
                    result[key] = [str(item) for item in value]
                else:
                    result[key] = str(value) if value else None
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erreur WHOIS pour {domain}: {str(e)}")
            return {"error": f"Erreur WHOIS: {str(e)}"}
    
    def get_dns_records(self, domain: str) -> Dict[str, List]:
        """
        Récupère les enregistrements DNS d'un domaine
        
        Args:
            domain: Nom de domaine à analyser
            
        Returns:
            Dict contenant les différents records DNS
        """
        try:
            domain = sanitize_input(domain)
            records = {}
            record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA']
            
            for record_type in record_types:
                try:
                    answers = dns.resolver.resolve(domain, record_type)
                    records[record_type] = [str(rdata) for rdata in answers]
                except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
                    records[record_type] = []
                except Exception as e:
                    records[record_type] = [f"Erreur: {str(e)}"]
            
            return records
            
        except Exception as e:
            self.logger.error(f"Erreur DNS pour {domain}: {str(e)}")
            return {"error": f"Erreur DNS: {str(e)}"}
    
    def get_ssl_certificate_info(self, domain: str) -> Dict[str, Any]:
        """
        Récupère les informations du certificat SSL
        
        Args:
            domain: Nom de domaine à analyser
            
        Returns:
            Dict contenant les infos du certificat SSL
        """
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    cert_info = {
                        'subject': dict(x[0] for x in cert['subject']),
                        'issuer': dict(x[0] for x in cert['issuer']),
                        'version': cert.get('version'),
                        'serialNumber': cert.get('serialNumber'),
                        'notBefore': cert.get('notBefore'),
                        'notAfter': cert.get('notAfter'),
                        'expires_in_days': self._days_until_expiry(cert.get('notAfter'))
                    }
                    
                    return cert_info
                    
        except Exception as e:
            self.logger.error(f"Erreur SSL pour {domain}: {str(e)}")
            return {"error": f"Erreur SSL: {str(e)}"}
    
    def _days_until_expiry(self, not_after: str) -> int:
        """Calcule les jours avant expiration du certificat"""
        try:
            expiry_date = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
            return (expiry_date - datetime.now()).days
        except:
            return -1
    
    def get_http_headers(self, domain: str) -> Dict[str, str]:
        """
        Récupère les en-têtes HTTP d'un domaine
        
        Args:
            domain: Nom de domaine à analyser
            
        Returns:
            Dict contenant les en-têtes HTTP
        """
        try:
            url = f"https://{domain}"
            response = self.session.get(url, timeout=10, allow_redirects=True)
            
            headers = dict(response.headers)
            security_headers = {
                'content_security_policy': headers.get('Content-Security-Policy'),
                'x_frame_options': headers.get('X-Frame-Options'),
                'x_content_type_options': headers.get('X-Content-Type-Options'),
                'strict_transport_security': headers.get('Strict-Transport-Security'),
                'x_xss_protection': headers.get('X-XSS-Protection'),
                'server': headers.get('Server')
            }
            
            return security_headers
            
        except Exception as e:
            self.logger.error(f"Erreur headers HTTP pour {domain}: {str(e)}")
            return {"error": f"Erreur HTTP: {str(e)}"}
    
    def get_subdomains(self, domain: str, wordlist: List[str] = None) -> List[str]:
        """
        Recherche des sous-domaines (approche basique)
        
        Args:
            domain: Nom de domaine principal
            wordlist: Liste de sous-domaines à tester
            
        Returns:
            Liste des sous-domaines trouvés
        """
        if wordlist is None:
            wordlist = ['www', 'mail', 'ftp', 'localhost', 'webmail', 'smtp', 'pop', 'ns1', 'webdisk', 'ns2', 'cpanel', 'whm', 'autodiscover']
        
        found_subdomains = []
        
        def check_subdomain(subdomain):
            try:
                full_domain = f"{subdomain}.{domain}"
                socket.gethostbyname(full_domain)
                return full_domain
            except socket.gaierror:
                return None
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_subdomain, sub) for sub in wordlist]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    found_subdomains.append(result)
        
        return found_subdomains
    
    def comprehensive_analysis(self, domain: str) -> Dict[str, Any]:
        """
        Analyse complète d'un domaine
        
        Args:
            domain: Nom de domaine à analyser
            
        Returns:
            Dict contenant toutes les informations du domaine
        """
        self.logger.info(f"Lancement de l'analyse complète pour: {domain}")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # Exécution parallèle des différentes analyses
            whois_future = executor.submit(self.get_whois_info, domain)
            dns_future = executor.submit(self.get_dns_records, domain)
            ssl_future = executor.submit(self.get_ssl_certificate_info, domain)
            headers_future = executor.submit(self.get_http_headers, domain)
            subdomains_future = executor.submit(self.get_subdomains, domain)
            
            # Récupération des résultats
            whois_info = whois_future.result()
            dns_info = dns_future.result()
            ssl_info = ssl_future.result()
            headers_info = headers_future.result()
            subdomains_info = subdomains_future.result()
        
        # Compilation des résultats
        analysis_result = {
            'domain': domain,
            'timestamp': datetime.now().isoformat(),
            'whois': whois_info,
            'dns_records': dns_info,
            'ssl_certificate': ssl_info,
            'http_headers': headers_info,
            'subdomains': subdomains_info,
            'analysis_summary': self._generate_summary(whois_info, dns_info, ssl_info)
        }
        
        return analysis_result
    
    def _generate_summary(self, whois: Dict, dns: Dict, ssl: Dict) -> Dict[str, Any]:
        """Génère un résumé de l'analyse"""
        summary = {
            'domain_registered': 'error' not in whois,
            'has_mx_records': len(dns.get('MX', [])) > 0,
            'ssl_valid': 'error' not in ssl,
            'ssl_expiry_days': ssl.get('expires_in_days', -1) if 'error' not in ssl else -1,
            'nameservers_count': len(dns.get('NS', [])),
            'subdomains_count': len(dns.get('CNAME', []))
        }
        
        # Évaluation de sécurité basique
        if summary['ssl_valid'] and summary['ssl_expiry_days'] > 30:
            summary['security_level'] = 'MEDIUM'
        elif summary['ssl_valid'] and summary['ssl_expiry_days'] > 0:
            summary['security_level'] = 'LOW'
        else:
            summary['security_level'] = 'CRITICAL'
        
        return summary

def main():
    """Fonction principale pour test du module"""
    from core.config_manager import ConfigManager
    
    config = ConfigManager()
    domain_intel = DomainIntel(config)
    
    domain = input("Entrez un domaine à analyser: ")
    
    print(f"\n🔍 Analyse du domaine: {domain}")
    print("=" * 50)
    
    result = domain_intel.comprehensive_analysis(domain)
    
    print(f"WHOIS: {'✅' if result['analysis_summary']['domain_registered'] else '❌'}")
    print(f"DNS MX: {'✅' if result['analysis_summary']['has_mx_records'] else '❌'}")
    print(f"SSL: {'✅' if result['analysis_summary']['ssl_valid'] else '❌'}")
    print(f"Jours avant expiration SSL: {result['analysis_summary']['ssl_expiry_days']}")
    print(f"Niveau de sécurité: {result['analysis_summary']['security_level']}")
    print(f"Sous-domaines trouvés: {len(result['subdomains'])}")

if __name__ == "__main__":
    main()
