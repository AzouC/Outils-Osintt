# modules/blockchain/ethereum.py
import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from web3 import Web3
import requests

class EthereumAnalyzer:
    def __init__(self, config_manager=None):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        self.web3 = None
        self.api_endpoints = self._setup_endpoints()
        self.initialize_web3()
        
    def _setup_endpoints(self) -> Dict[str, str]:
        """Configure les endpoints API Ethereum"""
        return {
            'etherscan': 'https://api.etherscan.io/api',
            'infura': 'https://mainnet.infura.io/v3/',
            'alchemy': 'https://eth-mainnet.alchemyapi.io/v2/',
            'moralis': 'https://deep-index.moralis.io/api/v2',
            'covalent': 'https://api.covalenthq.com/v1',
            'thegraph': 'https://api.thegraph.com/subgraphs/name/'
        }
    
    def initialize_web3(self):
        """Initialise la connexion Web3"""
        try:
            # Essayer différents providers
            providers = [
                f"https://mainnet.infura.io/v3/{self.config.get_api_key('blockchain', 'infura_key') if self.config else 'YOUR_INFURA_KEY'}",
                "https://cloudflare-eth.com",
                "https://rpc.ankr.com/eth",
                "https://eth-mainnet.public.blastapi.io"
            ]
            
            for provider_url in providers:
                try:
                    self.web3 = Web3(Web3.HTTPProvider(provider_url))
                    if self.web3.is_connected():
                        self.logger.info(f"✅ Connecté à Ethereum via: {provider_url}")
                        break
                except:
                    continue
            
            if not self.web3 or not self.web3.is_connected():
                self.logger.warning("❌ Impossible de se connecter à Ethereum")
                
        except Exception as e:
            self.logger.error(f"Erreur initialisation Web3: {e}")
    
    async def investigate(self, address: str, depth: int = 2) -> Dict[str, Any]:
        """
        Investigation complète d'une adresse Ethereum
        """
        self.logger.info(f"Investigation Ethereum pour: {address}")
        
        # Validation de l'adresse
        if not self._is_valid_ethereum_address(address):
            return {
                'error': f"Adresse Ethereum invalide: {address}",
                'valid_address': False
            }
        
        results = {
            'address': address,
            'valid_address': True,
            'checksum_address': Web3.to_checksum_address(address),
            'investigation_timestamp': datetime.now().isoformat(),
            'network_info': await self._get_network_info(),
            'account_info': {},
            'token_holdings': {},
            'transactions': {},
            'smart_contracts': {},
            'nft_assets': {},
            'defi_activity': {},
            'risk_assessment': {},
            'entity_analysis': {}
        }
        
        if depth >= 1:
            results['account_info'] = await self._get_account_info(address)
            results['token_holdings'] = await self._get_token_holdings(address)
        
        if depth >= 2:
            results['transactions'] = await self._analyze_transactions(address, depth)
            results['smart_contracts'] = await self._analyze_smart_contracts(address)
            results['risk_assessment'] = await self._assess_risk(address, results)
        
        if depth >= 3:
            results['nft_assets'] = await self._get_nft_assets(address)
            results['defi_activity'] = await self._analyze_defi_activity(address, results)
            results['entity_analysis'] = await self._analyze_entity(address, results)
            results['predictive_analysis'] = await self._predictive_analysis(results)
        
        return {'ethereum': results}
    
    def _is_valid_ethereum_address(self, address: str) -> bool:
        """Valide une adresse Ethereum"""
        try:
            return Web3.is_address(address)
        except:
            return False
    
    async def _get_network_info(self) -> Dict[str, Any]:
        """Récupère les informations du réseau Ethereum"""
        try:
            if self.web3 and self.web3.is_connected():
                return {
                    'network': 'mainnet',
                    'chain_id': self.web3.eth.chain_id,
                    'block_number': self.web3.eth.block_number,
                    'gas_price': self.web3.eth.gas_price,
                    'last_block_time': datetime.now().isoformat(),
                    'syncing': self.web3.eth.syncing
                }
            else:
                return {
                    'network': 'unknown',
                    'error': 'Non connecté à Ethereum'
                }
        except Exception as e:
            self.logger.error(f"Erreur info réseau: {e}")
            return {'error': str(e)}
    
    async def _get_account_info(self, address: str) -> Dict[str, Any]:
        """Récupère les informations basiques du compte"""
        info = {
            'address': address,
            'eth_balance': 0,
            'balance_usd': 0,
            'transaction_count': 0,
            'first_seen': None,
            'last_activity': None,
            'is_contract': False
        }
        
        try:
            # Balance ETH
            if self.web3 and self.web3.is_connected():
                balance_wei = self.web3.eth.get_balance(Web3.to_checksum_address(address))
                info['eth_balance'] = self.web3.from_wei(balance_wei, 'ether')
                
                # Nombre de transactions
                info['transaction_count'] = self.web3.eth.get_transaction_count(Web3.to_checksum_address(address))
            
            # Prix ETH en USD
            eth_price = await self._get_eth_price()
            if eth_price:
                info['balance_usd'] = float(info['eth_balance']) * eth_price
            
            # Vérifier si c'est un contrat
            info['is_contract'] = await self._is_contract_address(address)
            
            # Première et dernière activité via Etherscan
            activity_info = await self._get_account_activity(address)
            info.update(activity_info)
            
        except Exception as e:
            self.logger.error(f"Erreur info compte {address}: {e}")
            info['error'] = str(e)
        
        return info
    
    async def _get_token_holdings(self, address: str) -> Dict[str, Any]:
        """Récupère les holdings de tokens"""
        tokens = {
            'erc20_tokens': [],
            'total_tokens': 0,
            'total_value_usd': 0,
            'token_breakdown': {}
        }
        
        try:
            # Utiliser Covalent ou Moralis pour les tokens
            api_key = self.config.get_api_key('blockchain', 'covalent_key') if self.config else None
            
            if api_key:
                # API Covalent
                url = f"{self.api_endpoints['covalent']}/1/address/{address}/balances_v2/"
                params = {'key': api_key}
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            tokens_data = data.get('data', {}).get('items', [])
                            
                            for token in tokens_data:
                                if float(token.get('balance', 0)) > 0:
                                    token_info = {
                                        'contract_address': token.get('contract_address'),
                                        'name': token.get('contract_name'),
                                        'symbol': token.get('contract_ticker_symbol'),
                                        'decimals': token.get('contract_decimals', 18),
                                        'balance': float(token.get('balance', 0)) / (10 ** token.get('contract_decimals', 18)),
                                        'price_usd': token.get('quote_rate', 0),
                                        'value_usd': token.get('quote', 0)
                                    }
                                    tokens['erc20_tokens'].append(token_info)
            
            # Fallback: Tokens majeurs manuellement
            if not tokens['erc20_tokens']:
                major_tokens = await self._get_major_tokens_balance(address)
                tokens['erc20_tokens'] = major_tokens
            
            tokens['total_tokens'] = len(tokens['erc20_tokens'])
            tokens['total_value_usd'] = sum(token.get('value_usd', 0) for token in tokens['erc20_tokens'])
            
        except Exception as e:
            self.logger.error(f"Erreur tokens {address}: {e}")
            tokens['error'] = str(e)
        
        return tokens
    
    async def _get_major_tokens_balance(self, address: str) -> List[Dict]:
        """Récupère les balances des tokens majeurs"""
        major_tokens = [
            # USDT
            {
                'contract_address': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
                'name': 'Tether USD',
                'symbol': 'USDT',
                'decimals': 6
            },
            # USDC
            {
                'contract_address': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
                'name': 'USD Coin',
                'symbol': 'USDC',
                'decimals': 6
            },
            # DAI
            {
                'contract_address': '0x6B175474E89094C44Da98b954EedeAC495271d0F',
                'name': 'Dai Stablecoin',
                'symbol': 'DAI',
                'decimals': 18
            }
        ]
        
        balances = []
        
        try:
            if self.web3 and self.web3.is_connected():
                for token in major_tokens:
                    # ABI simplifié pour balanceOf
                    abi = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'
                    
                    contract = self.web3.eth.contract(
                        address=Web3.to_checksum_address(token['contract_address']),
                        abi=abi
                    )
                    
                    try:
                        balance = contract.functions.balanceOf(Web3.to_checksum_address(address)).call()
                        if balance > 0:
                            token_balance = balance / (10 ** token['decimals'])
                            token_info = token.copy()
                            token_info['balance'] = token_balance
                            token_info['value_usd'] = token_balance  # Approximation pour les stablecoins
                            balances.append(token_info)
                    except:
                        continue
                        
        except Exception as e:
            self.logger.error(f"Erreur tokens majeurs: {e}")
        
        return balances
    
    async def _analyze_transactions(self, address: str, depth: int) -> Dict[str, Any]:
        """Analyse détaillée des transactions"""
        transactions_analysis = {
            'total_transactions': 0,
            'transactions': [],
            'transaction_volume_eth': 0,
            'transaction_volume_usd': 0,
            'gas_usage': {},
            'interaction_patterns': [],
            'most_active_periods': [],
            'counterparties': []
        }
        
        try:
            # Récupérer les transactions via Etherscan
            api_key = self.config.get_api_key('blockchain', 'etherscan_api') if self.config else None
            
            # Transactions normales
            normal_txs = await self._get_normal_transactions(address, api_key, depth)
            # Transactions internes
            internal_txs = await self._get_internal_transactions(address, api_key, depth)
            # Transactions ERC20
            erc20_txs = await self._get_erc20_transactions(address, api_key, depth)
            
            transactions_analysis['transactions'] = normal_txs[:20 * depth]  # Limiter
            transactions_analysis['internal_transactions'] = internal_txs[:10 * depth]
            transactions_analysis['erc20_transactions'] = erc20_txs[:15 * depth]
            
            transactions_analysis['total_transactions'] = len(normal_txs) + len(internal_txs) + len(erc20_txs)
            
            # Analyse des volumes
            transactions_analysis.update(await self._analyze_transaction_volumes(normal_txs))
            
            # Patterns d'interaction
            transactions_analysis['interaction_patterns'] = await self._analyze_interaction_patterns(
                normal_txs + internal_txs + erc20_txs
            )
            
            # Contreparties
            transactions_analysis['counterparties'] = await self._analyze_transaction_counterparties(
                normal_txs + internal_txs
            )
            
        except Exception as e:
            self.logger.error(f"Erreur analyse transactions {address}: {e}")
            transactions_analysis['error'] = str(e)
        
        return transactions_analysis
    
    async def _get_normal_transactions(self, address: str, api_key: str, depth: int) -> List[Dict]:
        """Récupère les transactions normales"""
        try:
            url = f"{self.api_endpoints['etherscan']}"
            params = {
                'module': 'account',
                'action': 'txlist',
                'address': address,
                'startblock': 0,
                'endblock': 99999999,
                'sort': 'desc',
                'apikey': api_key or 'freekey'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('result', [])
                    else:
                        return []
        except Exception as e:
            self.logger.error(f"Erreur transactions normales: {e}")
            return []
    
    async def _get_internal_transactions(self, address: str, api_key: str, depth: int) -> List[Dict]:
        """Récupère les transactions internes"""
        try:
            url = f"{self.api_endpoints['etherscan']}"
            params = {
                'module': 'account',
                'action': 'txlistinternal',
                'address': address,
                'startblock': 0,
                'endblock': 99999999,
                'sort': 'desc',
                'apikey': api_key or 'freekey'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('result', [])
                    else:
                        return []
        except Exception as e:
            self.logger.error(f"Erreur transactions internes: {e}")
            return []
    
    async def _get_erc20_transactions(self, address: str, api_key: str, depth: int) -> List[Dict]:
        """Récupère les transactions ERC20"""
        try:
            url = f"{self.api_endpoints['etherscan']}"
            params = {
                'module': 'account',
                'action': 'tokentx',
                'address': address,
                'startblock': 0,
                'endblock': 99999999,
                'sort': 'desc',
                'apikey': api_key or 'freekey'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('result', [])
                    else:
                        return []
        except Exception as e:
            self.logger.error(f"Erreur transactions ERC20: {e}")
            return []
    
    async def _analyze_smart_contracts(self, address: str) -> Dict[str, Any]:
        """Analyse les interactions avec les smart contracts"""
        contracts_analysis = {
            'contract_interactions': [],
            'deployed_contracts': [],
            'popular_contracts': [],
            'contract_categories': {}
        }
        
        try:
            # Vérifier si l'adresse est un contrat déployé
            if await self._is_contract_address(address):
                contract_info = await self._analyze_contract_code(address)
                contracts_analysis['deployed_contracts'].append(contract_info)
            
            # Analyser les interactions avec d'autres contrats
            contracts_analysis['contract_interactions'] = await self._get_contract_interactions(address)
            
        except Exception as e:
            self.logger.error(f"Erreur analyse contrats {address}: {e}")
            contracts_analysis['error'] = str(e)
        
        return contracts_analysis
    
    async def _get_nft_assets(self, address: str) -> Dict[str, Any]:
        """Récupère les assets NFT"""
        nfts = {
            'nft_count': 0,
            'nft_collections': [],
            'total_value_estimate': 0,
            'nft_assets': []
        }
        
        try:
            # Utiliser Moralis ou OpenSea API
            api_key = self.config.get_api_key('blockchain', 'moralis_key') if self.config else None
            
            if api_key:
                url = f"{self.api_endpoints['moralis']}/{address}/nft"
                headers = {'X-API-Key': api_key}
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            nft_data = data.get('result', [])
                            
                            for nft in nft_data:
                                nft_info = {
                                    'token_address': nft.get('token_address'),
                                    'token_id': nft.get('token_id'),
                                    'name': nft.get('name'),
                                    'symbol': nft.get('symbol'),
                                    'metadata': nft.get('metadata'),
                                    'collection': nft.get('normalized_metadata', {}).get('name')
                                }
                                nfts['nft_assets'].append(nft_info)
            
            nfts['nft_count'] = len(nfts['nft_assets'])
            
        except Exception as e:
            self.logger.error(f"Erreur NFTs {address}: {e}")
            nfts['error'] = str(e)
        
        return nfts
    
    async def _analyze_defi_activity(self, address: str, investigation_data: Dict) -> Dict[str, Any]:
        """Analyse l'activité DeFi"""
        defi_analysis = {
            'defi_protocols': [],
            'lending_activity': {},
            'dex_trading': {},
            'yield_farming': {},
            'total_defi_value': 0
        }
        
        try:
            # Détecter les interactions avec les protocoles DeFi majeurs
            transactions = investigation_data.get('transactions', {}).get('transactions', [])
            token_holdings = investigation_data.get('token_holdings', {}).get('erc20_tokens', [])
            
            # Protocoles DeFi populaires
            defi_protocols = {
                '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D': 'Uniswap V2 Router',
                '0xE592427A0AEce92De3Edee1F18E0157C05861564': 'Uniswap V3 Router',
                '0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B': 'Compound',
                '0x398eC7346DcD622eDc5ae82352F02bE94C62d119': 'Aave V2',
                '0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9': 'Aave V2 Lending Pool'
            }
            
            for tx in transactions:
                to_address = tx.get('to', '').lower()
                if to_address in [addr.lower() for addr in defi_protocols.keys()]:
                    protocol_name = defi_protocols.get(to_address, 'Unknown DeFi')
                    if protocol_name not in defi_analysis['defi_protocols']:
                        defi_analysis['defi_protocols'].append(protocol_name)
            
            # Détection via tokens DeFi
            defi_tokens = ['UNI', 'AAVE', 'COMP', 'MKR', 'SNX', 'YFI']
            for token in token_holdings:
                if token.get('symbol') in defi_tokens and token.get('balance', 0) > 0:
                    defi_analysis['defi_protocols'].append(f"{token['symbol']} Holder")
            
        except Exception as e:
            self.logger.error(f"Erreur analyse DeFi {address}: {e}")
            defi_analysis['error'] = str(e)
        
        return defi_analysis
    
    async def _assess_risk(self, address: str, investigation_data: Dict) -> Dict[str, Any]:
        """Évalue les risques associés à l'adresse"""
        risk_indicators = []
        risk_score = 0
        
        try:
            account_info = investigation_data.get('account_info', {})
            transactions = investigation_data.get('transactions', {})
            
            # Indicateur 1: Nouvelle adresse
            tx_count = account_info.get('transaction_count', 0)
            if tx_count < 5:
                risk_indicators.append({
                    'type': 'new_address',
                    'level': 'medium',
                    'description': 'Adresse avec peu de transactions',
                    'confidence': 0.7
                })
                risk_score += 20
            
            # Indicateur 2: Activité DeFi
            defi_protocols = investigation_data.get('defi_activity', {}).get('defi_protocols', [])
            if len(defi_protocols) > 3:
                risk_indicators.append({
                    'type': 'high_defi_activity',
                    'level': 'medium',
                    'description': 'Activité DeFi intensive',
                    'confidence': 0.6
                })
                risk_score += 15
            
            # Indicateur 3: Contrat suspect
            if account_info.get('is_contract', False):
                risk_indicators.append({
                    'type': 'contract_address',
                    'level': 'low',
                    'description': 'Adresse de contrat - surveillance recommandée',
                    'confidence': 0.5
                })
                risk_score += 10
            
            # Indicateur 4: Volume élevé
            tx_volume = transactions.get('transaction_volume_eth', 0)
            if tx_volume > 100:  # Plus de 100 ETH
                risk_indicators.append({
                    'type': 'high_volume',
                    'level': 'high',
                    'description': 'Volume de transactions élevé',
                    'confidence': 0.8
                })
                risk_score += 25
            
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
    
    async def _analyze_entity(self, address: str, investigation_data: Dict) -> Dict[str, Any]:
        """Analyse l'entité derrière l'adresse"""
        entity_analysis = {
            'entity_type': 'unknown',
            'behavior_patterns': [],
            'wallet_characteristics': {},
            'cluster_analysis': {}
        }
        
        try:
            # Déterminer le type d'entité basé sur l'activité
            account_info = investigation_data.get('account_info', {})
            transactions = investigation_data.get('transactions', {})
            
            tx_count = account_info.get('transaction_count', 0)
            defi_activity = investigation_data.get('defi_activity', {})
            
            if account_info.get('is_contract', False):
                entity_analysis['entity_type'] = 'smart_contract'
            elif len(defi_activity.get('defi_protocols', [])) > 2:
                entity_analysis['entity_type'] = 'defi_user'
            elif tx_count > 100:
                entity_analysis['entity_type'] = 'active_trader'
            elif tx_count < 10:
                entity_analysis['entity_type'] = 'new_user'
            else:
                entity_analysis['entity_type'] = 'standard_user'
            
            # Analyse des patterns de comportement
            entity_analysis['behavior_patterns'] = await self._analyze_behavior_patterns(investigation_data)
            
        except Exception as e:
            self.logger.error(f"Erreur analyse entité {address}: {e}")
            entity_analysis['error'] = str(e)
        
        return entity_analysis
    
    async def _predictive_analysis(self, investigation_data: Dict) -> Dict[str, Any]:
        """Analyse prédictive du comportement"""
        predictive = {
            'future_activity': {},
            'risk_forecast': {},
            'wealth_trajectory': {}
        }
        
        try:
            account_info = investigation_data.get('account_info', {})
            tx_count = account_info.get('transaction_count', 0)
            balance = account_info.get('eth_balance', 0)
            
            # Prédictions basiques
            if tx_count == 0:
                predictive['future_activity'] = {
                    'prediction': 'inactive',
                    'confidence': 0.8
                }
            elif tx_count < 10:
                predictive['future_activity'] = {
                    'prediction': 'low_activity',
                    'confidence': 0.6
                }
            else:
                predictive['future_activity'] = {
                    'prediction': 'continued_activity',
                    'confidence': 0.7
                }
            
            predictive['risk_forecast'] = {
                'future_risk': 'stable',
                'factors': ['historical_patterns'],
                'confidence': 0.5
            }
            
        except Exception as e:
            self.logger.error(f"Erreur analyse prédictive: {e}")
            predictive['error'] = str(e)
        
        return predictive
    
    # ============================================================================
    # MÉTHODES D'ASSISTANCE
    # ============================================================================
    
    async def _is_contract_address(self, address: str) -> bool:
        """Vérifie si l'adresse est un contrat"""
        try:
            if self.web3 and self.web3.is_connected():
                code = self.web3.eth.get_code(Web3.to_checksum_address(address))
                return len(code) > 2  # Les contrats ont du code, les EOA non
            return False
        except:
            return False
    
    async def _get_eth_price(self) -> Optional[float]:
        """Récupère le prix actuel de l'ETH"""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('ethereum', {}).get('usd')
            return None
        except:
            return None
    
    async def _get_account_activity(self, address: str) -> Dict[str, Any]:
        """Récupère les informations d'activité du compte"""
        return {
            'first_seen': None,
            'last_activity': datetime.now().isoformat()
        }
    
    async def _analyze_transaction_volumes(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Analyse les volumes de transactions"""
        volumes = {
            'transaction_volume_eth': 0,
            'transaction_volume_usd': 0,
            'largest_transaction': 0,
            'average_transaction': 0
        }
        
        try:
            eth_values = []
            for tx in transactions:
                value = int(tx.get('value', 0)) / 10**18  # Conversion wei to ETH
                eth_values.append(value)
                volumes['transaction_volume_eth'] += value
            
            if eth_values:
                volumes['largest_transaction'] = max(eth_values)
                volumes['average_transaction'] = sum(eth_values) / len(eth_values)
            
            # Estimation USD
            eth_price = await self._get_eth_price()
            if eth_price:
                volumes['transaction_volume_usd'] = volumes['transaction_volume_eth'] * eth_price
                
        except Exception as e:
            self.logger.error(f"Erreur analyse volumes: {e}")
        
        return volumes
    
    async def _analyze_interaction_patterns(self, transactions: List[Dict]) -> List[Dict]:
        """Analyse les patterns d'interaction"""
        patterns = []
        
        try:
            # Détection de patterns basiques
            if len(transactions) > 50:
                patterns.append({
                    'type': 'high_frequency',
                    'description': 'Fréquence de transactions élevée',
                    'confidence': 0.7
                })
            
        except Exception as e:
            self.logger.error(f"Erreur analyse patterns: {e}")
        
        return patterns
    
    async def _analyze_transaction_counterparties(self, transactions: List[Dict]) -> List[Dict]:
        """Analyse les contreparties des transactions"""
        counterparties = []
        
        try:
            counterparty_counts = {}
            
            for tx in transactions[:100]:  # Limiter pour performance
                to_address = tx.get('to', '')
                from_address = tx.get('from', '')
                
                if to_address:
                    counterparty_counts[to_address] = counterparty_counts.get(to_address, 0) + 1
                if from_address:
                    counterparty_counts[from_address] = counterparty_counts.get(from_address, 0) + 1
            
            # Top 10 des contreparties
            for addr, count in sorted(counterparty_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                counterparties.append({
                    'address': addr,
                    'interaction_count': count,
                    'risk_level': 'unknown'
                })
                
        except Exception as e:
            self.logger.error(f"Erreur analyse contreparties: {e}")
        
        return counterparties
    
    async def _analyze_contract_code(self, address: str) -> Dict[str, Any]:
        """Analyse le code d'un contrat"""
        return {
            'address': address,
            'analysis': 'basic_analysis',
            'verified': False
        }
    
    async def _get_contract_interactions(self, address: str) -> List[Dict]:
        """Récupère les interactions avec les contrats"""
        return []
    
    async def _analyze_behavior_patterns(self, investigation_data: Dict) -> List[Dict]:
        """Analyse les patterns de comportement"""
        return []
    
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

# Utilisation principale
async def main():
    """Exemple d'utilisation"""
    analyzer = EthereumAnalyzer()
    
 # Test avec une adresse Ethereum exemple
    sample_address = "0x742d35Cc6634C0532925a3b8bc9e6c8a4e4e4e4e"  # Adresse exemple
    
    try:
        results = await analyzer.investigate(sample_address, depth=2)
        
        print("🔍 Investigation Ethereum terminée:")
        eth_data = results.get('ethereum', {})
        
        print(f"✅ Adresse: {eth_data.get('address')}")
        print(f"💰 Balance ETH: {eth_data.get('account_info', {}).get('eth_balance', 0)}")
        print(f"📊 Transactions: {eth_data.get('account_info', {}).get('transaction_count', 0)}")
        print(f"🎯 Type: {eth_data.get('entity_analysis', {}).get('entity_type', 'unknown')}")
        print(f"⚡ Risque: {eth_data.get('risk_assessment', {}).get('risk_level', 'unknown')}")
        print(f"🪙 Tokens: {eth_data.get('token_holdings', {}).get('total_tokens', 0)}")
        print(f"🎨 NFTs: {eth_data.get('nft_assets', {}).get('nft_count', 0)}")
        print(f"🔄 DeFi: {len(eth_data.get('defi_activity', {}).get('defi_protocols', []))} protocoles")
        
    except Exception as e:
        print(f"❌ Erreur investigation: {e}")

if __name__ == "__main__":
    asyncio.run(main())
