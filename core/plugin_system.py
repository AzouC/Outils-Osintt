# core/plugin_system.py
import importlib.util
import os
import sys
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

class PluginSystem:
    def __init__(self, config_manager=None):
        self.plugins = {}
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        self.plugins_dir = "plugins/custom_plugins"
        
    def load_plugins(self, plugin_dir: str = None) -> Dict[str, Any]:
        """Charge tous les plugins disponibles"""
        if plugin_dir:
            self.plugins_dir = plugin_dir
            
        if not os.path.exists(self.plugins_dir):
            self.logger.warning(f"Dossier plugins non trouvé: {self.plugins_dir}")
            os.makedirs(self.plugins_dir, exist_ok=True)
            return self.plugins
        
        self.logger.info(f"Chargement des plugins depuis: {self.plugins_dir}")
        
        for filename in os.listdir(self.plugins_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                plugin_name = filename[:-3]
                plugin_path = os.path.join(self.plugins_dir, filename)
                
                try:
                    # Chargement dynamique du module
                    spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[plugin_name] = module
                        spec.loader.exec_module(module)
                        
                        # Vérifier que le plugin a les méthodes requises
                        if hasattr(module, 'Plugin'):
                            plugin_instance = module.Plugin(self.config)
                            self.plugins[plugin_name] = plugin_instance
                            self.logger.info(f"✅ Plugin chargé: {plugin_name}")
                        else:
                            self.logger.warning(f"Plugin {plugin_name} n'a pas de classe Plugin")
                            
                except Exception as e:
                    self.logger.error(f"❌ Erreur chargement plugin {filename}: {e}")
        
        self.logger.info(f"Plugins chargés: {len(self.plugins)}")
        return self.plugins
    
    def get_plugins(self) -> Dict[str, Any]:
        """Retourne tous les plugins chargés"""
        return self.plugins
    
    def get_plugin(self, plugin_name: str) -> Optional[Any]:
        """Retourne un plugin spécifique"""
        return self.plugins.get(plugin_name)
    
    def execute_plugin_method(self, plugin_name: str, method: str, *args, **kwargs) -> Any:
        """Exécute une méthode d'un plugin"""
        plugin = self.get_plugin(plugin_name)
        if plugin and hasattr(plugin, method):
            return getattr(plugin, method)(*args, **kwargs)
        else:
            self.logger.error(f"Plugin {plugin_name} ou méthode {method} non trouvé")
            return None
    
    def get_available_plugins_info(self) -> List[Dict[str, str]]:
        """Retourne les informations sur les plugins disponibles"""
        plugins_info = []
        
        for plugin_name, plugin_instance in self.plugins.items():
            info = {
                'name': plugin_name,
                'description': getattr(plugin_instance, 'description', 'No description'),
                'version': getattr(plugin_instance, 'version', '1.0.0'),
                'author': getattr(plugin_instance, 'author', 'Unknown'),
                'enabled': True
            }
            plugins_info.append(info)
        
        return plugins_info
    
    def reload_plugins(self):
        """Recharge tous les plugins"""
        self.plugins.clear()
        self.load_plugins()
    
    def create_plugin_template(self, plugin_name: str):
        """Crée un template de plugin"""
        template = f'''"""
Plugin {plugin_name} pour OSINT Framework Pro
"""
import logging
from typing import Dict, Any

class Plugin:
    def __init__(self, config_manager=None):
        self.name = "{plugin_name}"
        self.description = "Description du plugin {plugin_name}"
        self.version = "1.0.0"
        self.author = "Votre Nom"
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        
    def investigate(self, target: str, target_type: str, depth: int = 1) -> Dict[str, Any]:
        """Méthode principale d'investigation"""
        self.logger.info(f"Plugin {{self.name}} investigation: {{target}}")
        
        return {{
            "plugin": self.name,
            "target": target,
            "results": {{
                "data": "Exemple de données du plugin",
                "status": "success"
            }}
        }}
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Retourne les capacités du plugin"""
        return {{
            "target_types": ["email", "phone", "username"],
            "depth_levels": [1, 2],
            "features": ["basic_search", "advanced_analysis"]
        }}
'''

        plugin_path = os.path.join(self.plugins_dir, f"{plugin_name}.py")
        with open(plugin_path, 'w', encoding='utf-8') as f:
            f.write(template)
        
        self.logger.info(f"Template de plugin créé: {plugin_path}")
        return plugin_path

# Exemple de plugin de base
class BasePlugin:
    """Classe de base pour tous les plugins"""
    
    def __init__(self, config_manager=None):
        self.config = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def validate_target(self, target: str, target_type: str) -> bool:
        """Valide la cible pour ce plugin"""
        return True
    
    def get_required_configs(self) -> List[str]:
        """Retourne les configurations requises"""
        return []
