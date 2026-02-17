Eine leichtgewichtige, Python-basierte **Plex/Kodi-Alternative** für Minimalisten. 

![Vorschau](https://raw.githubusercontent.com/nobleman82/VideoHub/main/preview.png)# 

🎥 VideoHub ist ein schlankes Media-Center zur 
Verwaltung und Präsentation privater Videoarchive. 
Das Projekt bietet volle Flexibilität: Nutze die **VideoTools** lokal unter Windows zur Aufbereitung oder hoste den **VideoServer** via Flask auf einem Ubuntu-System.

## ✨ Kernfunktionen

### 🌐 Der Hub & Server (Hosting)
- **Flask-Integration:** Ein robuster, leichtgewichtiger Webserver zur Auslieferung deines Hubs.
- **Cross-Platform:** Optimiert für den Betrieb unter **Windows** und **Ubuntu Linux**.
- **Deployment-Ready:** Enthält eine `setup_ubuntu.sh` und ein Systemd-Service-File (`video_hub.service`) für echtes 24/7-Hosting auf einem Server oder Raspberry Pi.
- **Modern UI:** Responsive Dark-Mode Interface für Filme und Serien.

### 🛠 Die VideoTools (Automatisierung)
Das Herzstück für ein sauberes Archiv (GUI-basiert für Windows):
- **Movie Converter:** Automatisiertes Umwandeln von Videodateien mittels FFmpeg.
- **File & Serien Renamer:** Bringt Ordnung in Dateinamen (S01E01-Schema).
- **Metadaten Editor:** Komfortables Bearbeiten von Filminfos und Postern direkt in der JSON-Datenbank.
- **Video Update:** Synchronisiert dein Dateisystem automatisch mit dem Hub.
## 🚀 Installation & Setup

## 📋 Voraussetzungen

Bevor du startest, benötigst du:
1. **Python 3.x** & **FFmpeg** (für den Converter).
2. **TMDB API Key:** Für die automatische Abfrage von Filminformationen und Postern benötigst du einen kostenlosen API-Key von [TheMovieDB.org](https://www.themoviedb.org/documentation/api).
   - Der Key muss in der `.env` Datei unter `TMDB_API_KEY=dein_key_hier` eingetragen werden.

### 1. Repository klonen
```bash
git clone [https://github.com/nobleman82/VideoHub.git](https://github.com/nobleman82/VideoHub.git)
cd VideoHub
````
### 2. Umgebung einrichten
Wir empfehlen die Nutzung eines Virtual Environments:

Bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r VideoHub/requirements.txt
3. Konfiguration
Kopiere die .env_example Dateien in den jeweiligen Ordnern zu .env und passe deine lokalen Pfade an:

VideoHub/.env: Pfade für den Web-Server und Metadaten.

VideoTools/.env: Pfade für die Automatisierungstools.

## 🚀 Installation & Setup

### 🪟 Windows (Lokal)
1. Umgebung einrichten:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r VideoHub/requirements.txt
.env_windows.example zu .env kopieren und Pfade anpassen.

Start des Servers via Flask oder Nutzung der Tools im Ordner VideoTools/.


### 🐧 Ubuntu Server (Remote Hosting)
Das Projekt ist für den Headless-Betrieb vorbereitet:

Skript ausführbar machen: chmod +x VideoHub/setup_ubuntu.sh

Installation starten: ./VideoHub/setup_ubuntu.sh

Die video_hub.service sorgt dafür, dass der Server nach jedem Neustart automatisch startet.


### 📂 Projektstruktur
VideoHub/: Enthält das Web-Frontend, CSS und die zentrale metadata.json.

VideoTools/: Die Python-Werkzeuge für das Datei-Management.

wwwroot/: Ort für generierte Thumbnails und statische Seiten.

### 🛠 Technologien
Backend/Tools: Python 3

Frontend: HTML5, CSS3 (Modern UI)

Verarbeitung: FFmpeg via Subprocess

Konfiguration: Dotenv (.env)

Entwickelt als schlanke Lösung für alle, die die volle Kontrolle über ihre Mediendaten behalten wollen.

### ⚖️Lizenz
Lizenz: Dieses Projekt steht unter der MIT-Lizenz (siehe LICENSE).
