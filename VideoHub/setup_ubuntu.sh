#!/bin/bash

# --- FARBEN FÜR DIE AUSGABE ---
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==============================================${NC}"
echo -e "${BLUE}   VideoHub Interaktives Setup (Ubuntu)       ${NC}"
echo -e "${BLUE}==============================================${NC}"

# --- ABFRAGEN ---

# 1. TMDB API Key
read -p "Bitte TMDB API Key eingeben: " TMDB_KEY
if [ -z "$TMDB_KEY" ]; then
    echo "Fehler: Ohne API Key funktioniert die Suche nicht."
    exit 1
fi

# 2. Apache Web-Root
read -e -p "Pfad zum Apache Web-Root [Default: /var/www/html]: " WWW_DIR
WWW_DIR=${WWW_DIR:-/var/www/html}

# 3. Pfad zu den Filmen
read -e -p "Pfad zu deinem Filme-Ordner: " FILME_PATH
if [ ! -d "$FILME_PATH" ]; then
    echo -e "Warnung: Pfad $FILME_PATH existiert aktuell nicht!"
fi

# 4. Pfad zu den Serien
read -e -p "Pfad zu deinem Serien-Ordner: " SERIEN_PATH
if [ ! -d "$SERIEN_PATH" ]; then
    echo -e "Warnung: Pfad $SERIEN_PATH existiert aktuell nicht!"
fi

echo -e "\n${GREEN}Konfiguration wird angewendet...${NC}\n"

# --- AB HIER STARTET DIE INSTALLATION ---

PROJECT_DIR=$(pwd)

# 1. System-Abhängigkeiten
sudo apt update && sudo apt install -y python3-pip python3-venv apache2 gunicorn

# 2. Frontend-Dateien in das Web-Root kopieren
echo "📂 Kopiere HTML/CSS Dateien nach $WWW_DIR..."
sudo mkdir -p $WWW_DIR/thumbs
sudo cp videohub_filme.html $WWW_DIR/
sudo cp videohub_serien.html $WWW_DIR/
sudo cp videohub_serien_silk.html $WWW_DIR/
sudo cp update_metadaten_status.html $WWW_DIR/
sudo cp videohub.css $WWW_DIR/

# 3. Berechtigungen setzen
sudo chown -R $USER:www-data $WWW_DIR
sudo chmod -R 775 $WWW_DIR

# 4. Python Umgebung & .env
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
./venv/bin/pip install flask flask-cors requests tmdbsimple python-dotenv gunicorn

# Linux .env Datei schreiben
cat <<EOF > .env
TMDB_API_KEY=$TMDB_KEY
APACHE_PATH=$WWW_DIR
FILME_PATH=$FILME_PATH
SERIEN_PATH=$SERIEN_PATH
EOF

# 5. Apache Aliase konfigurieren
CONF_FILE="/etc/apache2/conf-available/videohub-aliases.conf"
sudo bash -c "cat <<EOF > $CONF_FILE
Alias /Videos/Filme \"$FILME_PATH\"
Alias /Videos/Serie \"$SERIEN_PATH\"

<Directory \"$FILME_PATH\">
    Options Indexes FollowSymLinks
    AllowOverride None
    Require all granted
</Directory>

<Directory \"$SERIEN_PATH\">
    Options Indexes FollowSymLinks
    AllowOverride None
    Require all granted
</Directory>
EOF"

sudo a2enconf videohub-aliases
sudo systemctl reload apache2

# 6. Systemd Service einrichten
SERVICE_FILE="/etc/systemd/system/videohub.service"
sudo bash -c "cat <<EOF > $SERVICE_FILE
[Unit]
Description=VideoHub Flask Service
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment=\"PATH=$PROJECT_DIR/venv/bin\"
ExecStart=$PROJECT_DIR/venv/bin/gunicorn -w 1 -b 0.0.0.0:5000 video_update:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF"

sudo systemctl daemon-reload
sudo systemctl enable videohub
sudo systemctl start videohub

echo -e "\n${GREEN}✅ Installation erfolgreich abgeschlossen!${NC}"
echo -e "Webseite: ${BLUE}http://$(hostname -I | awk '{print $1}')${NC}"