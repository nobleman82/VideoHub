import os
import subprocess
import json
import threading
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox
import shutil
import time

# --- KONFIGURATION ---
CONVERT_EXTENSIONS = ('.avi', '.mpg', '.mpeg', '.mkv', '.divx')
COMPATIBLE_VIDEO_CODECS = ('h264', 'avc1')
COMPATIBLE_AUDIO_CODECS = ('aac', 'mp3')
OUTPUT_FOLDER_NAME = "ConvertetVideos_TEMP" # Wird jetzt als Temp-Ordner genutzt
# ---------------------

class VideoConverterApp:
    def __init__(self, master):
        self.master = master
        master.title("Video Konverter (FFmpeg) - Atomarer Austausch")

        self.source_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.files_to_process = []
        self.current_process = None
        self.is_running = False

        self.create_widgets()
        self.set_default_output_dir()

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TProgressbar", thickness=20)
        
        # Sicherstellen, dass FFmpeg/FFprobe erreichbar ist
        if shutil.which("ffmpeg") is None:
            messagebox.showerror("FFmpeg Fehler", "FFmpeg ist nicht im Systempfad verfügbar. Installation erforderlich.")
            self.start_button.config(state='disabled')


    # [ ... create_widgets, set_default_output_dir, log, select_source_folder bleiben gleich ... ]
    # Da diese unverändert bleiben und der Fokus auf den Verarbeitungsfunktionen liegt, 
    # lasse ich sie hier aus Platzgründen weg, aber sie sind in Ihrem vollständigen Skript vorhanden.

    def create_widgets(self):
        # Frame für Ordnerauswahl
        frame_path = tk.LabelFrame(self.master, text="Quellauswahl", padx=10, pady=10)
        frame_path.pack(padx=10, pady=10, fill="x")

        # Quellpfad (Source = Zielort der fertigen MP4s)
        tk.Label(frame_path, text="Ordner scannen:").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_source = tk.Entry(frame_path, textvariable=self.source_dir, width=60)
        self.entry_source.grid(row=0, column=1, padx=5, pady=5)
        tk.Button(frame_path, text="Ordner wählen...", command=self.select_source_folder).grid(row=0, column=2, padx=5, pady=5)

        # Zielpfad (TEMP-Ordner)
        tk.Label(frame_path, text="TEMP-Ordner:").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_output = tk.Entry(frame_path, textvariable=self.output_dir, width=60, state='readonly')
        self.entry_output.grid(row=1, column=1, padx=5, pady=5)

        # Buttons für manuelle Dateiauswahl
        tk.Button(frame_path, text="Dateien hinzufügen...", command=self.select_files_to_add).grid(row=2, column=1, sticky="w", padx=5, pady=5)
        tk.Button(frame_path, text="Liste leeren", command=self.clear_list).grid(row=2, column=2, sticky="w", padx=5, pady=5)

        # Frame für Dateiliste
        frame_list = tk.LabelFrame(self.master, text="Dateien zur Konvertierung", padx=10, pady=5)
        frame_list.pack(padx=10, fill="both", expand=True)
        
        # Liste der gefundenen Dateien (ListBox)
        self.listbox = tk.Listbox(frame_list, height=8, width=80)
        self.listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar = tk.Scrollbar(frame_list, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        # Frame für Steuerung und Fortschritt
        frame_control = tk.Frame(self.master, padx=10, pady=5)
        frame_control.pack(padx=10, fill="x")

        self.start_button = tk.Button(frame_control, text="Konvertierung Starten", command=self.start_conversion, bg='green', fg='white')
        self.start_button.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.stop_button = tk.Button(frame_control, text="STOPP", command=self.stop_conversion, bg='red', fg='white', state='disabled')
        self.stop_button.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        # Fortschrittsanzeige
        frame_progress_display = tk.Frame(self.master, padx=10, pady=5)
        frame_progress_display.pack(padx=10, fill="x")

        # Gesamtfortschritt
        tk.Label(frame_progress_display, text="Gesamtfortschritt:", anchor="w").pack(side="top", fill="x", padx=5, pady=(5,0))
        self.overall_progress_bar = ttk.Progressbar(frame_progress_display, orient="horizontal", length=100, mode="determinate", style="TProgressbar")
        self.overall_progress_bar.pack(side="top", fill="x", expand=True, padx=5, pady=2)
        self.overall_progress_label = tk.Label(frame_progress_display, text="Bereit", anchor="w")
        self.overall_progress_label.pack(side="top", fill="x", padx=5, pady=(0,10))

        # Fortschritt der aktuellen Datei
        self.current_file_label = tk.Label(frame_progress_display, text="Aktuelle Datei: -", anchor="w")
        self.current_file_label.pack(side="top", fill="x", padx=5, pady=2)
        self.current_file_progress_bar = ttk.Progressbar(frame_progress_display, orient="horizontal", length=100, mode="determinate", style="TProgressbar")
        self.current_file_progress_bar.pack(side="top", fill="x", expand=True, padx=5, pady=2)
        
        # Frame für detaillierte Status-Labels
        frame_stats = tk.Frame(frame_progress_display, bd=1, relief="sunken")
        frame_stats.pack(side="top", fill="x", padx=5, pady=5, ipady=5, ipadx=5)

        self.status_labels = {}
        stats_to_show = {
            "time": "Zeit", "speed": "Speed", "bitrate": "Bitrate",
            "fps": "FPS", "size": "Größe", "frame": "Frame"
        }

        col = 0
        for key, text in stats_to_show.items():
            # Label für die Bezeichnung (z.B. "Zeit:")
            label_text = tk.Label(frame_stats, text=f"{text}:", anchor="e")
            label_text.grid(row=col % 2, column=(col // 2) * 2, sticky="ew", padx=(5, 2))
            
            # Label für den Wert (wird aktualisiert)
            label_value = tk.Label(frame_stats, text="N/A", anchor="w", font=('Segoe UI', 9, 'bold'))
            label_value.grid(row=col % 2, column=(col // 2) * 2 + 1, sticky="ew", padx=(0, 10))
            
            self.status_labels[key] = label_value
            col += 1
        frame_stats.grid_columnconfigure(tuple(range(6)), weight=1)

        # Frame für das Protokoll
        frame_log = tk.LabelFrame(self.master, text="Protokoll / Debug-Meldungen", padx=10, pady=5)
        frame_log.pack(padx=10, pady=10, fill="x")

        # Textfeld für das Protokoll (Scrollbar)
        self.log_text = scrolledtext.ScrolledText(frame_log, wrap=tk.WORD, height=10, width=80, state='disabled')
        self.log_text.pack(fill="x", expand=True, padx=5, pady=5)
        

    def set_default_output_dir(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        default_output = os.path.join(script_dir, OUTPUT_FOLDER_NAME)
        self.output_dir.set(default_output)


    def log(self, message, is_error=False):
        self.log_text.config(state='normal')
        if is_error:
            self.log_text.insert(tk.END, f"❌ FEHLER: {message}\n", 'error')
        else:
            self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.log_text.tag_config('error', foreground='red')

    
    def select_source_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.source_dir.set(folder_selected)
            # Zielordner ist jetzt der temporäre Ordner innerhalb des Quellordners oder des Skriptordners
            temp_output = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_FOLDER_NAME)
            self.output_dir.set(temp_output)
            self.scan_files()
            
    def select_files_to_add(self):
        """Öffnet einen Dialog, um einzelne oder mehrere Dateien zur Liste hinzuzufügen."""
        files_selected = filedialog.askopenfilenames(
            title="Dateien zur Konvertierung auswählen",
            filetypes=[("Videodateien", " ".join(CONVERT_EXTENSIONS)), ("Alle Dateien", "*.*")]
        )
        
        if files_selected:
            added_count = 0
            for file_path in files_selected:
                if file_path not in self.files_to_process:
                    self.files_to_process.append(file_path)
                    self.listbox.insert(tk.END, file_path) # Zeige den vollen Pfad an
                    added_count += 1
            
            self.log(f"{added_count} Datei(en) zur Liste hinzugefügt.")
            self.start_button.config(state='normal' if self.files_to_process and not self.is_running else 'disabled')
            self.overall_progress_label.config(text=f"Bereit ({len(self.files_to_process)} Dateien)")

    def clear_list(self):
        """Leert die Liste der zu verarbeitenden Dateien."""
        self.listbox.delete(0, tk.END)
        self.files_to_process = []
        self.log("Konvertierungsliste wurde geleert.")
        self.start_button.config(state='disabled')
        self.overall_progress_label.config(text="Bereit (0 Dateien)")

    def scan_files(self):
        source = self.source_dir.get()
        if not source: return

        self.clear_list() # Leert die Liste, bevor ein neuer Ordner gescannt wird
        
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
        self.log(f"Starte Scan in: {source}")

        for dirpath, dirnames, filenames in os.walk(source):
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                # Nur Dateien konvertieren, die NICHT MP4 sind
                if ext in CONVERT_EXTENSIONS:
                    file_path = os.path.join(dirpath, filename)
                    self.files_to_process.append(file_path)
                    
                    # Zeige den relativen Pfad in der Liste an
                    relative_path = os.path.relpath(file_path, source)
                    self.listbox.insert(tk.END, relative_path)

        self.log(f"Scan abgeschlossen. {len(self.files_to_process)} Dateien zur Verarbeitung gefunden.")
        self.start_button.config(state='normal' if self.files_to_process and not self.is_running else 'disabled')
        self.overall_progress_label.config(text=f"Bereit ({len(self.files_to_process)} Dateien)")


    def stop_conversion(self):
        """Stoppt die Konvertierung sicher."""
        self.is_running = False
        self.log("🛑 STOPP-Signal empfangen. Aktueller Prozess wird abgeschlossen.", False)
        # Wenn der Thread noch läuft, wird er nach dem aktuellen Film beendet.


    def start_conversion(self):
        if not self.files_to_process:
            self.log("Keine Dateien zur Konvertierung.", is_error=True)
            return
            
        if self.is_running:
            self.log("Konvertierung läuft bereits.", is_error=True)
            return

        self.log("\n--- KONVERTIERUNG GESTARTET ---")
        self.is_running = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.overall_progress_bar['value'] = 0
        self.overall_progress_bar['maximum'] = len(self.files_to_process)
        self.current_file_progress_bar['value'] = 0
        
        self.current_process = threading.Thread(target=self.conversion_thread)
        self.current_process.start()


    def conversion_thread(self):
        converted_count = 0
        
        # Kopiere die Liste, da sie sich während des Prozesses im Haupt-Thread ändern könnte (z.B. durch erneutes Scannen)
        files_to_process_safe = list(self.files_to_process) 
        
        for i, file_path in enumerate(files_to_process_safe):
            if not self.is_running:
                self.log("🛑 Sicherer Abbruch nach dem letzten Film.", True)
                break
                
            self.master.after(0, self.update_progress_label, i + 1, os.path.basename(file_path))
            
            # Verarbeite die Datei und führe den atomaren Austausch durch
            if self.process_single_file(file_path):
                converted_count += 1
            
            self.master.after(0, self.overall_progress_bar.step, 1)

        self.master.after(0, self.finish_conversion, converted_count)
        
        
    def update_progress_label(self, current_num, filename):
        total = len(self.files_to_process)
        self.overall_progress_label.config(text=f"Gesamt: {current_num}/{total}")
        self.current_file_label.config(text=f"Aktuelle Datei: {filename}")
        self.current_file_progress_bar['value'] = 0 # Setze den Balken für die neue Datei zurück
        self.log(f"\n[START] {current_num}/{total}: {os.path.basename(filename)}")


    def finish_conversion(self, converted_count):
        self.is_running = False
        self.log(f"\n--- Konvertierung ABGESCHLOSSEN ({converted_count}/{len(self.files_to_process)} erfolgreich begonnen) ---")
        self.master.after(0, self.scan_files) # Wichtig: Erneuter Scan, um die Liste zu leeren
        self.start_button.config(state='normal' if self.files_to_process else 'disabled')
        self.stop_button.config(state='disabled')
        self.overall_progress_label.config(text="Fertig!")
        
    def update_status_bar(self, line):
        """Aktualisiert die Protokollkonsole mit Fortschrittsinformationen (von FFmpeg stderr)."""
        # Hier protokollieren wir die FFmpeg-Fortschrittszeilen direkt in die Log-Konsole.
        # Dies ist erforderlich, da der Code in process_single_file darauf zugreift:
        # self.master.after(0, self.update_status_bar, line.strip())
        self.log(f"  -> Status: {line}")
    # --- WICHTIGE NEUE/ANGEPASSTE LOGIK HIER ---

    def get_codec_info(self, file_path):
        """Führt FFprobe in zwei separaten Durchgängen aus (Video & Audio) für maximale Robustheit."""

        def run_ffprobe_stream_info(stream_type):
            command = [
                'ffprobe', '-v', 'error', 
                '-select_streams', stream_type,
                '-show_entries', 'stream=codec_name,codec_type', 
                '-of', 'json', 
                file_path
            ]
            try:
                result = subprocess.run(
                    command, capture_output=True, text=True, check=False,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode != 0 and result.returncode != 1:
                    self.master.after(0, self.log, f"  -> FFprobe Fehler (RC {result.returncode}) für Stream '{stream_type}'.", True)
                    return None
                data = json.loads(result.stdout)
                codec_name = next((s['codec_name'].lower() for s in data.get('streams', []) if s['codec_type'] == stream_type), None)
                return codec_name
            except json.JSONDecodeError:
                self.master.after(0, self.log, f"  -> JSON-Dekodierungsfehler bei Stream '{stream_type}'.", True)
                return None
            except Exception as e:
                self.master.after(0, self.log, f"  -> Analysefehler (Allgemein) bei Stream '{stream_type}': {e}", True)
                return None

        def run_ffprobe_duration():
            command = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', file_path]
            try:
                result = subprocess.run(command, capture_output=True, text=True, check=False, creationflags=subprocess.CREATE_NO_WINDOW)
                data = json.loads(result.stdout)
                return float(data['format']['duration']) if 'format' in data and 'duration' in data['format'] else 0.0
            except json.JSONDecodeError:
                self.master.after(0, self.log, f"  -> JSON-Dekodierungsfehler bei Stream '{stream_type}'.", True)
                return None
            except Exception as e:
                self.master.after(0, self.log, f"  -> Analysefehler (Allgemein) bei Stream '{stream_type}': {e}", True)
                return None
        
        video_codec = run_ffprobe_stream_info('video')
        audio_codec = run_ffprobe_stream_info('audio')
        duration = run_ffprobe_duration()
        
        self.master.after(0, self.log, f"  -> FFprobe Analyse: V={video_codec.upper() if video_codec else 'NICHT GEFUNDEN'}, A={audio_codec.upper() if audio_codec else 'NICHT GEFUNDEN'}, Dauer={duration:.2f}s", False)

        return video_codec, audio_codec, duration


    def process_single_file(self, file_path):
        """Verarbeitet, konvertiert in den TEMP-Ordner und führt den ATOMAREN AUSTAUSCH durch."""
        
        source_dir = self.source_dir.get()
        temp_dir = self.output_dir.get()
        
        # --- KORREKTUR FÜR MANUELL HINZUGEFÜGTE DATEIEN ---
        # Wenn kein Quellordner gesetzt ist (manuelle Auswahl),
        # wird der Pfad anders aufgebaut.
        if source_dir and file_path.startswith(os.path.abspath(source_dir)):
            # Fall 1: Datei ist Teil eines gescannten Ordners
            relative_path = os.path.relpath(file_path, source_dir)
            final_output_path = os.path.join(source_dir, os.path.splitext(relative_path)[0] + '.mp4')
        else:
            # Fall 2: Datei wurde manuell hinzugefügt
            relative_path = os.path.basename(file_path)
            final_output_path = os.path.join(os.path.dirname(file_path), os.path.splitext(relative_path)[0] + '.mp4')
        
        temp_filename = os.path.splitext(relative_path)[0].replace(os.sep, '_') + '.mp4'
        temp_output_path = os.path.join(temp_dir, temp_filename)
        
        # 1. Vorabprüfung auf abgeschlossene Konvertierung (Wiederaufnehmbarkeit)
        if os.path.exists(final_output_path):
             # Dies sollte der Scan bereits verhindern, aber als doppelte Sicherheit
             self.master.after(0, self.log, f"  -> MP4 existiert bereits im Quellordner. Überspringe.")
             return True

        os.makedirs(os.path.dirname(temp_output_path), exist_ok=True)
        
        # 2. Codec-Analyse und Befehlserstellung (Remuxing oder Transkodierung)
        video_codec, audio_codec, total_duration = self.get_codec_info(file_path)
        
        # [ ... is_remuxable Logik bleibt gleich ... ]
        is_remuxable = False
        if video_codec and audio_codec:
            is_remuxable = (
                video_codec in COMPATIBLE_VIDEO_CODECS and 
                audio_codec in COMPATIBLE_AUDIO_CODECS
            )
            
        ffmpeg_command = []
        process_type = ""

        if is_remuxable:
            # REMUXING
            process_type = "REMUXING"
            ffmpeg_command = [
                'ffmpeg', '-i', file_path, '-c:v', 'copy', '-c:a', 'copy',
                '-map', '0:v:0', '-map', '0:a:0', '-y', temp_output_path # WICHTIG: Ausgabe in den TEMP-Pfad
            ]
            self.master.after(0, self.log, f"  -> MODUS: Remuxing (Kopieren).")
        else:
            # TRANSKODIERUNG
            process_type = "TRANSKODIERUNG"
            reason = "Fehlende Analyse oder inkompatible Codecs"
            ffmpeg_command = [
                'ffmpeg', '-i', file_path, 
                '-c:v', 'libx264', '-preset', 'medium', '-crf', '23', 
                '-c:a', 'aac', '-b:a', '192k', 
                '-map', '0:v:0', 
                '-map', '0:a:0', 
                '-y', temp_output_path # WICHTIG: Ausgabe in den TEMP-Pfad
            ]
            self.master.after(0, self.log, f"  -> MODUS: Transkodierung. Grund: {reason}.")
            
        # 3. FFmpeg Ausführung (Unverändert)
        success = False
        try:
            # [ ... subprocess.Popen, Fortschritt und wait() Logik bleibt gleich ... ]
            with subprocess.Popen(
                ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, 
                creationflags=subprocess.CREATE_NO_WINDOW
            ) as process:
                # Regex, um Fortschrittsinformationen zu extrahieren
                progress_regex = re.compile(r'frame=\s*(?P<frame>\d+)\s*fps=\s*(?P<fps>[\d\.]+)\s*.*size=\s*(?P<size>\S+B)\s*time=(?P<time>[\d:.]+)\s*bitrate=\s*(?P<bitrate>\S+)\s*.*speed=\s*(?P<speed>\S+)')

                for line in process.stderr:
                    if not self.is_running:
                        process.terminate() # Prozess aktiv beenden, wenn gestoppt wird
                        break
                    match = progress_regex.search(line)
                    if match:
                        self.master.after(0, self.update_progress_display, match.groupdict(), total_duration)
                    else:
                        self.master.after(0, self.log, f"  -> FFmpeg: {line.strip()}")

                process.wait() # Warten, bis der Prozess von selbst endet oder terminiert wurde

            if process.returncode == 0 and os.path.exists(temp_output_path):
                self.master.after(0, self.log, f"✅ Konvertierung erfolgreich abgeschlossen.", False)
                success = True
            else:
                self.master.after(0, self.log, f"❌ {process_type} FEHLGESCHLAGEN. RC: {process.returncode}", True)
                if os.path.exists(temp_output_path): os.remove(temp_output_path) # Temp-Datei löschen
        except Exception as e:
            self.master.after(0, self.log, f"❌ Ausführungsfehler: {e}", True)
            if os.path.exists(temp_output_path): os.remove(temp_output_path)
            
        # 4. ATOMARER AUSTAUSCH
        if success:
            try:
                # Wichtig: Lösche die alte Datei, um Platz zu schaffen und den Scan beim nächsten Mal zu verhindern.
                os.remove(file_path) 
                
                # Verschiebe die fertige MP4 in den Quellordner
                shutil.move(temp_output_path, final_output_path)
                
                self.master.after(0, self.log, f"✅ ATOMARER AUSTAUSCH erfolgreich durchgeführt.", False)
                # Am Ende des Films ist alles sauber: MP4 im Quellordner, alte Datei weg.
                return True
            except Exception as e:
                self.master.after(0, self.log, f"❌ FEHLER BEIM AUSTAUSCH: {e}", True)
                # Wenn der Austausch fehlschlägt, bleibt die Temp-MP4 in ConvertetVideos_TEMP.
                return False
        
        return False

    def update_progress_display(self, progress_data, total_duration):
        
        for key, label in self.status_labels.items():
            value = progress_data.get(key, "N/A")
            label.config(text=value)

        # Aktualisiere die Progressbar
        current_time_str = progress_data.get('time')
        if current_time_str:
            try:
                h, m, s_ms = current_time_str.split(':')
                s, ms = map(float, s_ms.split('.'))
                current_seconds = int(h) * 3600 + int(m) * 60 + s + ms / 100
                
                if total_duration > 0:
                    percentage = min((current_seconds / total_duration) * 100, 100)
                    self.current_file_progress_bar['value'] = percentage
            except ValueError:
                pass # Ignoriere fehlerhafte Zeitformate


# --- ANWENDUNG STARTEN ---
if __name__ == '__main__':
    import re # Importiere re hier, da es in update_progress_display verwendet wird
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = 750
    window_height = 700
    x = (screen_width / 2) - (window_width / 2)
    y = (screen_height / 2) - (window_height / 2)
    root.geometry(f'{window_width}x{window_height}+{int(x)}+{int(y)}')
    
    app = VideoConverterApp(root)
    root.mainloop()