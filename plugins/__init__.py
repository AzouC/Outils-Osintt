# plugins/__init__.py
"""
Système de plugins pour OSINT Framework Pro
"""

import os
import importlib.util

def load_plugins(plugin_dir="custom_plugins"):
    """Charge dynamiquement tous les plugins"""
    plugins = []
    plugin_path = os.path.join(os.path.dirname(__file__), plugin_dir)
    
    if not os.path.exists(plugin_path):
        return plugins
    
    for filename in os.listdir(plugin_path):
        if filename.endswith('.py') and not filename.startswith('_'):
            plugin_name = filename[:-3]
            try:
                spec = importlib.util.spec_from_file_location(
                    plugin_name, 
                    os.path.join(plugin_path, filename)
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                plugins.append(module)
                print(f"✅ Plugin chargé: {plugin_name}")
            except Exception as e:
                print(f"❌ Erreur chargement plugin {filename}: {e}")
    
    return plugins

__all__ = ['load_plugins']
