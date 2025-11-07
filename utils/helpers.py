"""
Module d'utilitaires généraux
Fonctions helper réutilisables dans tout le projet
"""

import re
import time
import random
import hashlib
import ipaddress
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from urllib.parse import urlparse, quote, unquote
import socket
import os
from pathlib import Path
import json

def rate_limit(delay: float = 1.0, jitter: float = 0.3):
    """
    Pause avec délai aléatoire pour respecter les rate limits
    
    Args:
        delay: Délai de base en secondes
        jitter: Variation aléatoire (± jitter)
    """
    jitter_amount = random.uniform(-jitter, jitter)
    actual_delay = max(0.1, delay + jitter_amount)  # Minimum 0.1 seconde
    time.sleep(actual_delay)

def validate_email(email: str) -> bool:
    """
    Valide le format d'une adresse email
    
    Args:
        email: Adresse email à valider
        
    Returns:
        True si l'email est valide
    """
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email.strip()) is not None

def validate_domain(domain: str) -> bool:
    """
    Valide le format d'un nom de domaine
    
    Args:
        domain: Nom de domaine à valider
        
    Returns:
        True si le domaine est valide
    """
    if not domain or not isinstance(domain, str):
        return False
    
    domain = domain.strip().lower()
    
    # Pattern pour validation de domaine
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
    
    if not re.match(pattern, domain):
        return False
    
    # Vérification de la longueur totale
    if len(domain) > 253:
        return False
    
    # Vérification de chaque label
    labels = domain.split('.')
    for label in labels:
        if len(label) > 63:
            return False
    
    return True

def validate_ip(ip: str) -> bool:
    """
    Valide une adresse IP (IPv4 ou IPv6)
    
    Args:
        ip: Adresse IP à valider
        
    Returns:
        True si l'IP est valide
    """
    try:
        ipaddress.ip_address(ip.strip())
        return True
    except ValueError:
        return False

def validate_url(url: str) -> bool:
    """
    Valide le format d'une URL
    
    Args:
        url: URL à valider
        
    Returns:
        True si l'URL est valide
    """
    try:
        result = urlparse(url.strip())
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def normalize_url(url: str) -> str:
    """
    Normalise une URL pour la comparaison
    
    Args:
        url: URL à normaliser
        
    Returns:
        URL normalisée
    """
    try:
        parsed = urlparse(url.strip().lower())
        
        # Reconstruction sans fragments ni paramètres sensibles
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        # Ajout des paramètres de requête triés (optionnel)
        if parsed.query:
            params = sorted(parsed.query.split('&'))
            normalized += '?' + '&'.join(params)
        
        return normalized
    except Exception:
        return url.strip()

def generate_hash(data: str, algorithm: str = 'sha256') -> str:
    """
    Génère un hash d'une chaîne de caractères
    
    Args:
        data: Données à hacher
        algorithm: Algorithme de hachage (md5, sha1, sha256)
        
    Returns:
        Hash hexadécimal
    """
    if algorithm == 'md5':
        return hashlib.md5(data.encode('utf-8')).hexdigest()
    elif algorithm == 'sha1':
        return hashlib.sha1(data.encode('utf-8')).hexdigest()
    elif algorithm == 'sha256':
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    else:
        raise ValueError(f"Algorithme non supporté: {algorithm}")

def format_timestamp(timestamp: Union[str, datetime], format: str = 'iso') -> str:
    """
    Formate un timestamp dans différents formats
    
    Args:
        timestamp: Timestamp à formater
        format: Format de sortie (iso, human, file)
        
    Returns:
        Timestamp formaté
    """
    if isinstance(timestamp, str):
        try:
            # Essayer de parser le timestamp
            if 'T' in timestamp:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return timestamp
    
    if format == 'iso':
        return timestamp.isoformat()
    elif format == 'human':
        return timestamp.strftime('%d/%m/%Y %H:%M:%S')
    elif format == 'file':
        return timestamp.strftime('%Y%m%d_%H%M%S')
    else:
        return str(timestamp)

def parse_duration(duration_str: str) -> timedelta:
    """
    Parse une durée en chaîne de caractères en timedelta
    
    Args:
        duration_str: Durée sous forme de chaîne (ex: "1h30m", "2d", "45s")
        
    Returns:
        Objet timedelta
    """
    pattern = r'(\d+)([dhms])'
    matches = re.findall(pattern, duration_str.lower())
    
    if not matches:
        raise ValueError(f"Format de durée invalide: {duration_str}")
    
    duration = timedelta()
    for value, unit in matches:
        value = int(value)
        if unit == 'd':
            duration += timedelta(days=value)
        elif unit == 'h':
            duration += timedelta(hours=value)
        elif unit == 'm':
            duration += timedelta(minutes=value)
        elif unit == 's':
            duration += timedelta(seconds=value)
    
    return duration

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Divise une liste en chunks de taille fixe
    
    Args:
        lst: Liste à diviser
        chunk_size: Taille de chaque chunk
        
    Returns:
        Liste de chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def flatten_dict(nested_dict: Dict[str, Any], separator: str = '_', prefix: str = '') -> Dict[str, Any]:
    """
    Aplatit un dictionnaire imbriqué
    
    Args:
        nested_dict: Dictionnaire imbriqué
        separator: Séparateur pour les clés imbriquées
        prefix: Préfixe pour les clés
        
    Returns:
        Dictionnaire aplati
    """
    flattened = {}
    for key, value in nested_dict.items():
        new_key = f"{prefix}{separator}{key}" if prefix else key
        
        if isinstance(value, dict):
            flattened.update(flatten_dict(value, separator, new_key))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    flattened.update(flatten_dict(item, separator, f"{new_key}{separator}{i}"))
                else:
                    flattened[f"{new_key}{separator}{i}"] = item
        else:
            flattened[new_key] = value
    
    return flattened

def deep_get(dictionary: Dict[str, Any], keys: str, default: Any = None, separator: str = '.') -> Any:
    """
    Récupère une valeur imbriquée dans un dictionnaire avec une clé en notation pointée
    
    Args:
        dictionary: Dictionnaire source
        keys: Clé en notation pointée (ex: "user.profile.name")
        default: Valeur par défaut si la clé n'existe pas
        separator: Séparateur de clés
        
    Returns:
        Valeur trouvée ou valeur par défaut
    """
    try:
        keys_list = keys.split(separator)
        current = dictionary
        
        for key in keys_list:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    except (AttributeError, TypeError, KeyError):
        return default

def is_private_ip(ip: str) -> bool:
    """
    Vérifie si une IP est dans une plage privée
    
    Args:
        ip: Adresse IP à vérifier
        
    Returns:
        True si l'IP est privée
    """
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private
    except ValueError:
        return False

def get_hostname(ip: str) -> Optional[str]:
    """
    Récupère le hostname d'une adresse IP
    
    Args:
        ip: Adresse IP
        
    Returns:
        Hostname ou None
    """
    try:
        return socket.gethostbyaddr(ip)[0]
    except (socket.herror, socket.gaierror):
        return None

def clean_filename(filename: str, max_length: int = 255) -> str:
    """
    Nettoie un nom de fichier pour qu'il soit sûr
    
    Args:
        filename: Nom de fichier à nettoyer
        max_length: Longueur maximale
        
    Returns:
        Nom de fichier nettoyé
    """
    # Caractères interdits dans les noms de fichiers
    illegal_chars = r'[<>:"/\\|?*\x00-\x1f]'
    cleaned = re.sub(illegal_chars, '_', filename)
    
    # Suppression des espaces en début/fin
    cleaned = cleaned.strip()
    
    # Éviter les noms réservés Windows
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
        'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
        'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    
    if cleaned.upper() in reserved_names:
        cleaned = '_' + cleaned
    
    # Troncature si nécessaire
    if len(cleaned) > max_length:
        name, ext = os.path.splitext(cleaned)
        max_name_length = max_length - len(ext)
        cleaned = name[:max_name_length] + ext
    
    return cleaned

def human_readable_size(size_bytes: int) -> str:
    """
    Convertit une taille en bytes en format lisible
    
    Args:
        size_bytes: Taille en bytes
        
    Returns:
        Taille formatée (ex: "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    
    while size_bytes >= 1024 and unit_index < len(units) - 1:
        size_bytes /= 1024.0
        unit_index += 1
    
    return f"{size_bytes:.2f} {units[unit_index]}"

def retry_on_exception(max_retries: int = 3, delay: float = 1.0, 
                      exceptions: tuple = (Exception,), backoff: float = 2.0):
    """
    Décorateur pour réessayer une fonction en cas d'exception
    
    Args:
        max_retries: Nombre maximum de tentatives
        delay: Délai initial entre les tentatives
        exceptions: Exceptions à capturer
        backoff: Facteur de backoff exponentiel
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries > max_retries:
                        raise e
                    
                    time.sleep(current_delay)
                    current_delay *= backoff  # Backoff exponentiel
            
            return func(*args, **kwargs)  # Dernière tentative
        return wrapper
    return decorator

def timeout(seconds: float):
    """
    Décorateur pour timeout de fonction
    
    Args:
        seconds: Timeout en secondes
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")
            
            # Set up the signal handler
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(seconds))
            
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            
            return result
        return wrapper
    return decorator

def extract_emails(text: str) -> List[str]:
    """
    Extrait les adresses email d'un texte
    
    Args:
        text: Texte à analyser
        
    Returns:
        Liste d'emails trouvés
    """
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text)

def extract_urls(text: str) -> List[str]:
    """
    Extrait les URLs d'un texte
    
    Args:
        text: Texte à analyser
        
    Returns:
        Liste d'URLs trouvées
    """
    url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    urls = re.findall(url_pattern, text)
    
    # Normalisation des URLs
    normalized_urls = []
    for url in urls:
        if url.startswith('www.'):
            url = 'http://' + url
        normalized_urls.append(normalize_url(url))
    
    return normalized_urls

def extract_ips(text: str) -> List[str]:
    """
    Extrait les adresses IP d'un texte
    
    Args:
        text: Texte à analyser
        
    Returns:
        Liste d'IPs trouvées
    """
    ipv4_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    ipv6_pattern = r'\b(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}\b'
    
    ips = re.findall(ipv4_pattern, text) + re.findall(ipv6_pattern, text, re.IGNORECASE)
    
    # Validation des IPs trouvées
    valid_ips = []
    for ip in ips:
        if validate_ip(ip):
            valid_ips.append(ip)
    
    return valid_ips

def calculate_confidence_score(evidence: Dict[str, Any]) -> float:
    """
    Calcule un score de confiance basé sur des preuves
    
    Args:
        evidence: Dictionnaire de preuves et leurs poids
        
    Returns:
        Score de confiance entre 0 et 1
    """
    total_weight = 0
    weighted_sum = 0
    
    for proof, data in evidence.items():
        if isinstance(data, dict):
            weight = data.get('weight', 1.0)
            value = data.get('value', 0.0)
        else:
            weight = 1.0
            value = float(data)
        
        total_weight += weight
        weighted_sum += weight * value
    
    if total_weight == 0:
        return 0.0
    
    confidence = weighted_sum / total_weight
    return max(0.0, min(1.0, confidence))  # Clamp entre 0 et 1

def generate_user_agent() -> str:
    """
    Génère un User-Agent aléatoire réaliste
    
    Returns:
        User-Agent string
    """
    browsers = [
        # Chrome
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        # Firefox
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
        # Safari
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    ]
    
    return random.choice(browsers)

def is_json(data: str) -> bool:
    """
    Vérifie si une chaîne est un JSON valide
    
    Args:
        data: Chaîne à vérifier
        
    Returns:
        True si JSON valide
    """
    try:
        json.loads(data)
        return True
    except (json.JSONDecodeError, TypeError):
        return False

def safe_getenv(key: str, default: str = None) -> str:
    """
    Récupère une variable d'environnement de manière sécurisée
    
    Args:
        key: Clé de la variable d'environnement
        default: Valeur par défaut
        
    Returns:
        Valeur de la variable ou valeur par défaut
    """
    try:
        return os.getenv(key, default)
    except Exception:
        return default

def create_backup(filepath: str, backup_dir: str = None) -> Optional[str]:
    """
    Crée une sauvegarde d'un fichier
    
    Args:
        filepath: Chemin du fichier à sauvegarder
        backup_dir: Répertoire de sauvegarde
        
    Returns:
        Chemin de la sauvegarde ou None
    """
    try:
        path = Path(filepath)
        if not path.exists():
            return None
        
        if backup_dir is None:
            backup_dir = path.parent / 'backups'
        
        backup_path = Path(backup_dir)
        backup_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_path / f"{path.stem}_{timestamp}{path.suffix}"
        
        import shutil
        shutil.copy2(filepath, backup_file)
        
        return str(backup_file)
    except Exception:
        return None

def main():
    """Fonction principale pour test du module"""
    print("🛠️ Utilitaires Helper")
    print("=" * 40)
    
    # Tests des fonctions
    test_email = "test@example.com"
    test_ip = "192.168.1.1"
    test_url = "https://example.com/path?query=test"
    
    print(f"Email validation: {test_email} -> {validate_email(test_email)}")
    print(f"IP validation: {test_ip} -> {validate_ip(test_ip)}")
    print(f"URL validation: {test_url} -> {validate_url(test_url)}")
    print(f"Normalized URL: {test_url} -> {normalize_url(test_url)}")
    print(f"Hash SHA256: 'test' -> {generate_hash('test', 'sha256')}")
    print(f"Human readable size: 1024 -> {human_readable_size(1024)}")
    
    # Test extraction
    test_text = "Contact me at john@example.com or visit https://example.com"
    print(f"Emails in text: {extract_emails(test_text)}")
    print(f"URLs in text: {extract_urls(test_text)}")

if __name__ == "__main__":
    main()
