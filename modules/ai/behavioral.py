# modules/ai/behavioral.py
import asyncio
from typing import Dict, List, Any
from datetime import datetime, timedelta
import logging
import numpy as np
from collections import Counter, defaultdict

class BehavioralAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    async def analyze_behavioral_patterns(self, investigation_data: Dict) -> Dict[str, Any]:
        """
        Analyse les patterns comportementaux à partir des données d'investigation
        """
        self.logger.info("Début de l'analyse comportementale")
        
        return {
            'activity_patterns': await self._analyze_activity_patterns(investigation_data),
            'communication_style': await self._analyze_communication_style(investigation_data),
            'social_behavior': await self._analyze_social_behavior(investigation_data),
            'content_preferences': await self._analyze_content_preferences(investigation_data),
            'temporal_patterns': await self._analyze_temporal_patterns(investigation_data),
            'risk_indicators': await self._identify_risk_indicators(investigation_data),
            'behavioral_score': await self._calculate_behavioral_score(investigation_data)
        }
    
    async def _analyze_activity_patterns(self, data: Dict) -> Dict[str, Any]:
        """Analyse les patterns d'activité"""
        patterns = {
            'activity_level': 'medium',  # low, medium, high
            'peak_hours': [],
            'consistency_score': 0.0,
            'platform_diversity': 0,
            'engagement_frequency': 'regular'  # sporadic, regular, frequent
        }
        
        # Analyse de la fréquence des posts
        if 'modules' in data:
            post_counts = self._extract_post_counts(data)
            if post_counts:
                patterns['activity_level'] = self._assess_activity_level(post_counts)
                patterns['consistency_score'] = self._calculate_consistency(post_counts)
        
        # Diversité des plateformes
        platforms = self._extract_platforms(data)
        patterns['platform_diversity'] = len(platforms)
        
        # Heures de pic d'activité
        time_data = self._extract_timestamps(data)
        if time_data:
            patterns['peak_hours'] = self._find_peak_hours(time_data)
            patterns['engagement_frequency'] = self._assess_engagement_frequency(time_data)
        
        return patterns
    
    async def _analyze_communication_style(self, data: Dict) -> Dict[str, Any]:
        """Analyse le style de communication"""
        style = {
            'formality_level': 'neutral',  # casual, neutral, formal
            'vocabulary_complexity': 'medium',
            'emoji_usage': 'low',
            'response_time': 'variable',
            'interaction_pattern': 'balanced'  # listener, balanced, broadcaster
        }
        
        # Extraction du contenu textuel
        texts = self._extract_text_content(data)
        if texts:
            style['formality_level'] = self._assess_formality(texts)
            style['vocabulary_complexity'] = self._assess_vocabulary_complexity(texts)
            style['emoji_usage'] = self._assess_emoji_usage(texts)
        
        # Patterns d'interaction
        interaction_data = self._extract_interaction_patterns(data)
        if interaction_data:
            style['interaction_pattern'] = self._assess_interaction_pattern(interaction_data)
        
        return style
    
    async def _analyze_social_behavior(self, data: Dict) -> Dict[str, Any]:
        """Analyse le comportement social"""
        behavior = {
            'network_size': 'medium',
            'influence_score': 0.0,
            'community_engagement': 'moderate',
            'relationship_diversity': 'balanced',
            'social_connectivity': 'normal'
        }
        
        # Analyse du réseau social
        network_data = self._extract_network_info(data)
        if network_data:
            behavior['network_size'] = self._assess_network_size(network_data)
            behavior['influence_score'] = self._calculate_influence_score(network_data)
            behavior['social_connectivity'] = self._assess_connectivity(network_data)
        
        # Engagement communautaire
        engagement_data = self._extract_engagement_metrics(data)
        if engagement_data:
            behavior['community_engagement'] = self._assess_community_engagement(engagement_data)
        
        return behavior
    
    async def _analyze_content_preferences(self, data: Dict) -> Dict[str, Any]:
        """Analyse les préférences de contenu"""
        preferences = {
            'content_types': [],
            'topics_of_interest': [],
            'sentiment_trend': 'neutral',
            'controversy_level': 'low',
            'content_quality': 'medium'
        }
        
        # Types de contenu
        content_data = self._extract_content_types(data)
        if content_data:
            preferences['content_types'] = self._identify_content_types(content_data)
            preferences['topics_of_interest'] = self._extract_topics(content_data)
        
        # Analyse de sentiment
        sentiment_data = self._extract_sentiment_data(data)
        if sentiment_data:
            preferences['sentiment_trend'] = self._analyze_sentiment_trend(sentiment_data)
            preferences['controversy_level'] = self._assess_controversy(sentiment_data)
        
        return preferences
    
    async def _analyze_temporal_patterns(self, data: Dict) -> Dict[str, Any]:
        """Analyse les patterns temporels"""
        temporal = {
            'daily_rhythm': 'standard',
            'weekly_pattern': 'consistent',
            'seasonal_activity': 'stable',
            'response_timing': 'average',
            'online_presence': 'moderate'
        }
        
        time_data = self._extract_detailed_timestamps(data)
        if time_data:
            temporal['daily_rhythm'] = self._analyze_daily_patterns(time_data)
            temporal['weekly_pattern'] = self._analyze_weekly_patterns(time_data)
            temporal['online_presence'] = self._assess_online_presence(time_data)
        
        return temporal
    
    async def _identify_risk_indicators(self, data: Dict) -> List[Dict[str, Any]]:
        """Identifie les indicateurs de risque comportemental"""
        risk_indicators = []
        
        # Vérification des patterns suspects
        patterns = await self._analyze_activity_patterns(data)
        style = await self._analyze_communication_style(data)
        behavior = await self._analyze_social_behavior(data)
        
        # Indicateur 1: Activité anormale
        if patterns['activity_level'] == 'high' and patterns['consistency_score'] < 0.3:
            risk_indicators.append({
                'type': 'suspicious_activity',
                'level': 'medium',
                'description': 'Activité élevée mais incohérente - possible comportement automatisé',
                'confidence': 0.7
            })
        
        # Indicateur 2: Réseau social suspect
        if behavior['network_size'] == 'very_large' and behavior['influence_score'] < 0.2:
            risk_indicators.append({
                'type': 'suspicious_network',
                'level': 'low',
                'description': 'Grand réseau mais faible engagement - possible faux comptes',
                'confidence': 0.6
            })
        
        # Indicateur 3: Pattern temporel anormal
        temporal = await self._analyze_temporal_patterns(data)
        if temporal['daily_rhythm'] == 'nocturnal' and patterns['activity_level'] == 'high':
            risk_indicators.append({
                'type': 'unusual_timing',
                'level': 'medium',
                'description': 'Activité principalement nocturne avec volume élevé',
                'confidence': 0.65
            })
        
        # Indicateur 4: Style de communication incohérent
        if style['formality_level'] == 'mixed' and style['vocabulary_complexity'] == 'highly_variable':
            risk_indicators.append({
                'type': 'inconsistent_communication',
                'level': 'low',
                'description': 'Style de communication incohérent - possible multiple auteurs',
                'confidence': 0.55
            })
        
        return risk_indicators
    
    async def _calculate_behavioral_score(self, data: Dict) -> Dict[str, Any]:
        """Calcule un score comportemental global"""
        score_components = {}
        
        try:
            # Score d'activité (0-100)
            patterns = await self._analyze_activity_patterns(data)
            activity_score = self._calculate_activity_score(patterns)
            
            # Score social (0-100)
            behavior = await self._analyze_social_behavior(data)
            social_score = self._calculate_social_score(behavior)
            
            # Score de cohérence (0-100)
            consistency_score = self._calculate_consistency_score(data)
            
            # Score global pondéré
            overall_score = (
                activity_score * 0.3 +
                social_score * 0.4 +
                consistency_score * 0.3
            )
            
            score_components = {
                'overall_score': round(overall_score, 2),
                'activity_score': round(activity_score, 2),
                'social_score': round(social_score, 2),
                'consistency_score': round(consistency_score, 2),
                'risk_level': self._determine_risk_level(overall_score),
                'authenticity_confidence': self._calculate_authenticity_confidence(data)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur calcul score comportemental: {e}")
            score_components = {
                'overall_score': 50.0,
                'activity_score': 50.0,
                'social_score': 50.0,
                'consistency_score': 50.0,
                'risk_level': 'unknown',
                'authenticity_confidence': 0.5
            }
        
        return score_components
    
    # ============================================================================
    # MÉTHODES D'EXTRACTION DE DONNÉES (À IMPLÉMENTER)
    # ============================================================================
    
    def _extract_post_counts(self, data: Dict) -> List[int]:
        """Extrait le nombre de posts par période"""
        # Implémentation basique
        post_counts = []
        if 'modules' in data:
            for module_data in data['modules'].values():
                if isinstance(module_data, dict) and 'posts' in module_data:
                    post_counts.append(len(module_data['posts']))
        return post_counts if post_counts else [0]
    
    def _extract_platforms(self, data: Dict) -> List[str]:
        """Extrait la liste des plateformes utilisées"""
        platforms = []
        if 'modules' in data:
            platforms = list(data['modules'].keys())
        return platforms
    
    def _extract_timestamps(self, data: Dict) -> List[datetime]:
        """Extrait les horodatages des activités"""
        timestamps = []
        # Implémentation simplifiée
        return timestamps
    
    def _extract_text_content(self, data: Dict) -> List[str]:
        """Extrait le contenu textuel"""
        texts = []
        # Implémentation simplifiée
        return texts
    
    def _extract_interaction_patterns(self, data: Dict) -> Dict[str, Any]:
        """Extrait les patterns d'interaction"""
        return {}
    
    def _extract_network_info(self, data: Dict) -> Dict[str, Any]:
        """Extrait les informations du réseau social"""
        return {}
    
    def _extract_engagement_metrics(self, data: Dict) -> Dict[str, Any]:
        """Extrait les métriques d'engagement"""
        return {}
    
    def _extract_content_types(self, data: Dict) -> List[str]:
        """Extrait les types de contenu"""
        return []
    
    def _extract_sentiment_data(self, data: Dict) -> List[float]:
        """Extrait les données de sentiment"""
        return []
    
    def _extract_detailed_timestamps(self, data: Dict) -> List[datetime]:
        """Extrait les horodatages détaillés"""
        return []
    
    # ============================================================================
    # MÉTHODES D'ANALYSE (À IMPLÉMENTER)
    # ============================================================================
    
    def _assess_activity_level(self, post_counts: List[int]) -> str:
        """Évalue le niveau d'activité"""
        avg_posts = np.mean(post_counts) if post_counts else 0
        if avg_posts > 10:
            return 'high'
        elif avg_posts > 3:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_consistency(self, post_counts: List[int]) -> float:
        """Calcule le score de cohérence"""
        if len(post_counts) < 2:
            return 0.5
        return float(np.std(post_counts) / (np.mean(post_counts) + 1e-6))
    
    def _find_peak_hours(self, timestamps: List[datetime]) -> List[int]:
        """Trouve les heures de pic d'activité"""
        if not timestamps:
            return []
        hours = [ts.hour for ts in timestamps]
        hour_counts = Counter(hours)
        return [hour for hour, count in hour_counts.most_common(3)]
    
    def _assess_engagement_frequency(self, timestamps: List[datetime]) -> str:
        """Évalue la fréquence d'engagement"""
        if len(timestamps) < 2:
            return 'sporadic'
        
        time_diffs = []
        for i in range(1, len(timestamps)):
            diff = (timestamps[i] - timestamps[i-1]).total_seconds() / 3600  # en heures
            time_diffs.append(diff)
        
        avg_diff = np.mean(time_diffs)
        if avg_diff < 2:
            return 'frequent'
        elif avg_diff < 24:
            return 'regular'
        else:
            return 'sporadic'
    
    def _assess_formality(self, texts: List[str]) -> str:
        """Évalue le niveau de formalité"""
        # Implémentation simplifiée
        return 'neutral'
    
    def _assess_vocabulary_complexity(self, texts: List[str]) -> str:
        """Évalue la complexité du vocabulaire"""
        return 'medium'
    
    def _assess_emoji_usage(self, texts: List[str]) -> str:
        """Évalue l'utilisation d'emojis"""
        return 'low'
    
    def _assess_interaction_pattern(self, interaction_data: Dict) -> str:
        """Évalue le pattern d'interaction"""
        return 'balanced'
    
    def _assess_network_size(self, network_data: Dict) -> str:
        """Évalue la taille du réseau"""
        return 'medium'
    
    def _calculate_influence_score(self, network_data: Dict) -> float:
        """Calcule le score d'influence"""
        return 0.5
    
    def _assess_connectivity(self, network_data: Dict) -> str:
        """Évalue la connectivité sociale"""
        return 'normal'
    
    def _assess_community_engagement(self, engagement_data: Dict) -> str:
        """Évalue l'engagement communautaire"""
        return 'moderate'
    
    def _identify_content_types(self, content_data: List[str]) -> List[str]:
        """Identifie les types de contenu"""
        return ['text', 'images']
    
    def _extract_topics(self, content_data: List[str]) -> List[str]:
        """Extrait les sujets d'intérêt"""
        return ['technology', 'news']
    
    def _analyze_sentiment_trend(self, sentiment_data: List[float]) -> str:
        """Analyse la tendance de sentiment"""
        return 'neutral'
    
    def _assess_controversy(self, sentiment_data: List[float]) -> str:
        """Évalue le niveau de controverse"""
        return 'low'
    
    def _analyze_daily_patterns(self, time_data: List[datetime]) -> str:
        """Analyse les patterns quotidiens"""
        return 'standard'
    
    def _analyze_weekly_patterns(self, time_data: List[datetime]) -> str:
        """Analyse les patterns hebdomadaires"""
        return 'consistent'
    
    def _assess_online_presence(self, time_data: List[datetime]) -> str:
        """Évalue la présence en ligne"""
        return 'moderate'
    
    def _calculate_activity_score(self, patterns: Dict) -> float:
        """Calcule le score d'activité"""
        return 75.0
    
    def _calculate_social_score(self, behavior: Dict) -> float:
        """Calcule le score social"""
        return 65.0
    
    def _calculate_consistency_score(self, data: Dict) -> float:
        """Calcule le score de cohérence"""
        return 70.0
    
    def _determine_risk_level(self, overall_score: float) -> str:
        """Détermine le niveau de risque"""
        if overall_score > 80:
            return 'low'
        elif overall_score > 60:
            return 'medium'
        elif overall_score > 40:
            return 'high'
        else:
            return 'very_high'
    
    def _calculate_authenticity_confidence(self, data: Dict) -> float:
        """Calcule la confiance d'authenticité"""
        return 0.8

# Utilisation principale
async def main():
    """Exemple d'utilisation"""
    analyzer = BehavioralAnalyzer()
    
    # Données d'exemple
    sample_data = {
        'modules': {
            'twitter': {
                'posts': ['Post 1', 'Post 2'],
                'followers': 1500
            },
            'instagram': {
                'posts': ['Photo 1'],
                'followers': 800
            }
        }
    }
    
    results = await analyzer.analyze_behavioral_patterns(sample_data)
    print("Analyse comportementale terminée:")
    print(results)

if __name__ == "__main__":
    asyncio.run(main())
