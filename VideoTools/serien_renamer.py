import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import tmdbsimple as tmdb
import threading
from dotenv import load_dotenv

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
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

if not TMDB_API_KEY or TMDB_API_KEY == "dein_schluessel_hier":
    print("❌ FEHLER: Kein gültiger TMDB_API_KEY gefunden. Updates werden fehlschlagen.")



class SeriesRenamerApp:
    def __init__(self, master):
        self.master = master
        master.title("Serien-Umbenenner mit TMDB")
        master.geometry("900x700")

        if not TMDB_API_KEY or TMDB_API_KEY == "DEIN_TMDB_API_KEY":
            messagebox.showerror("Fehler", "Bitte trage deinen TMDB API Key im Skript ein.")
            master.destroy()
            return

        tmdb.API_KEY = TMDB_API_KEY

        self.directory = None
        self.series_id = None
        self.rename_plan = []

        self.create_widgets()

    def create_widgets(self):
        # --- Ordnerauswahl und Manuelle Suche ---
        frame_top = ttk.Frame(self.master, padding="10")
        frame_top.pack(fill='x')

        ttk.Button(frame_top, text="Serienordner auswählen...", command=self.select_directory).pack(side='left', padx=(0, 10))
        self.dir_label = ttk.Label(frame_top, text="Kein Ordner ausgewählt.", font=('Segoe UI', 10, 'italic'))
        self.dir_label.pack(side='left', expand=True, fill='x')
        
        # NEU: Manueller Such-Button
        self.manual_search_button = ttk.Button(frame_top, text="Manuell suchen...", command=self.open_manual_search, state='disabled')
        self.manual_search_button.pack(side='right', padx=(10, 0))

        # --- Vorschau-Tabelle ---
        frame_tree = ttk.Frame(self.master, padding="10")
        frame_tree.pack(fill='both', expand=True)

        self.tree = ttk.Treeview(frame_tree, columns=('original', 'new'), show='headings')
        self.tree.heading('original', text='Original-Dateiname')
        self.tree.heading('new', text='Neuer Dateiname')
        self.tree.column('original', width=400)
        self.tree.column('new', width=400)

        scrollbar = ttk.Scrollbar(frame_tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # --- Buttons ---
        frame_buttons = ttk.Frame(self.master, padding="10")
        frame_buttons.pack(fill='x')

        self.preview_button = ttk.Button(frame_buttons, text="Vorschau erstellen", command=self.start_preview_thread, state='disabled')
        self.preview_button.pack(side='left', padx=5)

        self.rename_button = ttk.Button(frame_buttons, text="Dateien umbenennen", command=self.perform_rename, state='disabled')
        self.rename_button.pack(side='left', padx=5)

        # --- Log-Fenster ---
        frame_log = ttk.LabelFrame(self.master, text="Protokoll", padding="10")
        frame_log.pack(fill='x', padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(frame_log, height=8, wrap=tk.WORD, state='disabled')
        self.log_text.pack(fill='both', expand=True)

    def log(self, message, is_error=False):
        """Schreibt eine Nachricht in das Protokollfenster im Main-Thread."""
        def _log():
            self.log_text.config(state='normal')
            tag = 'error' if is_error else 'info'
            self.log_text.tag_configure('error', foreground='red')
            self.log_text.insert(tk.END, f"{message}\n", tag)
            self.log_text.see(tk.END)
            self.log_text.config(state='disabled')
        self.master.after(0, _log)

    def select_directory(self):
        """Öffnet den Dialog zur Ordnerauswahl."""
        folder_selected = filedialog.askdirectory(title="Wähle den Hauptordner einer Serie")
        if folder_selected:
            self.directory = folder_selected
            self.series_id = None # WICHTIG: ID bei neuer Ordnerauswahl zurücksetzen
            self.dir_label.config(text=os.path.basename(self.directory))
            self.log(f"Ordner ausgewählt: {self.directory}")
            self.preview_button.config(state='normal')
            self.rename_button.config(state='disabled')
            self.manual_search_button.config(state='normal') # NEU: Button aktivieren
            # Liste leeren bei neuer Auswahl
            for i in self.tree.get_children():
                self.tree.delete(i)

    def parse_episode_info(self, filename):
        """Extrahiert Staffel- und Episodennummer aus dem Dateinamen."""
        
        # 1. Muster für S01E01, s01e01, SE01E01 etc.
        match = re.search(r'[Ss]([0-9]+)[\s\._-]*[Ee]([0-9]+)', filename, re.IGNORECASE)
        if match:
            return int(match.group(1)), int(match.group(2))

        # 2. NEU: Muster für "Episode 5 Staffel 3" oder "Staffel 3 Episode 5"
        # Sucht nach den Begriffen und fängt die Zahlen ein
        match_ep_st = re.search(r'Episode\s*(\d+).*Staffel\s*(\d+)', filename, re.IGNORECASE)
        if match_ep_st:
            # Achtung: Hier ist Gruppe 2 die Staffel und Gruppe 1 die Episode!
            return int(match_ep_st.group(2)), int(match_ep_st.group(1))
        
        match_st_ep = re.search(r'Staffel\s*(\d+).*Episode\s*(\d+)', filename, re.IGNORECASE)
        if match_st_ep:
            return int(match_st_ep.group(1)), int(match_st_ep.group(2))

        # 3. Muster für 1x01, 1x1, etc.
        match = re.search(r'(\d+)[xX](\d+)', filename, re.IGNORECASE)
        if match:
            return int(match.group(1)), int(match.group(2))

        return None, None

    def start_preview_thread(self):
        """Startet die Vorschau in einem separaten Thread, um die GUI nicht zu blockieren."""
        self.preview_button.config(state='disabled')
        self.rename_button.config(state='disabled')
        self.manual_search_button.config(state='disabled') # NEU: Button während der Vorschau deaktivieren
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.rename_plan = []

        thread = threading.Thread(target=self.generate_preview)
        thread.start()

    def generate_preview(self, series_id=None):
        """Sucht nach der Serie, holt Episodendaten und erstellt den Umbenennungsplan."""
        # NEU: series_id wird entweder übergeben (manuelle Suche) oder aus dem Attribut verwendet
        if not self.directory:
            self.log("Kein Ordner ausgewählt.", is_error=True)
            self.master.after(0, lambda: self.preview_button.config(state='normal'))
            self.master.after(0, lambda: self.manual_search_button.config(state='normal'))
            return

        if series_id:
            # Manuelle ID verwenden
            self.series_id = series_id
            series_name = f"ID: {self.series_id}"
            self.log(f"Verwende manuell festgelegte Serie (ID: {self.series_id}).")
        elif not self.series_id:
            # Automatische Suche, wenn keine ID festgelegt ist
            series_name = os.path.basename(self.directory)
            self.log(f"Suche nach Serie: '{series_name}' auf TMDB...")

            try:
                search = tmdb.Search()
                search.tv(query=series_name, language='de-DE')
                if not search.results:
                    self.log(f"Keine Serie mit dem Namen '{series_name}' gefunden.", is_error=True)
                    self.log("Tipp: Versuche die manuelle Suche, wenn die automatische Suche fehlschlägt.")
                    self.master.after(0, lambda: self.preview_button.config(state='normal'))
                    self.master.after(0, lambda: self.manual_search_button.config(state='normal'))
                    return

                # Wir nehmen das erste Ergebnis als das wahrscheinlichste
                series_info = search.results[0]
                self.series_id = series_info['id']
                original_series_name = series_info['name']
                clean_series_name = re.sub(r'[\\/*?:"<>|]', "", original_series_name)
                self.log(f"✅ Automatisch gefunden: '{original_series_name}' (ID: {self.series_id})")

            except Exception as e:
                self.log(f"Ein Fehler bei der automatischen Suche ist aufgetreten: {e}", is_error=True)
                self.master.after(0, lambda: self.preview_button.config(state='normal'))
                self.master.after(0, lambda: self.manual_search_button.config(state='normal'))
                return
        
        # NEU: Hole Seriendetails für den Namen, falls die ID manuell gesetzt wurde
        try:
            tv = tmdb.TV(self.series_id)
            details = tv.info(language='de-DE')
            original_series_name = details['name']
            clean_series_name = re.sub(r'[\\/*?:"<>|]', "", original_series_name)
        except Exception as e:
            self.log(f"Fehler beim Abrufen der Details für ID {self.series_id}: {e}", is_error=True)
            self.master.after(0, lambda: self.preview_button.config(state='normal'))
            self.master.after(0, lambda: self.manual_search_button.config(state='normal'))
            return

        # Episoden-Cache, um nicht für jede Datei die gleiche Staffel-API abzufragen
        episode_cache = {}

        # Ab hier ist der Code wie zuvor, er verwendet nun die festgelegte self.series_id
        try:
            for filename in sorted(os.listdir(self.directory)):
                filepath = os.path.join(self.directory, filename)
                if not os.path.isfile(filepath):
                    continue

                season_num, episode_num = self.parse_episode_info(filename)
                if season_num is None or episode_num is None:
                    self.log(f"   -> Ignoriere '{filename}' (Kein Staffel/Episoden-Muster gefunden).")
                    continue

                # Hole Staffeldetails, wenn noch nicht im Cache
                if season_num not in episode_cache:
                    self.log(f"   -> Lade Episoden-Infos für Staffel {season_num}...")
                    tv_season = tmdb.TV_Seasons(self.series_id, season_num)
                    season_details = tv_season.info(language='de-DE')
                    episode_cache[season_num] = {ep['episode_number']: ep for ep in season_details.get('episodes', [])}

                # Finde die Episode im Cache
                episode_data = episode_cache[season_num].get(episode_num)
                if not episode_data:
                    self.log(f"   -> Konnte Episode S{season_num:02d}E{episode_num:02d} nicht auf TMDB finden.", is_error=True)
                    continue

                episode_title = episode_data.get('name', f'Episode {episode_num}')
                # Bereinige den Titel von ungültigen Zeichen für Dateinamen
                episode_title_clean = re.sub(r'[\\/*?:"<>|]', "", episode_title)

                file_extension = os.path.splitext(filename)[1]
                
                new_filename = f"{clean_series_name} - S{season_num:02d}E{episode_num:02d} - {episode_title_clean}{file_extension}"

                # Füge zum Umbenennungsplan und zur GUI-Vorschau hinzu
                self.rename_plan.append({
                    'original_path': filepath,
                    'new_path': os.path.join(self.directory, new_filename)
                })
                self.master.after(0, lambda f=filename, n=new_filename: self.tree.insert('', 'end', values=(f, n)))

            if self.rename_plan:
                self.log(f"Vorschau abgeschlossen. {len(self.rename_plan)} Dateien können für die Serie '{original_series_name}' umbenannt werden.")
                self.master.after(0, lambda: self.rename_button.config(state='normal'))
            else:
                self.log("Keine umbenennbaren Dateien gefunden.")

        except Exception as e:
            self.log(f"Ein Fehler ist aufgetreten: {e}", is_error=True)
        finally:
            self.master.after(0, lambda: self.preview_button.config(state='normal'))
            self.master.after(0, lambda: self.manual_search_button.config(state='normal'))

    def perform_rename(self):
        """Führt die geplanten Umbenennungen nach Bestätigung durch."""
        if not self.rename_plan:
            messagebox.showwarning("Keine Aktion", "Es gibt nichts zum Umbenennen. Bitte erst Vorschau erstellen.")
            return

        if not messagebox.askyesno("Bestätigung", f"Sollen {len(self.rename_plan)} Dateien wirklich umbenannt werden?\n\nDieser Vorgang kann nicht rückgängig gemacht werden."):
            self.log("Umbenennung vom Benutzer abgebrochen.")
            return

        self.log("\n--- STARTE UMBENENNUNG ---")
        renamed_count = 0
        error_count = 0

        for plan in self.rename_plan:
            original = plan['original_path']
            new = plan['new_path']

            if original == new:
                self.log(f"   -> Überspringe '{os.path.basename(original)}' (bereits korrekt benannt).")
                continue

            if os.path.exists(new):
                self.log(f"   -> FEHLER: Zieldatei '{os.path.basename(new)}' existiert bereits. Überspringe.", is_error=True)
                error_count += 1
                continue

            try:
                os.rename(original, new)
                self.log(f"   -> '{os.path.basename(original)}' -> '{os.path.basename(new)}'")
                renamed_count += 1
            except Exception as e:
                self.log(f"   -> FEHLER beim Umbenennen von '{os.path.basename(original)}': {e}", is_error=True)
                error_count += 1

        self.log(f"--- UMBENENNUNG ABGESCHLOSSEN ---")
        self.log(f"✅ {renamed_count} Dateien erfolgreich umbenannt.")
        if error_count > 0:
            self.log(f"❌ {error_count} Fehler sind aufgetreten.")

        messagebox.showinfo("Abschluss", f"{renamed_count} von {len(self.rename_plan)} Dateien wurden umbenannt.")

        # GUI zurücksetzen
        self.rename_button.config(state='disabled')
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.rename_plan = []
        self.series_id = None # NEU: ID nach Abschluss zurücksetzen
        self.dir_label.config(text=os.path.basename(self.directory)) # Aktualisiert den Namen, falls er jetzt mit der TMDB-Info übereinstimmen soll (optional)

# ----------------------------------------------------------------------
# NEUE FUNKTIONALITÄT: MANUELLE SUCHE
# ----------------------------------------------------------------------
    def open_manual_search(self):
        """Öffnet ein separates Fenster für die manuelle TMDB-Seriensuche."""
        if not self.directory:
            messagebox.showwarning("Achtung", "Bitte wähle zuerst einen Serienordner aus.")
            return

        search_window = tk.Toplevel(self.master)
        search_window.title("Manuelle TMDB-Suche")
        search_window.geometry("500x400")
        search_window.transient(self.master)
        search_window.grab_set()

        frame_input = ttk.Frame(search_window, padding="10")
        frame_input.pack(fill='x')

        ttk.Label(frame_input, text="Serientitel eingeben:").pack(side='left', padx=5)
        search_entry = ttk.Entry(frame_input, width=30)
        search_entry.pack(side='left', expand=True, fill='x', padx=5)

        def search_series():
            query = search_entry.get().strip()
            if not query:
                return
            
            # Treeview leeren
            for i in tree_results.get_children():
                tree_results.delete(i)
            
            try:
                search = tmdb.Search()
                # Suchanfrage in separatem Thread, um GUI nicht zu blockieren
                def run_search():
                    try:
                        search.tv(query=query, language='de-DE')
                        results = search.results
                        self.master.after(0, lambda r=results: update_results_tree(r))
                    except Exception as e:
                        self.master.after(0, lambda: messagebox.showerror("API-Fehler", f"Fehler bei der TMDB-Suche: {e}"))
                
                threading.Thread(target=run_search).start()

            except Exception as e:
                messagebox.showerror("Fehler", f"Ein unerwarteter Fehler ist aufgetreten: {e}")

        def update_results_tree(results):
            if not results:
                tree_results.insert('', 'end', values=("Keine Ergebnisse gefunden.", "", ""))
                return

            for result in results:
                name = result.get('name', 'N/A')
                # Das Jahr aus dem Veröffentlichungsdatum extrahieren, falls vorhanden
                year = result.get('first_air_date', 'N/A')[:4]
                series_id = result.get('id', 'N/A')
                tree_results.insert('', 'end', values=(name, year, series_id), iid=series_id)

        ttk.Button(frame_input, text="Suchen", command=search_series).pack(side='left', padx=5)

        # --- Ergebnisse-Tabelle ---
        frame_results = ttk.Frame(search_window, padding="10")
        frame_results.pack(fill='both', expand=True)

        tree_results = ttk.Treeview(frame_results, columns=('title', 'year', 'id'), show='headings')
        tree_results.heading('title', text='Serientitel')
        tree_results.heading('year', text='Jahr')
        tree_results.heading('id', text='ID')
        tree_results.column('title', width=250, anchor='w')
        tree_results.column('year', width=50, anchor='center')
        tree_results.column('id', width=50, anchor='center')

        scrollbar = ttk.Scrollbar(frame_results, orient="vertical", command=tree_results.yview)
        tree_results.configure(yscrollcommand=scrollbar.set)

        tree_results.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        def set_series_id_and_close(event):
            """Setzt die ID und startet die Vorschau neu."""
            selected_item = tree_results.focus()
            if not selected_item:
                return

            # Die ID ist das iid des Items
            series_id_str = tree_results.item(selected_item, 'text') # Hier kann auch 'iid' verwendet werden, da wir die ID als iid gesetzt haben.
            
            # Hole die ID erneut aus den values, falls iid nicht automatisch geht
            values = tree_results.item(selected_item, 'values')
            if len(values) >= 3 and values[2].isdigit():
                series_id = int(values[2])
                
                # Bestätigung
                selected_title = values[0]
                if messagebox.askyesno("Bestätigen", f"Möchtest du '{selected_title}' (ID: {series_id}) für die Umbenennung verwenden?"):
                    search_window.destroy()
                    self.series_id = series_id # ID im Hauptobjekt festlegen
                    self.dir_label.config(text=f"{os.path.basename(self.directory)} [ID: {series_id}]") # Visuelle Bestätigung
                    self.log(f"Manuell ausgewählte Serie: '{selected_title}' (ID: {series_id})")
                    self.start_preview_thread() # Vorschau mit der manuell gesetzten ID starten
            else:
                 messagebox.showwarning("Auswahlfehler", "Bitte wähle eine gültige Serie aus.")

        tree_results.bind('<Double-1>', set_series_id_and_close)
        
        ttk.Button(search_window, text="Auswahl bestätigen (Doppelklick)", command=lambda: set_series_id_and_close(None)).pack(pady=10)

        search_window.mainloop()

# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = SeriesRenamerApp(root)
    root.mainloop()