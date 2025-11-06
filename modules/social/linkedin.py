# modules/social/linkedin.py
import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import re
import json

class LinkedInIntel:
    def __init__(self, config_manager=None):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.api_endpoints = {
            'linkedin': 'https://www.linkedin.com',
            'api': 'https://api.linkedin.com/v2',
            'mobile': 'https://www.linkedin.com/mwl'
        }
        
    async def investigate(self, profile_url: str, depth: int = 2) -> Dict[str, Any]:
        """
        Investigation d'un profil LinkedIn
        """
        self.logger.info(f"Investigation LinkedIn pour: {profile_url}")
        
        results = {
            'profile_url': profile_url,
            'username': self._extract_username(profile_url),
            'investigation_timestamp': datetime.now().isoformat(),
            'profile_info': {},
            'experience_analysis': {},
            'education_analysis': {},
            'skills_analysis': {},
            'network_analysis': {},
            'privacy_assessment': {}
        }
        
        if depth >= 1:
            results['profile_info'] = await self._get_profile_info(profile_url)
            results['privacy_assessment'] = await self._assess_privacy(profile_url, results)
        
        if depth >= 2:
            results['experience_analysis'] = await self._analyze_experience(results)
            results['education_analysis'] = await self._analyze_education(results)
            results['skills_analysis'] = await self._analyze_skills(results)
        
        if depth >= 3:
            results['network_analysis'] = await self._analyze_network(results)
            results['risk_assessment'] = await self._assess_risks(results)
            results['career_analysis'] = await self._analyze_career_patterns(results)
        
        return {'linkedin': results}
    
    def _extract_username(self, profile_url: str) -> str:
        """Extrait le nom d'utilisateur depuis l'URL"""
        try:
            # Formats d'URL LinkedIn courants
            patterns = [
                r'linkedin\.com/in/([^/?]+)',
                r'linkedin\.com/pub/([^/?]+)',
                r'linkedin\.com/company/([^/?]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, profile_url)
                if match:
                    return match.group(1)
            
            return "unknown"
        except:
            return "unknown"
    
    async def _get_profile_info(self, profile_url: str) -> Dict[str, Any]:
        """Récupère les informations du profil LinkedIn"""
        profile_info = {
            'profile_exists': False,
            'basic_info': {},
            'contact_info': {},
            'summary': {},
            'premium_status': 'none',
            'profile_completeness': 0
        }
        
        try:
            methods = [
                self._scrape_public_profile,
                self._try_mobile_version,
                self._try_api_access
            ]
            
            for method in methods:
                try:
                    info = await method(profile_url)
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
            self.logger.error(f"Erreur info profil {profile_url}: {e}")
            profile_info['error'] = str(e)
        
        return profile_info
    
    async def _scrape_public_profile(self, profile_url: str) -> Dict[str, Any]:
        """Scraping du profil public"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.8,en-US;q=0.5,en;q=0.3'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(profile_url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        return await self._parse_public_html(html, profile_url)
                    elif response.status == 999:  # LinkedIn bloque souvent
                        return {'profile_exists': True, 'access_restricted': True}
                    elif response.status == 404:
                        return {'profile_exists': False}
                    else:
                        return {'profile_exists': False, 'error': f"HTTP {response.status}"}
                        
        except Exception as e:
            self.logger.debug(f"Scraping public échoué: {e}")
            return {'profile_exists': False}
    
    async def _try_mobile_version(self, profile_url: str) -> Dict[str, Any]:
        """Essaie la version mobile"""
        try:
            mobile_url = profile_url.replace('www.linkedin.com', 'www.linkedin.com/mwl')
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(mobile_url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        return await self._parse_mobile_html(html, profile_url)
                    else:
                        return {'profile_exists': False}
                        
        except Exception as e:
            self.logger.debug(f"Version mobile échouée: {e}")
            return {'profile_exists': False}
    
    async def _try_api_access(self, profile_url: str) -> Dict[str, Any]:
        """Essaie l'accès API (nécessite token)"""
        try:
            access_token = self.config.get_api_key('linkedin', 'access_token') if self.config else None
            if not access_token:
                return {'profile_exists': False, 'error': 'No access token'}
            
            username = self._extract_username(profile_url)
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # API LinkedIn v2
            url = f"{self.api_endpoints['api']}/people/(id:{username})"
            params = {
                'projection': '(id,firstName,lastName,headline,location,industry,summary)'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return await self._parse_api_response(data, profile_url)
                    else:
                        return {'profile_exists': False}
                        
        except Exception as e:
            self.logger.debug(f"API échouée: {e}")
            return {'profile_exists': False}
    
    async def _parse_public_html(self, html: str, profile_url: str) -> Dict[str, Any]:
        """Parse le HTML public"""
        info = {
            'profile_exists': True,
            'basic_info': {},
            'scraping_method': 'public_html'
        }
        
        try:
            # Nom et titre
            name_match = re.search(r'<title[^>]*>([^<]+)</title>', html)
            if name_match:
                title_parts = name_match.group(1).split('|')[0].split('-')
                if len(title_parts) >= 2:
                    info['basic_info']['full_name'] = title_parts[0].strip()
                    info['basic_info']['headline'] = title_parts[1].strip()
            
            # Localisation
            location_match = re.search(r'"location"[^>]*>([^<]+)</span>', html)
            if location_match:
                info['basic_info']['location'] = location_match.group(1).strip()
            
            # Industrie
            industry_match = re.search(r'"industry"[^>]*>([^<]+)</span>', html)
            if industry_match:
                info['basic_info']['industry'] = industry_match.group(1).strip()
            
            # Résumé/About
            about_match = re.search(r'"summary"[^>]*>([^<]+)</p>', html, re.DOTALL)
            if about_match:
                info['basic_info']['summary'] = about_match.group(1).strip()
            
            # Expérience actuelle
            current_exp_match = re.search(r'"experience"[^>]*>([^<]+)</span>', html)
            if current_exp_match:
                info['basic_info']['current_position'] = current_exp_match.group(1).strip()
            
            # Éducation
            education_match = re.search(r'"education"[^>]*>([^<]+)</span>', html)
            if education_match:
                info['basic_info']['education'] = education_match.group(1).strip()
            
            # Vérifier si le profil est complet
            completeness_score = 0
            if info['basic_info'].get('full_name'):
                completeness_score += 20
            if info['basic_info'].get('headline'):
                completeness_score += 20
            if info['basic_info'].get('location'):
                completeness_score += 15
            if info['basic_info'].get('industry'):
                completeness_score += 15
            if info['basic_info'].get('summary'):
                completeness_score += 30
            
            info['profile_completeness'] = completeness_score
            
        except Exception as e:
            self.logger.error(f"Erreur parsing HTML public: {e}")
        
        return info
    
    async def _parse_mobile_html(self, html: str, profile_url: str) -> Dict[str, Any]:
        """Parse la version mobile"""
        info = {
            'profile_exists': True,
            'basic_info': {},
            'scraping_method': 'mobile'
        }
        
        try:
            # Nom
            name_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
            if name_match:
                info['basic_info']['full_name'] = name_match.group(1).strip()
            
            # Titre
            headline_match = re.search(r'<div[^>]*class="[^"]*headline[^"]*"[^>]*>([^<]+)</div>', html)
            if headline_match:
                info['basic_info']['headline'] = headline_match.group(1).strip()
            
            # Localisation
            location_match = re.search(r'<div[^>]*class="[^"]*location[^"]*"[^>]*>([^<]+)</div>', html)
            if location_match:
                info['basic_info']['location'] = location_match.group(1).strip()
            
        except Exception as e:
            self.logger.error(f"Erreur parsing mobile: {e}")
        
        return info
    
    async def _parse_api_response(self, data: Dict, profile_url: str) -> Dict[str, Any]:
        """Parse la réponse API"""
        info = {
            'profile_exists': True,
            'basic_info': {},
            'api_method': 'linkedin_api'
        }
        
        try:
            info['basic_info'] = {
                'id': data.get('id'),
                'first_name': data.get('firstName', {}).get('localized', {}).get('fr_FR'),
                'last_name': data.get('lastName', {}).get('localized', {}).get('fr_FR'),
                'headline': data.get('headline', {}).get('localized', {}).get('fr_FR'),
                'location': data.get('locationName'),
                'industry': data.get('industry'),
                'summary': data.get('summary', {}).get('localized', {}).get('fr_FR')
            }
            
            # Nom complet
            if info['basic_info']['first_name'] and info['basic_info']['last_name']:
                info['basic_info']['full_name'] = f"{info['basic_info']['first_name']} {info['basic_info']['last_name']}"
            
        except Exception as e:
            self.logger.error(f"Erreur parsing API: {e}")
        
        return info
    
    async def _analyze_experience(self, investigation_data: Dict) -> Dict[str, Any]:
        """Analyse l'expérience professionnelle"""
        experience_analysis = {
            'total_experience_years': 0,
            'companies_worked': [],
            'positions_held': [],
            'career_progression': {},
            'industry_expertise': [],
            'current_role': {}
        }
        
        try:
            profile_info = investigation_data.get('profile_info', {})
            basic_info = profile_info.get('basic_info', {})
            
            # Poste actuel
            if basic_info.get('current_position'):
                experience_analysis['current_role'] = {
                    'position': basic_info['current_position'],
                    'company': self._extract_company(basic_info['current_position']),
                    'status': 'current'
                }
            
            # Estimation de l'expérience basée sur le titre
            headline = basic_info.get('headline', '')
            experience_analysis['total_experience_years'] = self._estimate_experience(headline)
            
            # Compétences déduites du titre
            experience_analysis['industry_expertise'] = self._extract_expertise(headline)
            
            # Progression de carrière
            experience_analysis['career_progression'] = {
                'level': self._assess_career_level(headline),
                'seniority': self._assess_seniority(headline),
                'management_potential': self._assess_management(headline)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur analyse expérience: {e}")
            experience_analysis['error'] = str(e)
        
        return experience_analysis
    
    async def _analyze_education(self, investigation_data: Dict) -> Dict[str, Any]:
        """Analyse l'éducation et formation"""
        education_analysis = {
            'degrees': [],
            'institutions': [],
            'fields_of_study': [],
            'education_level': 'unknown',
            'certifications': []
        }
        
        try:
            profile_info = investigation_data.get('profile_info', {})
            basic_info = profile_info.get('basic_info', {})
            
            # Éducation depuis les infos basiques
            if basic_info.get('education'):
                education_analysis['institutions'].append(basic_info['education'])
                
                # Niveau d'éducation déduit
                education_analysis['education_level'] = self._infer_education_level(basic_info['education'])
                
                # Domaines d'étude
                education_analysis['fields_of_study'] = self._extract_study_fields(basic_info['education'])
            
            # Compétences liées à l'éducation
            headline = basic_info.get('headline', '')
            education_analysis['certifications'] = self._extract_certifications(headline)
            
        except Exception as e:
            self.logger.error(f"Erreur analyse éducation: {e}")
            education_analysis['error'] = str(e)
        
        return education_analysis
    
    async def _analyze_skills(self, investigation_data: Dict) -> Dict[str, Any]:
        """Analyse les compétences"""
        skills_analysis = {
            'technical_skills': [],
            'soft_skills': [],
            'industry_skills': [],
            'skill_categories': {},
            'skill_levels': {}
        }
        
        try:
            profile_info = investigation_data.get('profile_info', {})
            basic_info = profile_info.get('basic_info', {})
            
            headline = basic_info.get('headline', '')
            summary = basic_info.get('summary', '')
            
            # Extraire les compétences du titre et du résumé
            all_text = f"{headline} {summary}".lower()
            
            # Compétences techniques
            technical_keywords = [
                'python', 'java', 'javascript', 'sql', 'aws', 'azure', 'docker', 'kubernetes',
                'machine learning', 'ai', 'data science', 'analytics', 'cloud', 'devops',
                'react', 'angular', 'vue', 'node.js', 'typescript', 'php', 'ruby', 'go',
                'cybersecurity', 'network', 'infrastructure', 'database', 'api'
            ]
            
            skills_analysis['technical_skills'] = [
                skill for skill in technical_keywords if skill in all_text
            ]
            
            # Compétences générales
            soft_keywords = [
                'management', 'leadership', 'communication', 'teamwork', 'problem solving',
                'project management', 'strategy', 'innovation', 'analytical', 'creative',
                'negotiation', 'presentation', 'planning', 'organization', 'collaboration'
            ]
            
            skills_analysis['soft_skills'] = [
                skill for skill in soft_keywords if skill in all_text
            ]
            
            # Catégoriser les compétences
            skills_analysis['skill_categories'] = {
                'technical': len(skills_analysis['technical_skills']),
                'soft': len(skills_analysis['soft_skills']),
                'total': len(skills_analysis['technical_skills']) + len(skills_analysis['soft_skills'])
            }
            
        except Exception as e:
            self.logger.error(f"Erreur analyse compétences: {e}")
            skills_analysis['error'] = str(e)
        
        return skills_analysis
    
    async def _analyze_network(self, investigation_data: Dict) -> Dict[str, Any]:
        """Analyse le réseau et les connexions"""
        network_analysis = {
            'network_size': 'unknown',
            'connection_strength': 'unknown',
            'industry_connections': [],
            'geographic_reach': 'unknown',
            'influence_metrics': {}
        }
        
        try:
            profile_info = investigation_data.get('profile_info', {})
            basic_info = profile_info.get('basic_info', {})
            
            # Estimation basée sur le profil
            headline = basic_info.get('headline', '')
            industry = basic_info.get('industry', '')
            
            # Taille du réseau estimée
            if 'director' in headline.lower() or 'head' in headline.lower():
                network_analysis['network_size'] = 'large'
                network_analysis['connection_strength'] = 'strong'
            elif 'manager' in headline.lower():
                network_analysis['network_size'] = 'medium'
                network_analysis['connection_strength'] = 'medium'
            else:
                network_analysis['network_size'] = 'small'
                network_analysis['connection_strength'] = 'weak'
            
            # Portée géographique
            location = basic_info.get('location', '')
            if 'paris' in location.lower() or 'london' in location.lower() or 'new york' in location.lower():
                network_analysis['geographic_reach'] = 'global'
            elif 'france' in location.lower():
                network_analysis['geographic_reach'] = 'national'
            else:
                network_analysis['geographic_reach'] = 'local'
            
            # Métriques d'influence
            network_analysis['influence_metrics'] = {
                'estimated_influence': self._estimate_influence(headline, industry),
                'network_potential': 'medium',
                'connection_quality': 'unknown'
            }
            
        except Exception as e:
            self.logger.error(f"Erreur analyse réseau: {e}")
            network_analysis['error'] = str(e)
        
        return network_analysis
    
    async def _analyze_career_patterns(self, investigation_data: Dict) -> Dict[str, Any]:
        """Analyse les patterns de carrière"""
        career_analysis = {
            'career_trajectory': 'stable',
            'industry_mobility': 'low',
            'promotion_pace': 'normal',
            'career_ambition': 'medium',
            'market_value': 'average'
        }
        
        try:
            experience = investigation_data.get('experience_analysis', {})
            education = investigation_data.get('education_analysis', {})
            skills = investigation_data.get('skills_analysis', {})
            
            # Trajectoire de carrière
            total_experience = experience.get('total_experience_years', 0)
            career_level = experience.get('career_progression', {}).get('level', 'entry')
            
            if career_level == 'senior' and total_experience < 5:
                career_analysis['career_trajectory'] = 'fast_track'
                career_analysis['promotion_pace'] = 'fast'
            elif career_level == 'mid' and total_experience > 10:
                career_analysis['career_trajectory'] = 'slow'
                career_analysis['promotion_pace'] = 'slow'
            
            # Mobilité sectorielle
            technical_skills_count = len(skills.get('technical_skills', []))
            if technical_skills_count > 8:
                career_analysis['industry_mobility'] = 'high'
                career_analysis['market_value'] = 'high'
            elif technical_skills_count > 4:
                career_analysis['industry_mobility'] = 'medium'
                career_analysis['market_value'] = 'above_average'
            
            # Ambition de carrière
            education_level = education.get('education_level', 'unknown')
            if education_level in ['master', 'phd']:
                career_analysis['career_ambition'] = 'high'
            
        except Exception as e:
            self.logger.error(f"Erreur analyse carrière: {e}")
            career_analysis['error'] = str(e)
        
        return career_analysis
    
    async def _assess_privacy(self, profile_url: str, investigation_data: Dict) -> Dict[str, Any]:
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
            if basic_info.get('full_name'):
                visible_info.append('full_name')
            if basic_info.get('headline'):
                visible_info.append('professional_headline')
            if basic_info.get('location'):
                visible_info.append('location')
            if basic_info.get('industry'):
                visible_info.append('industry')
            if basic_info.get('summary'):
                visible_info.append('professional_summary')
            if basic_info.get('current_position'):
                visible_info.append('current_position')
            if basic_info.get('education'):
                visible_info.append('education')
            
            privacy_assessment['visible_information'] = visible_info
            
            # Niveau de confidentialité
            if len(visible_info) >= 6:
                privacy_assessment['privacy_level'] = 'low'
                privacy_assessment['privacy_risks'].append('Trop d\'informations professionnelles visibles')
            elif len(visible_info) >= 3:
                privacy_assessment['privacy_level'] = 'medium'
            else:
                privacy_assessment['privacy_level'] = 'high'
            
            # Recommandations
            if privacy_assessment['privacy_level'] in ['low', 'medium']:
                privacy_assessment['recommendations'].append('Réviser les paramètres de confidentialité LinkedIn')
                privacy_assessment['recommendations'].append('Limiter les informations de contact visibles')
                privacy_assessment['recommendations'].append('Éviter les détails trop spécifiques sur l\'emploi actuel')
            
        except Exception as e:
            self.logger.error(f"Erreur évaluation confidentialité: {e}")
            privacy_assessment['error'] = str(e)
        
        return privacy_assessment
    
    async def _assess_risks(self, investigation_data: Dict) -> Dict[str, Any]:
        """Évalue les risques professionnels et de sécurité"""
        risk_assessment = {
            'professional_risks': [],
            'security_risks': [],
            'reputation_risks': [],
            'overall_risk_level': 'low'
        }
        
        try:
            profile_info = investigation_data.get('profile_info', {})
            basic_info = profile_info.get('basic_info', {})
            privacy = investigation_data.get('privacy_assessment', {})
            
            # Risques professionnels
            if basic_info.get('current_position'):
                risk_assessment['professional_risks'].append({
                    'type': 'current_employer_exposed',
                    'severity': 'medium',
                    'description': 'Employeur actuel visible publiquement'
                })
            
            # Risques de sécurité
            if privacy.get('privacy_level') == 'low':
                risk_assessment['security_risks'].append({
                    'type': 'low_privacy_settings',
                    'severity': 'high',
                    'description': 'Paramètres de confidentialité faibles'
                })
            
            # Risques de réputation
            summary = basic_info.get('summary', '')
            if any(word in summary.lower() for word in ['confidentiel', 'secret', 'classified']):
                risk_assessment['reputation_risks'].append({
                    'type': 'sensitive_info_disclosure',
                    'severity': 'high',
                    'description': 'Informations potentiellement sensibles dans le résumé'
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
    
    def _extract_company(self, position: str) -> str:
        """Extrait le nom de l'entreprise depuis le poste"""
        try:
            # Patterns courants: "Position at Company"
            patterns = [
                r'at\s+([^|]+)',
                r'chez\s+([^|]+)',
                r'@\s+([^|]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, position, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
            
            return "Unknown"
        except:
            return "Unknown"
    
    def _estimate_experience(self, headline: str) -> int:
        """Estime l'expérience en années depuis le titre"""
        try:
            headline_lower = headline.lower()
            
            if any(word in headline_lower for word in ['junior', 'entry', 'débutant']):
                return 2
            elif any(word in headline_lower for word in ['senior', 'lead', 'principal', 'chef']):
                return 8
            elif any(word in headline_lower for word in ['manager', 'director', 'head of']):
                return 12
            elif any(word in headline_lower for word in ['vp', 'vice president', 'c-level', 'ceo']):
                return 15
            else:
                return 5  # Par défaut
        except:
            return 0
    
    def _extract_expertise(self, headline: str) -> List[str]:
        """Extrait les domaines d'expertise depuis le titre"""
        expertise = []
        headline_lower = headline.lower()
        
        domain_keywords = {
            'technology': ['tech', 'software', 'it', 'developer', 'engineer'],
            'management': ['manager', 'director', 'lead', 'head'],
            'sales': ['sales', 'business development', 'account executive'],
            'marketing': ['marketing', 'growth', 'digital marketing'],
            'finance': ['finance', 'accounting', 'cfo', 'financial'],
            'hr': ['hr', 'human resources', 'talent', 'recruitment']
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in headline_lower for keyword in keywords):
                expertise.append(domain)
        
        return expertise
    
    def _assess_career_level(self, headline: str) -> str:
        """Évalue le niveau de carrière"""
        headline_lower = headline.lower()
        
        if any(word in headline_lower for word in ['intern', 'stagiaire', 'apprentice']):
            return 'intern'
        elif any(word in headline_lower for word in ['junior', 'entry']):
            return 'entry'
        elif any(word in headline_lower for word in ['senior', 'lead', 'principal']):
            return 'senior'
        elif any(word in headline_lower for word in ['manager', 'director']):
            return 'management'
        elif any(word in headline_lower for word in ['vp', 'vice president', 'c-level', 'ceo']):
            return 'executive'
        else:
            return 'mid'
    
    def _assess_seniority(self, headline: str) -> str:
        """Évalue le niveau de séniorité"""
        level = self._assess_career_level(headline)
        
        seniority_map = {
            'intern': 'low',
            'entry': 'low',
            'mid': 'medium', 
            'senior': 'high',
            'management': 'high',
            'executive': 'very_high'
        }
        
        return seniority_map.get(level, 'medium')
    
    def _assess_management(self, headline: str) -> str:
        """Évalue le potentiel de management"""
        headline_lower = headline.lower()
        
        if any(word in headline_lower for word in ['manager', 'director', 'head of', 'team lead']):
            return 'manager'
        elif any(word in headline_lower for word in ['vp', 'vice president', 'c-level']):
            return 'executive'
        else:
            return 'individual_contributor'
    
    def _infer_education_level(self, education: str) -> str:
        """Infère le niveau d'éducation"""
        education_lower = education.lower()
        
        if any(word in education_lower for word in ['phd', 'doctorat', 'doctoral']):
            return 'phd'
        elif any(word in education_lower for word in ['master', 'msc', 'ms', 'mba']):
            return 'master'
        elif any(word in education_lower for word in ['bachelor', 'bsc', 'license', 'undergraduate']):
            return 'bachelor'
        elif any(word in education_lower for word in ['associate', 'diploma', 'certificate']):
            return 'associate'
        else:
            return 'unknown'
    
    def _extract_study_fields(self, education: str) -> List[str]:
        """Extrait les domaines d'étude"""
        fields = []
        education_lower = education.lower()
        
        field_keywords = {
            'computer_science': ['computer science', 'informatique', 'software engineering'],
            'business': ['business', 'management', 'administration', 'mba'],
            'engineering': ['engineering', 'engineer', 'ingénieur'],
            'finance': ['finance', 'accounting', 'economics'],
            'marketing': ['marketing', 'communication'],
            'science': ['science', 'physics', 'chemistry', 'biology']
        }
        
        for field, keywords in field_keywords.items():
            if any(keyword in education_lower for keyword in keywords):
                fields.append(field)
        
        return fields
    
    def _extract_certifications(self, headline: str) -> List[str]:
        """Extrait les certifications potentielles"""
        certifications = []
        headline_lower = headline.lower()
        
        cert_keywords = [
            'pmp', 'pmi', 'scrum', 'agile', 'six sigma', 'aws', 'azure',
            'google cloud', 'cisco', 'microsoft', 'oracle', 'sap'
        ]
        
        for cert in cert_keywords:
            if cert in headline_lower:
                certifications.append(cert.upper())
        
        return certifications
    
    def _estimate_influence(self, headline: str, industry: str) -> str:
        """Estime le niveau d'influence"""
        level = self._assess_career_level(headline)
        
        influence_map = {
            'intern': 'low',
            'entry': 'low',
            'mid': 'medium',
            'senior': 'high',
            'management': 'high',
            'executive': 'very_high'
        }
        
        return influence_map.get(level, 'medium')

# Utilisation principale
async def main():
    """Exemple d'utilisation du analyseur LinkedIn"""
    analyzer = LinkedInIntel()
    
    # Test avec une URL de profil exemple
    sample_profile = "https://www.linkedin.com/in/williamhgates/"
    
    try:
        results = await analyzer.investigate(sample_profile, depth=2)
        
        print("💼 Analyse LinkedIn terminée:")
        linkedin_data = results.get('linkedin', {})
        
        print(f"👤 Utilisateur: {linkedin_data.get('username')}")
        print(f"✅ Profil existe: {linkedin_data.get('profile_info', {}).get('profile_exists', False)}")
        
        if linkedin_data.get('profile_info', {}).get('profile_exists'):
            basic_info = linkedin_data['profile_info']['basic_info']
            experience = linkedin_data['experience_analysis']
            
            print(f"📝 Nom: {basic_info.get('full_name', 'Non disponible')}")
            print(f"🎯 Titre: {basic_info.get('headline', 'Non disponible')}")
            print(f"📍 Localisation: {basic_info.get('location', 'Non disponible')}")
            print(f"🏢 Industrie: {basic_info.get('industry', 'Non disponible')}")
            
            print(f"📈 Expérience: {experience.get('total_experience_years', 0)} ans")
            print(f"🎓 Niveau carrière: {experience.get('career_progression', {}).get('level', 'unknown')}")
            print(f"🛡️ Confidentialité: {linkedin_data.get('privacy_assessment', {}).get('privacy_level', 'unknown')}")
            print(f"⚠️ Risque global: {linkedin_data.get('risk_assessment', {}).get('overall_risk_level', 'unknown')}")
        else:
            print("❌ Profil non trouvé ou inaccessible")
        
    except Exception as e:
        print(f"❌ Erreur investigation: {e}")

if __name__ == "__main__":
    asyncio.run(main())
