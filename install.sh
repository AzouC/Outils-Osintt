#!/bin/bash
# install.sh
echo "🕵️ OSINT Framework Pro - Installation Complete"
echo "=============================================="

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Fonction de logging
log() {
    echo -e "${GREEN}[+]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

error() {
    echo -e "${RED}[-]${NC} $1"
}

# Vérification root
if [ "$EUID" -eq 0 ]; then
    warn "Running as root - this is not recommended for security reasons"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

log "Starting OSINT Framework Pro installation..."

# Mise à jour du système
log "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Installation des dépendances système
log "Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    tor \
    proxychains4 \
    docker.io \
    docker-compose \
    chromium-browser \
    chromium-driver \
    libxml2-dev \
    libxslt-dev \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    zlib1g-dev

# Création de l'environnement virtuel
log "Creating Python virtual environment..."
python3 -m venv osint-env
source osint-env/bin/activate

# Installation des dépendances Python
log "Installing Python dependencies..."
pip install --upgrade pip

cat > requirements.txt << 'EOF'
# Core
aiohttp==3.8.5
asyncio==3.4.3
requests==2.31.0

# Data Analysis
pandas==2.0.3
numpy==1.24.3
scikit-learn==1.3.0

# Web & Scraping
beautifulsoup4==4.12.2
selenium==4.10.0
scrapy==2.9.0
flask==2.3.3
flask-socketio==5.3.6
flask-cors==4.0.0

# AI & ML
torch==2.0.1
transformers==4.31.0
opencv-python==4.8.0.74
face-recognition==1.3.0
spacy==3.6.0
textblob==0.17.1
nltk==3.8.1

# Blockchain
web3==6.5.0
blockchain==1.4.4

# Geolocation
geopy==2.3.0
phonenumbers==8.13.11
python-whois==0.8.0

# Visualization
plotly==5.15.0
matplotlib==3.7.2
networkx==3.1
pyvis==0.3.2
folium==0.14.0

# Security
cryptography==41.0.3
pycryptodome==3.18.0
stem==1.8.2

# Utilities
python-dotenv==1.0.0
pyyaml==6.0
colorama==0.4.6
tqdm==4.65.0
pillow==10.0.0
qrcode==7.4.2

# APIs
tweepy==4.14.0
telethon==1.28.5
instagram-private-api==1.6.0
python-linkedin==2.1
shodan==1.29.0
EOF

pip install -r requirements.txt

# Téléchargement des modèles NLP
log "Downloading AI models..."
python3 -c "
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('vader_lexicon')
nltk.download('averaged_perceptron_tagger')
"

python3 -m spacy download en_core_web_sm
python3 -m spacy download fr_core_news_sm

# Installation des outils externes
log "Installing external OSINT tools..."

# Sherlock
git clone https://github.com/sherlock-project/sherlock.git
cd sherlock
pip install -r requirements.txt
cd ..

# PhoneInfoga
git clone https://github.com/sundowndev/phoneinfoga.git
cd phoneinfoga
sudo docker build -t phoneinfoga .
cd ..

# theHarvester
sudo apt install -y theharvester

# Recon-ng
git clone https://github.com/lanmaster53/recon-ng.git
cd recon-ng
pip install -r REQUIREMENTS
cd ..

# Maltego (optionnel)
wget -O maltego.deb https://maltego-downloads.s3.us-east-2.amazonaws.com/linux/Maltego.v4.3.0.deb
sudo dpkg -i maltego.deb || sudo apt-get install -f -y
rm maltego.deb

# Configuration des dossiers
log "Setting up directory structure..."
mkdir -p {data/{cache,exports,databases},logs,config,plugins/custom_plugins}

# Configuration initiale
cat > config/api_keys.yaml << 'EOF'
# OSINT Framework Pro - Configuration des APIs
# Obtenez ces clés depuis les sites des fournisseurs

shodan:
  api_key: "YOUR_SHODAN_API_KEY"

twitter:
  consumer_key: "YOUR_TWITTER_CONSUMER_KEY"
  consumer_secret: "YOUR_TWITTER_CONSUMER_SECRET"
  access_token: "YOUR_TWITTER_ACCESS_TOKEN"
  access_token_secret: "YOUR_TWITTER_ACCESS_TOKEN_SECRET"

telegram:
  api_id: "YOUR_TELEGRAM_API_ID"
  api_hash: "YOUR_TELEGRAM_API_HASH"

instagram:
  session_id: "YOUR_INSTAGRAM_SESSION_ID"

hibp:
  api_key: "YOUR_HIBP_API_KEY"

google:
  api_key: "YOUR_GOOGLE_API_KEY"
  cse_id: "YOUR_GOOGLE_CSE_ID"

blockchain:
  etherscan_api: "YOUR_ETHERSCAN_API_KEY"
  blockchain_com_api: "YOUR_BLOCKCHAIN_COM_API_KEY"

virustotal:
  api_key: "YOUR_VIRUSTOTAL_API_KEY"

# Configuration Tor
tor:
  enabled: true
  socks_port: 9050
  control_port: 9051
EOF

cat > config/settings.yaml << 'EOF'
# Paramètres de l'application
app:
  name: "OSINT Framework Pro"
  version: "1.0.0"
  debug: false
  secret_key: "change-this-in-production"
  
investigation:
  default_depth: 2
  max_concurrent_requests: 10
  request_timeout: 30
  rate_limit_delay: 1

security:
  use_tor: true
  proxy_rotation: true
  user_agent_rotation: true
  encrypt_local_data: true
  
ai:
  enabled: true
  sentiment_analysis: true
  entity_recognition: true
  risk_assessment: true

export:
  default_formats: ["json", "html"]
  include_timestamps: true
  compress_exports: true
EOF

# Configuration de Tor
log "Configuring Tor..."
sudo systemctl enable tor
sudo systemctl start tor

# Création du script de lancement
cat > osint-pro << 'EOF'
#!/bin/bash
source osint-env/bin/activate
python3 core/main.py "$@"
EOF

chmod +x osint-pro
sudo mv osint-pro /usr/local/bin/

# Finalisation
log "Installation completed successfully!"
echo ""
echo "🎉 OSINT Framework Pro is ready to use!"
echo ""
echo "Quick start:"
echo "  osint-pro --interactive"
echo "  osint-pro -t email -v target@example.com -d 2"
echo "  osint-pro --web-ui"
echo ""
echo "Don't forget to:"
echo "  1. Configure your API keys in config/api_keys.yaml"
echo "  2. Review settings in config/settings.yaml"
echo "  3. Test the installation with: osint-pro --help"
echo ""
echo "Documentation: https://github.com/yourusername/osint-pro"
