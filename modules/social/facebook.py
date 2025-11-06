# modules/social/facebook.py
import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import re
import json

class FacebookIntel:
    def __init__(self, config_manager=None):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.api_endpoints = {
            'graph_api': 'https://graph.facebook.com/v18.0',
            'facebook': 'https://www.facebook.com',
            'mbasic': 'https://mbasic.facebook.com'
        }
        
    async def investigate(self, username: str, depth: int = 2) -> Dict[str, Any]:
        """
        Investigation d'un profil Facebook
        """
        self.logger.info(f"Investigation Facebook pour: {username}")
        
        results = {
            'username': username,
            'profile_url': f"https://facebook.com/{username}",
            'investigation_timestamp': datetime.now().isoformat(),
            'profile_info': {},
            'public_posts': {},
            'friends_analysis': {},
            'photos_analysis': {},
            'activity_analysis': {},
            'privacy_assessment': {}
        }
        
        if depth >= 1:
            results['profile_info'] = await self._get_profile_info(username)
            results['privacy_assessment'] = await self._assess_privacy(username, results)
        
        if depth >= 2:
            results['public_posts'] = await self._get_public_posts(username)
            results['photos_analysis'] = await self._analyze_photos(username)
        
        if depth >= 3:
            results['friends_analysis'] = await self._analyze_friends(username)
            results['activity_analysis'] = await self._analyze_activity(username, results)
            results['risk_assessment'] = await self._assess_risks(results)
        
        return {'facebook': results}
    
    async def _get_profile_info(self, username: str) -> Dict[str, Any]:
        """Récupère les informations basiques du profil"""
        profile_info = {
            'username': username,
            'profile_exists': False,
            'basic_info': {},
            'contact_info': {},
            'education_work': {},
            'places': {},
            'family_relationships': {}
        }
        
        try:
            # Essayer différentes méthodes pour récupérer les infos
            methods = [
                self._scrape_basic_info,
                self._scrape_mbasic_info,
                self._try_graph_api
            ]
            
            for method in methods:
                try:
                    info = await method(username)
                    if info and info.get('profile_exists', False):
                        profile_info.update(info)
                        profile_info['profile_exists'] = True
                        break
                except Exception as e:
                    self.logger.debug(f"Échec méthode {method.__name__}: {e}")
                    continue
            
            if not profile_info['profile_exists']:
                profile_info['error'] = "Profil non trouvé ou inaccessible"
            
        except Exception as e:
            self.logger.error(f"Erreur info profil {username}: {e}")
            profile_info['error'] = str(e)
        
        return profile_info
    
    async def _scrape_basic_info(self, username: str) -> Dict[str, Any]:
        """Scraping des informations basiques"""
        try:
            url = f"{self.api_endpoints['facebook']}/{username}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.8,en-US;q=0.5,en;q=0.3'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        return {
                            'profile_exists': True,
                            'basic_info': await self._parse_basic_info(html),
                            'scraping_method': 'desktop'
                        }
                    elif response.status == 404:
                        return {'profile_exists': False}
                    else:
                        return {'profile_exists': False, 'error': f"HTTP {response.status}"}
                        
        except Exception as e:
            self.logger.debug(f"Scraping basic échoué: {e}")
            return {'profile_exists': False}
    
    async def _scrape_mbasic_info(self, username: str) -> Dict[str, Any]:
        """Scraping via la version mobile basique"""
        try:
            url = f"{self.api_endpoints['mbasic']}/{username}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        return {
                            'profile_exists': True,
                            'basic_info': await self._parse_mbasic_info(html),
                            'scraping_method': 'mbasic'
                        }
                    else:
                        return {'profile_exists': False}
                        
        except Exception as e:
            self.logger.debug(f"Scraping mbasic échoué: {e}")
            return {'profile_exists': False}
    
    async def _try_graph_api(self, username: str) -> Dict[str, Any]:
        """Essaie l'API Graph (nécessite token)"""
        try:
            access_token = self.config.get_api_key('facebook', 'access_token') if self.config else None
            if not access_token:
                return {'profile_exists': False, 'error': 'No access token'}
            
            url = f"{self.api_endpoints['graph_api']}/{username}"
            params = {
                'fields': 'id,name,first_name,last_name,middle_name,email,link,gender,locale,verified',
                'access_token': access_token
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'profile_exists': True,
                            'basic_info': data,
                            'api_method': 'graph_api'
                        }
                    else:
                        return {'profile_exists': False}
                        
        except Exception as e:
            self.logger.debug(f"API Graph échouée: {e}")
            return {'profile_exists': False}
    
    async def _parse_basic_info(self, html: str) -> Dict[str, Any]:
        """Parse les informations basiques depuis le HTML"""
        info = {}
        
        try:
            # Nom complet
            name_match = re.search(r'<title[^>]*>([^<]+)</title>', html)
            if name_match:
                info['name'] = name_match.group(1).replace(' | Facebook', '').strip()
            
            # ID utilisateur
            id_match = re.search(r'"userID":"(\d+)"', html)
            if id_match:
                info['user_id'] = id_match.group(1)
            
            # Vérification
            verified_match = re.search(r'Verified</div>', html)
            if verified_match:
                info['verified'] = True
            
            # Bio/description
            bio_match = re.search(r'<div[^>]*class="[^"]*bio[^"]*"[^>]*>([^<]+)</div>', html, re.IGNORECASE)
            if bio_match:
                info['bio'] = bio_match.group(1).strip()
            
            # Localisation
            location_match = re.search(r'Lives in[^>]*>([^<]+)</', html, re.IGNORECASE)
            if location_match:
                info['location'] = location_match.group(1).strip()
            
            # Travail
            work_match = re.search(r'Works? at[^>]*>([^<]+)</', html, re.IGNORECASE)
            if work_match:
                info['work'] = work_match.group(1).strip()
            
            # Éducation
            edu_match = re.search(r'Studied at[^>]*>([^<]+)</', html, re.IGNORECASE)
            if edu_match:
                info['education'] = edu_match.group(1).strip()
                
        except Exception as e:
            self.logger.error(f"Erreur parsing info: {e}")
        
        return info
    
    async def _parse_mbasic_info(self, html: str) -> Dict[str, Any]:
        """Parse les informations depuis la version mbasic"""
        info = {}
        
        try:
            # Nom
            name_match = re.search(r'<title[^>]*>([^<]+)</title>', html)
            if name_match:
                info['name'] = name_match.group(1).replace(' | Facebook', '').strip()
            
            # Informations de profil
            info_sections = re.findall(r'<div[^>]*>([^<]+)</div>', html)
            for section in info_sections:
                if 'Lives in' in section:
                    info['location'] = section.replace('Lives in', '').strip()
                elif 'Works at' in section:
                    info['work'] = section.replace('Works at', '').strip()
                elif 'From' in section:
                    info['hometown'] = section.replace('From', '').strip()
            
        except Exception as e:
            self.logger.error(f"Erreur parsing mbasic: {e}")
        
        return info
    
    async def _get_public_posts(self, username: str) -> Dict[str, Any]:
        """Récupère les posts publics"""
        posts_analysis = {
            'posts_count': 0,
            'recent_posts': [],
            'engagement_metrics': {},
            'content_analysis': {},
            'posting_patterns': {}
        }
        
        try:
            # Scraping des posts publics
            url = f"{self.api_endpoints['mbasic']}/{username}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Extraire les posts
                        posts = await self._extract_posts(html)
                        posts_analysis['posts_count'] = len(posts)
                        posts_analysis['recent_posts'] = posts[:10]  # Limiter aux 10 derniers
                        
                        # Analyser l'engagement
                        posts_analysis['engagement_metrics'] = await self._analyze_engagement(posts)
                        
                        # Analyser le contenu
                        posts_analysis['content_analysis'] = await self._analyze_content(posts)
                        
                        # Patterns de publication
                        posts_analysis['posting_patterns'] = await self._analyze_posting_patterns(posts)
            
        except Exception as e:
            self.logger.error(f"Erreur posts publics {username}: {e}")
            posts_analysis['error'] = str(e)
        
        return posts_analysis
    
    async def _extract_posts(self, html: str) -> List[Dict]:
        """Extrait les posts depuis le HTML"""
        posts = []
        
        try:
            # Pattern pour les posts mbasic
            post_pattern = r'<div[^>]*class="[^"]*story[^"]*"[^>]*>.*?</div>\s*</div>'
            post_matches = re.findall(post_pattern, html, re.DOTALL)
            
            for post_html in post_matches[:10]:  # Limiter
                post = await self._parse_post(post_html)
                if post:
                    posts.append(post)
            
        except Exception as e:
            self.logger.error(f"Erreur extraction posts: {e}")
        
        return posts
    
    async def _parse_post(self, post_html: str) -> Optional[Dict]:
        """Parse un post individuel"""
        try:
            post = {
                'timestamp': None,
                'content': '',
                'reactions': 0,
                'comments': 0,
                'shares': 0
            }
            
            # Contenu
            content_match = re.search(r'<p[^>]*>(.*?)</p>', post_html, re.DOTALL)
            if content_match:
                post['content'] = re.sub(r'<[^>]+>', '', content_match.group(1)).strip()
            
            # Date
            date_match = re.search(r'(\d+\s+(?:min|hour|day|week|month|year)s?\s+ago)', post_html)
            if date_match:
                post['timestamp'] = date_match.group(1)
            
            # Réactions
            reactions_match = re.search(r'(\d+)\s*Like', post_html)
            if reactions_match:
                post['reactions'] = int(reactions_match.group(1))
            
            # Commentaires
            comments_match = re.search(r'(\d+)\s*Comment', post_html)
            if comments_match:
                post['comments'] = int(comments_match.group(1))
            
            # Partages
            shares_match = re.search(r'(\d+)\s*Share', post_html)
            if shares_match:
                post['shares'] = int(shares_match.group(1))
            
            return post if post['content'] else None
            
        except Exception as e:
            self.logger.debug(f"Erreur parsing post: {e}")
            return None
    
    async def _analyze_photos(self, username: str) -> Dict[str, Any]:
        """Analyse les photos de profil et de couverture"""
        photos_analysis = {
            'profile_pictures': [],
            'cover_photos': [],
            'photo_count': 0,
            'last_updated': None,
            'photo_analysis': {}
        }
        
        try:
            # URLs communes pour les photos
            profile_photo_urls = [
                f"{self.api_endpoints['facebook']}/{username}/picture?type=large",
                f"{self.api_endpoints['graph_api']}/{username}/picture?type=large"
            ]
            
            for url in profile_photo_urls:
                async with aiohttp.ClientSession() as session:
                    async with session.head(url) as response:
                        if response.status == 200:
                            photos_analysis['profile_pictures'].append({
                                'url': url,
                                'accessible': True,
                                'type': 'profile_picture'
                            })
                            break
            
            # Analyse EXIF basique (serait fait par le module image_analysis)
            if photos_analysis['profile_pictures']:
                photos_analysis['photo_analysis'] = {
                    'has_profile_picture': True,
                    'analysis_available': 'via_image_module'
                }
            
        except Exception as e:
            self.logger.error(f"Erreur analyse photos {username}: {e}")
            photos_analysis['error'] = str(e)
        
        return photos_analysis
    
    async def _analyze_friends(self, username: str) -> Dict[str, Any]:
        """Analyse les amis/mutual friends"""
        friends_analysis = {
            'friends_count': 'unknown',
            'mutual_friends': [],
            'network_analysis': {},
            'privacy_level': 'high'
        }
        
        try:
            # Scraping des amis communs (si accessible)
            url = f"{self.api_endpoints['mbasic']}/{username}/friends"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Vérifier si la liste est accessible
                        if 'friends' in html.lower():
                            friends_analysis['privacy_level'] = 'low'
                            friends_analysis['friends_count'] = await self._estimate_friends_count(html)
                        else:
                            friends_analysis['privacy_level'] = 'high'
                    
                    else:
                        friends_analysis['privacy_level'] = 'high'
            
        except Exception as e:
            self.logger.error(f"Erreur analyse amis {username}: {e}")
            friends_analysis['error'] = str(e)
        
        return friends_analysis
    
    async def _analyze_activity(self, username: str, investigation_data: Dict) -> Dict[str, Any]:
        """Analyse l'activité générale"""
        activity_analysis = {
            'activity_level': 'unknown',
            'recent_activity': {},
            'interaction_patterns': [],
            'content_types': []
        }
        
        try:
            posts_data = investigation_data.get('public_posts', {})
            posts = posts_data.get('recent_posts', [])
            
            # Niveau d'activité basé sur les posts
            if len(posts) >= 10:
                activity_analysis['activity_level'] = 'high'
            elif len(posts) >= 3:
                activity_analysis['activity_level'] = 'medium'
            elif len(posts) >= 1:
                activity_analysis['activity_level'] = 'low'
            else:
                activity_analysis['activity_level'] = 'inactive'
            
            # Types de contenu
            content_types = set()
            for post in posts:
                content = post.get('content', '').lower()
                if any(word in content for word in ['photo', 'image', 'picture']):
                    content_types.add('photos')
                if any(word in content for word in ['video', 'watch']):
                    content_types.add('videos')
                if any(word in content for word in ['http', 'www.', '.com']):
                    content_types.add('links')
                if len(content) > 100:
                    content_types.add('long_text')
                else:
                    content_types.add('short_text')
            
            activity_analysis['content_types'] = list(content_types)
            
        except Exception as e:
            self.logger.error(f"Erreur analyse activité {username}: {e}")
            activity_analysis['error'] = str(e)
        
        return activity_analysis
    
    async def _assess_privacy(self, username: str, investigation_data: Dict) -> Dict[str, Any]:
        """Évalue les paramètres de confidentialité"""
        privacy_assessment = {
            'overall_privacy': 'unknown',
            'visible_information': [],
            'privacy_risks': [],
            'recommendations': []
        }
        
        try:
            profile_info = investigation_data.get('profile_info', {})
            basic_info = profile_info.get('basic_info', {})
            
            # Informations visibles
            visible_info = []
            if basic_info.get('name'):
                visible_info.append('name')
            if basic_info.get('location'):
                visible_info.append('location')
            if basic_info.get('work'):
                visible_info.append('work')
            if basic_info.get('education'):
                visible_info.append('education')
            
            privacy_assessment['visible_information'] = visible_info
            
            # Évaluation globale
            if len(visible_info) >= 4:
                privacy_assessment['overall_privacy'] = 'low'
                privacy_assessment['privacy_risks'].append('Trop d\'informations personnelles visibles')
            elif len(visible_info) >= 2:
                privacy_assessment['overall_privacy'] = 'medium'
            else:
                privacy_assessment['overall_privacy'] = 'high'
            
            # Recommandations
            if privacy_assessment['overall_privacy'] in ['low', 'medium']:
                privacy_assessment['recommendations'].append('Réviser les paramètres de confidentialité')
                privacy_assessment['recommendations'].append('Limiter les informations professionnelles visibles')
                privacy_assessment['recommendations'].append('Éviter la géolocalisation dans les posts')
            
        except Exception as e:
            self.logger.error(f"Erreur évaluation confidentialité {username}: {e}")
            privacy_assessment['error'] = str(e)
        
        return privacy_assessment
    
    async def _assess_risks(self, investigation_data: Dict) -> Dict[str, Any]:
        """Évalue les risques globaux"""
        risk_assessment = {
            'risk_level': 'low',
            'identified_risks': [],
            'confidence_score': 0.5
        }
        
        try:
            profile_info = investigation_data.get('profile_info', {})
            privacy = investigation_data.get('privacy_assessment', {})
            activity = investigation_data.get('activity_analysis', {})
            
            # Risque 1: Confidentialité faible
            if privacy.get('overall_privacy') == 'low':
                risk_assessment['identified_risks'].append({
                    'type': 'low_privacy',
                    'severity': 'medium',
                    'description': 'Paramètres de confidentialité faibles'
                })
                risk_assessment['risk_level'] = 'medium'
            
            # Risque 2: Activité élevée
            if activity.get('activity_level') == 'high':
                risk_assessment['identified_risks'].append({
                    'type': 'high_activity',
                    'severity': 'low',
                    'description': 'Activité importante - plus de données exposées'
                })
            
            # Risque 3: Informations sensibles visibles
            basic_info = profile_info.get('basic_info', {})
            if basic_info.get('work') and basic_info.get('location'):
                risk_assessment['identified_risks'].append({
                    'type': 'work_location_exposed',
                    'severity': 'medium',
                    'description': 'Lieu de travail et localisation visibles'
                })
                risk_assessment['risk_level'] = max(risk_assessment['risk_level'], 'medium')
            
            # Score de confiance
            if risk_assessment['risk_level'] == 'medium':
                risk_assessment['confidence_score'] = 0.7
            elif risk_assessment['risk_level'] == 'high':
                risk_assessment['confidence_score'] = 0.9
            else:
                risk_assessment['confidence_score'] = 0.5
            
        except Exception as e:
            self.logger.error(f"Erreur évaluation risques: {e}")
            risk_assessment['error'] = str(e)
        
        return risk_assessment
    
    # ============================================================================
    # MÉTHODES D'ANALYSE D'ASSISTANCE
    # ============================================================================
    
    async def _analyze_engagement(self, posts: List[Dict]) -> Dict[str, Any]:
        """Analyse l'engagement sur les posts"""
        engagement = {
            'average_reactions': 0,
            'average_comments': 0,
            'average_shares': 0,
            'engagement_rate': 0
        }
        
        try:
            if posts:
                total_reactions = sum(post.get('reactions', 0) for post in posts)
                total_comments = sum(post.get('comments', 0) for post in posts)
                total_shares = sum(post.get('shares', 0) for post in posts)
                
                engagement['average_reactions'] = total_reactions / len(posts)
                engagement['average_comments'] = total_comments / len(posts)
                engagement['average_shares'] = total_shares / len(posts)
                engagement['engagement_rate'] = (total_reactions + total_comments + total_shares) / len(posts)
            
        except Exception as e:
            self.logger.error(f"Erreur analyse engagement: {e}")
        
        return engagement
    
    async def _analyze_content(self, posts: List[Dict]) -> Dict[str, Any]:
        """Analyse le contenu des posts"""
        content_analysis = {
            'common_topics': [],
            'sentiment_trend': 'neutral',
            'content_length_avg': 0,
            'media_usage': 'low'
        }
        
        try:
            if posts:
                # Longueur moyenne
                lengths = [len(post.get('content', '')) for post in posts]
                content_analysis['content_length_avg'] = sum(lengths) / len(lengths)
                
                # Usage média
                media_posts = [p for p in posts if any(word in p.get('content', '').lower() for word in ['photo', 'video', 'watch'])]
                if len(media_posts) > len(posts) * 0.5:
                    content_analysis['media_usage'] = 'high'
                elif len(media_posts) > len(posts) * 0.2:
                    content_analysis['media_usage'] = 'medium'
                
        except Exception as e:
            self.logger.error(f"Erreur analyse contenu: {e}")
        
        return content_analysis
    
    async def _analyze_posting_patterns(self, posts: List[Dict]) -> Dict[str, Any]:
        """Analyse les patterns de publication"""
        patterns = {
            'posting_frequency': 'unknown',
            'optimal_times': [],
            'consistency': 'low'
        }
        
        try:
            if len(posts) >= 3:
                patterns['posting_frequency'] = 'regular'
                patterns['consistency'] = 'medium'
            elif len(posts) >= 1:
                patterns['posting_frequency'] = 'sporadic'
            else:
                patterns['posting_frequency'] = 'inactive'
            
        except Exception as e:
            self.logger.error(f"Erreur analyse patterns: {e}")
        
        return patterns
    
    async def _estimate_friends_count(self, html: str) -> int:
        """Estime le nombre d'amis"""
        try:
            # Pattern pour le compteur d'amis
            count_match = re.search(r'(\d+)\s+friends?', html, re.IGNORECASE)
            if count_match:
                return int(count_match.group(1))
            
           # Estimation basée sur le nombre d'éléments
            friend_elements = re.findall(r'friend[^>]*>', html, re.IGNORECASE)
            return len(friend_elements)
        except:
            return 0

# Utilisation principale
async def main():
    """Exemple d'utilisation du analyseur Facebook"""
    analyzer = FacebookIntel()
    
    # Test avec un nom d'utilisateur exemple
    sample_username = "zuck"  # Mark Zuckerberg
    
    try:
        results = await analyzer.investigate(sample_username, depth=2)
        
        print("📘 Analyse Facebook terminée:")
        fb_data = results.get('facebook', {})
        
        print(f"👤 Utilisateur: {fb_data.get('username')}")
        print(f"✅ Profil existe: {fb_data.get('profile_info', {}).get('profile_exists', False)}")
        
        if fb_data.get('profile_info', {}).get('profile_exists'):
            basic_info = fb_data['profile_info']['basic_info']
            print(f"📝 Nom: {basic_info.get('name', 'Non disponible')}")
            print(f"📍 Localisation: {basic_info.get('location', 'Non disponible')}")
            print(f"💼 Travail: {basic_info.get('work', 'Non disponible')}")
            print(f"🎓 Éducation: {basic_info.get('education', 'Non disponible')}")
            
            print(f"📊 Activité: {fb_data.get('activity_analysis', {}).get('activity_level', 'unknown')}")
            print(f"📱 Posts publics: {fb_data.get('public_posts', {}).get('posts_count', 0)}")
            print(f"🛡️ Confidentialité: {fb_data.get('privacy_assessment', {}).get('overall_privacy', 'unknown')}")
            print(f"⚠️ Niveau risque: {fb_data.get('risk_assessment', {}).get('risk_level', 'unknown')}")
        else:
            print("❌ Profil non trouvé ou inaccessible")
        
    except Exception as e:
        print(f"❌ Erreur investigation: {e}")

if __name__ == "__main__":
    asyncio.run(main())
