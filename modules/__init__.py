# web/__init__.py
"""
Interface web pour OSINT Framework Pro
"""

from .app import create_app
from .api import api_bp

__all__ = [
    'create_app',
    'api_bp'
]
