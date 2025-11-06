# modules/social/instagram.py
import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import re
import json

class InstagramIntel:
    def __init__(self, config_manager=None):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.api_endpoints = {
            'instagram': 'https://www.instagram.com',
            'graphql': 'https://www.instagram.com/graphql/query',
            'api': 'https://i.instagram.com/api/v1'
        }
        
    async def investigate(self, username: str, depth: int = 2) -> Dict[str, Any]:
        """
        Investigation d'un profil Instagram
        """
        self.logger.info(f"Investigation Instagram pour: {username}")
        
        results = {
            'username': username,
            'profile_url': f"https://instagram.com/{username}",
            'investigation_timestamp': datetime.now().isoformat(),
            'profile_info': {},
            'posts_analysis': {},
            'followers_analysis': {},
            'stories_analysis': {},
            'engagement_analysis': {},
            'privacy_assessment': {}
        }
        
        if depth >= 1:
            results['profile_info'] = await self._get_profile_info(username)
            results['privacy_assessment'] = await self._assess_privacy(username, results)
        
        if depth >= 2:
            results['posts_analysis'] = await self._analyze_posts(username)
            results['engagement_analysis'] = await self._analyze_engagement(results)
        
        if depth >= 3:
            results['followers_analysis'] = await self._analyze_followers(username)
            results['stories_analysis'] = await self._analyze_stories(username)
            results['risk_assessment'] = await self._assess_risks(results)
        
        return {'instagram': results}
    
    async def _get_profile_info(self, username: str) -> Dict[str, Any]:
        """Récupère les informations du profil Instagram"""
        profile_info = {
            'username': username,
            'profile_exists': False,
            'basic_info': {},
            'contact_info': {},
            'statistics': {},
            'metadata': {}
        }
        
        try:
            methods = [
                self._scrape_public_data,
                self._try_private_api,
                self._scrape_mobile_data
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
    
    async def _scrape_public_data(self, username: str) -> Dict[str, Any]:
        """Scraping des données publiques"""
        try:
            url = f"{self.api_endpoints['instagram']}/{username}/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.8,en-US;q=0.5,en;q=0.3'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        return await self._parse_public_html(html, username)
                    elif response.status == 404:
                        return {'profile_exists': False}
                    else:
                        return {'profile_exists': False, 'error': f"HTTP {response.status}"}
                        
        except Exception as e:
            self.logger.debug(f"Scraping public échoué: {e}")
            return {'profile_exists': False}
    
    async def _try_private_api(self, username: str) -> Dict[str, Any]:
        """Essaie l'API privée (nécessite session)"""
        try:
            session_id = self.config.get_api_key('instagram', 'session_id') if self.config else None
            if not session_id:
                return {'profile_exists': False, 'error': 'No session ID'}
            
            headers = {
                'User-Agent': 'Instagram 219.0.0.12.117 Android',
                'Cookie': f'sessionid={session_id}'
            }
            
            url = f"{self.api_endpoints['api']}/users/web_profile_info/"
            params = {
                'username': username
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return await self._parse_api_response(data, username)
                    else:
                        return {'profile_exists': False}
                        
        except Exception as e:
            self.logger.debug(f"API privée échouée: {e}")
            return {'profile_exists': False}
    
    async def _scrape_mobile_data(self, username: str) -> Dict[str, Any]:
        """Scraping via version mobile"""
        try:
            url = f"{self.api_endpoints['instagram']}/{username}/?__a=1"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return await self._parse_mobile_json(data, username)
                    else:
                        return {'profile_exists': False}
                        
        except Exception as e:
            self.logger.debug(f"Scraping mobile échoué: {e}")
            return {'profile_exists': False}
    
    async def _parse_public_html(self, html: str, username: str) -> Dict[str, Any]:
        """Parse le HTML public"""
        info = {
            'profile_exists': True,
            'basic_info': {},
            'statistics': {},
            'scraping_method': 'public_html'
        }
        
        try:
            # Extraire les données JSON embarquées
            json_pattern = r'window\._sharedData\s*=\s*({.+?})\s*;\s*</script>'
            json_match = re.search(json_pattern, html)
            
            if json_match:
                json_data = json.loads(json_match.group(1))
                user_data = self._extract_user_data_from_json(json_data, username)
                if user_data:
                    info['basic_info'] = user_data.get('basic_info', {})
                    info['statistics'] = user_data.get('statistics', {})
                    return info
            
            # Fallback: parsing HTML basique
            basic_info = await self._parse_basic_html(html)
            info['basic_info'] = basic_info
            
        except Exception as e:
            self.logger.error(f"Erreur parsing HTML: {e}")
        
        return info
    
    async def _parse_basic_html(self, html: str) -> Dict[str, Any]:
        """Parse les informations basiques depuis le HTML"""
        info = {}
        
        try:
            # Titre
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html)
            if title_match:
                title = title_match.group(1)
                if 'Instagram' in title:
                    info['full_name'] = title.split('•')[0].strip()
            
            # Description
            desc_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]*)"', html)
            if desc_match:
                info['description'] = desc_match.group(1)
            
            # Compte vérifié
            if 'Verified' in html:
                info['is_verified'] = True
            
            # Compte privé
            if 'This Account is Private' in html:
                info['is_private'] = True
            
        except Exception as e:
            self.logger.error(f"Erreur parsing HTML basique: {e}")
        
        return info
    
    def _extract_user_data_from_json(self, json_data: Dict, username: str) -> Optional[Dict]:
        """Extrait les données utilisateur depuis le JSON"""
        try:
            # Naviguer dans la structure JSON complexe d'Instagram
            user_data = {}
            
            # Essayer différents chemins
            paths = [
                ['entry_data', 'ProfilePage', 0, 'graphql', 'user'],
                ['entry_data', 'ProfilePage', 0, 'graphql', 'user'],
                ['graphql', 'user']
            ]
            
            user = None
            for path in paths:
                try:
                    current = json_data
                    for key in path:
                        if isinstance(key, int) and isinstance(current, list):
                            current = current[key]
                        else:
                            current = current[key]
                    user = current
                    break
                except (KeyError, IndexError, TypeError):
                    continue
            
            if not user:
                return None
            
            # Informations basiques
            user_data['basic_info'] = {
                'id': user.get('id'),
                'username': user.get('username'),
                'full_name': user.get('full_name'),
                'biography': user.get('biography'),
                'external_url': user.get('external_url'),
                'is_private': user.get('is_private', False),
                'is_verified': user.get('is_verified', False),
                'profile_pic_url': user.get('profile_pic_url'),
                'profile_pic_url_hd': user.get('profile_pic_url_hd')
            }
            
            # Statistiques
            user_data['statistics'] = {
                'followers_count': user.get('edge_followed_by', {}).get('count', 0),
                'following_count': user.get('edge_follow', {}).get('count', 0),
                'posts_count': user.get('edge_owner_to_timeline_media', {}).get('count', 0),
                'total_igtv_videos': user.get('edge_felix_video_timeline', {}).get('count', 0),
                'total_clips': user.get('edge_highlight_reels', {}).get('count', 0)
            }
            
            return user_data
            
        except Exception as e:
            self.logger.error(f"Erreur extraction JSON: {e}")
            return None
    
    async def _parse_api_response(self, data: Dict, username: str) -> Dict[str, Any]:
        """Parse la réponse de l'API privée"""
        info = {
            'profile_exists': True,
            'basic_info': {},
            'statistics': {},
            'api_method': 'private_api'
        }
        
        try:
            user = data.get('data', {}).get('user', {})
            
            info['basic_info'] = {
                'id': user.get('id'),
                'username': user.get('username'),
                'full_name': user.get('full_name'),
                'biography': user.get('biography'),
                'external_url': user.get('external_url'),
                'is_private': user.get('is_private', False),
                'is_verified': user.get('is_verified', False),
                'profile_pic_url': user.get('profile_pic_url'),
                'pronouns': user.get('pronouns', [])
            }
            
            info['statistics'] = {
                'followers_count': user.get('edge_followed_by', {}).get('count', 0),
                'following_count': user.get('edge_follow', {}).get('count', 0),
                'posts_count': user.get('edge_owner_to_timeline_media', {}).get('count', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur parsing API: {e}")
        
        return info
    
    async def _parse_mobile_json(self, data: Dict, username: str) -> Dict[str, Any]:
        """Parse le JSON de la version mobile"""
        info = {
            'profile_exists': True,
            'basic_info': {},
            'statistics': {},
            'scraping_method': 'mobile_json'
        }
        
        try:
            user = data.get('graphql', {}).get('user', {})
            
            info['basic_info'] = {
                'id': user.get('id'),
                'username': user.get('username'),
                'full_name': user.get('full_name'),
                'biography': user.get('biography'),
                'external_url': user.get('external_url'),
                'is_private': user.get('is_private', False),
                'is_verified': user.get('is_verified', False),
                'profile_pic_url': user.get('profile_pic_url')
            }
            
            info['statistics'] = {
                'followers_count': user.get('edge_followed_by', {}).get('count', 0),
                'following_count': user.get('edge_follow', {}).get('count', 0),
                'posts_count': user.get('edge_owner_to_timeline_media', {}).get('count', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur parsing mobile JSON: {e}")
        
        return info
    
    async def _analyze_posts(self, username: str) -> Dict[str, Any]:
        """Analyse les posts/publications"""
        posts_analysis = {
            'posts_count': 0,
            'recent_posts': [],
            'engagement_metrics': {},
            'content_analysis': {},
            'hashtag_analysis': {},
            'media_analysis': {}
        }
        
        try:
            # Récupérer les posts récents
            posts = await self._get_recent_posts(username)
            posts_analysis['posts_count'] = len(posts)
            posts_analysis['recent_posts'] = posts[:12]  # 12 derniers posts
            
            # Analyser l'engagement
            posts_analysis['engagement_metrics'] = await self._analyze_posts_engagement(posts)
            
            # Analyser le contenu
            posts_analysis['content_analysis'] = await self._analyze_posts_content(posts)
            
            # Analyser les hashtags
            posts_analysis['hashtag_analysis'] = await self._analyze_hashtags(posts)
            
            # Analyser les médias
            posts_analysis['media_analysis'] = await self._analyze_media_types(posts)
            
        except Exception as e:
            self.logger.error(f"Erreur analyse posts {username}: {e}")
            posts_analysis['error'] = str(e)
        
        return posts_analysis
    
    async def _get_recent_posts(self, username: str) -> List[Dict]:
        """Récupère les posts récents"""
        posts = []
        
        try:
            # Essayer l'API privée d'abord
            session_id = self.config.get_api_key('instagram', 'session_id') if self.config else None
            if session_id:
                posts = await self._get_posts_private_api(username)
            else:
                # Fallback: scraping public
                posts = await self._get_posts_public(username)
            
        except Exception as e:
            self.logger.error(f"Erreur récupération posts: {e}")
        
        return posts
    
    async def _get_posts_private_api(self, username: str) -> List[Dict]:
        """Récupère les posts via API privée"""
        try:
            headers = {
                'User-Agent': 'Instagram 219.0.0.12.117 Android',
                'Cookie': f'sessionid={self.config.get_api_key("instagram", "session_id")}'
            }
            
            url = f"{self.api_endpoints['api']}/feed/user/{username}/"
            params = {
                'count': 12
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return await self._parse_posts_api(data)
                    else:
                        return []
                        
        except Exception as e:
            self.logger.debug(f"API posts échouée: {e}")
            return []
    
    async def _get_posts_public(self, username: str) -> List[Dict]:
        """Récupère les posts via scraping public"""
        try:
            url = f"{self.api_endpoints['instagram']}/{username}/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        return await self._parse_posts_html(html)
                    else:
                        return []
                        
        except Exception as e:
            self.logger.debug(f"Scraping posts échoué: {e}")
            return []
    
    async def _analyze_followers(self, username: str) -> Dict[str, Any]:
        """Analyse les followers/abonnements"""
        followers_analysis = {
            'followers_count': 0,
            'following_count': 0,
            'follower_ratio': 0,
            'growth_analysis': {},
            'authenticity_metrics': {}
        }
        
        try:
            profile_info = await self._get_profile_info(username)
            stats = profile_info.get('statistics', {})
            
            followers_analysis['followers_count'] = stats.get('followers_count', 0)
            followers_analysis['following_count'] = stats.get('following_count', 0)
            
            # Ratio followers/following
            if followers_analysis['following_count'] > 0:
                followers_analysis['follower_ratio'] = (
                    followers_analysis['followers_count'] / followers_analysis['following_count']
                )
            
            # Métriques d'authenticité
            followers_analysis['authenticity_metrics'] = await self._assess_authenticity(
                followers_analysis['followers_count'],
                followers_analysis['following_count'],
                followers_analysis['follower_ratio']
            )
            
        except Exception as e:
            self.logger.error(f"Erreur analyse followers {username}: {e}")
            followers_analysis['error'] = str(e)
        
        return followers_analysis
    
    async def _analyze_stories(self, username: str) -> Dict[str, Any]:
        """Analyse les stories"""
        stories_analysis = {
            'has_stories': False,
            'stories_count': 0,
            'story_activity': 'low',
            'story_metrics': {}
        }
        
        try:
            session_id = self.config.get_api_key('instagram', 'session_id') if self.config else None
            if session_id:
                # Récupérer les stories via API privée
                stories = await self._get_stories_private_api(username)
                stories_analysis['has_stories'] = len(stories) > 0
                stories_analysis['stories_count'] = len(stories)
                
                if len(stories) >= 5:
                    stories_analysis['story_activity'] = 'high'
                elif len(stories) >= 2:
                    stories_analysis['story_activity'] = 'medium'
            
        except Exception as e:
            self.logger.error(f"Erreur analyse stories {username}: {e}")
            stories_analysis['error'] = str(e)
        
        return stories_analysis
    
    async def _analyze_engagement(self, investigation_data: Dict) -> Dict[str, Any]:
        """Analyse l'engagement global"""
        engagement_analysis = {
            'overall_engagement': 'low',
            'engagement_rate': 0,
            'interaction_patterns': [],
            'optimal_posting_times': []
        }
        
        try:
            posts_analysis = investigation_data.get('posts_analysis', {})
            engagement_metrics = posts_analysis.get('engagement_metrics', {})
            profile_info = investigation_data.get('profile_info', {})
            stats = profile_info.get('statistics', {})
            
            followers_count = stats.get('followers_count', 1)
            
            # Taux d'engagement moyen
            avg_likes = engagement_metrics.get('average_likes', 0)
            avg_comments = engagement_metrics.get('average_comments', 0)
            
            if followers_count > 0:
                engagement_rate = ((avg_likes + avg_comments) / followers_count) * 100
                engagement_analysis['engagement_rate'] = engagement_rate
                
                if engagement_rate > 5:
                    engagement_analysis['overall_engagement'] = 'high'
                elif engagement_rate > 2:
                    engagement_analysis['overall_engagement'] = 'medium'
                else:
                    engagement_analysis['overall_engagement'] = 'low'
            
        except Exception as e:
            self.logger.error(f"Erreur analyse engagement: {e}")
            engagement_analysis['error'] = str(e)
        
        return engagement_analysis
    
    async def _assess_privacy(self, username: str, investigation_data: Dict) -> Dict[str, Any]:
        """Évalue les paramètres de confidentialité"""
        privacy_assessment = {
            'privacy_level': 'unknown',
            'visible_information': [],
            'privacy_risks': [],
            'recommendations': []
        }
        
        try:
            profile_info = investigation_data.get('profile_info', {})
            basic_info = profile_info.get('basic_info', {})
            
            # Niveau de confidentialité basé sur les paramètres
            if basic_info.get('is_private', False):
                privacy_assessment['privacy_level'] = 'high'
            else:
                privacy_assessment['privacy_level'] = 'low'
            
            # Informations visibles
            visible_info = []
            if basic_info.get('full_name'):
                visible_info.append('full_name')
            if basic_info.get('biography'):
                visible_info.append('biography')
            if basic_info.get('external_url'):
                visible_info.append('website')
            if basic_info.get('profile_pic_url'):
                visible_info.append('profile_picture')
            
            privacy_assessment['visible_information'] = visible_info
            
            # Recommandations
            if privacy_assessment['privacy_level'] == 'low':
                privacy_assessment['recommendations'].append('Passer le compte en privé')
                privacy_assessment['recommendations'].append('Limiter les informations personnelles dans la bio')
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
            engagement = investigation_data.get('engagement_analysis', {})
            
            # Risque 1: Compte public
            if privacy.get('privacy_level') == 'low':
                risk_assessment['identified_risks'].append({
                    'type': 'public_account',
                    'severity': 'medium',
                    'description': 'Compte public - toutes les publications sont visibles'
                })
                risk_assessment['risk_level'] = 'medium'
            
            # Risque 2: Fort engagement
            if engagement.get('overall_engagement') == 'high':
                risk_assessment['identified_risks'].append({
                    'type': 'high_visibility',
                    'severity': 'low',
                    'description': 'Fort engagement - plus grande visibilité'
                })
            
            # Risque 3: Informations personnelles dans la bio
            basic_info = profile_info.get('basic_info', {})
            if basic_info.get('external_url') or basic_info.get('biography'):
                risk_assessment['identified_risks'].append({
                    'type': 'personal_info_exposed',
                    'severity': 'medium',
                    'description': 'Informations personnelles dans la biographie'
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
    
    async def _parse_posts_api(self, data: Dict) -> List[Dict]:
        """Parse les posts de l'API"""
        posts = []
        
        try:
            items = data.get('items', [])
            for item in items[:12]:  # Limiter aux 12 derniers
                post = {
                    'id': item.get('id'),
                    'timestamp': item.get('taken_at'),
                    'caption': item.get('caption', {}).get('text', ''),
                    'like_count': item.get('like_count', 0),
                    'comment_count': item.get('comment_count', 0),
                    'media_type': item.get('media_type', 1),  # 1=photo, 2=video, 8=carousel
                    'media_url': item.get('image_versions2', {}).get('candidates', [{}])[0].get('url'),
                    'hashtags': re.findall(r'#(\w+)', item.get('caption', {}).get('text', ''))
                }
                posts.append(post)
            
        except Exception as e:
            self.logger.error(f"Erreur parsing posts API: {e}")
        
        return posts
    
    async def _parse_posts_html(self, html: str) -> List[Dict]:
        """Parse les posts depuis le HTML"""
        posts = []
        
        try:
            # Extraire les données JSON
            json_pattern = r'window\._sharedData\s*=\s*({.+?})\s*;\s*</script>'
            json_match = re.search(json_pattern, html)
            
            if json_match:
                json_data = json.loads(json_match.group(1))
                
                # Naviguer vers les posts
                user = None
                paths = [
                    ['entry_data', 'ProfilePage', 0, 'graphql', 'user'],
                    ['entry_data', 'ProfilePage', 0, 'graphql', 'user']
                ]
                
                for path in paths:
                    try:
                        current = json_data
                        for key in path:
                            current = current[key]
                        user = current
                        break
                    except (KeyError, IndexError, TypeError):
                        continue
                
                if user:
                    edges = user.get('edge_owner_to_timeline_media', {}).get('edges', [])
                    for edge in edges[:12]:
                        node = edge.get('node', {})
                        post = {
                            'id': node.get('id'),
                            'timestamp': node.get('taken_at_timestamp'),
                            'caption': node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', ''),
                            'like_count': node.get('edge_liked_by', {}).get('count', 0),
                            'comment_count': node.get('edge_media_to_comment', {}).get('count', 0),
                            'media_type': 'photo' if node.get('__typename') == 'GraphImage' else 'video',
                            'media_url': node.get('display_url'),
                            'hashtags': re.findall(r'#(\w+)', node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', ''))
                        }
                        posts.append(post)
            
        except Exception as e:
            self.logger.error(f"Erreur parsing posts HTML: {e}")
        
        return posts
    
    async def _analyze_posts_engagement(self, posts: List[Dict]) -> Dict[str, Any]:
        """Analyse l'engagement des posts"""
        engagement = {
            'average_likes': 0,
            'average_comments': 0,
            'engagement_rate': 0,
            'most_engaged_posts': []
        }
        
        try:
            if posts:
                total_likes = sum(post.get('like_count', 0) for post in posts)
                total_comments = sum(post.get('comment_count', 0) for post in posts)
                
                engagement['average_likes'] = total_likes / len(posts)
                engagement['average_comments'] = total_comments / len(posts)
                
                # Posts les plus engagés
                engagement['most_engaged_posts'] = sorted(
                    posts, 
                    key=lambda x: x.get('like_count', 0) + x.get('comment_count', 0), 
                    reverse=True
                )[:3]
            
        except Exception as e:
            self.logger.error(f"Erreur analyse engagement posts: {e}")
        
        return engagement
    
    async def _analyze_posts_content(self, posts: List[Dict]) -> Dict[str, Any]:
        """Analyse le contenu des posts"""
        content_analysis = {
            'common_themes': [],
            'caption_length_avg': 0,
            'emoji_usage': 'low',
            'mention_frequency': 'low'
        }
        
        try:
            if posts:
                # Longueur moyenne des légendes
                lengths = [len(post.get('caption', '')) for post in posts]
                content_analysis['caption_length_avg'] = sum(lengths) / len(lengths)
                
                # Usage d'emojis
                emoji_count = sum(len(re.findall(r'[^\w\s,.]', post.get('caption', ''))) for post in posts)
                if emoji_count > len(posts) * 3:
                    content_analysis['emoji_usage'] = 'high'
                elif emoji_count > len(posts):
                    content_analysis['emoji_usage'] = 'medium'
                
                # Mentions
                mention_count = sum(len(re.findall(r'@(\w+)', post.get('caption', ''))) for post in posts)
                if mention_count > len(posts) * 2:
                    content_analysis['mention_frequency'] = 'high'
                elif mention_count > len(posts):
                    content_analysis['mention_frequency'] = 'medium'
                
        except Exception as e:
            self.logger.error(f"Erreur analyse contenu: {e}")
        
        return content_analysis
    
    async def _analyze_hashtags(self, posts: List[Dict]) -> Dict[str, Any]:
        """Analyse les hashtags utilisés"""
        hashtag_analysis = {
            'total_hashtags': 0,
            'unique_hashtags': [],
            'most_used_hashtags': [],
            'hashtag_categories': []
        }
        
        try:
            all_hashtags = []
            for post in posts:
                all_hashtags.extend(post.get('hashtags', []))
            
            hashtag_analysis['total_hashtags'] = len(all_hashtags)
            hashtag_analysis['unique_hashtags'] = list(set(all_hashtags))
            
            # Hashtags les plus utilisés
            from collections import Counter
            hashtag_counts = Counter(all_hashtags)
            hashtag_analysis['most_used_hashtags'] = hashtag_counts.most_common(10)
            
        except Exception as e:
            self.logger.error(f"Erreur analyse hashtags: {e}")
        
        return hashtag_analysis
    
    async def _analyze_media_types(self, posts: List[Dict]) -> Dict[str, Any]:
        """Analyse les types de médias"""
        media_analysis = {
            'photo_count': 0,
            'video_count': 0,
            'carousel_count': 0,
            'media_distribution': {}
        }
        
        try:
            for post in posts:
                media_type = post.get('media_type', 'photo')
                if media_type == 'photo' or media_type == 1:
                    media_analysis['photo_count'] += 1
                elif media_type == 'video' or media_type == 2:
                    media_analysis['video_count'] += 1
                elif media_type == 8:
                    media_analysis['carousel_count'] += 1
            
            total = len(posts)
            if total > 0:
                media_analysis['media_distribution'] = {
                    'photos': (media_analysis['photo_count'] / total) * 100,
                    'videos': (media_analysis['video_count'] / total) * 100,
                    'carousels': (media_analysis['carousel_count'] / total) * 100
                }
            
        except Exception as e:
            self.logger.error(f"Erreur analyse médias: {e}")
        
        return media_analysis
    
    async def _get_stories_private_api(self, username: str) -> List[Dict]:
        """Récupère les stories via API privée"""
        try:
            headers = {
                'User-Agent': 'Instagram 219.0.0.12.117 Android',
                'Cookie': f'sessionid={self.config.get_api_key("instagram", "session_id")}'
            }
            
            # D'abord récupérer l'ID utilisateur
            user_id = await self._get_user_id(username)
            if not user_id:
                return []
            
            url = f"{self.api_endpoints['api']}/feed/user/{user_id}/story/"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('reel', {}).get('items', [])
                    else:
                        return []
                        
        except Exception as e:
            self.logger.debug(f"API stories échouée: {e}")
            return []
    
    async def _get_user_id(self, username: str) -> Optional[str]:
        """Récupère l'ID utilisateur"""
        try:
            profile_info = await self._get_profile_info(username)
            return profile_info.get('basic_info', {}).get('id')
        except:
            return None
    
    async def _assess_authenticity(self, followers: int, following: int, ratio: float) -> Dict[str, Any]:
        """Évalue l'authenticité du compte"""
        authenticity = {
            'authenticity_score': 0,
            'authenticity_level': 'unknown',
            'red_flags': [],
            'green_flags': []
        }
        
        try:
            score = 50  # Score de base
            
            # Ratio followers/following
            if ratio < 0.1:
                authenticity['red_flags'].append('Ratio followers/following très faible')
                score -= 20
            elif ratio > 10:
                authenticity['green_flags'].append('Ratio followers/following élevé')
                score += 10
            
            # Nombre de followers
            if followers > 10000:
                score += 10
            elif followers < 100:
                score -= 10
            
            # Nombre d'abonnements
            if following > 5000:
                authenticity['red_flags'].append('Trop d\'abonnements')
                score -= 15
            
            authenticity['authenticity_score'] = max(0, min(100, score))
            
            if authenticity['authenticity_score'] >= 70:
                authenticity['authenticity_level'] = 'high'
            elif authenticity['authenticity_score'] >= 40:
                authenticity['authenticity_level'] = 'medium'
            else:
                authenticity['authenticity_level'] = 'low'
            
        except Exception as e:
            self.logger.error(f"Erreur évaluation authenticité: {e}")
        
        return authenticity

# Utilisation principale
async def main():
    """Exemple d'utilisation du analyseur Instagram"""
    analyzer = InstagramIntel()
    
    # Test avec un nom d'utilisateur exemple
    sample_username = "instagram"  # Compte officiel
    
    try:
        results = await analyzer.investigate(sample_username, depth=2)
        
        print("📸 Analyse Instagram terminée:")
        ig_data = results.get('instagram', {})
        
        print(f"👤 Utilisateur: {ig_data.get('username')}")
        print(f"✅ Profil existe: {ig_data.get('profile_info', {}).get('profile_exists', False)}")
        
        if ig_data.get('profile_info', {}).get('profile_exists'):
            basic_info = ig_data['profile_info']['basic_info']
            stats = ig_data['profile_info']['statistics']
            
            print(f"📝 Nom: {basic_info.get('full_name', 'Non disponible')}")
            print(f"📊 Followers: {stats.get('followers_count', 0)}")
            print(f"👥 Abonnements: {stats.get('following_count', 0)}")
            print(f"📷 Posts: {stats.get('posts_count', 0)}")
            print(f"🔒 Privé: {basic_info.get('is_private', False)}")
            print(f"✅ Vérifié: {basic_info.get('is_verified', False)}")
            
            print(f"📈 Engagement: {ig_data.get('engagement_analysis', {}).get('overall_engagement', 'unknown')}")
            print(f"🛡️ Confidentialité: {ig_data.get('privacy_assessment', {}).get('privacy_level', 'unknown')}")
            print(f"⚠️ Niveau risque: {ig_data.get('risk_assessment', {}).get('risk_level', 'unknown')}")
        else:
            print("❌ Profil non trouvé ou inaccessible")
        
    except Exception as e:
        print(f"❌ Erreur investigation: {e}")

if __name__ == "__main__":
    asyncio.run(main())
