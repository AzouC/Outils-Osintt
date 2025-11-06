# modules/ai/analyzer.py
import asyncio
from typing import Dict, List
import numpy as np
from transformers import pipeline
import torch

class AIAnalyzer:
    def __init__(self):
        self.sentiment_analyzer = pipeline("sentiment-analysis")
        self.ner_analyzer = pipeline("ner")
        self.similarity_analyzer = None  # Charger un modèle de similarité
        
    async def analyze_investigation(self, investigation_data: Dict) -> Dict:
        """Analyse IA complète des données d'investigation"""
        return {
            'sentiment_analysis': await self._analyze_sentiment(investigation_data),
            'entity_recognition': await self._extract_entities(investigation_data),
            'behavioral_patterns': await self._analyze_behavioral_patterns(investigation_data),
            'risk_assessment': await self._assess_risk(investigation_data),
            'correlation_analysis': await self._find_ai_correlations(investigation_data)
        }
    
    async def _analyze_sentiment(self, data: Dict) -> Dict:
        """Analyse de sentiment sur le contenu textuel"""
        texts = self._extract_texts(data)
        if texts:
            sentiments = self.sentiment_analyzer(texts)
            return {
                'overall_sentiment': self._aggregate_sentiments(sentiments),
                'detailed_analysis': sentiments
            }
        return {}
    
    async def _extract_entities(self, data: Dict) -> List[Dict]:
        """Reconnaissance d'entités nommées"""
        texts = self._extract_texts(data)
        entities = []
        for text in texts:
            if len(text) > 0:
                entities.extend(self.ner_analyzer(text))
        return entities
    
    async def _analyze_behavioral_patterns(self, data: Dict) -> Dict:
        """Analyse des patterns comportementaux"""
        patterns = {
            'activity_times': await self._analyze_activity_times(data),
            'communication_patterns': await self._analyze_communication_patterns(data),
            'content_themes': await self._analyze_content_themes(data),
            'social_connectivity': await self._analyze_social_connectivity(data)
        }
        return patterns
    
    async def risk_assessment(self, data: Dict) -> Dict:
        """Évaluation automatisée des risques"""
        risk_factors = await self._identify_risk_factors(data)
        
        risk_score = sum(factor['score'] for factor in risk_factors) / len(risk_factors)
        
        return {
            'overall_risk_score': risk_score,
            'risk_level': self._determine_risk_level(risk_score),
            'risk_factors': risk_factors,
            'recommendations': await self._generate_recommendations(risk_factors)
        }
