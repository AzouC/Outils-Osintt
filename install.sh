
## 📁 **Fichier : `install.sh`**

```bash
#!/bin/bash

# Outils OSINT - Script d'installation
# Développé par AzouC - https://github.com/AzouC/Outils-Osintt

set -e

# Couleurs pour l'output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction de logging
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Vérification des prérequis
check_requirements() {
    log "Vérification des prérequis..."
    
    # Vérifier Python
    if command -v python3 &>/dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &>/dev/null; then
        PYTHON_CMD="python"
    else
        error "Python 3.8+ est requis mais non installé"
        exit 1
    fi
    
    # Vérifier la version de Python
    PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    if [[ $(echo "$PYTHON_VERSION < 3.8" | bc -l) -eq 1 ]]; then
        error "Python 3.8+ requis. Version actuelle: $PYTHON_VERSION"
        exit 1
    fi
    
    log "Python $PYTHON_VERSION détecté"
    
    # Vérifier pip
    if ! command -v pip3 &>/dev/null && ! command -v pip &>/dev/null; then
        error "pip est requis mais non installé"
        exit 1
    fi
    
    # Vérifier git
    if ! command -v git &>/dev/null; then
        error "git est requis mais non installé"
        exit 1
    fi
}

# Installation des dépendances système
install_system_deps() {
    log "Installation des dépendances système..."
    
    # Détection de la distribution
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
    else
        error "Impossible de détecter le système d'exploitation"
        exit 1
    fi
    
    case $OS in
        *"Kali"*|*"Debian"*|*"Ubuntu"*)
            warn "Installation des paquets système pour Debian/Ubuntu/Kali..."
            sudo apt update
            sudo apt install -y python3-venv python3-pip build-essential \
                libssl-dev libffi-dev python3-dev &>/dev/null
            ;;
        *"Fedora"*|*"Red Hat"*)
            warn "Installation des paquets système pour Fedora/RHEL..."
            sudo dnf install -y python3-venv python3-pip gcc openssl-devel \
                libffi-devel python3-devel &>/dev/null
            ;;
        *"Arch"*)
            warn "Installation des paquets système pour Arch Linux..."
            sudo pacman -S --noconfirm python python-pip base-devel \
                openssl libffi &>/dev/null
            ;;
        *)
            warn "Distribution non reconnue. Installation manuelle des dépendances requise."
            ;;
    esac
}

# Création de l'environnement virtuel
setup_venv() {
    log "Configuration de l'environnement virtuel..."
    
    if [ ! -d "venv" ]; then
        $PYTHON_CMD -m venv venv
        log "Environnement virtuel créé"
    else
        warn "Environnement virtuel existant détecté"
    fi
    
    # Activation de l'environnement
    source venv/bin/activate
    
    # Mise à jour de pip
    pip install --upgrade pip &>/dev/null
}

# Installation des dépendances Python
install_python_deps() {
    log "Installation des dépendances Python..."
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log "Dépendances Python installées"
    else
        error "Fichier requirements.txt non trouvé"
        exit 1
    fi
}

# Configuration initiale
setup_config() {
    log "Configuration initiale..."
    
    # Création des répertoires de données
    mkdir -p data/{databases,cache,exports,logs,visualizations}
    
    # Configuration des exemples
    if [ ! -f "config/api_keys.yml" ]; then
        if [ -f "config/api_keys.yml.example" ]; then
            cp config/api_keys.yml.example config/api_keys.yml
            warn "Fichier de configuration API créé. Configurez vos clés dans config/api_keys.yml"
        else
            warn "Création du fichier de configuration API..."
            cat > config/api_keys.yml << EOF
# Configuration des clés API
api_keys:
  shodan: "VOTRE_CLE_API_SHODAN_ICI"
  # twitter_bearer_token: "VOTRE_TOKEN_TWITTER_ICI"
  # virus_total: "VOTRE_CLE_VIRUSTOTAL_ICI"
  # hibp: "VOTRE_CLE_HIBP_ICI"

# Note: Remplacer les valeurs par vos clés API réelles
EOF
        fi
    fi
    
    # Configuration des paramètres
    if [ ! -f "config/settings.yml" ]; then
        cat > config/settings.yml << EOF
# Paramètres de l'application
settings:
  log_level: "INFO"
  log_directory: "data/logs"
  export_directory: "data/exports"
  visualization_directory: "data/visualizations"
  max_concurrent_requests: 5
  request_timeout: 30
  enable_encryption: true
  theme: "dark"
  language: "fr"
EOF
    fi
}

# Vérification de l'installation
verify_installation() {
    log "Vérification de l'installation..."
    
    # Test d'import Python
    if $PYTHON_CMD -c "
import sys
sys.path.append('.')
try:
    from core.main import OSINTFramework
    from utils.logger import get_logger
    print('Import des modules: OK')
except Exception as e:
    print(f'Erreur import: {e}')
    sys.exit(1)
" ; then
        log "Tests d'import réussis"
    else
        error "Erreur lors des tests d'import"
        exit 1
    fi
    
    # Vérification des répertoires
    for dir in data data/databases data/cache data/exports data/logs data/visualizations; do
        if [ -d "$dir" ]; then
            log "Répertoire $dir: OK"
        else
            error "Répertoire $dir manquant"
            exit 1
        fi
    done
}

# Message de fin
show_completion() {
    echo
    log "🎉 Installation terminée avec succès !"
    echo
    info "Prochaines étapes:"
    echo "1. Configurez vos clés API dans: config/api_keys.yml"
    echo "2. Activez l'environnement virtuel: source venv/bin/activate"
    echo "3. Lancez l'application: python -m core.main"
    echo
    info "Commandes utiles:"
    echo "  - Interface principale: python -m core.main"
    echo "  - Interface web: python web/app.py"
    echo "  - Tests: python -m pytest tests/"
    echo
    warn "⚠️  N'oubliez pas de configurer vos clés API avant utilisation !"
    echo
}

# Fonction principale
main() {
    clear
    echo "================================================"
    echo "    Installation d'Outils OSINT"
    echo "    Développé par AzouC"
    echo "================================================"
    echo
    
    check_requirements
    install_system_deps
    setup_venv
    install_python_deps
    setup_config
    verify_installation
    show_completion
}

# Exécution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
