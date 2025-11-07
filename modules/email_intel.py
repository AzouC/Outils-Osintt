"""
Module d'intelligence sur les emails
Validation, vérification et collecte d'informations sur les adresses email
"""

import re
import dns.resolver
import socket
import smtplib
import requests
import hashlib
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from urllib.parse import urlencode
import json

from utils.logger import Logger
from utils.helpers import rate_limit, validate_email
from core.security import sanitize_input, hash_data

class EmailIntel:
    """
    Classe principale pour l'analyse des adresses email
    """
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.logger = Logger(__name__)
        self.session = requests.Session()
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
    
    def validate_email_syntax(self, email: str) -> Dict[str, Any]:
        """
        Validation syntaxique d'une adresse email
        
        Args:
            email: Adresse email à valider
            
        Returns:
            Dict contenant les résultats de validation
        """
        try:
            email = sanitize_input(email.lower().strip())
            
            # Pattern de validation d'email
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            is_valid = re.match(pattern, email) is not None
            
            result = {
                'email': email,
                'syntax_valid': is_valid,
                'timestamp': datetime.now().isoformat()
            }
            
            if is_valid:
                # Extraction des composants
                username, domain = email.split('@')
                result.update({
                    'username': username,
                    'domain': domain,
                    'username_length': len(username),
                    'domain_length': len(domain),
                    'is_free_provider': self._is_free_email_provider(domain)
                })
            else:
                result['error'] = "Format d'email invalide"
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erreur validation syntaxique {email}: {str(e)}")
            return {"error": f"Erreur de validation: {str(e)}", "email": email}
    
    def verify_email_existence(self, email: str) -> Dict[str, Any]:
        """
        Vérifie l'existence d'une adresse email via SMTP
        
        Args:
            email: Adresse email à vérifier
            
        Returns:
            Dict contenant les résultats de vérification
        """
        try:
            email = sanitize_input(email.lower().strip())
            validation = self.validate_email_syntax(email)
            
            if not validation.get('syntax_valid'):
                return validation
            
            domain = validation['domain']
            
            # Recherche des serveurs MX
            try:
                mx_records = dns.resolver.resolve(domain, 'MX')
                mx_servers = [str(r.exchange).rstrip('.') for r in mx_records]
                mx_servers.sort()  # Tri par priorité
            except Exception as e:
                return {
                    'email': email,
                    'domain': domain,
                    'mx_records_found': False,
                    'error': f"Impossible de trouver les serveurs MX: {str(e)}"
                }
            
            # Tentative de vérification via SMTP
            smtp_results = []
            for mx_server in mx_servers[:3]:  # Test les 3 premiers MX
                try:
                    result = self._smtp_check(mx_server, email)
                    smtp_results.append(result)
                    
                    if result.get('exists', False):
                        break  # Stop si email vérifié
                        
                except Exception as e:
                    smtp_results.append({
                        'server': mx_server,
                        'error': str(e)
                    })
            
            return {
                'email': email,
                'domain': domain,
                'mx_records_found': True,
                'mx_servers': mx_servers,
                'smtp_checks': smtp_results,
                'likely_exists': any(r.get('exists', False) for r in smtp_results),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erreur vérification existence {email}: {str(e)}")
            return {"error": f"Erreur de vérification: {str(e)}", "email": email}
    
    def _smtp_check(self, mx_server: str, email: str) -> Dict[str, Any]:
        """
        Vérification SMTP d'une adresse email
        
        Args:
            mx_server: Serveur MX à tester
            email: Adresse email à vérifier
            
        Returns:
            Résultat de la vérification SMTP
        """
        try:
            # Connexion au serveur SMTP
            server = smtplib.SMTP(mx_server, timeout=10)
            server.ehlo()
            
            # Début de la transaction
            server.mail('test@example.com')
            code, message = server.rcpt(email)
            
            server.quit()
            
            # Analyse du code de retour
            exists = code == 250  # 250 = adresse acceptée
            
            return {
                'server': mx_server,
                'response_code': code,
                'response_message': message.decode() if isinstance(message, bytes) else str(message),
                'exists': exists
            }
            
        except Exception as e:
            return {
                'server': mx_server,
                'error': str(e),
                'exists': False
            }
    
    def check_breaches(self, email: str) -> Dict[str, Any]:
        """
        Vérifie si l'email apparaît dans des fuites de données
        
        Args:
            email: Adresse email à vérifier
            
        Returns:
            Dict contenant les informations sur les fuites
        """
        try:
            email = sanitize_input(email.lower().strip())
            
            # Hachage de l'email pour l'API Have I Been Pwned
            email_hash = hashlib.sha1(email.encode('utf-8')).hexdigest().upper()
            prefix = email_hash[:5]
            
            # Appel à l'API HIBP
            url = f"https://api.pwnedpasswords.com/range/{prefix}"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                suffixes = response.text.split('\r\n')
                found_breaches = []
                
                for suffix in suffixes:
                    if suffix.startswith(email_hash[5:]):
                        count = int(suffix.split(':')[1])
                        found_breaches.append({
                            'email': email,
                            'breached': True,
                            'breach_count': count,
                            'hash_prefix': prefix,
                            'message': f"Email trouvé dans {count} fuite(s) de données"
                        })
                        break
                
                if found_breaches:
                    return found_breaches[0]
                else:
                    return {
                        'email': email,
                        'breached': False,
                        'message': "Aucune fuite de données trouvée"
                    }
            else:
                return {
                    'email': email,
                    'error': f"Erreur API HIBP: {response.status_code}",
                    'breached': False
                }
                
        except Exception as e:
            self.logger.error(f"Erreur vérification fuites {email}: {str(e)}")
            return {"error": f"Erreur de vérification: {str(e)}", "email": email}
    
    def get_social_profiles(self, email: str) -> Dict[str, Any]:
        """
        Recherche des profils sociaux associés à un email (approche basique)
        
        Args:
            email: Adresse email à investiguer
            
        Returns:
            Dict contenant les profils potentiels
        """
        try:
            email = sanitize_input(email.lower().strip())
            
            # Cette méthode utilise des techniques OSINT basiques
            # Note: Respectez toujours les conditions d'utilisation des plateformes
            
            profiles = {
                'email': email,
                'potential_profiles': [],
                'search_techniques_used': []
            }
            
            # Recherche via email directement sur certaines plateformes
            search_queries = [
                f"https://www.google.com/search?q=%22{email}%22",
                f"https://www.linkedin.com/sales/gmail/profile/viewByEmail/{email}",
                f"https://www.facebook.com/search/people/?q={email}",
            ]
            
            profiles['search_queries'] = search_queries
            profiles['note'] = "Ces liens doivent être utilisés manuellement et en respectant les CGU"
            
            return profiles
            
        except Exception as e:
            self.logger.error(f"Erreur recherche profils {email}: {str(e)}")
            return {"error": f"Erreur de recherche: {str(e)}", "email": email}
    
    def get_domain_info(self, email: str) -> Dict[str, Any]:
        """
        Récupère des informations sur le domaine de l'email
        
        Args:
            email: Adresse email à analyser
            
        Returns:
            Dict contenant les informations du domaine
        """
        try:
            email = sanitize_input(email.lower().strip())
            validation = self.validate_email_syntax(email)
            
            if not validation.get('syntax_valid'):
                return validation
            
            domain = validation['domain']
            
            # Informations DNS du domaine
            dns_info = {}
            record_types = ['A', 'MX', 'TXT', 'NS']
            
            for record_type in record_types:
                try:
                    answers = dns.resolver.resolve(domain, record_type)
                    dns_info[record_type] = [str(rdata) for rdata in answers]
                except:
                    dns_info[record_type] = []
            
            # Vérification SPF/DKIM/DMARC
            spf_records = self._check_spf_record(domain)
            dmarc_record = self._check_dmarc_record(domain)
            
            return {
                'email': email,
                'domain': domain,
                'dns_records': dns_info,
                'security_records': {
                    'spf': spf_records,
                    'dmarc': dmarc_record,
                    'security_score': self._calculate_domain_security_score(spf_records, dmarc_record)
                },
                'domain_age': self._get_domain_creation_date(domain),
                'is_business_domain': not self._is_free_email_provider(domain)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur info domaine {email}: {str(e)}")
            return {"error": f"Erreur d'analyse: {str(e)}", "email": email}
    
    def _check_spf_record(self, domain: str) -> Dict[str, Any]:
        """Vérifie les enregistrements SPF"""
        try:
            answers = dns.resolver.resolve(domain, 'TXT')
            spf_records = []
            
            for rdata in answers:
                record = str(rdata)
                if 'v=spf1' in record:
                    spf_records.append(record)
            
            return {
                'found': len(spf_records) > 0,
                'records': spf_records,
                'status': 'VALID' if spf_records else 'MISSING'
            }
        except:
            return {'found': False, 'records': [], 'status': 'MISSING'}
    
    def _check_dmarc_record(self, domain: str) -> Dict[str, Any]:
        """Vérifie les enregistrements DMARC"""
        try:
            dmarc_domain = f'_dmarc.{domain}'
            answers = dns.resolver.resolve(dmarc_domain, 'TXT')
            dmarc_records = []
            
            for rdata in answers:
                record = str(rdata)
                if 'v=DMARC1' in record:
                    dmarc_records.append(record)
            
            return {
                'found': len(dmarc_records) > 0,
                'records': dmarc_records,
                'status': 'VALID' if dmarc_records else 'MISSING'
            }
        except:
            return {'found': False, 'records': [], 'status': 'MISSING'}
    
    def _calculate_domain_security_score(self, spf: Dict, dmarc: Dict) -> int:
        """Calcule un score de sécurité pour le domaine"""
        score = 0
        if spf.get('found'):
            score += 50
        if dmarc.get('found'):
            score += 50
        return score
    
    def _get_domain_creation_date(self, domain: str) -> Optional[str]:
        """Tente de récupérer la date de création du domaine"""
        try:
            import whois
            domain_info = whois.whois(domain)
            if domain_info.creation_date:
                if isinstance(domain_info.creation_date, list):
                    return str(domain_info.creation_date[0])
                return str(domain_info.creation_date)
        except:
            pass
        return None
    
    def _is_free_email_provider(self, domain: str) -> bool:
        """Vérifie si le domaine est un fournisseur d'email gratuit"""
        free_domains = [
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'aol.com', 'protonmail.com', 'icloud.com', 'mail.com',
            'yandex.com', 'zoho.com', 'gmx.com', 'live.com'
        ]
        return domain.lower() in free_domains
    
    def comprehensive_analysis(self, email: str) -> Dict[str, Any]:
        """
        Analyse complète d'une adresse email
        
        Args:
            email: Adresse email à analyser
            
        Returns:
            Dict contenant l'analyse complète
        """
        self.logger.info(f"Lancement de l'analyse complète pour: {email}")
        
        # Exécution des différentes analyses
        syntax_validation = self.validate_email_syntax(email)
        existence_check = self.verify_email_existence(email)
        breach_check = self.check_breaches(email)
        domain_info = self.get_domain_info(email)
        social_profiles = self.get_social_profiles(email)
        
        # Compilation des résultats
        analysis_result = {
            'email': email,
            'timestamp': datetime.now().isoformat(),
            'syntax_validation': syntax_validation,
            'existence_check': existence_check,
            'breach_check': breach_check,
            'domain_analysis': domain_info,
            'social_profiles': social_profiles,
            'risk_assessment': self._assess_risk_level(
                syntax_validation, 
                existence_check, 
                breach_check, 
                domain_info
            )
        }
        
        return analysis_result
    
    def _assess_risk_level(self, syntax: Dict, existence: Dict, breach: Dict, domain: Dict) -> Dict[str, Any]:
        """Évalue le niveau de risque de l'email"""
        risk_score = 0
        warnings = []
        
        # Validation syntaxique
        if not syntax.get('syntax_valid'):
            risk_score += 30
            warnings.append("Format d'email invalide")
        
        # Existence
        if not existence.get('likely_exists', False):
            risk_score += 20
            warnings.append("Email probablement inexistant")
        
        # Fuites de données
        if breach.get('breached', False):
            risk_score += 40
            warnings.append(f"Email trouvé dans {breach.get('breach_count', 0)} fuite(s) de données")
        
        # Domaine
        domain_security = domain.get('security_records', {}).get('security_score', 0)
        if domain_security < 50:
            risk_score += 20
            warnings.append("Sécurité du domaine insuffisante")
        
        # Détermination du niveau de risque
        if risk_score >= 70:
            risk_level = "ÉLEVÉ"
        elif risk_score >= 40:
            risk_level = "MOYEN"
        else:
            risk_level = "FAIBLE"
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'warnings': warnings,
            'recommendations': self._generate_recommendations(warnings)
        }
    
    def _generate_recommendations(self, warnings: List[str]) -> List[str]:
        """Génère des recommandations basées sur les warnings"""
        recommendations = []
        
        if "Format d'email invalide" in warnings:
            recommendations.append("Vérifier le format de l'email")
        
        if "Email probablement inexistant" in warnings:
            recommendations.append("Confirmer l'existence de l'email")
        
        if "fuite(s) de données" in ' '.join(warnings):
            recommendations.append("Changer le mot de passe et activer la 2FA")
        
        if "Sécurité du domaine insuffisante" in warnings:
            recommendations.append("Vérifier la configuration SPF/DKIM/DMARC")
        
        return recommendations

def main():
    """Fonction principale pour test du module"""
    from core.config_manager import ConfigManager
    
    config = ConfigManager()
    email_intel = EmailIntel(config)
    
    print("🔍 Email Intelligence")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Validation syntaxique")
        print("2. Vérification existence")
        print("3. Vérification fuites de données")
        print("4. Analyse du domaine")
        print("5. Recherche profils sociaux")
        print("6. Analyse complète")
        print("7. Quitter")
        
        choice = input("\nChoisissez une option (1-7): ").strip()
        
        if choice == '1':
            email = input("Entrez l'email: ").strip()
            result = email_intel.validate_email_syntax(email)
            print(f"\nValidation syntaxique:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        elif choice == '2':
            email = input("Entrez l'email: ").strip()
            result = email_intel.verify_email_existence(email)
            print(f"\nVérification existence:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        elif choice == '3':
            email = input("Entrez l'email: ").strip()
            result = email_intel.check_breaches(email)
            print(f"\nVérification fuites:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        elif choice == '4':
            email = input("Entrez l'email: ").strip()
            result = email_intel.get_domain_info(email)
            print(f"\nAnalyse domaine:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        elif choice == '5':
            email = input("Entrez l'email: ").strip()
            result = email_intel.get_social_profiles(email)
            print(f"\nRecherche profils:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        elif choice == '6':
            email = input("Entrez l'email: ").strip()
            result = email_intel.comprehensive_analysis(email)
            print(f"\nAnalyse complète:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        elif choice == '7':
            break
        else:
            print("Option invalide")

if __name__ == "__main__":
    main()
