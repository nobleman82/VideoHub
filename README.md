# 🎥 VideoHub

Eine leichtgewichtige, Python-basierte **Plex/Kodi-Alternative** für Minimalisten. 

VideoHub ist ein schlankes Media-Center zur Verwaltung und Präsentation privater Videoarchive. Im Gegensatz zu überladenen Lösungen setzt VideoHub auf Transparenz, lokale Kontrolle und verzichtet auf komplexe Datenbank-Silos. Alle Metadaten werden in einer einfachen `metadata.json` verwaltet.

## ✨ Kernfunktionen

### 🌐 Der Hub (Web-Interface)
- **Responsive Design:** Optimiert für Desktop und mobile Endgeräte.
- **Dark Mode:** Modernes, augenschonendes Interface für Filme und Serien.
- **Statische Struktur:** Extrem schnell durch HTML/JSON-Basis – kein schwerfälliger Webserver-Overkill.

### 🛠 Die VideoTools (Automatisierung)
Das Herzstück für ein sauberes Archiv. Die Suite umfasst:
- **Movie Converter:** Automatisiertes Umwandeln von Videodateien mittels FFmpeg.
- **File & Serien Renamer:** Bringt Ordnung in Dateinamen (unterstützt S01E01-Schema).
- **Metadaten Editor:** Komfortables Bearbeiten von Filminfos und Postern direkt in der JSON-Datenbank.
- **Video Update:** Automatische Synchronisierung deines Dateisystems mit dem Hub.

## 🚀 Installation & Setup

### Voraussetzungen
- **Python 3.x**
- **FFmpeg** (muss im System-PATH registriert sein für den Converter)

### 1. Repository klonen
```bash
git clone [https://github.com/nobleman82/VideoHub.git](https://github.com/nobleman82/VideoHub.git)
cd VideoHub
2. Umgebung einrichten
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

📂 Projektstruktur
VideoHub/: Enthält das Web-Frontend, CSS und die zentrale metadata.json.

VideoTools/: Die Python-Werkzeuge für das Datei-Management.

wwwroot/: Ort für generierte Thumbnails und statische Seiten.

🛠 Technologien
Backend/Tools: Python 3

Frontend: HTML5, CSS3 (Modern UI)

Verarbeitung: FFmpeg via Subprocess

Konfiguration: Dotenv (.env)

Entwickelt als schlanke Lösung für alle, die die volle Kontrolle über ihre Mediendaten behalten wollen.
