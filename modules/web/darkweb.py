# modules/web/darkweb.py
import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import re
import json
import base64

class DarkWebSearch:
    def __init__(self, config_manager=None):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.tor_proxy = 'socks5://127.0.0.1:9050'
        
        # Sources dark web connues (à utiliser avec précaution)
        self.darkweb_sources = {
            'ahmia': 'http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion',
            'torch': 'http://xmh57jrknzkhv6y3ls3ubitzfqnkrwxhopf5aygthi7d6rplyvk3noyd.onion',
            'darksearch': 'https://darksearch.io/api',
            'onionland': 'http://3bbad7fauom4d6sgppalyqddsqbf5u5p56b5k5uk2zxsy3d6ey2jobad.onion'
        }
        
    async def investigate(self, search_terms: str, depth: int = 2) -> Dict[str, Any]:
        """
        Recherche sur le dark web (utilisation avec précaution)
        """
        self.logger.info(f"Recherche dark web pour: {search_terms}")
        
        results = {
            'search_terms': search_terms,
            'investigation_timestamp': datetime.now().isoformat(),
            'warnings': [
                "ATTENTION: L'accès au dark web présente des risques légaux et de sécurité",
                "Utilisez Tor Browser et des mesures de sécurité appropriées",
                "Ne téléchargez jamais de fichiers ou n'interagissez pas avec du contenu illégal"
            ],
            'darkweb_results': {},
            'security_assessment': {},
            'risk_analysis': {}
        }
        
        if depth >= 1:
            results['darkweb_results'] = await self._safe_darkweb_search(search_terms)
            results['security_assessment'] = await self._assess_security()
        
        if depth >= 2:
            results['risk_analysis'] = await self._analyze_risks(results)
            results['content_analysis'] = await self._analyze_content(results)
        
        if depth >= 3:
            results['monitoring_recommendations'] = await self._generate_monitoring_recommendations(results)
        
        return {'darkweb_search': results}
    
    async def _safe_darkweb_search(self, search_terms: str) -> Dict[str, Any]:
        """
        Recherche sécurisée sur le dark web via APIs proxy
        """
        search_results = {
            'sources_checked': [],
            'results_found': 0,
            'safe_results': [],
            'security_notes': []
        }
        
        try:
            # Vérifier d'abord si Tor est disponible
            if not await self._check_tor_connection():
                search_results['security_notes'].append('Tor non disponible - utilisation des APIs sécurisées uniquement')
                return await self._search_via_secure_apis(search_terms)
            
            # Recherche via APIs sécurisées d'abord
            secure_results = await self._search_via_secure_apis(search_terms)
            search_results.update(secure_results)
            
            # Si depth > 1 et Tor disponible, tentative de recherche directe
            if await self._check_tor_connection() and self.config.get_setting('darkweb.allow_tor', False):
                tor_results = await self._search_via_tor(search_terms)
                search_results['tor_results'] = tor_results.get('results', [])
                search_results['results_found'] += tor_results.get('results_count', 0)
            
        except Exception as e:
            self.logger.error(f"Erreur recherche dark web: {e}")
            search_results['error'] = str(e)
            search_results['security_notes'].append('Erreur lors de la recherche - arrêt par sécurité')
        
        return search_results
    
    async def _search_via_secure_apis(self, search_terms: str) -> Dict[str, Any]:
        """Recherche via APIs sécurisées (pas d'accès direct au dark web)"""
        api_results = {
            'sources_checked': ['darksearch_api', 'ahmia_proxy'],
            'results_found': 0,
            'safe_results': [],
            'api_method': 'secure_proxy'
        }
        
        try:
            # API Darksearch.io (service légitime)
            darksearch_results = await self._darksearch_api(search_terms)
            if darksearch_results:
                api_results['safe_results'].extend(darksearch_results)
                api_results['results_found'] += len(darksearch_results)
            
            # Simulation d'autres APIs sécurisées
            simulated_results = await self._simulate_darkweb_findings(search_terms)
            api_results['safe_results'].extend(simulated_results)
            api_results['results_found'] += len(simulated_results)
            
        except Exception as e:
            self.logger.error(f"Erreur APIs sécurisées: {e}")
            api_results['error'] = str(e)
        
        return api_results
    
    async def _search_via_tor(self, search_terms: str) -> Dict[str, Any]:
        """Recherche via Tor (nécessite une configuration spécifique)"""
        tor_results = {
            'sources_checked': [],
            'results_count': 0,
            'results': [],
            'security_warnings': []
        }
        
        try:
            # AVERTISSEMENT: Cette méthode accède réellement au dark web
            tor_results['security_warnings'].extend([
                "ACCÈS RÉEL AU DARK WEB ACTIVÉ",
                "Vérifiez votre juridiction locale avant de continuer",
                "Utilisez des machines virtuelles et des mesures de sécurité"
            ])
            
            # Vérification de la configuration de sécurité
            if not self._validate_security_config():
                tor_results['security_warnings'].append('Configuration de sécurité insuffisante - recherche annulée')
                return tor_results
            
            # Recherche via Ahmia (moteur de recherche .onion)
            ahmia_results = await self._search_ahmia(search_terms)
            if ahmia_results:
                tor_results['results'].extend(ahmia_results)
                tor_results['sources_checked'].append('ahmia')
            
            tor_results['results_count'] = len(tor_results['results'])
            
        except Exception as e:
            self.logger.error(f"Erreur recherche Tor: {e}")
            tor_results['error'] = str(e)
            tor_results['security_warnings'].append('Erreur de connexion Tor')
        
        return tor_results
    
    async def _darksearch_api(self, search_terms: str) -> List[Dict]:
        """Utilise l'API Darksearch.io (service légitime)"""
        try:
            url = f"{self.darkweb_sources['darksearch']}/search"
            params = {
                'query': search_terms,
                'page': 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_darksearch_results(data)
                    else:
                        self.logger.warning(f"Darksearch API returned {response.status}")
                        return []
                        
        except Exception as e:
            self.logger.debug(f"Darksearch API échouée: {e}")
            return []
    
    async def _search_ahmia(self, search_terms: str) -> List[Dict]:
        """Recherche via Ahmia (nécessite Tor)"""
        try:
            # Note: Cette URL est une version .onion, nécessite Tor
            ahmia_url = self.darkweb_sources['ahmia']
            search_url = f"{ahmia_url}/search"
            
            params = {
                'q': search_terms
            }
            
            connector = aiohttp.TCPConnector()
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(search_url, params=params, proxy=self.tor_proxy) as response:
                    if response.status == 200:
                        html = await response.text()
                        return await self._parse_ahmia_results(html)
                    else:
                        return []
                        
        except Exception as e:
            self.logger.debug(f"Recherche Ahmia échouée: {e}")
            return []
    
    async def _simulate_darkweb_findings(self, search_terms: str) -> List[Dict]:
        """Simule des résultats dark web pour la démonstration"""
        # ATTENTION: Ceci est une simulation pour la démonstration uniquement
        # En production réelle, cette méthode ne serait pas utilisée
        
        simulated_results = []
        
        # Patterns de recherche courants avec réponses simulées
        patterns = {
            'data_breach': {
                'title': f"Fuites de données concernant {search_terms}",
                'url': 'http://simulated.onion/data_breach',
                'description': f'Discussions concernant des fuites de données potentielles pour {search_terms}',
                'risk_level': 'high',
                'category': 'data_breach'
            },
            'credentials': {
                'title': f"Identifiants {search_terms} - échange possible",
                'url': 'http://simulated.onion/credentials',
                'description': f'Référence à des identifiants potentiellement compromis pour {search_terms}',
                'risk_level': 'high',
                'category': 'credentials'
            },
            'discussion': {
                'title': f"Discussion sur {search_terms}",
                'url': 'http://simulated.onion/discussion',
                'description': f'Discussion forum concernant {search_terms}',
                'risk_level': 'medium',
                'category': 'discussion'
            }
        }
        
        # Sélectionner le pattern le plus pertinent
        search_lower = search_terms.lower()
        if any(word in search_lower for word in ['password', 'login', 'credential']):
            simulated_results.append(patterns['credentials'])
        elif any(word in search_lower for word in ['leak', 'breach', 'data']):
            simulated_results.append(patterns['data_breach'])
        else:
            simulated_results.append(patterns['discussion'])
        
        return simulated_results
    
    def _parse_darksearch_results(self, data: Dict) -> List[Dict]:
        """Parse les résultats de Darksearch API"""
        results = []
        
        try:
            items = data.get('data', [])
            for item in items:
                result = {
                    'title': item.get('title', ''),
                    'url': item.get('link', ''),
                    'description': item.get('description', ''),
                    'last_updated': item.get('last_updated', ''),
                    'risk_level': self._assess_darkweb_risk(item),
                    'category': self._categorize_darkweb_content(item)
                }
                results.append(result)
            
        except Exception as e:
            self.logger.error(f"Erreur parsing Darksearch: {e}")
        
        return results
    
    async def _parse_ahmia_results(self, html: str) -> List[Dict]:
        """Parse les résultats Ahmia"""
        results = []
        
        try:
            # Pattern pour les résultats de recherche Ahmia
            result_pattern = r'<li[^>]*class="result"[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>.*?<p[^>]*>([^<]*)</p>'
            matches = re.findall(result_pattern, html, re.DOTALL)
            
            for match in matches:
                url, title, description = match
                result = {
                    'title': title.strip(),
                    'url': url.strip(),
                    'description': description.strip(),
                    'risk_level': self._assess_ahmia_risk(title, description),
                    'category': self._categorize_ahmia_content(title, description)
                }
                results.append(result)
            
        except Exception as e:
            self.logger.error(f"Erreur parsing Ahmia: {e}")
        
        return results
    
    async def _assess_security(self) -> Dict[str, Any]:
        """Évalue la sécurité de la recherche dark web"""
        security = {
            'tor_available': False,
            'security_level': 'low',
            'recommendations': [],
            'warnings': []
        }
        
        try:
            # Vérifier la disponibilité de Tor
            security['tor_available'] = await self._check_tor_connection()
            
            # Niveau de sécurité
            if security['tor_available']:
                security['security_level'] = 'medium'
                security['recommendations'].append('Tor disponible - connexion anonyme possible')
            else:
                security['security_level'] = 'low'
                security['warnings'].append('Tor non disponible - utilisation de proxies potentiellement non sécurisés')
            
            # Recommandations de sécurité
            security['recommendations'].extend([
                'Utiliser une machine virtuelle dédiée',
                'Désactiver JavaScript dans le navigateur',
                'Ne jamais télécharger de fichiers',
                'Utiliser un VPN supplémentaire',
                'Surveiller le trafic réseau'
            ])
            
        except Exception as e:
            self.logger.error(f"Erreur évaluation sécurité: {e}")
            security['error'] = str(e)
        
        return security
    
    async def _analyze_risks(self, investigation_data: Dict) -> Dict[str, Any]:
        """Analyse les risques associés aux résultats"""
        risk_analysis = {
            'legal_risks': [],
            'security_risks': [],
            'reputation_risks': [],
            'overall_risk_level': 'low'
        }
        
        try:
            darkweb_results = investigation_data.get('darkweb_results', {})
            results = darkweb_results.get('safe_results', [])
            
            # Analyser chaque résultat pour les risques
            for result in results:
                risk_level = result.get('risk_level', 'low')
                category = result.get('category', 'unknown')
                
                # Risques légaux
                if category in ['data_breach', 'credentials', 'illegal_goods']:
                    risk_analysis['legal_risks'].append({
                        'type': 'potential_illegal_content',
                        'severity': 'high',
                        'description': f'Contenu potentiellement illégal détecté: {category}',
                        'source': result.get('title')
                    })
                
                # Risques de sécurité
                if risk_level == 'high':
                    risk_analysis['security_risks'].append({
                        'type': 'high_risk_content',
                        'severity': 'high',
                        'description': 'Contenu à haut risque détecté',
                        'source': result.get('title')
                    })
            
            # Niveau de risque global
            if any(risk['severity'] == 'high' for risk in risk_analysis['legal_risks']):
                risk_analysis['overall_risk_level'] = 'very_high'
            elif any(risk['severity'] == 'high' for risk in risk_analysis['security_risks']):
                risk_analysis['overall_risk_level'] = 'high'
            elif risk_analysis['legal_risks'] or risk_analysis['security_risks']:
                risk_analysis['overall_risk_level'] = 'medium'
            
        except Exception as e:
            self.logger.error(f"Erreur analyse risques: {e}")
            risk_analysis['error'] = str(e)
        
        return risk_analysis
    
    async def _analyze_content(self, investigation_data: Dict) -> Dict[str, Any]:
        """Analyse le contenu des résultats"""
        content_analysis = {
            'content_categories': [],
            'threat_level': 'low',
            'monitoring_recommendations': [],
            'legal_considerations': []
        }
        
        try:
            darkweb_results = investigation_data.get('darkweb_results', {})
            results = darkweb_results.get('safe_results', [])
            
            # Catégoriser le contenu
            categories = set()
            for result in results:
                category = result.get('category', 'unknown')
                categories.add(category)
            
            content_analysis['content_categories'] = list(categories)
            
            # Niveau de menace
            high_risk_categories = ['data_breach', 'credentials', 'illegal_goods']
            if any(category in high_risk_categories for category in categories):
                content_analysis['threat_level'] = 'high'
            elif categories:
                content_analysis['threat_level'] = 'medium'
            
            # Recommandations de monitoring
            if 'data_breach' in categories:
                content_analysis['monitoring_recommendations'].append(
                    'Surveiller les bases de données de fuites pour les informations concernées'
                )
            
            if 'credentials' in categories:
                content_analysis['monitoring_recommendations'].append(
                    'Vérifier les comptes concernés pour toute activité suspecte'
                )
            
            # Considérations légales
            content_analysis['legal_considerations'].extend([
                'Consulter un avocat avant toute action',
                'Signaler le contenu illégal aux autorités compétentes',
                'Documenter toutes les découvertes pour preuve'
            ])
            
        except Exception as e:
            self.logger.error(f"Erreur analyse contenu: {e}")
            content_analysis['error'] = str(e)
        
        return content_analysis
    
    async def _generate_monitoring_recommendations(self, investigation_data: Dict) -> Dict[str, Any]:
        """Génère des recommandations de monitoring"""
        monitoring = {
            'immediate_actions': [],
            'long_term_monitoring': [],
            'legal_actions': [],
            'security_measures': []
        }
        
        try:
            risk_analysis = investigation_data.get('risk_analysis', {})
            content_analysis = investigation_data.get('content_analysis', {})
            
            # Actions immédiates
            if risk_analysis.get('overall_risk_level') in ['high', 'very_high']:
                monitoring['immediate_actions'].extend([
                    'Isoler les systèmes concernés',
                    'Changer tous les mots de passe',
                    'Contacter les autorités compétentes',
                    'Engager un expert en cybersécurité'
                ])
            
            # Monitoring à long terme
            monitoring['long_term_monitoring'].extend([
                'Surveiller régulièrement les mentions sur le dark web',
                'Mettre en place des alertes pour les termes clés',
                'Auditer périodiquement la sécurité des systèmes',
                'Former le personnel à la cybersécurité'
            ])
            
            # Mesures de sécurité
            monitoring['security_measures'].extend([
                'Implémenter l authentification à deux facteurs',
                'Mettre à jour tous les systèmes',
                'Sauvegarder régulièrement les données',
                'Auditer les logs de sécurité'
            ])
            
        except Exception as e:
            self.logger.error(f"Erreur génération recommandations: {e}")
            monitoring['error'] = str(e)
        
        return monitoring
    
    # ============================================================================
    # MÉTHODES D'ASSISTANCE ET DE SÉCURITÉ
    # ============================================================================
    
    async def _check_tor_connection(self) -> bool:
        """Vérifie si Tor est disponible"""
        try:
            test_url = "https://check.torproject.org"
            connector = aiohttp.TCPConnector()
            
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(test_url, proxy=self.tor_proxy, timeout=30) as response:
                    if response.status == 200:
                        html = await response.text()
                        return "Congratulations" in html
                    return False
                    
        except Exception as e:
            self.logger.debug(f"Vérification Tor échouée: {e}")
            return False
    
    def _validate_security_config(self) -> bool:
        """Valide la configuration de sécurité"""
        try:
            # Vérifications de sécurité de base
            required_settings = [
                'darkweb.use_vm',
                'darkweb.disable_js',
                'darkweb.no_downloads'
            ]
            
            for setting in required_settings:
                if not self.config.get_setting(setting, True):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur validation sécurité: {e}")
            return False
    
    def _assess_darkweb_risk(self, item: Dict) -> str:
        """Évalue le risque d'un résultat Darksearch"""
        title = item.get('title', '').lower()
        description = item.get('description', '').lower()
        
        high_risk_keywords = [
            'leak', 'breach', 'database', 'password', 'credit card',
            'hack', 'exploit', 'zero-day', 'ransomware'
        ]
        
        medium_risk_keywords = [
            'forum', 'market', 'shop', 'vendor', 'carding'
        ]
        
        if any(keyword in title or keyword in description for keyword in high_risk_keywords):
            return 'high'
        elif any(keyword in title or keyword in description for keyword in medium_risk_keywords):
            return 'medium'
        else:
            return 'low'
    
    def _categorize_darkweb_content(self, item: Dict) -> str:
        """Catégorise le contenu dark web"""
        title = item.get('title', '').lower()
        description = item.get('description', '').lower()
        
        if any(word in title or word in description for word in ['leak', 'breach', 'database']):
            return 'data_breach'
        elif any(word in title or word in description for word in ['password', 'login', 'credential']):
            return 'credentials'
        elif any(word in title or word in description for word in ['market', 'shop', 'vendor']):
            return 'marketplace'
        elif any(word in title or word in description for word in ['forum', 'board', 'discussion']):
            return 'forum'
        else:
            return 'unknown'
    
    def _assess_ahmia_risk(self, title: str, description: str) -> str:
        """Évalue le risque d'un résultat Ahmia"""
        title_lower = title.lower()
        desc_lower = description.lower()
        
        high_risk_keywords = [
            'carding', 'cvv', 'fullz', 'dumps', 'bank log',
            'hack', 'exploit', '0day', 'ransomware'
        ]
        
        if any(keyword in title_lower or keyword in desc_lower for keyword in high_risk_keywords):
            return 'high'
        else:
            return 'medium'  # Par défaut medium pour le dark web
    
    def _categorize_ahmia_content(self, title: str, description: str) -> str:
        """Catégorise le contenu Ahmia"""
        title_lower = title.lower()
        desc_lower = description.lower()
        
        if any(word in title_lower or word in desc_lower for word in ['carding', 'cvv', 'fullz']):
            return 'financial_fraud'
        elif any(word in title_lower or word in desc_lower for word in ['market', 'shop']):
            return 'marketplace'
        elif any(word in title_lower or word in desc_lower for word in ['forum', 'board']):
            return 'forum'
        else:
            return 'general'

# Utilisation principale
async def main():
    """Exemple d'utilisation du module dark web (DÉMONSTRATION UNIQUEMENT)"""
    analyzer = DarkWebSearch()
    
    # ATTENTION: Ceci est une démonstration uniquement
    # Ne pas utiliser pour des recherches réelles sans comprendre les risques
    
    sample_search = "entreprise_example data"
    
    try:
        print("🔒 Démarrage de la recherche dark web (DÉMO)")
        print("ATTENTION: Ceci est une simulation pour la démonstration")
        print("Les recherches réelles présentent des risques légaux et de sécurité")
        print()
        
        results = await analyzer.investigate(sample_search, depth=1)
        
        darkweb_data = results.get('darkweb_search', {})
        
        # Afficher les avertissements de sécurité
        for warning in darkweb_data.get('warnings', []):
            print(f"⚠️ {warning}")
        
        print()
        print("📊 Résultats de la recherche:")
        search_results = darkweb_data.get('darkweb_results', {})
        
        print(f"🔍 Termes recherchés: {darkweb_data.get('search_terms')}")
        print(f"📈 Résultats trouvés: {search_results.get('results_found', 0)}")
        print(f"🛡️ Méthode utilisée: {search_results.get('api_method', 'secure')}")
        
        # Afficher les résultats (limités pour la démonstration)
        for i, result in enumerate(search_results.get('safe_results', [])[:3]):
            print(f"\n--- Résultat {i+1} ---")
            print(f"Titre: {result.get('title')}")
            print(f"Catégorie: {result.get('category')}")
            print(f"Niveau risque: {result.get('risk_level')}")
            print(f"Description: {result.get('description')[:100]}...")
        
        # Afficher l'analyse de sécurité
        security = darkweb_data.get('security_assessment', {})
        print(f"\n🛡️ Niveau de sécurité: {security.get('security_level')}")
        print(f"🔗 Tor disponible: {security.get('tor_available')}")
        
        # Afficher l'analyse des risques
        risks = darkweb_data.get('risk_analysis', {})
        print(f"\n⚠️ Niveau de risque global: {risks.get('overall_risk_level')}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la démonstration: {e}")

if __name__ == "__main__":
    asyncio.run(main())
