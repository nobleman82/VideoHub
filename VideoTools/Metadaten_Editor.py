import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import json
import requests
import re
import shutil
from dotenv import load_dotenv

# --- KONFIGURATION & HILFSFUNKTIONEN ---

if os.name == 'nt':  # Windows
    env_file = ".env_windows"
    default_www = r"C:/Users/mario/Documents/VB2026/VideoHub/VideoHub/VideoHub/wwwroot"
else:  # Ubuntu / Linux
    env_file = ".env"
    default_www = "/var/www/html"

if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    print(f"⚠️ WARNUNG: {env_file} nicht gefunden!")

WWWROOT_PATH = os.getenv("APACHE_PATH", default_www)
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

TMDB_BASE_URL = "https://api.themoviedb.org/3"
METADATA_FILE = os.path.join(WWWROOT_PATH, 'metadata.json')
THUMBS_DIR = os.path.join(WWWROOT_PATH, 'thumbs')  
THUMBS_WEB_PATH = 'thumbs/'

# --- FARBSCHEMA ---
COLORS = {
    "bg": "#1e1e1e",
    "fg": "#ffffff",
    "card": "#2d2d2d",
    "accent": "#0078d4",
    "success": "#28a745",
    "error": "#dc3545",
    "list_bg": "#252526"
}

def search_tmdb_movies(query, year=None):
    if not TMDB_API_KEY:
        return {"error": "TMDB API Key fehlt."}
    params = {'api_key': TMDB_API_KEY, 'query': query, 'language': 'de-DE'}
    if year: params['year'] = year
    try:
        response = requests.get(f"{TMDB_BASE_URL}/search/movie", params=params)
        response.raise_for_status()
        return response.json().get('results', [])
    except Exception as e:
        return {"error": str(e)}

class MetadataEditorApp:
    def __init__(self, master):
        self.master = master
        self.master.title("🎬 VideoHub - Metadaten Editor")
        self.master.geometry("950x750")
        self.master.configure(bg=COLORS["bg"])

        # Styles definieren
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("Treeview", background=COLORS["list_bg"], foreground=COLORS["fg"], fieldbackground=COLORS["list_bg"], borderwidth=0)
        self.style.map("Treeview", background=[('selected', COLORS["accent"])])

        if not os.path.exists(THUMBS_DIR):
            os.makedirs(THUMBS_DIR)

        self.metadata = self.load_metadata()
        self.metadata_items = []
        self.create_widgets()
        self.populate_listbox()

    def load_metadata(self):
        if os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_metadata(self):
        try:
            with open(METADATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=4, ensure_ascii=False)
            self.log("✅ Metadaten erfolgreich gespeichert.")
            return True
        except Exception as e:
            messagebox.showerror("Fehler", str(e))
            return False

    def create_widgets(self):
        # Header
        header = tk.Label(self.master, text="Metadaten Korrektur-Center", font=('Segoe UI', 18, 'bold'), bg=COLORS["bg"], fg=COLORS["accent"])
        header.pack(pady=15)

        # Container für Liste
        list_frame = tk.Frame(self.master, bg=COLORS["bg"])
        list_frame.pack(padx=20, fill="both", expand=True)

        self.tree = ttk.Treeview(list_frame, columns=("file", "title"), show="headings", height=12)
        self.tree.heading("file", text="Dateischlüssel (JSON-Key)")
        self.tree.heading("title", text="Aktueller Titel")
        self.tree.column("file", width=400)
        self.tree.column("title", width=400)
        self.tree.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.config(yscrollcommand=sb.set)

        # Button Panel
        btn_panel = tk.Frame(self.master, bg=COLORS["bg"])
        btn_panel.pack(pady=20)

        # Styling Buttons
        def create_btn(parent, text, cmd, color):
            return tk.Button(parent, text=text, command=cmd, bg=color, fg="white", font=("Segoe UI", 10, "bold"), 
                             padx=15, pady=5, relief="flat", activebackground=COLORS["accent"], cursor="hand2")

        create_btn(btn_panel, "🔍 TMDB Korrektur", self.show_search_dialog, COLORS["accent"]).pack(side="left", padx=10)
        create_btn(btn_panel, "🔄 Liste laden", self.populate_listbox, COLORS["card"]).pack(side="left", padx=10)
        create_btn(btn_panel, "💾 Speichern & Schließen", self.save_and_close, COLORS["success"]).pack(side="left", padx=10)

        # Log Bereich
        log_frame = tk.LabelFrame(self.master, text="Protokoll", bg=COLORS["bg"], fg=COLORS["fg"], padx=10, pady=5)
        log_frame.pack(padx=20, pady=10, fill="x")
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=6, bg="#121212", fg="#00ff00", font=("Consolas", 9), borderwidth=0)
        self.log_text.pack(fill="both", expand=True)

    def log(self, msg):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"[{os.path.basename(METADATA_FILE)}] {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def populate_listbox(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        self.metadata_items = []
        for key in sorted(self.metadata.keys()):
            self.tree.insert("", tk.END, values=(key, self.metadata[key].get('title', 'N/A')))
            self.metadata_items.append(key)

    def save_and_close(self):
        if self.save_metadata(): self.master.destroy()

    def download_image(self, tmdb_path, local_filename):
        if not tmdb_path: return None
        url = f"https://image.tmdb.org/t/p/{'w500' if '_p.jpg' in local_filename else 'w1280'}{tmdb_path}"
        local_path = os.path.join(THUMBS_DIR, local_filename)
        try:
            r = requests.get(url, stream=True, timeout=10)
            with open(local_path, 'wb') as f: shutil.copyfileobj(r.raw, f)
            return f"{THUMBS_WEB_PATH}{local_filename}"
        except: return None

    def show_search_dialog(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Achtung", "Bitte einen Film wählen!")
            return

        item_idx = self.tree.index(sel[0])
        file_key = self.metadata_items[item_idx]
        
        sw = tk.Toplevel(self.master)
        sw.title(f"Suche: {file_key}")
        sw.geometry("700x550")
        sw.configure(bg=COLORS["card"])

        top_f = tk.Frame(sw, bg=COLORS["card"], pady=10)
        top_f.pack(fill="x")
        
        tk.Label(top_f, text="Titel:", bg=COLORS["card"], fg="white").pack(side="left", padx=5)
        q_var = tk.StringVar(value=self.metadata[file_key].get('title', file_key))
        tk.Entry(top_f, textvariable=q_var, width=30).pack(side="left", padx=5)
        
        y_var = tk.StringVar()
        tk.Label(top_f, text="Jahr:", bg=COLORS["card"], fg="white").pack(side="left", padx=5)
        tk.Entry(top_f, textvariable=y_var, width=6).pack(side="left", padx=5)

        res_lb = tk.Listbox(sw, bg=COLORS["list_bg"], fg="white", borderwidth=0)
        res_lb.pack(padx=20, pady=10, fill="both", expand=True)

        def do_search():
            res_lb.delete(0, tk.END)
            results = search_tmdb_movies(q_var.get(), y_var.get() if y_var.get().isdigit() else None)
            if "error" in results: return
            sw.results = results
            for r in results:
                res_lb.insert(tk.END, f"{r.get('title')} ({r.get('release_date', '')[:4]}) - ID: {r.get('id')}")

        def apply():
            try:
                idx = res_lb.curselection()[0]
                res = sw.results[idx]
                
                # Bilder & Daten verarbeiten
                clean_key = file_key.replace(os.path.sep, '_').replace('.', '_')
                p_url = self.download_image(res.get('poster_path'), f"{clean_key}_p.jpg")
                b_url = self.download_image(res.get('backdrop_path'), f"{clean_key}_b.jpg")

                self.metadata[file_key].update({
                    'title': res.get('title'),
                    'overview': res.get('overview'),
                    'poster_local_url': p_url or "",
                    'backdrop_local_url': b_url or ""
                })
                self.save_metadata()
                self.populate_listbox()
                sw.destroy()
            except: messagebox.showerror("Fehler", "Auswahl ungültig!")

        tk.Button(top_f, text="Suchen", command=do_search, bg=COLORS["accent"], fg="white").pack(side="left", padx=10)
        tk.Button(sw, text="✅ Auswahl übernehmen", command=apply, bg=COLORS["success"], fg="white", pady=5).pack(fill="x", padx=20, pady=10)

        do_search() # Sofort-Suche beim Öffnen

if __name__ == '__main__':
    root = tk.Tk()
    app = MetadataEditorApp(root)
    root.mainloop()