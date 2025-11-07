"""
Package blockchain - Modules d'analyse blockchain et cryptomonnaies

Ce package contient les modules spécialisés dans l'analyse des blockchains,
la traçabilité des transactions cryptos et l'intelligence sur les portefeuilles.

Fonctionnalités:
- Analyse de transactions Bitcoin et Ethereum
- Tracking de portefeuilles
- Investigation d'adresses
- Analyse de smart contracts
"""

import importlib
from typing import Dict, List, Any, Optional, Union
from decimal import Decimal
from utils.logger import get_logger

# Configuration du logger
logger = get_logger(__name__)

# Métadonnées du package
__version__ = "1.0.0"
__author__ = "AzouC"
__description__ = "Modules d'analyse blockchain OSINT"

# Liste des modules disponibles dans ce package
__all__ = ['bitcoin', 'ethereum', 'crypto_tracker']

# Registre des modules blockchain
_BLOCKCHAIN_MODULES = {}

class BlockchainManager:
    """
    Gestionnaire central des modules d'analyse blockchain
    
    Fournit une interface unifiée pour l'analyse des transactions,
    le tracking de portefeuilles et l'investigation cryptographique.
    """
    
    def __init__(self, config_manager):
        """
        Initialise le gestionnaire des modules blockchain
        
        Args:
            config_manager: Gestionnaire de configuration
        """
        self.config = config_manager
        self.logger = logger
        self.modules = {}
        self._initialize_blockchain_modules()
    
    def _initialize_blockchain_modules(self):
        """Initialise tous les modules blockchain disponibles"""
        self.logger.info("⛓️ Initialisation des modules blockchain...")
        
        # Modules blockchain à initialiser
        blockchain_modules = [
            ('bitcoin', 'BitcoinIntel'),
            ('ethereum', 'EthereumIntel'),
            ('crypto_tracker', 'CryptoTracker')
        ]
        
        for module_name, class_name in blockchain_modules:
            self._try_initialize_blockchain_module(module_name, class_name)
        
        self.logger.info(f"✅ {len(self.modules)} modules blockchain initialisés")
    
    def _try_initialize_blockchain_module(self, module_name: str, class_name: str):
        """
        Tente d'initialiser un module blockchain spécifique
        
        Args:
            module_name: Nom du module (ex: 'bitcoin')
            class_name: Nom de la classe à instancier
        """
        try:
            # Import dynamique du module
            module = importlib.import_module(f'.{module_name}', 'modules.blockchain')
            module_class = getattr(module, class_name)
            
            # Création de l'instance
            instance = module_class(self.config)
            self.modules[module_name] = instance
            _BLOCKCHAIN_MODULES[module_name] = True
            
            self.logger.debug(f"✅ Module {module_name} initialisé")
            
        except ImportError as e:
            self.logger.warning(f"⚠️ Module {module_name} non disponible: {e}")
            _BLOCKCHAIN_MODULES[module_name] = False
        except AttributeError as e:
            self.logger.warning(f"⚠️ Classe {class_name} non trouvée: {e}")
            _BLOCKCHAIN_MODULES[module_name] = False
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation {module_name}: {e}")
            _BLOCKCHAIN_MODULES[module_name] = False
    
    def get_transaction(self, tx_hash: str, blockchain: str = "bitcoin") -> Dict[str, Any]:
        """
        Récupère les détails d'une transaction blockchain
        
        Args:
            tx_hash: Hash de la transaction
            blockchain: Blockchain cible ('bitcoin', 'ethereum')
            
        Returns:
            Détails de la transaction
        """
        if blockchain not in self.modules:
            return {"error": f"Blockchain {blockchain} non disponible"}
        
        try:
            module = self.modules[blockchain]
            return module.get_transaction(tx_hash)
        except Exception as e:
            return {"error": f"Erreur récupération transaction: {str(e)}"}
    
    def get_address_info(self, address: str, blockchain: str = "bitcoin") -> Dict[str, Any]:
        """
        Récupère les informations d'une adresse blockchain
        
        Args:
            address: Adresse à analyser
            blockchain: Blockchain cible
            
        Returns:
            Informations de l'adresse
        """
        if blockchain not in self.modules:
            return {"error": f"Blockchain {blockchain} non disponible"}
        
        try:
            module = self.modules[blockchain]
            return module.get_address_info(address)
        except Exception as e:
            return {"error": f"Erreur analyse adresse: {str(e)}"}
    
    def get_balance(self, address: str, blockchain: str = "bitcoin") -> Dict[str, Any]:
        """
        Récupère le solde d'une adresse
        
        Args:
            address: Adresse à vérifier
            blockchain: Blockchain cible
            
        Returns:
            Solde et informations
        """
        if blockchain not in self.modules:
            return {"error": f"Blockchain {blockchain} non disponible"}
        
        try:
            module = self.modules[blockchain]
            return module.get_balance(address)
        except Exception as e:
            return {"error": f"Erreur récupération solde: {str(e)}"}
    
    def track_transactions(self, address: str, blockchain: str = "bitcoin", 
                          limit: int = 50) -> Dict[str, Any]:
        """
        Suit les transactions d'une adresse
        
        Args:
            address: Adresse à tracker
            blockchain: Blockchain cible
            limit: Nombre maximum de transactions
            
        Returns:
            Historique des transactions
        """
        if blockchain not in self.modules:
            return {"error": f"Blockchain {blockchain} non disponible"}
        
        try:
            module = self.modules[blockchain]
            return module.track_transactions(address, limit)
        except Exception as e:
            return {"error": f"Erreur tracking transactions: {str(e)}"}
    
    def analyze_address_risk(self, address: str, blockchain: str = "bitcoin") -> Dict[str, Any]:
        """
        Analyse le risque associé à une adresse
        
        Args:
            address: Adresse à analyser
            blockchain: Blockchain cible
            
        Returns:
            Évaluation du risque
        """
        if blockchain not in self.modules:
            return {"error": f"Blockchain {blockchain} non disponible"}
        
        try:
            module = self.modules[blockchain]
            if hasattr(module, 'analyze_address_risk'):
                return module.analyze_address_risk(address)
            else:
                # Fallback basique
                info = module.get_address_info(address)
                return {
                    "address": address,
                    "risk_score": 0.5,  # Valeur par défaut
                    "risk_level": "MEDIUM",
                    "analysis": info
                }
        except Exception as e:
            return {"error": f"Erreur analyse risque: {str(e)}"}
    
    def find_connections(self, address: str, depth: int = 2, 
                        blockchain: str = "bitcoin") -> Dict[str, Any]:
        """
        Trouve les connexions d'une adresse dans le graphe de transactions
        
        Args:
            address: Adresse source
            depth: Profondeur de recherche
            blockchain: Blockchain cible
            
        Returns:
            Réseau de connexions
        """
        if blockchain not in self.modules:
            return {"error": f"Blockchain {blockchain} non disponible"}
        
        try:
            module = self.modules[blockchain]
            if hasattr(module, 'find_connections'):
                return module.find_connections(address, depth)
            else:
                return {"error": "Analyse de connexions non supportée"}
        except Exception as e:
            return {"error": f"Erreur recherche connexions: {str(e)}"}
    
    def monitor_address(self, address: str, blockchain: str = "bitcoin", 
                       callback: callable = None) -> Dict[str, Any]:
        """
        Démarre la surveillance d'une adresse
        
        Args:
            address: Adresse à surveiller
            blockchain: Blockchain cible
            callback: Fonction à appeler lors de nouvelles transactions
            
        Returns:
            Statut de la surveillance
        """
        if 'crypto_tracker' not in self.modules:
            return {"error": "Module de tracking non disponible"}
        
        try:
            tracker = self.modules['crypto_tracker']
            return tracker.monitor_address(address, blockchain, callback)
        except Exception as e:
            return {"error": f"Erreur surveillance adresse: {str(e)}"}
    
    def get_crypto_price(self, cryptocurrency: str, vs_currency: str = "usd") -> Dict[str, Any]:
        """
        Récupère le prix actuel d'une cryptomonnaie
        
        Args:
            cryptocurrency: Cryptomonnaie (ex: 'bitcoin', 'ethereum')
            vs_currency: Devise de référence
            
        Returns:
            Données de prix
        """
        if 'crypto_tracker' not in self.modules:
            return {"error": "Module de tracking non disponible"}
        
        try:
            tracker = self.modules['crypto_tracker']
            return tracker.get_crypto_price(cryptocurrency, vs_currency)
        except Exception as e:
            return {"error": f"Erreur récupération prix: {str(e)}"}
    
    def analyze_transaction_pattern(self, address: str, 
                                  blockchain: str = "bitcoin") -> Dict[str, Any]:
        """
        Analyse les patterns de transaction d'une adresse
        
        Args:
            address: Adresse à analyser
            blockchain: Blockchain cible
            
        Returns:
            Patterns détectés
        """
        if blockchain not in self.modules:
            return {"error": f"Blockchain {blockchain} non disponible"}
        
        try:
            module = self.modules[blockchain]
            if hasattr(module, 'analyze_transaction_pattern'):
                return module.analyze_transaction_pattern(address)
            else:
                # Analyse basique basée sur l'historique
                transactions = self.track_transactions(address, blockchain, 100)
                if 'error' in transactions:
                    return transactions
                
                # Calcul de métriques simples
                tx_count = len(transactions.get('transactions', []))
                return {
                    "address": address,
                    "transaction_count": tx_count,
                    "pattern_analysis": "BASIC",
                    "metrics": {
                        "total_transactions": tx_count,
                        "analysis_available": False
                    }
                }
        except Exception as e:
            return {"error": f"Erreur analyse patterns: {str(e)}"}
    
    def get_blockchain_stats(self, blockchain: str = "bitcoin") -> Dict[str, Any]:
        """
        Récupère les statistiques d'une blockchain
        
        Args:
            blockchain: Blockchain cible
            
        Returns:
            Statistiques globales
        """
        if blockchain not in self.modules:
            return {"error": f"Blockchain {blockchain} non disponible"}
        
        try:
            module = self.modules[blockchain]
            if hasattr(module, 'get_blockchain_stats'):
                return module.get_blockchain_stats()
            else:
                return {"error": "Statistiques blockchain non disponibles"}
        except Exception as e:
            return {"error": f"Erreur récupération stats: {str(e)}"}
    
    def get_supported_blockchains(self) -> List[str]:
        """
        Liste les blockchains supportées
        
        Returns:
            Liste des blockchains disponibles
        """
        return list(self.modules.keys())
    
    def is_blockchain_supported(self, blockchain: str) -> bool:
        """
        Vérifie si une blockchain est supportée
        
        Args:
            blockchain: Nom de la blockchain
            
        Returns:
            True si supportée
        """
        return blockchain in self.modules
    
    def get_module_capabilities(self) -> Dict[str, Any]:
        """
        Retourne les capacités des modules blockchain
        
        Returns:
            Détails des fonctionnalités supportées
        """
        capabilities = {}
        
        for blockchain, module in self.modules.items():
            module_caps = {
                "transaction_lookup": hasattr(module, 'get_transaction'),
                "address_analysis": hasattr(module, 'get_address_info'),
                "balance_check": hasattr(module, 'get_balance'),
                "transaction_tracking": hasattr(module, 'track_transactions'),
                "risk_analysis": hasattr(module, 'analyze_address_risk'),
                "connection_analysis": hasattr(module, 'find_connections'),
                "pattern_analysis": hasattr(module, 'analyze_transaction_pattern')
            }
            capabilities[blockchain] = module_caps
        
        # Capacités du tracker global
        if 'crypto_tracker' in self.modules:
            tracker = self.modules['crypto_tracker']
            capabilities['tracker'] = {
                "price_monitoring": hasattr(tracker, 'get_crypto_price'),
                "address_monitoring": hasattr(tracker, 'monitor_address'),
                "alert_system": hasattr(tracker, 'set_alert')
            }
        
        return capabilities

# Fonctions utilitaires pour un usage rapide
def get_blockchain_manager(config_manager) -> BlockchainManager:
    """
    Récupère une instance du gestionnaire blockchain
    
    Args:
        config_manager: Gestionnaire de configuration
        
    Returns:
        Instance de BlockchainManager
    """
    return BlockchainManager(config_manager)

def quick_address_analysis(address: str, config_manager, blockchain: str = "bitcoin") -> Dict[str, Any]:
    """
    Analyse rapide d'une adresse blockchain
    
    Args:
        address: Adresse à analyser
        config_manager: Gestionnaire de configuration
        blockchain: Blockchain cible
        
    Returns:
        Résultats de l'analyse
    """
    manager = get_blockchain_manager(config_manager)
    return manager.get_address_info(address, blockchain)

def quick_transaction_lookup(tx_hash: str, config_manager, blockchain: str = "bitcoin") -> Dict[str, Any]:
    """
    Recherche rapide d'une transaction
    
    Args:
        tx_hash: Hash de la transaction
        config_manager: Gestionnaire de configuration
        blockchain: Blockchain cible
        
    Returns:
        Détails de la transaction
    """
    manager = get_blockchain_manager(config_manager)
    return manager.get_transaction(tx_hash, blockchain)

# Initialisation au chargement du package
logger.info(f"⛓️ Package blockchain OSINT v{__version__} chargé")

# Vérification de la disponibilité des modules blockchain
def _check_blockchain_modules():
    """Vérifie la disponibilité des modules blockchain"""
    available = {}
    for module_name in __all__:
        try:
            importlib.import_module(f'.{module_name}', 'modules.blockchain')
            available[module_name] = True
            logger.debug(f"⛓️ Module {module_name} disponible")
        except ImportError as e:
            available[module_name] = False
            logger.warning(f"⛓️ Module {module_name} non disponible: {e}")
    
    return available

# Vérification au chargement
_BLOCKCHAIN_MODULES_AVAILABILITY = _check_blockchain_modules()

if __name__ == "__main__":
    # Mode démonstration
    print("⛓️ Modules Blockchain OSINT - Démonstration")
    print("=" * 50)
    
    from core.config_manager import ConfigManager
    
    config = ConfigManager()
    manager = BlockchainManager(config)
    
    print(f"📊 Blockchains supportées: {manager.get_supported_blockchains()}")
    print(f"🔧 Capacités: {manager.get_module_capabilities()}")
    
    # Exemples d'utilisation
    if manager.get_supported_blockchains():
        print("\n💡 Exemples d'utilisation:")
        print("  manager.get_address_info('1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa', 'bitcoin')")
        print("  manager.track_transactions('0x742d35Cc6634C0532925a3b8D', 'ethereum')")
        print("  manager.analyze_address_risk('adresse_ici', 'bitcoin')")
    
    print("💡 Prêt pour les investigations blockchain!")

