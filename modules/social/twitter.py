# modules/social/twitter.py
import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import re
import json
import base64

class TwitterIntel:
    def __init__(self, config_manager=None):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.api_endpoints = {
            'twitter': 'https://twitter.com',
            'api': 'https://api.twitter.com',
            'api_v2': 'https://api.twitter.com/2',
            'mobile': 'https://mobile.twitter.com'
        }
        
    async def investigate(self, username: str, depth: int = 2) -> Dict[str, Any]:
        """
        Investigation d'un profil Twitter
        """
        self.logger.info(f"Investigation Twitter pour: {username}")
        
        results = {
            'username': username,
            'profile_url': f"https://twitter.com/{username}",
            'investigation_timestamp': datetime.now().isoformat(),
            'profile_info': {},
            'tweets_analysis': {},
            'followers_analysis': {},
            'engagement_analysis': {},
            'content_analysis': {},
            'privacy_assessment': {}
        }
        
        if depth >= 1:
            results['profile_info'] = await self._get_profile_info(username)
            results['privacy_assessment'] = await self._assess_privacy(username, results)
        
        if depth >= 2:
            results['tweets_analysis'] = await self._analyze_tweets(username)
            results['engagement_analysis'] = await self._analyze_engagement(results)
        
        if depth >= 3:
            results['followers_analysis'] = await self._analyze_followers(username)
            results['content_analysis'] = await self._analyze_content(results)
            results['risk_assessment'] = await self._assess_risks(results)
        
        return {'twitter': results}
    
    async def _get_profile_info(self, username: str) -> Dict[str, Any]:
        """Récupère les informations du profil Twitter"""
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
                self._scrape_public_profile,
                self._try_api_v2,
                self._scrape_mobile_profile
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
    
    async def _scrape_public_profile(self, username: str) -> Dict[str, Any]:
        """Scraping du profil public"""
        try:
            url = f"{self.api_endpoints['twitter']}/{username}"
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
    
    async def _try_api_v2(self, username: str) -> Dict[str, Any]:
        """Essaie l'API Twitter v2 (nécessite bearer token)"""
        try:
            bearer_token = self.config.get_api_key('twitter', 'bearer_token') if self.config else None
            if not bearer_token:
                return {'profile_exists': False, 'error': 'No bearer token'}
            
            headers = {
                'Authorization': f'Bearer {bearer_token}'
            }
            
            url = f"{self.api_endpoints['api_v2']}/users/by/username/{username}"
            params = {
                'user.fields': 'created_at,description,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,public_metrics,url,username,verified,withheld'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return await self._parse_api_v2_response(data, username)
                    else:
                        return {'profile_exists': False}
                        
        except Exception as e:
            self.logger.debug(f"API v2 échouée: {e}")
            return {'profile_exists': False}
    
    async def _scrape_mobile_profile(self, username: str) -> Dict[str, Any]:
        """Scraping via version mobile"""
        try:
            url = f"{self.api_endpoints['mobile']}/{username}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        return await self._parse_mobile_html(html, username)
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
            json_pattern = r'<script[^>]*data-testid="server-response"[^>]*>({.+?})</script>'
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
                if 'Twitter' in title:
                    info['name'] = title.split('(@')[0].strip()
            
            # Description/bio
            desc_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]*)"', html)
            if desc_match:
                info['description'] = desc_match.group(1)
            
            # Compte vérifié
            if 'Verified' in html:
                info['verified'] = True
            
            # Compte protégé
            if 'Protected Tweets' in html:
                info['protected'] = True
            
            # Localisation
            location_match = re.search(r'"location"[^>]*>([^<]+)</span>', html)
            if location_match:
                info['location'] = location_match.group(1).strip()
            
            # Site web
            website_match = re.search(r'"url"[^>]*>([^<]+)</a>', html)
            if website_match:
                info['website'] = website_match.group(1).strip()
            
        except Exception as e:
            self.logger.error(f"Erreur parsing HTML basique: {e}")
        
        return info
    
    def _extract_user_data_from_json(self, json_data: Dict, username: str) -> Optional[Dict]:
        """Extrait les données utilisateur depuis le JSON"""
        try:
            user_data = {}
            
            # Naviguer dans la structure JSON complexe de Twitter
            def find_user_data(obj, path=[]):
                if isinstance(obj, dict):
                    if 'user' in obj and 'legacy' in obj.get('user', {}):
                        return obj['user']
                    if 'data' in obj and 'user' in obj.get('data', {}):
                        return obj['data']['user']
                    for key, value in obj.items():
                        result = find_user_data(value, path + [key])
                        if result:
                            return result
                elif isinstance(obj, list):
                    for item in obj:
                        result = find_user_data(item, path + ['[]'])
                        if result:
                            return result
                return None
            
            user = find_user_data(json_data)
            if not user:
                return None
            
            legacy = user.get('legacy', {})
            
            # Informations basiques
            user_data['basic_info'] = {
                'id': user.get('rest_id'),
                'name': legacy.get('name'),
                'screen_name': legacy.get('screen_name'),
                'description': legacy.get('description'),
                'location': legacy.get('location'),
                'url': legacy.get('url'),
                'verified': legacy.get('verified', False),
                'protected': legacy.get('protected', False),
                'created_at': legacy.get('created_at'),
                'profile_image_url': legacy.get('profile_image_url_https'),
                'profile_banner_url': legacy.get('profile_banner_url')
            }
            
            # Statistiques
            user_data['statistics'] = {
                'followers_count': legacy.get('followers_count', 0),
                'following_count': legacy.get('friends_count', 0),
                'tweets_count': legacy.get('statuses_count', 0),
                'listed_count': legacy.get('listed_count', 0),
                'favourites_count': legacy.get('favourites_count', 0)
            }
            
            return user_data
            
        except Exception as e:
            self.logger.error(f"Erreur extraction JSON: {e}")
            return None
    
    async def _parse_api_v2_response(self, data: Dict, username: str) -> Dict[str, Any]:
        """Parse la réponse de l'API v2"""
        info = {
            'profile_exists': True,
            'basic_info': {},
            'statistics': {},
            'api_method': 'twitter_api_v2'
        }
        
        try:
            user_data = data.get('data', {})
            public_metrics = user_data.get('public_metrics', {})
            
            info['basic_info'] = {
                'id': user_data.get('id'),
                'name': user_data.get('name'),
                'username': user_data.get('username'),
                'description': user_data.get('description'),
                'location': user_data.get('location'),
                'url': user_data.get('url'),
                'verified': user_data.get('verified', False),
                'protected': user_data.get('protected', False),
                'created_at': user_data.get('created_at'),
                'profile_image_url': user_data.get('profile_image_url')
            }
            
            info['statistics'] = {
                'followers_count': public_metrics.get('followers_count', 0),
                'following_count': public_metrics.get('following_count', 0),
                'tweets_count': public_metrics.get('tweet_count', 0),
                'listed_count': public_metrics.get('listed_count', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur parsing API v2: {e}")
        
        return info
    
    async def _parse_mobile_html(self, html: str, username: str) -> Dict[str, Any]:
        """Parse la version mobile"""
        info = {
            'profile_exists': True,
            'basic_info': {},
            'scraping_method': 'mobile'
        }
        
        try:
            # Nom
            name_match = re.search(r'<div[^>]*class="[^"]*fullname[^"]*"[^>]*>([^<]+)</div>', html)
            if name_match:
                info['basic_info']['name'] = name_match.group(1).strip()
            
            # Description
            desc_match = re.search(r'<div[^>]*class="[^"]*bio[^"]*"[^>]*>([^<]+)</div>', html)
            if desc_match:
                info['basic_info']['description'] = desc_match.group(1).strip()
            
            # Localisation
            location_match = re.search(r'<div[^>]*class="[^"]*location[^"]*"[^>]*>([^<]+)</div>', html)
            if location_match:
                info['basic_info']['location'] = location_match.group(1).strip()
            
            # Site web
            website_match = re.search(r'<div[^>]*class="[^"]*url[^"]*"[^>]*>([^<]+)</div>', html)
            if website_match:
                info['basic_info']['website'] = website_match.group(1).strip()
            
        except Exception as e:
            self.logger.error(f"Erreur parsing mobile: {e}")
        
        return info
    
    async def _analyze_tweets(self, username: str) -> Dict[str, Any]:
        """Analyse les tweets"""
        tweets_analysis = {
            'tweets_count': 0,
            'recent_tweets': [],
            'engagement_metrics': {},
            'content_analysis': {},
            'hashtag_analysis': {},
            'temporal_analysis': {}
        }
        
        try:
            # Récupérer les tweets récents
            tweets = await self._get_recent_tweets(username)
            tweets_analysis['tweets_count'] = len(tweets)
            tweets_analysis['recent_tweets'] = tweets[:10]  # 10 derniers tweets
            
            # Analyser l'engagement
            tweets_analysis['engagement_metrics'] = await self._analyze_tweets_engagement(tweets)
            
            # Analyser le contenu
            tweets_analysis['content_analysis'] = await self._analyze_tweets_content(tweets)
            
            # Analyser les hashtags
            tweets_analysis['hashtag_analysis'] = await self._analyze_tweets_hashtags(tweets)
            
            # Analyser les patterns temporels
            tweets_analysis['temporal_analysis'] = await self._analyze_tweets_timing(tweets)
            
        except Exception as e:
            self.logger.error(f"Erreur analyse tweets {username}: {e}")
            tweets_analysis['error'] = str(e)
        
        return tweets_analysis
    
    async def _get_recent_tweets(self, username: str) -> List[Dict]:
        """Récupère les tweets récents"""
        tweets = []
        
        try:
            # Essayer l'API v2 d'abord
            bearer_token = self.config.get_api_key('twitter', 'bearer_token') if self.config else None
            if bearer_token:
                tweets = await self._get_tweets_api_v2(username)
            else:
                # Fallback: scraping public
                tweets = await self._get_tweets_public(username)
            
        except Exception as e:
            self.logger.error(f"Erreur récupération tweets: {e}")
        
        return tweets
    
    async def _get_tweets_api_v2(self, username: str) -> List[Dict]:
        """Récupère les tweets via API v2"""
        try:
            bearer_token = self.config.get_api_key('twitter', 'bearer_token')
            headers = {
                'Authorization': f'Bearer {bearer_token}'
            }
            
            # D'abord récupérer l'ID utilisateur
            user_url = f"{self.api_endpoints['api_v2']}/users/by/username/{username}"
            async with aiohttp.ClientSession() as session:
                async with session.get(user_url, headers=headers) as response:
                    if response.status == 200:
                        user_data = await response.json()
                        user_id = user_data.get('data', {}).get('id')
                        
                        if user_id:
                            # Récupérer les tweets
                            tweets_url = f"{self.api_endpoints['api_v2']}/users/{user_id}/tweets"
                            params = {
                                'max_results': 10,
                                'tweet.fields': 'created_at,public_metrics,text,source,lang'
                            }
                            
                            async with session.get(tweets_url, headers=headers, params=params) as response:
                                if response.status == 200:
                                    tweets_data = await response.json()
                                    return await self._parse_tweets_api_v2(tweets_data)
            
            return []
                        
        except Exception as e:
            self.logger.debug(f"API tweets v2 échouée: {e}")
            return []
    
    async def _get_tweets_public(self, username: str) -> List[Dict]:
        """Récupère les tweets via scraping public"""
        try:
            url = f"{self.api_endpoints['twitter']}/{username}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        return await self._parse_tweets_html(html)
                    else:
                        return []
                        
        except Exception as e:
            self.logger.debug(f"Scraping tweets échoué: {e}")
            return []
    
    async def _analyze_followers(self, username: str) -> Dict[str, Any]:
        """Analyse les followers"""
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
            followers_analysis['authenticity_metrics'] = await self._assess_twitter_authenticity(
                followers_analysis['followers_count'],
                followers_analysis['following_count'],
                followers_analysis['follower_ratio']
            )
            
        except Exception as e:
            self.logger.error(f"Erreur analyse followers {username}: {e}")
            followers_analysis['error'] = str(e)
        
        return followers_analysis
    
    async def _analyze_engagement(self, investigation_data: Dict) -> Dict[str, Any]:
        """Analyse l'engagement global"""
        engagement_analysis = {
            'overall_engagement': 'low',
            'engagement_rate': 0,
            'interaction_patterns': [],
            'influence_metrics': {}
        }
        
        try:
            tweets_analysis = investigation_data.get('tweets_analysis', {})
            engagement_metrics = tweets_analysis.get('engagement_metrics', {})
            profile_info = investigation_data.get('profile_info', {})
            stats = profile_info.get('statistics', {})
            
            followers_count = stats.get('followers_count', 1)
            
            # Taux d'engagement moyen
            avg_likes = engagement_metrics.get('average_likes', 0)
            avg_retweets = engagement_metrics.get('average_retweets', 0)
            avg_replies = engagement_metrics.get('average_replies', 0)
            
            if followers_count > 0:
                engagement_rate = ((avg_likes + avg_retweets + avg_replies) / followers_count) * 100
                engagement_analysis['engagement_rate'] = engagement_rate
                
                if engagement_rate > 5:
                    engagement_analysis['overall_engagement'] = 'high'
                elif engagement_rate > 2:
                    engagement_analysis['overall_engagement'] = 'medium'
                else:
                    engagement_analysis['overall_engagement'] = 'low'
            
            # Métriques d'influence
            engagement_analysis['influence_metrics'] = {
                'estimated_influence': self._estimate_twitter_influence(stats),
                'reach_potential': 'medium',
                'content_impact': 'unknown'
            }
            
        except Exception as e:
            self.logger.error(f"Erreur analyse engagement: {e}")
            engagement_analysis['error'] = str(e)
        
        return engagement_analysis
    
    async def _analyze_content(self, investigation_data: Dict) -> Dict[str, Any]:
        """Analyse le contenu et les topics"""
        content_analysis = {
            'primary_topics': [],
            'content_sentiment': 'neutral',
            'language_analysis': {},
            'media_usage': 'low',
            'controversy_level': 'low'
        }
        
        try:
            profile_info = investigation_data.get('profile_info', {})
            tweets_analysis = investigation_data.get('tweets_analysis', {})
            
            description = profile_info.get('basic_info', {}).get('description', '')
            tweets = tweets_analysis.get('recent_tweets', [])
            
            # Combiner tout le texte pour l'analyse
            all_text = description + ' ' + ' '.join([tweet.get('text', '') for tweet in tweets])
            
            # Analyse des topics principaux
            content_analysis['primary_topics'] = self._extract_twitter_topics(all_text)
            
            # Analyse de langue
            content_analysis['language_analysis'] = await self._analyze_twitter_language(all_text)
            
            # Usage média
            media_tweets = [tweet for tweet in tweets if tweet.get('has_media', False)]
            if len(media_tweets) > len(tweets) * 0.5:
                content_analysis['media_usage'] = 'high'
            elif len(media_tweets) > len(tweets) * 0.2:
                content_analysis['media_usage'] = 'medium'
            
            # Niveau de controverse
            content_analysis['controversy_level'] = self._assess_twitter_controversy(all_text)
            
        except Exception as e:
            self.logger.error(f"Erreur analyse contenu: {e}")
            content_analysis['error'] = str(e)
        
        return content_analysis
    
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
            
            # Informations visibles
            visible_info = []
            if basic_info.get('name'):
                visible_info.append('name')
            if basic_info.get('description'):
                visible_info.append('bio')
            if basic_info.get('location'):
                visible_info.append('location')
            if basic_info.get('website'):
                visible_info.append('website')
            if basic_info.get('profile_image_url'):
                visible_info.append('profile_image')
            
            privacy_assessment['visible_information'] = visible_info
            
            # Niveau de confidentialité basé sur les paramètres
            if basic_info.get('protected', False):
                privacy_assessment['privacy_level'] = 'high'
            else:
                privacy_assessment['privacy_level'] = 'low'
            
            # Risques de confidentialité
            if basic_info.get('location'):
                privacy_assessment['privacy_risks'].append('Localisation géographique exposée')
            
            if basic_info.get('website'):
                privacy_assessment['privacy_risks'].append('Site web personnel visible')
            
            # Recommandations
            if privacy_assessment['privacy_level'] == 'low':
                privacy_assessment['recommendations'].append('Envisager de protéger les tweets')
                privacy_assessment['recommendations'].append('Réviser les informations de localisation')
                privacy_assessment['recommendations'].append('Limiter les informations personnelles dans la bio')
            
        except Exception as e:
            self.logger.error(f"Erreur évaluation confidentialité {username}: {e}")
            privacy_assessment['error'] = str(e)
        
        return privacy_assessment
    
    async def _assess_risks(self, investigation_data: Dict) -> Dict[str, Any]:
        """Évalue les risques"""
        risk_assessment = {
            'security_risks': [],
            'reputation_risks': [],
            'content_risks': [],
            'overall_risk_level': 'low'
        }
        
        try:
            profile_info = investigation_data.get('profile_info', {})
            basic_info = profile_info.get('basic_info', {})
            content_analysis = investigation_data.get('content_analysis', {})
            
            # Risques de sécurité
            if not basic_info.get('protected', False):
                risk_assessment['security_risks'].append({
                    'type': 'public_tweets',
                    'severity': 'medium',
                    'description': 'Tweets publics - toutes les publications sont visibles'
                })
            
            # Risques de réputation
            controversy_level = content_analysis.get('controversy_level', 'low')
            if controversy_level == 'high':
                risk_assessment['reputation_risks'].append({
                    'type': 'controversial_content',
                    'severity': 'medium',
                    'description': 'Contenu potentiellement controversé détecté'
                })
            
            # Risques de contenu
            topics = content_analysis.get('primary_topics', [])
            sensitive_topics = ['political', 'religious', 'crypto', 'investment']
            if any(topic in topics for topic in sensitive_topics):
                risk_assessment['content_risks'].append({
                    'type': 'sensitive_topics',
                    'severity': 'low',
                    'description': 'Discussion de sujets sensibles'
                })
            
            # Niveau de risque global
            if any(risk['severity'] == 'high' for risk in risk_assessment['security_risks']):
                risk_assessment['overall_risk_level'] = 'high'
            elif any(risk['severity'] == 'medium' for risk in risk_assessment['security_risks']):
                risk_assessment['overall_risk_level'] = 'medium'
            
        except Exception as e:
            self.logger.error(f"Erreur évaluation risques: {e}")
            risk_assessment['error'] = str(e)
        
        return risk_assessment
    
    # ============================================================================
    # MÉTHODES D'ANALYSE D'ASSISTANCE
    # ============================================================================
    
    async def _parse_tweets_api_v2(self, tweets_data: Dict) -> List[Dict]:
        """Parse les tweets de l'API v2"""
        tweets = []
        
        try:
            tweet_items = tweets_data.get('data', [])
            for tweet in tweet_items:
                public_metrics = tweet.get('public_metrics', {})
                tweet_info = {
                    'id': tweet.get('id'),
                    'text': tweet.get('text'),
                    'created_at': tweet.get('created_at'),
                    'like_count': public_metrics.get('like_count', 0),
                    'retweet_count': public_metrics.get('retweet_count', 0),
                    'reply_count': public_metrics.get('reply_count', 0),
                    'quote_count': public_metrics.get('quote_count', 0),
                    'lang': tweet.get('lang'),
                    'source': tweet.get('source'),
                    'has_media': 'media' in tweet.get('attachments', {}),
                    'hashtags': re.findall(r'#(\w+)', tweet.get('text', ''))
                }
                tweets.append(tweet_info)
            
        except Exception as e:
            self.logger.error(f"Erreur parsing tweets API v2: {e}")
        
        return tweets
    
    async def _parse_tweets_html(self, html: str) -> List[Dict]:
        """Parse les tweets depuis le HTML"""
        tweets = []
        
        try:
            # Pattern pour les tweets dans le HTML
            tweet_pattern = r'<article[^>]*data-testid="tweet"[^>]*>.*?</article>'
            tweet_matches = re.findall(tweet_pattern, html, re.DOTALL)
            
            for tweet_html in tweet_matches[:5]:  # Limiter à 5 tweets
                tweet = await self._parse_tweet_html(tweet_html)
                if tweet:
                    tweets.append(tweet)
            
        except Exception as e:
            self.logger.error(f"Erreur parsing tweets HTML: {e}")
        
        return tweets
    
    async def _parse_tweet_html(self, tweet_html: str) -> Optional[Dict]:
        """Parse un tweet individuel depuis le HTML"""
        try:
            tweet = {
                'text': '',
                'like_count': 0,
                'retweet_count': 0,
                'reply_count': 0,
                'hashtags': []
            }
            
            # Texte du tweet
            text_match = re.search(r'<div[^>]*dir="auto"[^>]*>([^<]+)</div>', tweet_html)
            if text_match:
                tweet['text'] = text_match.group(1).strip()
            
            # Likes
            likes_match = re.search(r'data-testid="like"[^>]*>.*?(\d+)', tweet_html, re.DOTALL)
            if likes_match:
                tweet['like_count'] = int(likes_match.group(1))
            
            # Retweets
            retweets_match = re.search(r'data-testid="retweet"[^>]*>.*?(\d+)', tweet_html, re.DOTALL)
            if retweets_match:
                tweet['retweet_count'] = int(retweets_match.group(1))
            
            # Réponses
            replies_match = re.search(r'data-testid="reply"[^>]*>.*?(\d+)', tweet_html, re.DOTALL)
            if replies_match:
                tweet['reply_count'] = int(replies_match.group(1))
            
            # Hashtags
            tweet['hashtags'] = re.findall(r'#(\w+)', tweet['text'])
            
            return tweet if tweet['text'] else None
            
        except Exception as e:
            self.logger.debug(f"Erreur parsing tweet HTML: {e}")
            return None
    
    async def _analyze_tweets_engagement(self, tweets: List[Dict]) -> Dict[str, Any]:
        """Analyse l'engagement des tweets"""
        engagement = {
            'average_likes': 0,
            'average_retweets': 0,
            'average_replies': 0,
            'engagement_rate': 0,
            'most_engaged_tweets': []
        }
        
        try:
            if tweets:
                total_likes = sum(tweet.get('like_count', 0) for tweet in tweets)
                total_retweets = sum(tweet.get('retweet_count', 0) for tweet in tweets)
                total_replies = sum(tweet.get('reply_count', 0) for tweet in tweets)
                
                engagement['average_likes'] = total_likes / len(tweets)
                engagement['average_retweets'] = total_retweets / len(tweets)
                engagement['average_replies'] = total_replies / len(tweets)
                
                # Tweets les plus engagés
                engagement['most_engaged_tweets'] = sorted(
                    tweets, 
                    key=lambda x: x.get('like_count', 0) + x.get('retweet_count', 0), 
                    reverse=True
                )[:3]
            
        except Exception as e:
            self.logger.error(f"Erreur analyse engagement tweets: {e}")
        
        return engagement
    
    async def _analyze_tweets_content(self, tweets: List[Dict]) -> Dict[str, Any]:
        """Analyse le contenu des tweets"""
        content_analysis = {
            'common_themes': [],
            'tweet_length_avg': 0,
            'mention_frequency': 'low',
            'link_usage': 'low'
        }
        
        try:
            if tweets:
                # Longueur moyenne des tweets
                lengths = [len(tweet.get('text', '')) for tweet in tweets]
                content_analysis['tweet_length_avg'] = sum(lengths) / len(lengths)
                
                # Fréquence des mentions
                mention_count = sum(len(re.findall(r'@(\w+)', tweet.get('text', ''))) for tweet in tweets)
                if mention_count > len(tweets) * 2:
                    content_analysis['mention_frequency'] = 'high'
                elif mention_count > len(tweets):
                    content_analysis['mention_frequency'] = 'medium'
                
                # Usage des liens
                link_count = sum(len(re.findall(r'https?://\S+', tweet.get('text', ''))) for tweet in tweets)
                if link_count > len(tweets) * 0.5:
                    content_analysis['link_usage'] = 'high'
                elif link_count > len(tweets) * 0.2:
                    content_analysis['link_usage'] = 'medium'
                
        except Exception as e:
            self.logger.error(f"Erreur analyse contenu tweets: {e}")
        
        return content_analysis
    
    async def _analyze_tweets_hashtags(self, tweets: List[Dict]) -> Dict[str, Any]:
        """Analyse les hashtags utilisés"""
        hashtag_analysis = {
            'total_hashtags': 0,
            'unique_hashtags': [],
            'most_used_hashtags': [],
            'hashtag_categories': []
        }
        
        try:
            all_hashtags = []
            for tweet in tweets:
                all_hashtags.extend(tweet.get('hashtags', []))
            
            hashtag_analysis['total_hashtags'] = len(all_hashtags)
            hashtag_analysis['unique_hashtags'] = list(set(all_hashtags))
            
            # Hashtags les plus utilisés
            from collections import Counter
            hashtag_counts = Counter(all_hashtags)
            hashtag_analysis['most_used_hashtags'] = hashtag_counts.most_common(10)
            
        except Exception as e:
            self.logger.error(f"Erreur analyse hashtags: {e}")
        
        return hashtag_analysis
    
    async def _analyze_tweets_timing(self, tweets: List[Dict]) -> Dict[str, Any]:
        """Analyse les patterns temporels des tweets"""
        timing_analysis = {
            'posting_frequency': 'unknown',
            'optimal_times': [],
            'consistency': 'low'
        }
        
        try:
            if len(tweets) >= 5:
                timing_analysis['posting_frequency'] = 'regular'
                timing_analysis['consistency'] = 'medium'
            elif len(tweets) >= 2:
                timing_analysis['posting_frequency'] = 'sporadic'
            else:
                timing_analysis['posting_frequency'] = 'inactive'
            
        except Exception as e:
            self.logger.error(f"Erreur analyse timing: {e}")
        
        return timing_analysis
    
    async def _assess_twitter_authenticity(self, followers: int, following: int, ratio: float) -> Dict[str, Any]:
        """Évalue l'authenticité du compte Twitter"""
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
    
    def _estimate_twitter_influence(self, stats: Dict) -> str:
        """Estime l'influence sur Twitter"""
        followers = stats.get('followers_count', 0)
        
        if followers > 100000:
            return 'very_high'
        elif followers > 10000:
            return 'high'
        elif followers > 1000:
            return 'medium'
        else:
            return 'low'
    
    def _extract_twitter_topics(self, text: str) -> List[str]:
        """Extrait les topics principaux"""
        topics = []
        text_lower = text.lower()
        
        topic_keywords = {
            'technology': ['tech', 'software', 'programming', 'coding', 'developer', 'ai', 'machine learning'],
            'politics': ['politics', 'government', 'election', 'policy', 'democrat', 'republican'],
            'news': ['news', 'update', 'alert', 'breaking', 'headline'],
            'sports': ['sports', 'game', 'team', 'player', 'championship'],
            'entertainment': ['movie', 'music', 'celebrity', 'film', 'show', 'entertainment'],
            'business': ['business', 'entrepreneur', 'startup', 'marketing', 'finance'],
            'crypto': ['crypto', 'bitcoin', 'blockchain', 'nft', 'defi', 'ethereum']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    async def _analyze_twitter_language(self, text: str) -> Dict[str, Any]:
        """Analyse la langue et le style"""
        language_analysis = {
            'detected_languages': [],
            'formality_level': 'neutral',
            'sentiment_trend': 'neutral'
        }
        
        try:
            # Détection basique de langue
            if any(word in text for word in ['le', 'la', 'les', 'de', 'des']):
                language_analysis['detected_languages'].append('french')
            if any(word in text for word in ['the', 'and', 'is', 'are']):
                language_analysis['detected_languages'].append('english')
            
            # Niveau de formalité
            if any(word in text for word in ['official', 'announcement', 'news']):
                language_analysis['formality_level'] = 'formal'
            elif any(word in text for word in ['lol', 'haha', 'omg']):
                language_analysis['formality_level'] = 'informal'
            
            # Sentiment basique
            positive_words = ['good', 'great', 'awesome', 'amazing', 'love', 'happy']
            negative_words = ['bad', 'terrible', 'awful', 'hate', 'angry', 'sad']
            
            positive_count = sum(1 for word in positive_words if word in text.lower())
            negative_count = sum(1 for word in negative_words if word in text.lower())
            
            if positive_count > negative_count:
                language_analysis['sentiment_trend'] = 'positive'
            elif negative_count > positive_count:
                language_analysis['sentiment_trend'] = 'negative'
            
        except Exception as e:
            self.logger.error(f"Erreur analyse langue: {e}")
        
        return language_analysis
    
    def _assess_twitter_controversy(self, text: str) -> str:
        """Évalue le niveau de controverse"""
        text_lower = text.lower()
        
        controversial_keywords = [
            'conspiracy', 'fake', 'hoax', 'scam', 'fraud',
            'extremist', 'radical', 'hate', 'illegal', 'violence'
        ]
        
        if any(keyword in text_lower for keyword in controversial_keywords):
            return 'high'
        else:
            return 'low'

# Utilisation principale
async def main():
    """Exemple d'utilisation du analyseur Twitter"""
    analyzer = TwitterIntel()
    
    # Test avec un compte exemple
    sample_username = "twitter"  # Compte officiel
    
    try:
        results = await analyzer.investigate(sample_username, depth=2)
        
        print("🐦 Analyse Twitter terminée:")
        twitter_data = results.get('twitter', {})
        
        print(f"👤 Utilisateur: {twitter_data.get('username')}")
        print(f"✅ Profil existe: {twitter_data.get('profile_info', {}).get('profile_exists', False)}")
        
        if twitter_data.get('profile_info', {}).get('profile_exists'):
            basic_info = twitter_data['profile_info']['basic_info']
            stats = twitter_data['profile_info']['statistics']
            
            print(f"📝 Nom: {basic_info.get('name', 'Non disponible')}")
            print(f"📊 Followers: {stats.get('followers_count', 0)}")
            print(f"👥 Following: {stats.get('following_count', 0)}")
            print(f"🐦 Tweets: {stats.get('tweets_count', 0)}")
            print(f"✅ Vérifié: {basic_info.get('verified', False)}")
            print(f"🔒 Protégé: {basic_info.get('protected', False)}")
            
            print(f"📈 Engagement: {twitter_data.get('engagement_analysis', {}).get('overall_engagement', 'unknown')}")
            print(f"🛡️ Confidentialité: {twitter_data.get('privacy_assessment', {}).get('privacy_level', 'unknown')}")
            print(f"⚠️ Risque global: {twitter_data.get('risk_assessment', {}).get('overall_risk_level', 'unknown')}")
        else:
            print("❌ Profil non trouvé ou inaccessible")
        
    except Exception as e:
        print(f"❌ Erreur investigation: {e}")

if __name__ == "__main__":
    asyncio.run(main())
