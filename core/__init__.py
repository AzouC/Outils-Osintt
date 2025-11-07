# core/__init__.py
"""
OSINT Framework Pro - Core Package
Outil d'investigation OSINT avancé avec IA et analyse comportementale
"""

__version__ = "1.0.0"
__author__ = "AzouC"
__license__ = "MIT"

from .main import OSINTFramework
from .config_manager import ConfigManager
from .plugin_system import PluginSystem
from .security import SecurityManager

__all__ = [
    'OSINTFramework',
    'ConfigManager', 
    'PluginSystem',
    'SecurityManager'
]

# Initialisation du logging
import logging
from utils.logger import setup_logging

# Configuration du logging au démarrage
setup_logging()

logger = logging.getLogger(__name__)
logger.info("OSINT Framework Pro Core package initialized")
