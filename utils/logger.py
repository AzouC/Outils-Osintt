"""
Module de logging avancé
Système de journalisation unifié pour l'application OSINT
"""

import logging
import logging.handlers
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import inspect
import os
from threading import Lock

class JSONFormatter(logging.Formatter):
    """
    Formateur de logs en JSON pour une meilleure intégration
    """
    
    def __init__(self):
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format le log record en JSON
        
        Args:
            record: Record de log
            
        Returns:
            Chaîne JSON formatée
        """
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
            'process_id': record.process,
            'thread_id': record.thread,
            'thread_name': record.threadName
        }
        
        # Ajout des données supplémentaires
        if hasattr(record, 'extra_data'):
            log_entry['extra_data'] = record.extra_data
        
        # Gestion des exceptions
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)

class ColorFormatter(logging.Formatter):
    """
    Formateur de logs avec couleurs pour la console
    """
    
    # Codes de couleurs ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Vert
        'WARNING': '\033[33m',    # Jaune
        'ERROR': '\033[31m',      # Rouge
        'CRITICAL': '\033[41m',   # Fond rouge
        'RESET': '\033[0m'        # Reset
    }
    
    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        fmt = fmt or '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
        super().__init__(fmt, datefmt)
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format le log record avec couleurs
        
        Args:
            record: Record de log
            
        Returns:
            Chaîne formatée avec couleurs
        """
        # Sauvegarde du format original
        original_fmt = self._style._fmt
        
        # Ajout des couleurs
        if record.levelname in self.COLORS:
            color = self.COLORS[record.levelname]
            reset = self.COLORS['RESET']
            self._style._fmt = f"{color}{original_fmt}{reset}"
        
        result = super().format(record)
        
        # Restauration du format original
        self._style._fmt = original_fmt
        
        return result

class Logger:
    """
    Logger personnalisé avec fonctionnalités étendues
    """
    
    _instances: Dict[str, 'Logger'] = {}
    _lock = Lock()
    
    def __init__(self, name: str = None, config: Dict[str, Any] = None):
        """
        Initialise le logger
        
        Args:
            name: Nom du logger (généralement __name__)
            config: Configuration du logging
        """
        if name is None:
            # Utilise le nom du module appelant
            frame = inspect.currentframe()
            try:
                caller_frame = frame.f_back
                name = caller_frame.f_globals.get('__name__', 'unknown')
            finally:
                del frame
        
        self.name = name
        self.config = config or {}
        self._logger = logging.getLogger(name)
        
        # Évite la propagation vers le root logger pour éviter les doublons
        self._logger.propagate = False
        
        # Configuration du niveau de log
        self._setup_log_level()
        
        # Configuration des handlers s'ils n'existent pas déjà
        if not self._logger.handlers:
            self._setup_handlers()
        
        # Stockage de l'instance
        with Logger._lock:
            Logger._instances[name] = self
    
    def _setup_log_level(self):
        """Configure le niveau de log"""
        log_level = self.config.get('log_level', 'INFO')
        level = getattr(logging, log_level.upper(), logging.INFO)
        self._logger.setLevel(level)
    
    def _setup_handlers(self):
        """Configure les handlers de log"""
        # Handler console
        console_handler = self._create_console_handler()
        self._logger.addHandler(console_handler)
        
        # Handler fichier
        file_handler = self._create_file_handler()
        if file_handler:
            self._logger.addHandler(file_handler)
        
        # Handler JSON pour l'analyse
        json_handler = self._create_json_handler()
        if json_handler:
            self._logger.addHandler(json_handler)
    
    def _create_console_handler(self) -> logging.Handler:
        """
        Crée le handler pour la console
        
        Returns:
            Handler configuré
        """
        handler = logging.StreamHandler(sys.stdout)
        
        # Utilise le formateur couleur si supporté
        if sys.stdout.isatty():
            formatter = ColorFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        handler.setFormatter(formatter)
        handler.setLevel(self._logger.level)
        
        return handler
    
    def _create_file_handler(self) -> Optional[logging.Handler]:
        """
        Crée le handler pour les fichiers
        
        Returns:
            Handler configuré ou None
        """
        try:
            log_dir = self.config.get('log_directory', 'logs')
            log_path = Path(log_dir)
            
            # Création du répertoire si nécessaire
            log_path.mkdir(parents=True, exist_ok=True)
            
            # Nom du fichier avec timestamp
            timestamp = datetime.now().strftime('%Y%m%d')
            log_file = log_path / f"osint_tool_{timestamp}.log"
            
            handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5,
                encoding='utf-8'
            )
            
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)-20s | %(module)s:%(funcName)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            handler.setFormatter(formatter)
            handler.setLevel(logging.DEBUG)  # Fichier contient tous les logs
            
            return handler
            
        except Exception as e:
            print(f"Impossible de créer le handler fichier: {e}")
            return None
    
    def _create_json_handler(self) -> Optional[logging.Handler]:
        """
        Crée le handler JSON pour l'analyse
        
        Returns:
            Handler JSON configuré ou None
        """
        try:
            log_dir = self.config.get('log_directory', 'logs')
            log_path = Path(log_dir)
            log_path.mkdir(parents=True, exist_ok=True)
            
            # Fichier JSON séparé
            timestamp = datetime.now().strftime('%Y%m%d')
            json_log_file = log_path / f"osint_tool_{timestamp}.json.log"
            
            handler = logging.handlers.RotatingFileHandler(
                json_log_file,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=3,
                encoding='utf-8'
            )
            
            formatter = JSONFormatter()
            handler.setFormatter(formatter)
            handler.setLevel(logging.INFO)
            
            return handler
            
        except Exception as e:
            print(f"Impossible de créer le handler JSON: {e}")
            return None
    
    def debug(self, message: str, extra_data: Dict[str, Any] = None, **kwargs):
        """Log niveau DEBUG"""
        self._log(logging.DEBUG, message, extra_data, **kwargs)
    
    def info(self, message: str, extra_data: Dict[str, Any] = None, **kwargs):
        """Log niveau INFO"""
        self._log(logging.INFO, message, extra_data, **kwargs)
    
    def warning(self, message: str, extra_data: Dict[str, Any] = None, **kwargs):
        """Log niveau WARNING"""
        self._log(logging.WARNING, message, extra_data, **kwargs)
    
    def error(self, message: str, extra_data: Dict[str, Any] = None, **kwargs):
        """Log niveau ERROR"""
        self._log(logging.ERROR, message, extra_data, **kwargs)
    
    def critical(self, message: str, extra_data: Dict[str, Any] = None, **kwargs):
        """Log niveau CRITICAL"""
        self._log(logging.CRITICAL, message, extra_data, **kwargs)
    
    def _log(self, level: int, message: str, extra_data: Dict[str, Any] = None, **kwargs):
        """
        Méthode de log interne
        
        Args:
            level: Niveau de log
            message: Message à logger
            extra_data: Données supplémentaires
            **kwargs: Arguments supplémentaires
        """
        if extra_data is None:
            extra_data = {}
        
        # Fusion avec les kwargs
        extra_data.update(kwargs)
        
        # Création du record avec données supplémentaires
        if extra_data:
            record = self._logger.makeRecord(
                self._logger.name, level, 
                fn='', lno=0, 
                msg=message, args=(), 
                exc_info=None, 
                extra={'extra_data': extra_data}
            )
        else:
            record = self._logger.makeRecord(
                self._logger.name, level, 
                fn='', lno=0, 
                msg=message, args=(), 
                exc_info=None
            )
        
        self._logger.handle(record)
    
    def log_operation(self, operation: str, target: str, status: str, 
                     details: Dict[str, Any] = None):
        """
        Log une opération OSINT structurée
        
        Args:
            operation: Type d'opération (ex: "email_analysis", "domain_lookup")
            target: Cible de l'opération
            status: Statut ("started", "completed", "failed")
            details: Détails supplémentaires
        """
        if details is None:
            details = {}
        
        log_data = {
            'operation': operation,
            'target': target,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            **details
        }
        
        if status == 'failed':
            self.error(f"Operation {operation} failed for {target}", extra_data=log_data)
        elif status == 'completed':
            self.info(f"Operation {operation} completed for {target}", extra_data=log_data)
        else:
            self.info(f"Operation {operation} {status} for {target}", extra_data=log_data)
    
    def log_api_call(self, service: str, endpoint: str, method: str = 'GET',
                    status_code: int = None, response_time: float = None,
                    error: str = None):
        """
        Log un appel API structuré
        
        Args:
            service: Service API (ex: "shodan", "whois")
            endpoint: Point de terminaison
            method: Méthode HTTP
            status_code: Code de statut HTTP
            response_time: Temps de réponse en secondes
            error: Message d'erreur
        """
        log_data = {
            'api_service': service,
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'response_time': response_time,
            'timestamp': datetime.now().isoformat()
        }
        
        if error:
            log_data['error'] = error
            self.error(f"API call to {service} failed: {error}", extra_data=log_data)
        else:
            level = logging.DEBUG if status_code and status_code < 400 else logging.WARNING
            message = f"API call to {service}: {method} {endpoint} - {status_code}"
            if response_time:
                message += f" ({response_time:.2f}s)"
            
            self._log(level, message, extra_data=log_data)
    
    def set_level(self, level: str):
        """
        Change le niveau de log dynamiquement
        
        Args:
            level: Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        level_obj = getattr(logging, level.upper(), logging.INFO)
        self._logger.setLevel(level_obj)
        
        # Met à jour tous les handlers
        for handler in self._logger.handlers:
            if not isinstance(handler, logging.FileHandler):
                handler.setLevel(level_obj)
    
    def get_log_file_path(self) -> Optional[Path]:
        """
        Récupère le chemin du fichier de log actuel
        
        Returns:
            Chemin du fichier ou None
        """
        for handler in self._logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                return Path(handler.baseFilename)
        return None
    
    @classmethod
    def get_logger(cls, name: str = None, config: Dict[str, Any] = None) -> 'Logger':
        """
        Récupère ou crée un logger (pattern Singleton)
        
        Args:
            name: Nom du logger
            config: Configuration
            
        Returns:
            Instance du logger
        """
        if name is None:
            frame = inspect.currentframe()
            try:
                caller_frame = frame.f_back
                name = caller_frame.f_globals.get('__name__', 'unknown')
            finally:
                del frame
        
        with cls._lock:
            if name not in cls._instances:
                cls._instances[name] = cls(name, config)
            
            return cls._instances[name]
    
    @classmethod
    def shutdown_all(cls):
        """Ferme tous les loggers"""
        for logger in cls._instances.values():
            for handler in logger._logger.handlers:
                handler.close()
        
        cls._instances.clear()

# Fonction utilitaire pour une utilisation rapide
def setup_logging(config: Dict[str, Any] = None) -> Logger:
    """
    Configure le logging global et retourne le root logger
    
    Args:
        config: Configuration du logging
        
    Returns:
        Logger racine
    """
    if config is None:
        config = {}
    
    # Configuration par défaut
    default_config = {
        'log_level': 'INFO',
        'log_directory': 'logs',
        'enable_file_logging': True,
        'enable_json_logging': True
    }
    
    default_config.update(config)
    
    # Création du logger racine
    root_logger = Logger.get_logger('osint_tool', default_config)
    
    return root_logger

def get_logger(name: str = None) -> Logger:
    """
    Récupère un logger par nom (raccourci)
    
    Args:
        name: Nom du logger
        
    Returns:
        Instance du logger
    """
    return Logger.get_logger(name)

# Context manager pour le logging
class LoggingContext:
    """
    Context manager pour le logging avec temporisation
    """
    
    def __init__(self, logger: Logger, level: int = logging.INFO, message: str = None):
        self.logger = logger
        self.level = level
        self.message = message
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        if self.message:
            self.logger._log(self.level, f"START: {self.message}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type:
            self.logger.error(
                f"FAILED: {self.message} (duration: {duration:.2f}s)",
                extra_data={'duration': duration, 'exception': str(exc_val)}
            )
        elif self.message:
            self.logger._log(
                self.level, 
                f"COMPLETED: {self.message} (duration: {duration:.2f}s)",
                extra_data={'duration': duration}
            )

def main():
    """Fonction de démonstration"""
    # Configuration de base
    config = {
        'log_level': 'DEBUG',
        'log_directory': 'test_logs'
    }
    
    logger = setup_logging(config)
    
    print("📝 Système de Logging OSINT")
    print("=" * 40)
    
    # Test des différents niveaux de log
    logger.debug("Message de debug - détails techniques")
    logger.info("Message d'information - opération normale")
    logger.warning("Message d'avertissement - attention requise")
    logger.error("Message d'erreur - problème détecté")
    
    # Log structuré
    logger.log_operation(
        operation="email_analysis",
        target="test@example.com",
        status="completed",
        details={"breaches_found": 2, "risk_level": "medium"}
    )
    
    # Log API
    logger.log_api_call(
        service="shodan",
        endpoint="/host/8.8.8.8",
        method="GET",
        status_code=200,
        response_time=1.23
    )
    
    # Utilisation du context manager
    with LoggingContext(logger, logging.INFO, "Test operation"):
        time.sleep(0.1)  # Simulation d'une opération
        print("Operation en cours...")
    
    print("\n✅ Logs générés avec succès")
    print(f"📁 Fichiers de log dans: {logger.get_log_file_path()}")

if __name__ == "__main__":
    import time
    main()
