import os
import sys
import json
import requests
import tmdbsimple as tmdb
import time
import re 
from flask import Flask, render_template, jsonify, send_from_directory
from flask_cors import CORS 
from threading import Thread
from dotenv import load_dotenv

# --- 1. BETRIEBSSYSTEM-CHECK & ENV LADEN ---
if os.name == 'nt':  # Windows
    env_file = ".env_windows"
    default_www = r"C:/Users/mario/Documents/VB2026/VideoHub/VideoHub/VideoHub/wwwroot"
else:  # Ubuntu / Linux
    env_file = ".env"
    default_www = "/var/www/html"

if os.path.exists(env_file):
    load_dotenv(env_file)
    print(f"--- {env_file} erfolgreich geladen ---")
else:
    print(f"⚠️ WARNUNG: {env_file} nicht gefunden! Bitte erstelle sie aus der .example Datei.")

# Werte auslesen mit Fallback auf Standardwerte
WWWROOT_PATH = os.getenv("APACHE_PATH", default_www)
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

if not TMDB_API_KEY or TMDB_API_KEY == "dein_schluessel_hier":
    print("❌ FEHLER: Kein gültiger TMDB_API_KEY gefunden. Updates werden fehlschlagen.")

# --- 2. FLASK SETUP ---
# Wir nutzen WWWROOT_PATH für Templates (HTML) und statische Dateien
app = Flask(__name__, template_folder=WWWROOT_PATH, static_folder=WWWROOT_PATH)
CORS(app) 

# --- 3. KONFIGURATION ---
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
tmdb.API_KEY = TMDB_API_KEY

IMAGE_BASE_URL = "https://image.tmdb.org/t/p/"
POSTER_SIZE = "w300" 
BACKDROP_SIZE = "w1280"

# Pfade für Datenbank und Bilder (relativ zum Webroot)
DB_FILE = os.path.join(WWWROOT_PATH, 'metadata.json')
THUMBS_DIR = os.path.join(WWWROOT_PATH, 'thumbs')      
THUMBS_WEB_PATH = 'thumbs/'

# Video-Quellen aus ENV beziehen
FILME_PATH = os.getenv("FILME_PATH")
SERIEN_PATH = os.getenv("SERIEN_PATH")

VIDEO_SOURCES = {
    "Filme": {
        "type": "movie",                     
        "source_path": FILME_PATH,          
        "web_alias": 'Videos/Filme',         
    },
    "Serien": {
        "type": "tv",                        
        "source_path": SERIEN_PATH,        
        "web_alias": 'Videos/Serie',        
    }
}

ALLOWED_EXTENSIONS = ('.mp4', '.mkv', '.webm', '.avi', '.mov')
current_log = []
scan_status = "IDLE"

def log_message(msg, is_error=False):
    """Fügt eine Nachricht zum Log hinzu und gibt sie auf der Konsole aus."""
    prefix = "❌ FEHLER" if is_error else "✅ INFO"
    log_line = f"[{time.strftime('%H:%M:%S')}] {prefix}: {msg}"
    current_log.append(log_line)
    if is_error:
        print(log_line, file=sys.stderr)
    else:
        print(log_line)

# ------------------------------------------------
# HILFSFUNKTIONEN
# ------------------------------------------------

def clean_title_for_search(title, is_tv=False):
    title = title.replace('_', ' ').replace('.', ' ').strip()
    if is_tv:
        title = re.sub(r'[\s\.\-]+[Ss]\d+[Ee]\d+.*', '', title, flags=re.IGNORECASE).strip()
        title = re.sub(r'[\s\.\-]+(\d+x\d+).*', '', title, flags=re.IGNORECASE).strip()
        title = re.sub(r'[\s\.\-]+[Ss]taffel\s*\d+.*', '', title, flags=re.IGNORECASE).strip()
        parts = re.split(r' - | \- ', title, 1)
        if len(parts) > 1 and re.search(r'\d+', parts[1], flags=re.IGNORECASE):
             title = parts[0].strip()
    title = re.sub(r'_\d+$', '', title).strip()
    title = re.sub(r'\s*\(\d{4}\)$', '', title).strip()
    title = re.sub(r'\s*\d{4}$', '', title).strip()
    title = re.sub(r'\s*\[.*?\]', '', title, flags=re.DOTALL).strip()
    title = re.sub(r'\s*\(.*?\)', '', title, flags=re.DOTALL).strip() 
    title = re.sub(r'\s+', ' ', title).strip()
    title = re.sub(r'[_\-\s]+$', '', title).strip() 
    return title

def parse_episode_info(filename):
    match = re.search(r'[Ss](\d+)[Ee](\d+)', filename, re.IGNORECASE)
    if match: return int(match.group(1)), int(match.group(2))
    match = re.search(r'(\d+)[xX](\d+)', filename, re.IGNORECASE)
    if match: return int(match.group(1)), int(match.group(2))
    path_match = re.search(r'[Ss]taffel\s*(\d+)', filename, re.IGNORECASE)
    if path_match:
         season = int(path_match.group(1))
         match = re.search(r'(\d{1,3})$', filename.replace(path_match.group(0), ''), re.IGNORECASE)
         if match: return season, int(match.group(1))
    return 1, 1

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except json.JSONDecodeError:
                log_message("Konnte JSON-Datenbank nicht lesen. Erstelle neue.", is_error=True)
                return {}
    return {}

def save_db(db):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=4, ensure_ascii=False)
    except Exception as e:
        log_message(f"FEHLER beim Speichern der Datenbank: {e}", is_error=True)

def download_image(url, filename):
    if not url: return ""
    os.makedirs(THUMBS_DIR, exist_ok=True)
    local_path = os.path.join(THUMBS_DIR, filename)
    
    if os.path.exists(local_path):
        return os.path.join(THUMBS_WEB_PATH, filename).replace('\\', '/')
    
    try:
        log_message(f"Downloade Bild: {filename}")
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        with open(local_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192): file.write(chunk)
        return os.path.join(THUMBS_WEB_PATH, filename).replace('\\', '/')
    except Exception as e:
        log_message(f"FEHLER beim Download von {url}: {e}", is_error=True)
        return ""


def fetch_and_cache_metadata(title, media_type, file_unique_id, db, season=0, episode=0):
    # 1. CACHE-HIT PRÜFUNG & BILD-RECHECK
    if file_unique_id in db:
        data = db[file_unique_id]
        if data.get('not_found'):
            return None 
        
        # Re-Check, ob lokale Bilder noch vorhanden sind
        if data.get('poster_path'):
            data['poster_local_url'] = download_image(f"{IMAGE_BASE_URL}{POSTER_SIZE}{data['poster_path']}", f"{file_unique_id}_p.jpg")
            
        if data.get('backdrop_path'):
            data['backdrop_local_url'] = download_image(f"{IMAGE_BASE_URL}{BACKDROP_SIZE}{data['backdrop_path']}", f"{file_unique_id}_b.jpg")
        
        if media_type == 'tv' and data.get('episode_still_path'):
            data['episode_still_local_url'] = download_image(f"{IMAGE_BASE_URL}{BACKDROP_SIZE}{data['episode_still_path']}", f"{file_unique_id}_e.jpg")
                 
        log_message(f"Cache-Hit für: {title}")
        return data

    # 2. CACHE-MISS: TMDB ABFRAGE
    log_message(f"Cache-Miss, frage TMDB ab für: {title} ({media_type})")
    
    try:
        search = tmdb.Search()
        
        if media_type == 'movie':
            response = search.movie(query=title, language='de-DE')
        elif media_type == 'tv':
            response = search.tv(query=title, language='de-DE')
        else:
            log_message(f"  -> Unbekannter Medientyp: {media_type}")
            return None
        
        time.sleep(0.5)

        result = next((item for item in response['results']), None)

        if not result:
            log_message("  -> TMDB: Kein passendes Ergebnis gefunden.")
            db[file_unique_id] = {'not_found': True}
            return None

        # --- BASISDATEN STRUKTUR ---
        if media_type == 'movie':
            data = {
                'tmdb_id': result.get('id'),
                'title': (result.get('title') if media_type == 'movie' else result.get('name')).strip(),
                'overview': result.get('overview', 'Keine Beschreibung verfügbar.').strip(),
                'genres': [g['name'] for g in result.get('genres', [])] if result else [],
                'poster_path': result.get('poster_path', ''),
                'backdrop_path': result.get('backdrop_path', ''),
                'episode_still_path': '', 
            }
        elif media_type == 'tv':
            data = {
                'tmdb_id': result.get('id'),
                'title': result.get('name', '').strip(),
                'overview': result.get('overview', 'Keine Beschreibung verfügbar.').strip(),
                'genres': [g['name'] for g in result.get('genres', [])] if result else [],
                'poster_path': result.get('poster_path', ''),
                'backdrop_path': result.get('backdrop_path', ''),
                'episode_still_path': ''
            }

            # --- EPISODEN-DATEN LADEN (falls vorhanden) ---
            if media_type == 'tv' and season > 0 and episode > 0:
                try:
                    tv_episode = tmdb.TV_Episodes(data['tmdb_id'], season, episode)
                    ep_info = tv_episode.info(language='de-DE')
                    if ep_info:
                        data['overview'] = ep_info.get('overview', data['overview'])
                        data['episode_still_path'] = ep_info.get('still_path', '')
                        log_message(f"  -> Episodeninfos gefunden: S{season}E{episode}")
                except Exception as e:
                    log_message(f"  -> Konnte Episodeninfos nicht laden: {e}")

        # --- LOKALE BILDER HERUNTERLADEN ---
        poster_filename = f"{file_unique_id}_p.jpg"
        data['poster_local_url'] = download_image(f"{IMAGE_BASE_URL}{POSTER_SIZE}{data['poster_path']}", poster_filename)
        
        backdrop_filename = f"{file_unique_id}_b.jpg"
        data['backdrop_local_url'] = download_image(f"{IMAGE_BASE_URL}{BACKDROP_SIZE}{data['backdrop_path']}", backdrop_filename)

        if data.get('episode_still_path'):
            still_filename = f"{file_unique_id}_e.jpg"
            data['episode_still_local_url'] = download_image(f"{IMAGE_BASE_URL}{BACKDROP_SIZE}{data['episode_still_path']}", still_filename)
        else:
            data['episode_still_local_url'] = ""

        db[file_unique_id] = data
        return data

    except Exception as e:
        log_message(f"FEHLER bei TMDB-Abfrage für '{title}': {e}", is_error=True)
        return None




# ------------------------------------------------
# HAUPT-SCAN-TASK (Wird im Thread ausgeführt)
# ------------------------------------------------

def run_metadata_update_task():
    global scan_status
    
    if scan_status == "RUNNING": return

    scan_status = "RUNNING"
    current_log.clear()
    log_message("Starte Scan und Caching...")
    
    try:
        if not TMDB_API_KEY:
            raise ValueError("TMDB_API_KEY fehlt.")

        db = load_db()
        found_file_ids = set() 
        
        movie_count = 0
        tv_episode_count = 0

        for menu_name, source_config in VIDEO_SOURCES.items():
            
            root_path = source_config['source_path']
            media_type = source_config['type']
            
            log_message(f"Starte Scan für Kategorie: {menu_name} ({media_type})")
            
            if not os.path.isdir(root_path):
                 log_message(f"Pfad '{root_path}' existiert nicht. Überspringe.", is_error=True)
                 continue
                 
            for dirpath, dirnames, filenames in os.walk(root_path):
                
                for filename in filenames:
                    if filename.lower().endswith(ALLOWED_EXTENSIONS):
                        
                        relative_path_for_id = os.path.relpath(os.path.join(dirpath, filename), os.path.dirname(root_path))
                        file_unique_id = relative_path_for_id.replace(os.sep, '_').replace('.', '_')
                        
                        found_file_ids.add(file_unique_id) 
                        
                        raw_title = os.path.splitext(filename)[0]
                        is_tv = (media_type == 'tv')
                        title_search = clean_title_for_search(raw_title, is_tv=is_tv)

                        if not title_search:
                            log_message(f"Bereinigter Titel für '{raw_title}' ist leer. Überspringe.")
                            continue
                        
                        # NEU: S/E-Nummern VOR dem Metadaten-Abruf extrahieren
                        season_num, episode_num = 0, 0
                        if media_type == 'tv':
                             season_num, episode_num = parse_episode_info(raw_title)
                             
                        # Metadaten abrufen/cachen
                        metadata = fetch_and_cache_metadata(
                            title_search, 
                            media_type, 
                            file_unique_id, 
                            db,
                            season=season_num, # S/E-Nummern übergeben
                            episode=episode_num 
                        )
                        
                        if metadata:
                            if media_type == 'movie':
                                movie_count += 1
                            elif media_type == 'tv':
                                tv_episode_count += 1
                        
            log_message(f"Kategorie {menu_name} abgeschlossen.")
            
        # ----------------------------------------------------
        # BEREINIGUNG DER VERWAISTEN EINTRÄGE
        # ----------------------------------------------------
        log_message("\n--- Starte Bereinigung der verwaisten Einträge (metadata.json) ---")
        
        keys_to_delete = []
        for file_unique_id in db.keys():
            if file_unique_id not in found_file_ids:
                keys_to_delete.append(file_unique_id)
        
        deleted_count = 0
        for key in keys_to_delete:
            log_message(f"Entferne verwaisten Eintrag: {key}")
            del db[key]
            deleted_count += 1
            
        if deleted_count > 0:
            log_message(f"✅ Bereinigung abgeschlossen. {deleted_count} verwaiste Einträge wurden entfernt.")
        else:
            log_message("Keine verwaisten Einträge gefunden.")
            
        # ----------------------------------------------------
        
        save_db(db)
        
        log_message(f"\n========================================================")
        log_message(f"GESAMT ERFOLGREICH!")
        log_message(f"Aktualisiert: {movie_count} Filme und {tv_episode_count} Episoden.")
        log_message(f"========================================================")

        scan_status = "FINISHED_OK"

    except Exception as e:
        log_message(f"Ein kritischer Fehler ist aufgetreten: {e}", is_error=True)
        scan_status = "FINISHED_ERROR"

# ------------------------------------------------
# FLASK API ENDPUNKTE
# ------------------------------------------------

@app.route('/', methods=['GET'])
def index():
    return render_template('update_metadaten_status.html')

@app.route('/api/start_update', methods=['POST'])
def start_update():
    global scan_status
    if scan_status == "RUNNING":
        return jsonify({"status": "RUNNING", "message": "Der Scan läuft bereits."}), 200
        
    thread = Thread(target=run_metadata_update_task)
    thread.start()
    return jsonify({"status": "STARTED", "message": "Der Metadaten-Scan wurde gestartet."}), 202

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        "status": scan_status,
        "log": "\n".join(current_log)
    }), 200

@app.route('/<path:path>')
def send_report(path):
    return send_from_directory(WWWROOT_PATH, path)

@app.route('/Videos/Filme/<path:filename>')
def serve_filme(filename):
    # Nutzt den oben erkannten Pfad
    return send_from_directory(FILME_PATH, filename)

@app.route('/Videos/Serie/<path:filename>')
def serve_serien(filename):
    return send_from_directory(SERIEN_PATH, filename)



# ------------------------------------------------
# STARTE FLASK-APP
# ------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)