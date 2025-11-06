# modules/blockchain/crypto_tracker.py
import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import hashlib

class CryptoTracker:
    def __init__(self, config_manager=None):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.api_endpoints = self._setup_endpoints()
        
    def _setup_endpoints(self) -> Dict[str, str]:
        """Configure les endpoints API"""
        return {
            'blockchain_com': 'https://blockchain.info',
            'blockcypher': 'https://api.blockcypher.com/v1',
            'etherscan': 'https://api.etherscan.io/api',
            'blockexplorer': 'https://blockexplorer.com/api',
            'cryptocompare': 'https://min-api.cryptocompare.com',
            'whale_alert': 'https://api.whale-alert.io/v1'
        }
    
    async def investigate(self, address: str, depth: int = 2) -> Dict[str, Any]:
        """
        Investigation complète d'une adresse crypto
        """
        self.logger.info(f"Investigation crypto pour: {address}")
        
        results = {
            'address': address,
            'address_type': await self._identify_address_type(address),
            'investigation_timestamp': datetime.now().isoformat(),
            'basic_info': {},
            'transactions': {},
            'balance_analysis': {},
            'risk_assessment': {},
            'entity_clustering': {},
            'monitoring_alerts': {}
        }
        
        if depth >= 1:
            results['basic_info'] = await self._get_basic_info(address)
            results['balance_analysis'] = await self._analyze_balances(address)
        
        if depth >= 2:
            results['transactions'] = await self._analyze_transactions(address, depth)
            results['risk_assessment'] = await self._assess_risk(address, results)
        
        if depth >= 3:
            results['entity_clustering'] = await self._cluster_analysis(address, results)
            results['monitoring_alerts'] = await self._setup_monitoring(address)
            results['predictive_analysis'] = await self._predictive_analysis(results)
        
        return {'crypto_tracker': results}
    
    async def _identify_address_type(self, address: str) -> Dict[str, str]:
        """Identifie le type d'adresse crypto"""
        address_lower = address.lower()
        
        # Bitcoin
        if (address_lower.startswith('1') or 
            address_lower.startswith('3') or 
            address_lower.startswith('bc1')):
            return {
                'currency': 'bitcoin',
                'type': self._detect_btc_address_type(address),
                'network': 'mainnet'
            }
        
        # Ethereum
        elif address_lower.startswith('0x') and len(address) == 42:
            return {
                'currency': 'ethereum',
                'type': 'address',
                'network': 'mainnet'
            }
        
        # Litecoin
        elif (address_lower.startswith('l') or 
              address_lower.startswith('m') or 
              address_lower.startswith('3')):
            return {
                'currency': 'litecoin', 
                'type': 'address',
                'network': 'mainnet'
            }
        
        # Autres
        else:
            return {
                'currency': 'unknown',
                'type': 'unknown',
                'network': 'unknown'
            }
    
    def _detect_btc_address_type(self, address: str) -> str:
        """Détecte le type d'adresse Bitcoin"""
        if address.startswith('1'):
            return 'p2pkh'  # Pay to Public Key Hash
        elif address.startswith('3'):
            return 'p2sh'   # Pay to Script Hash
        elif address.startswith('bc1'):
            return 'p2wpkh' # Pay to Witness Public Key Hash
        else:
            return 'unknown'
    
    async def _get_basic_info(self, address: str) -> Dict[str, Any]:
        """Récupère les informations basiques"""
        info = {
            'address': address,
            'first_seen': None,
            'last_activity': None,
            'total_received': 0,
            'total_sent': 0,
            'current_balance': 0,
            'transaction_count': 0
        }
        
        try:
            # Essayer différentes APIs
            address_type = await self._identify_address_type(address)
            currency = address_type.get('currency')
            
            if currency == 'bitcoin':
                btc_info = await self._get_btc_info(address)
                info.update(btc_info)
            elif currency == 'ethereum':
                eth_info = await self._get_eth_info(address)
                info.update(eth_info)
            else:
                # Fallback générique
                generic_info = await self._get_generic_info(address)
                info.update(generic_info)
                
        except Exception as e:
            self.logger.error(f"Erreur info basique {address}: {e}")
            info['error'] = str(e)
        
        return info
    
    async def _get_btc_info(self, address: str) -> Dict[str, Any]:
        """Récupère les infos Bitcoin"""
        try:
            async with aiohttp.ClientSession() as session:
                # API Blockchain.com
                url = f"{self.api_endpoints['blockchain_com']}/rawaddr/{address}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'first_seen': datetime.fromtimestamp(data.get('first_seen', 0)).isoformat() if data.get('first_seen') else None,
                            'last_activity': datetime.fromtimestamp(data.get('last_seen', 0)).isoformat() if data.get('last_seen') else None,
                            'total_received': data.get('total_received', 0),
                            'total_sent': data.get('total_sent', 0),
                            'current_balance': data.get('final_balance', 0),
                            'transaction_count': data.get('n_tx', 0),
                            'data_source': 'blockchain.com'
                        }
                    else:
                        return {'error': f"API error: {response.status}"}
        except Exception as e:
            self.logger.error(f"Erreur BTC info {address}: {e}")
            return {'error': str(e)}
    
    async def _get_eth_info(self, address: str) -> Dict[str, Any]:
        """Récupère les infos Ethereum"""
        try:
            api_key = self.config.get_api_key('blockchain', 'etherscan_api') if self.config else None
            
            async with aiohttp.ClientSession() as session:
                # API Etherscan
                url = f"{self.api_endpoints['etherscan']}"
                params = {
                    'module': 'account',
                    'action': 'balance',
                    'address': address,
                    'tag': 'latest',
                    'apikey': api_key or 'freekey'
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        balance = int(data.get('result', 0)) / 10**18  # Conversion wei to ETH
                        
                        return {
                            'current_balance': balance,
                            'data_source': 'etherscan',
                            'currency': 'ETH'
                        }
                    else:
                        return {'error': f"API error: {response.status}"}
        except Exception as e:
            self.logger.error(f"Erreur ETH info {address}: {e}")
            return {'error': str(e)}
    
    async def _get_generic_info(self, address: str) -> Dict[str, Any]:
        """Récupère des infos génériques via BlockCypher"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_endpoints['blockcypher']}/btc/main/addrs/{address}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'current_balance': data.get('final_balance', 0),
                            'total_received': data.get('total_received', 0),
                            'transaction_count': data.get('n_tx', 0),
                            'data_source': 'blockcypher'
                        }
                    else:
                        return {'error': f"API error: {response.status}"}
        except Exception as e:
            self.logger.error(f"Erreur info générique {address}: {e}")
            return {'error': str(e)}
    
    async def _analyze_balances(self, address: str) -> Dict[str, Any]:
        """Analyse les balances et l'historique"""
        analysis = {
            'current_balance': 0,
            'balance_history': [],
            'wealth_estimation': {},
            'activity_level': 'low',
            'balance_trend': 'stable'
        }
        
        try:
            address_type = await self._identify_address_type(address)
            currency = address_type.get('currency')
            
            if currency == 'bitcoin':
                # Récupérer l'historique des balances
                async with aiohttp.ClientSession() as session:
                    url = f"{self.api_endpoints['blockchain_com']}/rawaddr/{address}"
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            balance = data.get('final_balance', 0) / 10**8  # Conversion satoshis to BTC
                            
                            analysis['current_balance'] = balance
                            analysis['wealth_estimation'] = await self._estimate_wealth(balance, currency)
                            analysis['activity_level'] = self._assess_activity_level(data.get('n_tx', 0))
                            
            elif currency == 'ethereum':
                # Estimation pour Ethereum
                analysis['wealth_estimation'] = await self._estimate_wealth(0, currency)
                
        except Exception as e:
            self.logger.error(f"Erreur analyse balances {address}: {e}")
            analysis['error'] = str(e)
        
        return analysis
    
    async def _analyze_transactions(self, address: str, depth: int) -> Dict[str, Any]:
        """Analyse détaillée des transactions"""
        transactions_analysis = {
            'total_transactions': 0,
            'transaction_volume': 0,
            'largest_transaction': 0,
            'average_transaction': 0,
            'transaction_frequency': 'low',
            'suspicious_patterns': [],
            'counterparties': [],
            'timeline_analysis': {}
        }
        
        try:
            address_type = await self._identify_address_type(address)
            
            if address_type.get('currency') == 'bitcoin':
                tx_data = await self._get_btc_transactions(address, depth)
                transactions_analysis.update(tx_data)
                
            elif address_type.get('currency') == 'ethereum':
                tx_data = await self._get_eth_transactions(address, depth)
                transactions_analysis.update(tx_data)
                
            # Analyse des patterns
            transactions_analysis['suspicious_patterns'] = await self._detect_suspicious_patterns(transactions_analysis)
            transactions_analysis['counterparties'] = await self._analyze_counterparties(transactions_analysis)
            
        except Exception as e:
            self.logger.error(f"Erreur analyse transactions {address}: {e}")
            transactions_analysis['error'] = str(e)
        
        return transactions_analysis
    
    async def _get_btc_transactions(self, address: str, depth: int) -> Dict[str, Any]:
        """Récupère les transactions Bitcoin"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_endpoints['blockchain_com']}/rawaddr/{address}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        txs = data.get('txs', [])
                        
                        return {
                            'total_transactions': len(txs),
                            'transactions': txs[:10 * depth],  # Limiter selon la profondeur
                            'transaction_volume': data.get('total_sent', 0) / 10**8,
                            'data_source': 'blockchain.com'
                        }
                    else:
                        return {'error': f"API error: {response.status}"}
        except Exception as e:
            self.logger.error(f"Erreur BTC transactions {address}: {e}")
            return {'error': str(e)}
    
    async def _get_eth_transactions(self, address: str, depth: int) -> Dict[str, Any]:
        """Récupère les transactions Ethereum"""
        try:
            api_key = self.config.get_api_key('blockchain', 'etherscan_api') if self.config else None
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_endpoints['etherscan']}/api"
                params = {
                    'module': 'account',
                    'action': 'txlist',
                    'address': address,
                    'startblock': 0,
                    'endblock': 99999999,
                    'sort': 'desc',
                    'apikey': api_key or 'freekey'
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        txs = data.get('result', [])
                        
                        return {
                            'total_transactions': len(txs),
                            'transactions': txs[:10 * depth],
                            'data_source': 'etherscan'
                        }
                    else:
                        return {'error': f"API error: {response.status}"}
        except Exception as e:
            self.logger.error(f"Erreur ETH transactions {address}: {e}")
            return {'error': str(e)}
    
    async def _assess_risk(self, address: str, investigation_data: Dict) -> Dict[str, Any]:
        """Évalue les risques associés à l'adresse"""
        risk_indicators = []
        risk_score = 0
        
        try:
            basic_info = investigation_data.get('basic_info', {})
            transactions = investigation_data.get('transactions', {})
            
            # Indicateur 1: Adresse nouvelle
            if basic_info.get('transaction_count', 0) < 3:
                risk_indicators.append({
                    'type': 'new_address',
                    'level': 'medium',
                    'description': 'Adresse avec peu de transactions',
                    'confidence': 0.7
                })
                risk_score += 20
            
            # Indicateur 2: Volume anormal
            tx_volume = transactions.get('transaction_volume', 0)
            if tx_volume > 100:  # Plus de 100 BTC
                risk_indicators.append({
                    'type': 'high_volume',
                    'level': 'high',
                    'description': 'Volume de transactions élevé',
                    'confidence': 0.8
                })
                risk_score += 30
            
            # Indicateur 3: Patterns suspects
            suspicious_patterns = transactions.get('suspicious_patterns', [])
            if suspicious_patterns:
                risk_indicators.append({
                    'type': 'suspicious_patterns',
                    'level': 'high',
                    'description': f'Patterns suspects détectés: {len(suspicious_patterns)}',
                    'confidence': 0.9
                })
                risk_score += 40
            
            # Indicateur 4: Contreparties à risque
            counterparties = transactions.get('counterparties', [])
            high_risk_counterparties = [c for c in counterparties if c.get('risk_level') == 'high']
            if high_risk_counterparties:
                risk_indicators.append({
                    'type': 'high_risk_counterparties',
                    'level': 'high',
                    'description': f'Contreparties à risque: {len(high_risk_counterparties)}',
                    'confidence': 0.85
                })
                risk_score += 35
            
            # Score final
            risk_score = min(risk_score, 100)
            
            return {
                'risk_score': risk_score,
                'risk_level': self._determine_risk_level(risk_score),
                'risk_indicators': risk_indicators,
                'recommendations': await self._generate_risk_recommendations(risk_indicators)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur évaluation risque {address}: {e}")
            return {
                'risk_score': 50,
                'risk_level': 'unknown',
                'error': str(e)
            }
    
    async def _cluster_analysis(self, address: str, investigation_data: Dict) -> Dict[str, Any]:
        """Analyse de clustering et relations"""
        clustering = {
            'entity_clusters': [],
            'relationship_graph': {},
            'connected_addresses': [],
            'wallet_identification': {}
        }
        
        try:
            # Analyse des contreparties récurrentes
            transactions = investigation_data.get('transactions', {})
            tx_list = transactions.get('transactions', [])
            
            # Extraire les adresses connectées
            connected_addresses = set()
            for tx in tx_list[:50]:  # Limiter pour performance
                inputs = tx.get('inputs', [])
                outputs = tx.get('outputs', [])
                
                for inp in inputs:
                    if 'prev_out' in inp and 'addr' in inp['prev_out']:
                        connected_addresses.add(inp['prev_out']['addr'])
                
                for out in outputs:
                    if 'addr' in out:
                        connected_addresses.add(out['addr'])
            
            clustering['connected_addresses'] = list(connected_addresses)[:20]
            
            # Identification de wallet potentielle
            clustering['wallet_identification'] = await self._identify_wallet_type(address, investigation_data)
            
            # Clusters d'entités
            clustering['entity_clusters'] = await self._detect_entity_clusters(address, list(connected_addresses))
            
        except Exception as e:
            self.logger.error(f"Erreur clustering {address}: {e}")
            clustering['error'] = str(e)
        
        return clustering
    
    async def _setup_monitoring(self, address: str) -> Dict[str, Any]:
        """Configure le monitoring de l'adresse"""
        monitoring = {
            'monitoring_enabled': False,
            'alerts': [],
            'monitoring_features': []
        }
        
        try:
            # Configuration basique du monitoring
            monitoring['monitoring_features'] = [
                'new_transactions',
                'large_transfers',
                'balance_changes',
                'suspicious_activity'
            ]
            
            monitoring['alerts'] = [{
                'type': 'configuration_required',
                'message': 'Monitoring nécessite une configuration manuelle',
                'level': 'info'
            }]
            
        except Exception as e:
            self.logger.error(f"Erreur setup monitoring {address}: {e}")
            monitoring['error'] = str(e)
        
        return monitoring
    
    async def _predictive_analysis(self, investigation_data: Dict) -> Dict[str, Any]:
        """Analyse prédictive du comportement"""
        predictive = {
            'behavior_prediction': {},
            'risk_forecast': {},
            'anomaly_detection': {}
        }
        
        try:
            # Analyse du comportement futur basé sur l'historique
            basic_info = investigation_data.get('basic_info', {})
            tx_count = basic_info.get('transaction_count', 0)
            balance = basic_info.get('current_balance', 0)
            
            predictive['behavior_prediction'] = {
                'likely_activity': 'low' if tx_count < 10 else 'medium',
                'wealth_trend': 'stable',
                'prediction_confidence': 0.6
            }
            
            predictive['risk_forecast'] = {
                'future_risk': 'medium',
                'factors': ['historical_patterns', 'balance_size'],
                'confidence': 0.5
            }
            
        except Exception as e:
            self.logger.error(f"Erreur analyse prédictive: {e}")
            predictive['error'] = str(e)
        
        return predictive
    
    # ============================================================================
    # MÉTHODES D'ASSISTANCE
    # ============================================================================
    
    async def _estimate_wealth(self, balance: float, currency: str) -> Dict[str, Any]:
        """Estime la richesse basée sur le solde"""
        wealth_levels = {
            'bitcoin': {
                'small': 0.1,
                'medium': 1.0,
                'large': 10.0,
                'whale': 100.0
            },
            'ethereum': {
                'small': 1.0,
                'medium': 10.0,
                'large': 100.0,
                'whale': 1000.0
            }
        }
        
        levels = wealth_levels.get(currency, wealth_levels['bitcoin'])
        wealth_category = 'small'
        
        for category, threshold in levels.items():
            if balance >= threshold:
                wealth_category = category
        
        return {
            'estimated_wealth': wealth_category,
            'balance': balance,
            'currency': currency,
            'description': self._get_wealth_description(wealth_category, currency)
        }
    
    def _get_wealth_description(self, category: str, currency: str) -> str:
        """Retourne une description de la catégorie de richesse"""
        descriptions = {
            'small': f"Portefeuille {currency} standard",
            'medium': f"Portefeuille {currency} substantiel", 
            'large': f"Gros portefeuille {currency}",
            'whale': f"Baleine {currency} - solde très important"
        }
        return descriptions.get(category, "Catégorie inconnue")
    
    def _assess_activity_level(self, tx_count: int) -> str:
        """Évalue le niveau d'activité"""
        if tx_count == 0:
            return 'inactive'
        elif tx_count < 10:
            return 'low'
        elif tx_count < 100:
            return 'medium'
        else:
            return 'high'
    
    async def _detect_suspicious_patterns(self, transactions_analysis: Dict) -> List[Dict]:
        """Détecte les patterns suspects"""
        patterns = []
        
        try:
            tx_list = transactions_analysis.get('transactions', [])
            
            # Pattern 1: Transactions en peigne (peeling)
            if len(tx_list) > 10:
                # Vérifier les transactions de petite valeur répétitives
                small_txs = [tx for tx in tx_list if self._get_tx_value(tx) < 0.01]
                if len(small_txs) > len(tx_list) * 0.7:  # 70% de petites transactions
                    patterns.append({
                        'type': 'peeling_pattern',
                        'description': 'Transactions de petite valeur répétitives',
                        'confidence': 0.75
                    })
            
            # Pattern 2: Mélange de valeurs (possible mixing)
            values = [self._get_tx_value(tx) for tx in tx_list if self._get_tx_value(tx) > 0]
            if values:
                value_std = np.std(values) if len(values) > 1 else 0
                if value_std > np.mean(values) * 2:  # Forte variance
                    patterns.append({
                        'type': 'value_mixing',
                        'description': 'Valeurs de transactions très variables',
                        'confidence': 0.6
                    })
                    
        except Exception as e:
            self.logger.error(f"Erreur détection patterns: {e}")
        
        return patterns
    
    def _get_tx_value(self, transaction: Dict) -> float:
        """Extrait la valeur d'une transaction"""
        try:
            # Implémentation basique pour Bitcoin
            if 'result' in transaction:  # Format Ethereum
                return abs(int(transaction.get('result', 0))) / 10**18
            else:  # Format Bitcoin
                return abs(transaction.get('result', 0)) / 10**8
        except:
            return 0
    
    async def _analyze_counterparties(self, transactions_analysis: Dict) -> List[Dict]:
        """Analyse les contreparties"""
        counterparties = []
        
        try:
            tx_list = transactions_analysis.get('transactions', [])
            counterparty_counts = {}
            
            for tx in tx_list[:100]:  # Limiter pour performance
                # Logique d'analyse des contreparties
                pass
                
        except Exception as e:
            self.logger.error(f"Erreur analyse contreparties: {e}")
        
        return counterparties
    
    def _determine_risk_level(self, risk_score: int) -> str:
        """Détermine le niveau de risque"""
        if risk_score >= 80:
            return 'very_high'
        elif risk_score >= 60:
            return 'high'
        elif risk_score >= 40:
            return 'medium'
        elif risk_score >= 20:
            return 'low'
        else:
            return 'very_low'
    
    async def _generate_risk_recommendations(self, risk_indicators: List[Dict]) -> List[str]:
        """Génère des recommandations basées sur les risques"""
        recommendations = []
        
        for indicator in risk_indicators:
            if indicator['level'] in ['high', 'very_high']:
                recommendations.append(
                    f"Surveillance recommandée: {indicator['description']}"
                )
        
        if not recommendations:
            recommendations.append("Aucune action spécifique recommandée")
        
        return recommendations
    
    async def _identify_wallet_type(self, address: str, investigation_data: Dict) -> Dict[str, Any]:
        """Tente d'identifier le type de wallet"""
        return {
            'likely_wallet': 'unknown',
            'confidence': 0.0,
            'characteristics': []
        }
    
    async def _detect_entity_clusters(self, address: str, connected_addresses: List[str]) -> List[Dict]:
        """Détecte les clusters d'entités"""
        return [{
            'cluster_id': 'default',
            'addresses': connected_addresses[:5],
            'cluster_type': 'connected_addresses'
        }]

# Utilisation principale
async def main():
    """Exemple d'utilisation"""
    tracker = CryptoTracker()
    
    # Test avec une adresse Bitcoin exemple
    sample_address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"  # Genesis block
    
    try:
        results = await tracker.investigate(sample_address, depth=2)
        
        print("🔍 Investigation crypto terminée:")
        crypto_data = results.get('crypto_tracker', {})
        
        print(f"✅ Adresse: {crypto_data.get('address')}")
        print(f"💰 Type: {crypto_data.get('address_type', {}).get('currency')}")
        print(f"📊 Transactions: {crypto_data.get('basic_info', {}).get('transaction_count', 0)}")
        print(f"⚡ Risque: {crypto_data.get('risk_assessment', {}).get('risk_level', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Erreur investigation: {e}")

if __name__ == "__main__":
    asyncio.run(main())
