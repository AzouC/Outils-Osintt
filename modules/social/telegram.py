# modules/social/telegram.py
import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import re
import json

class TelegramIntel:
    def __init__(self, config_manager=None):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.api_endpoints = {
            'telegram': 'https://t.me',
            'api': 'https://api.telegram.org',
            'web': 'https://web.telegram.org'
        }
        
    async def investigate(self, username: str, depth: int = 2) -> Dict[str, Any]:
        """
        Investigation d'un profil/channel Telegram
        """
        self.logger.info(f"Investigation Telegram pour: {username}")
        
        results = {
            'username': username,
            'profile_url': f"https://t.me/{username}",
            'investigation_timestamp': datetime.now().isoformat(),
            'profile_info': {},
            'channel_analysis': {},
            'group_analysis': {},
            'activity_analysis': {},
            'privacy_assessment': {}
        }
        
        if depth >= 1:
            results['profile_info'] = await self._get_profile_info(username)
            results['privacy_assessment'] = await self._assess_privacy(username, results)
        
        if depth >= 2:
            results['channel_analysis'] = await self._analyze_channel(username)
            results['activity_analysis'] = await self._analyze_activity(username, results)
        
        if depth >= 3:
            results['group_analysis'] = await self._analyze_groups(username)
            results['risk_assessment'] = await self._assess_risks(results)
            results['content_analysis'] = await self._analyze_content(results)
        
        return {'telegram': results}
    
    async def _get_profile_info(self, username: str) -> Dict[str, Any]:
        """Récupère les informations du profil Telegram"""
        profile_info = {
            'username': username,
            'profile_exists': False,
            'basic_info': {},
            'contact_info': {},
            'privacy_settings': {},
            'metadata': {}
        }
        
        try:
            methods = [
                self._scrape_web_profile,
                self._try_telegram_api,
                self._scrape_mobile_view
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
    
    async def _scrape_web_profile(self, username: str) -> Dict[str, Any]:
        """Scraping du profil via le web"""
        try:
            url = f"{self.api_endpoints['telegram']}/{username}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.8,en-US;q=0.5,en;q=0.3'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        return await self._parse_web_html(html, username)
                    elif response.status == 404:
                        return {'profile_exists': False}
                    else:
                        return {'profile_exists': False, 'error': f"HTTP {response.status}"}
                        
        except Exception as e:
            self.logger.debug(f"Scraping web échoué: {e}")
            return {'profile_exists': False}
    
    async def _try_telegram_api(self, username: str) -> Dict[str, Any]:
        """Essaie l'API Telegram (nécessite token bot)"""
        try:
            bot_token = self.config.get_api_key('telegram', 'bot_token') if self.config else None
            if not bot_token:
                return {'profile_exists': False, 'error': 'No bot token'}
            
            # Méthode getChat pour les channels/public groups
            url = f"{self.api_endpoints['api']}/bot{bot_token}/getChat"
            data = {
                'chat_id': f"@{username}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        api_data = await response.json()
                        if api_data.get('ok'):
                            return await self._parse_api_response(api_data, username)
                    else:
                        return {'profile_exists': False}
                        
        except Exception as e:
            self.logger.debug(f"API Telegram échouée: {e}")
            return {'profile_exists': False}
    
    async def _scrape_mobile_view(self, username: str) -> Dict[str, Any]:
        """Scraping via la vue mobile"""
        try:
            url = f"{self.api_endpoints['telegram']}/{username}?embed=1"
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
    
    async def _parse_web_html(self, html: str, username: str) -> Dict[str, Any]:
        """Parse le HTML web"""
        info = {
            'profile_exists': True,
            'basic_info': {},
            'scraping_method': 'web_html'
        }
        
        try:
            # Nom du profil
            name_match = re.search(r'<div[^>]*class="[^"]*tgme_page_title[^"]*"[^>]*>([^<]+)</div>', html)
            if name_match:
                info['basic_info']['title'] = name_match.group(1).strip()
            
            # Description
            desc_match = re.search(r'<div[^>]*class="[^"]*tgme_page_description[^"]*"[^>]*>([^<]+)</div>', html)
            if desc_match:
                info['basic_info']['description'] = desc_match.group(1).strip()
            
            # Nombre d'abonnés/membres
            members_match = re.search(r'<div[^>]*class="[^"]*tgme_page_extra[^"]*"[^>]*>([^<]+)</div>', html)
            if members_match:
                members_text = members_match.group(1).strip()
                info['basic_info']['members_text'] = members_text
                
                # Extraire le nombre
                numbers = re.findall(r'[\d,]+', members_text)
                if numbers:
                    info['basic_info']['members_count'] = int(numbers[0].replace(',', ''))
            
            # Image de profil
            image_match = re.search(r'<img[^>]*class="[^"]*tgme_page_photo_image[^"]*"[^>]*src="([^"]+)"', html)
            if image_match:
                info['basic_info']['profile_image'] = image_match.group(1)
            
            # Vérifier le type (channel, group, user)
            if 'channel' in html.lower():
                info['basic_info']['type'] = 'channel'
            elif 'group' in html.lower():
                info['basic_info']['type'] = 'group'
            else:
                info['basic_info']['type'] = 'user'
            
            # Vérifié
            if 'verified' in html.lower():
                info['basic_info']['verified'] = True
            
        except Exception as e:
            self.logger.error(f"Erreur parsing HTML web: {e}")
        
        return info
    
    async def _parse_api_response(self, api_data: Dict, username: str) -> Dict[str, Any]:
        """Parse la réponse de l'API"""
        info = {
            'profile_exists': True,
            'basic_info': {},
            'api_method': 'telegram_api'
        }
        
        try:
            chat_data = api_data.get('result', {})
            
            info['basic_info'] = {
                'id': chat_data.get('id'),
                'title': chat_data.get('title'),
                'username': chat_data.get('username'),
                'type': chat_data.get('type'),  # channel, group, private, etc.
                'description': chat_data.get('description'),
                'members_count': chat_data.get('members_count'),
                'verified': chat_data.get('is_verified', False),
                'restricted': chat_data.get('is_restricted', False),
                'scam': chat_data.get('is_scam', False),
                'fake': chat_data.get('is_fake', False)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur parsing API: {e}")
        
        return info
    
    async def _parse_mobile_html(self, html: str, username: str) -> Dict[str, Any]:
        """Parse le HTML mobile"""
        info = {
            'profile_exists': True,
            'basic_info': {},
            'scraping_method': 'mobile'
        }
        
        try:
            # Titre
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html)
            if title_match:
                info['basic_info']['title'] = title_match.group(1).replace('Telegram: ', '').strip()
            
            # Description
            desc_match = re.search(r'<div[^>]*class="[^"]*chat_description[^"]*"[^>]*>([^<]+)</div>', html)
            if desc_match:
                info['basic_info']['description'] = desc_match.group(1).strip()
            
        except Exception as e:
            self.logger.error(f"Erreur parsing mobile: {e}")
        
        return info
    
    async def _analyze_channel(self, username: str) -> Dict[str, Any]:
        """Analyse un channel Telegram"""
        channel_analysis = {
            'is_channel': False,
            'channel_metrics': {},
            'content_analysis': {},
            'growth_metrics': {},
            'engagement_metrics': {}
        }
        
        try:
            profile_info = await self._get_profile_info(username)
            basic_info = profile_info.get('basic_info', {})
            
            if basic_info.get('type') == 'channel':
                channel_analysis['is_channel'] = True
                
                # Métriques du channel
                channel_analysis['channel_metrics'] = {
                    'subscribers': basic_info.get('members_count', 0),
                    'verification_status': basic_info.get('verified', False),
                    'restricted': basic_info.get('restricted', False),
                    'scam_flag': basic_info.get('scam', False),
                    'fake_flag': basic_info.get('fake', False)
                }
                
                # Analyse de croissance
                channel_analysis['growth_metrics'] = await self._estimate_growth(basic_info)
                
                # Analyse d'engagement
                channel_analysis['engagement_metrics'] = await self._estimate_engagement(basic_info)
            
        except Exception as e:
            self.logger.error(f"Erreur analyse channel {username}: {e}")
            channel_analysis['error'] = str(e)
        
        return channel_analysis
    
    async def _analyze_groups(self, username: str) -> Dict[str, Any]:
        """Analyse les groupes associés"""
        group_analysis = {
            'public_groups': [],
            'estimated_group_count': 0,
            'group_types': [],
            'moderation_analysis': {}
        }
        
        try:
            # Recherche de groupes publics associés
            search_results = await self._search_related_groups(username)
            group_analysis['public_groups'] = search_results[:5]  # Limiter à 5 résultats
            
            # Estimation basée sur le profil
            profile_info = await self._get_profile_info(username)
            basic_info = profile_info.get('basic_info', {})
            
            if basic_info.get('members_count', 0) > 1000:
                group_analysis['estimated_group_count'] = 'multiple'
                group_analysis['group_types'] = ['large_community']
            elif basic_info.get('members_count', 0) > 100:
                group_analysis['estimated_group_count'] = 'few'
                group_analysis['group_types'] = ['medium_community']
            else:
                group_analysis['estimated_group_count'] = 'single'
                group_analysis['group_types'] = ['small_community']
            
            # Analyse de modération
            group_analysis['moderation_analysis'] = await self._analyze_moderation(basic_info)
            
        except Exception as e:
            self.logger.error(f"Erreur analyse groupes {username}: {e}")
            group_analysis['error'] = str(e)
        
        return group_analysis
    
    async def _analyze_activity(self, username: str, investigation_data: Dict) -> Dict[str, Any]:
        """Analyse l'activité"""
        activity_analysis = {
            'activity_level': 'unknown',
            'posting_frequency': 'unknown',
            'content_types': [],
            'temporal_patterns': {},
            'interaction_level': 'low'
        }
        
        try:
            profile_info = investigation_data.get('profile_info', {})
            basic_info = profile_info.get('basic_info', {})
            
            # Niveau d'activité basé sur les métriques
            members_count = basic_info.get('members_count', 0)
            description = basic_info.get('description', '')
            
            if members_count > 10000:
                activity_analysis['activity_level'] = 'high'
                activity_analysis['interaction_level'] = 'high'
            elif members_count > 1000:
                activity_analysis['activity_level'] = 'medium'
                activity_analysis['interaction_level'] = 'medium'
            else:
                activity_analysis['activity_level'] = 'low'
                activity_analysis['interaction_level'] = 'low'
            
            # Fréquence de publication estimée
            if 'daily' in description.lower():
                activity_analysis['posting_frequency'] = 'daily'
            elif 'weekly' in description.lower():
                activity_analysis['posting_frequency'] = 'weekly'
            elif 'monthly' in description.lower():
                activity_analysis['posting_frequency'] = 'monthly'
            else:
                activity_analysis['posting_frequency'] = 'irregular'
            
            # Types de contenu
            content_types = set()
            desc_lower = description.lower()
            
            if any(word in desc_lower for word in ['news', 'update', 'alert']):
                content_types.add('news')
            if any(word in desc_lower for word in ['media', 'video', 'photo']):
                content_types.add('media')
            if any(word in desc_lower for word in ['discussion', 'chat', 'talk']):
                content_types.add('discussion')
            if any(word in desc_lower for word in ['announcement', 'official']):
                content_types.add('announcements')
            
            activity_analysis['content_types'] = list(content_types)
            
        except Exception as e:
            self.logger.error(f"Erreur analyse activité {username}: {e}")
            activity_analysis['error'] = str(e)
        
        return activity_analysis
    
    async def _analyze_content(self, investigation_data: Dict) -> Dict[str, Any]:
        """Analyse le contenu et les topics"""
        content_analysis = {
            'primary_topics': [],
            'content_quality': 'unknown',
            'language_analysis': {},
            'sentiment_trend': 'neutral',
            'controversy_level': 'low'
        }
        
        try:
            profile_info = investigation_data.get('profile_info', {})
            basic_info = profile_info.get('basic_info', {})
            
            description = basic_info.get('description', '')
            title = basic_info.get('title', '')
            
            # Analyse des topics principaux
            all_text = f"{title} {description}".lower()
            content_analysis['primary_topics'] = self._extract_topics(all_text)
            
            # Qualité du contenu
            content_analysis['content_quality'] = self._assess_content_quality(description)
            
            # Analyse de langue
            content_analysis['language_analysis'] = await self._analyze_language(all_text)
            
            # Niveau de controverse
            content_analysis['controversy_level'] = self._assess_controversy(all_text)
            
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
            if basic_info.get('title'):
                visible_info.append('profile_title')
            if basic_info.get('description'):
                visible_info.append('profile_description')
            if basic_info.get('profile_image'):
                visible_info.append('profile_image')
            if basic_info.get('members_count'):
                visible_info.append('members_count')
            if basic_info.get('verified'):
                visible_info.append('verification_status')
            
            privacy_assessment['visible_information'] = visible_info
            
            # Niveau de confidentialité
            profile_type = basic_info.get('type', 'user')
            
            if profile_type == 'channel' and len(visible_info) >= 3:
                privacy_assessment['privacy_level'] = 'low'
            elif profile_type == 'group' and len(visible_info) >= 2:
                privacy_assessment['privacy_level'] = 'medium'
            else:
                privacy_assessment['privacy_level'] = 'high'
            
            # Risques de confidentialité
            if basic_info.get('members_count', 0) > 10000:
                privacy_assessment['privacy_risks'].append('Large audience - high visibility')
            
            if basic_info.get('verified'):
                privacy_assessment['privacy_risks'].append('Verified account - higher trust but more exposure')
            
            # Recommandations
            if privacy_assessment['privacy_level'] in ['low', 'medium']:
                privacy_assessment['recommendations'].append('Review description for personal information')
                privacy_assessment['recommendations'].append('Consider making group private if sensitive')
                privacy_assessment['recommendations'].append('Regularly audit shared content')
            
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
            if basic_info.get('scam', False):
                risk_assessment['security_risks'].append({
                    'type': 'scam_account',
                    'severity': 'high',
                    'description': 'Compte marqué comme arnaque'
                })
            
            if basic_info.get('fake', False):
                risk_assessment['security_risks'].append({
                    'type': 'fake_account',
                    'severity': 'high',
                    'description': 'Compte marqué comme faux'
                })
            
            if basic_info.get('restricted', False):
                risk_assessment['security_risks'].append({
                    'type': 'restricted_account',
                    'severity': 'medium',
                    'description': 'Compte restreint par Telegram'
                })
            
            # Risques de réputation
            controversy_level = content_analysis.get('controversy_level', 'low')
            if controversy_level == 'high':
                risk_assessment['reputation_risks'].append({
                    'type': 'controversial_content',
                    'severity': 'medium',
                    'description': 'Contenu potentiellement controversé'
                })
            
            # Risques de contenu
            topics = content_analysis.get('primary_topics', [])
            sensitive_topics = ['crypto', 'investment', 'money', 'political', 'religious']
            if any(topic in topics for topic in sensitive_topics):
                risk_assessment['content_risks'].append({
                    'type': 'sensitive_topics',
                    'severity': 'medium',
                    'description': 'Discussion de sujets sensibles'
                })
            
            # Niveau de risque global
            high_risks = sum(1 for risk in risk_assessment['security_risks'] if risk['severity'] == 'high')
            if high_risks > 0:
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
    
    async def _search_related_groups(self, username: str) -> List[Dict]:
        """Recherche des groupes associés"""
        related_groups = []
        
        try:
            # Recherche basique par similarité de nom
            search_terms = [
                username,
                username.replace('_', ''),
                username.split('_')[0] if '_' in username else username
            ]
            
            for term in search_terms:
                # Simulation de recherche - en pratique, utiliserait une API de recherche
                if len(term) > 3:
                    related_groups.append({
                        'name': f"{term}_group",
                        'type': 'possible_related',
                        'confidence': 'low'
                    })
            
        except Exception as e:
            self.logger.error(f"Erreur recherche groupes: {e}")
        
        return related_groups
    
    async def _estimate_growth(self, basic_info: Dict) -> Dict[str, Any]:
        """Estime la croissance du channel"""
        growth_metrics = {
            'growth_trend': 'stable',
            'estimated_growth_rate': 'medium',
            'popularity_level': 'unknown'
        }
        
        try:
            members_count = basic_info.get('members_count', 0)
            
            if members_count > 100000:
                growth_metrics['popularity_level'] = 'very_high'
                growth_metrics['growth_trend'] = 'rapid'
            elif members_count > 10000:
                growth_metrics['popularity_level'] = 'high'
                growth_metrics['growth_trend'] = 'growing'
            elif members_count > 1000:
                growth_metrics['popularity_level'] = 'medium'
                growth_metrics['growth_trend'] = 'stable'
            else:
                growth_metrics['popularity_level'] = 'low'
                growth_metrics['growth_trend'] = 'slow'
            
        except Exception as e:
            self.logger.error(f"Erreur estimation croissance: {e}")
        
        return growth_metrics
    
    async def _estimate_engagement(self, basic_info: Dict) -> Dict[str, Any]:
        """Estime l'engagement"""
        engagement_metrics = {
            'engagement_level': 'low',
            'interaction_quality': 'unknown',
            'community_health': 'good'
        }
        
        try:
            members_count = basic_info.get('members_count', 0)
            description = basic_info.get('description', '')
            
            if members_count > 50000:
                engagement_metrics['engagement_level'] = 'high'
            elif members_count > 5000:
                engagement_metrics['engagement_level'] = 'medium'
            else:
                engagement_metrics['engagement_level'] = 'low'
            
            # Qualité des interactions basée sur la description
            if any(word in description.lower() for word in ['discussion', 'chat', 'q&a', 'questions']):
                engagement_metrics['interaction_quality'] = 'high'
            else:
                engagement_metrics['interaction_quality'] = 'low'
            
        except Exception as e:
            self.logger.error(f"Erreur estimation engagement: {e}")
        
        return engagement_metrics
    
    async def _analyze_moderation(self, basic_info: Dict) -> Dict[str, Any]:
        """Analyse la modération"""
        moderation_analysis = {
            'moderation_level': 'unknown',
            'content_controls': [],
            'safety_measures': 'basic'
        }
        
        try:
            description = basic_info.get('description', '').lower()
            
            if any(word in description for word in ['rules', 'guidelines', 'moderated']):
                moderation_analysis['moderation_level'] = 'high'
                moderation_analysis['content_controls'].append('explicit_rules')
            else:
                moderation_analysis['moderation_level'] = 'low'
            
            if any(word in description for word in ['report', 'abuse', 'block']):
                moderation_analysis['safety_measures'] = 'advanced'
                moderation_analysis['content_controls'].append('reporting_system')
            
        except Exception as e:
            self.logger.error(f"Erreur analyse modération: {e}")
        
        return moderation_analysis
    
    async def _analyze_language(self, text: str) -> Dict[str, Any]:
        """Analyse la langue et le style"""
        language_analysis = {
            'detected_languages': [],
            'formality_level': 'neutral',
            'readability_score': 0
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
            elif any(word in text for word in ['chat', 'discuss', 'talk']):
                language_analysis['formality_level'] = 'informal'
            
            # Score de lisibilité basique
            word_count = len(text.split())
            if word_count > 50:
                language_analysis['readability_score'] = 80
            elif word_count > 20:
                language_analysis['readability_score'] = 60
            else:
                language_analysis['readability_score'] = 40
            
        except Exception as e:
            self.logger.error(f"Erreur analyse langue: {e}")
        
        return language_analysis
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extrait les topics principaux"""
        topics = []
        text_lower = text.lower()
        
        topic_keywords = {
            'technology': ['tech', 'software', 'programming', 'coding', 'developer'],
            'crypto': ['crypto', 'bitcoin', 'blockchain', 'nft', 'defi'],
            'news': ['news', 'update', 'alert', 'breaking'],
            'education': ['learn', 'tutorial', 'course', 'education'],
            'entertainment': ['fun', 'meme', 'humor', 'entertainment'],
            'business': ['business', 'entrepreneur', 'startup', 'marketing'],
            'politics': ['politics', 'government', 'election', 'policy']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def _assess_content_quality(self, description: str) -> str:
        """Évalue la qualité du contenu"""
        if not description:
            return 'unknown'
        
        desc_lower = description.lower()
        
        if len(description) < 10:
            return 'low'
        elif any(word in desc_lower for word in ['official', 'verified', 'trusted']):
            return 'high'
        elif any(word in desc_lower for word in ['news', 'update', 'information']):
            return 'medium'
        else:
            return 'low'
    
    def _assess_controversy(self, text: str) -> str:
        """Évalue le niveau de controverse"""
        text_lower = text.lower()
        
        controversial_keywords = [
            'conspiracy', 'fake', 'hoax', 'scam', 'fraud',
            'extremist', 'radical', 'hate', 'illegal'
        ]
        
        if any(keyword in text_lower for keyword in controversial_keywords):
            return 'high'
        else:
            return 'low'

# Utilisation principale
async def main():
    """Exemple d'utilisation du analyseur Telegram"""
    analyzer = TelegramIntel()
    
    # Test avec un channel exemple
    sample_username = "telegram"  # Channel officiel
    
    try:
        results = await analyzer.investigate(sample_username, depth=2)
        
        print("📱 Analyse Telegram terminée:")
        tg_data = results.get('telegram', {})
        
        print(f"👤 Utilisateur: {tg_data.get('username')}")
        print(f"✅ Profil existe: {tg_data.get('profile_info', {}).get('profile_exists', False)}")
        
        if tg_data.get('profile_info', {}).get('profile_exists'):
            basic_info = tg_data['profile_info']['basic_info']
            channel_analysis = tg_data['channel_analysis']
            
            print(f"📝 Titre: {basic_info.get('title', 'Non disponible')}")
            print(f"📋 Type: {basic_info.get('type', 'unknown')}")
            print(f"👥 Membres: {basic_info.get('members_count', 'Non disponible')}")
            print(f"✅ Vérifié: {basic_info.get('verified', False)}")
            
            print(f"📈 Est. channel: {channel_analysis.get('is_channel', False)}")
            print(f"📊 Niveau activité: {tg_data.get('activity_analysis', {}).get('activity_level', 'unknown')}")
            print(f"🛡️ Confidentialité: {tg_data.get('privacy_assessment', {}).get('privacy_level', 'unknown')}")
            print(f"⚠️ Risque global: {tg_data.get('risk_assessment', {}).get('overall_risk_level', 'unknown')}")
        else:
            print("❌ Profil non trouvé ou inaccessible")
        
    except Exception as e:
        print(f"❌ Erreur investigation: {e}")

if __name__ == "__main__":
    asyncio.run(main())
