import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# --- FARBSCHEMA (Modern Dark) ---
COLORS = {
    "bg": "#1e1e1e",
    "fg": "#ffffff",
    "card": "#2d2d2d",
    "accent": "#0078d4",      # Windows Blue
    "success": "#28a745",     # Green
    "error": "#dc3545",       # Red
    "input_bg": "#252526",
    "list_bg": "#252526"
}

class FileRenameTool:
    def __init__(self, master):
        self.master = master
        self.master.title("✏️ FileHub - Datei-Umbenennungstool")
        self.master.geometry("800x700")
        self.master.configure(bg=COLORS["bg"])
        
        self.directory = None
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # UI Styling
        self.style.configure("Treeview", 
                             background=COLORS["list_bg"], 
                             foreground="white", 
                             fieldbackground=COLORS["list_bg"],
                             bordercolor=COLORS["bg"])
        self.style.map("Treeview", background=[('selected', COLORS["accent"])])

        self.create_widgets()

    def create_widgets(self):
        # Header
        header = tk.Label(self.master, text="Datei-Umbenennung", font=('Segoe UI', 18, 'bold'), 
                          bg=COLORS["bg"], fg=COLORS["accent"])
        header.pack(pady=(20, 10))

        # --- ORDNERAUSWAHL ---
        path_frame = tk.LabelFrame(self.master, text=" Quellauswahl ", bg=COLORS["bg"], fg=COLORS["fg"], padx=15, pady=10)
        path_frame.pack(padx=20, pady=10, fill="x")

        self.label_dir = tk.Label(path_frame, text="Kein Ordner ausgewählt", bg=COLORS["bg"], fg="gray", wraplength=500)
        self.label_dir.pack(side="left", fill="x", expand=True)
        
        tk.Button(path_frame, text="Ordner wählen", command=self.select_directory, 
                  bg=COLORS["card"], fg="white", relief="flat", padx=10).pack(side="right")

        # --- EINSTELLUNGEN ---
        settings_frame = tk.Frame(self.master, bg=COLORS["bg"])
        settings_frame.pack(padx=20, pady=10, fill="x")

        # Original Text
        tk.Label(settings_frame, text="Suchen nach:", bg=COLORS["bg"], fg="white").grid(row=0, column=0, sticky="w", pady=5)
        self.old_text_entry = tk.Entry(settings_frame, width=40, bg=COLORS["input_bg"], fg="white", 
                                       insertbackground="white", borderwidth=0)
        self.old_text_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        # Neuer Text
        tk.Label(settings_frame, text="Ersetzen durch:", bg=COLORS["bg"], fg="white").grid(row=1, column=0, sticky="w", pady=5)
        self.new_text_entry = tk.Entry(settings_frame, width=40, bg=COLORS["input_bg"], fg="white", 
                                       insertbackground="white", borderwidth=0)
        self.new_text_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        settings_frame.grid_columnconfigure(1, weight=1)

        # --- VORSCHAU TABELLE ---
        list_frame = tk.LabelFrame(self.master, text=" Vorschau der Änderungen ", bg=COLORS["bg"], fg=COLORS["fg"], padx=10, pady=10)
        list_frame.pack(padx=20, pady=10, fill="both", expand=True)

        self.tree = ttk.Treeview(list_frame, columns=("Original", "Neu"), show='headings')
        self.tree.heading("Original", text="Originaler Dateiname")
        self.tree.heading("Neu", text="Neuer Dateiname")
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # --- STATUS & BUTTONS ---
        status_frame = tk.Frame(self.master, bg=COLORS["bg"], padx=20)
        status_frame.pack(fill="x", pady=10)

        self.log_label = tk.Label(status_frame, text="Status: Bereit", bg=COLORS["bg"], fg="white", font=("Segoe UI", 9))
        self.log_label.pack(side="left")

        btn_frame = tk.Frame(self.master, bg=COLORS["bg"])
        btn_frame.pack(pady=(0, 20))

        tk.Button(btn_frame, text="🔍 Vorschau generieren", command=self.preview_rename, 
                  bg=COLORS["card"], fg="white", font=("Segoe UI", 10), padx=15, pady=5, relief="flat").pack(side="left", padx=10)
        
        self.rename_button = tk.Button(btn_frame, text="💾 Umbenennen ausführen", command=self.perform_rename, 
                                       bg=COLORS["success"], fg="white", font=("Segoe UI", 10, "bold"), padx=15, pady=5, relief="flat")
        self.rename_button.pack(side="left", padx=10)

    # --- LOGIK ---

    def select_directory(self):
        folder_selected = filedialog.askdirectory(title="Ordner mit Dateien wählen")
        if folder_selected:
            self.directory = folder_selected
            self.label_dir.config(text=self.directory, fg=COLORS["accent"])
            self.update_log(f"Ordner geladen: {os.path.basename(self.directory)}")
            self.clear_preview()

    def update_log(self, message, is_error=False):
        color = COLORS["error"] if is_error else "white"
        self.log_label.config(text=f"Status: {message}", fg=color)

    def clear_preview(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

    def get_renames(self):
        old_text = self.old_text_entry.get()
        new_text = self.new_text_entry.get()
        
        if not self.directory:
            self.update_log("Bitte zuerst einen Ordner auswählen.", is_error=True)
            return None
        if not old_text:
            self.update_log("Geben Sie einen Text zum Ersetzen ein.", is_error=True)
            return None

        rename_list = []
        new_names_check = set()
        
        try:
            for filename in os.listdir(self.directory):
                current_path = os.path.join(self.directory, filename)
                
                if old_text in filename and os.path.isfile(current_path):
                    new_filename = filename.replace(old_text, new_text)
                    new_path = os.path.join(self.directory, new_filename)

                    # Validierung
                    if new_filename in new_names_check:
                        self.update_log(f"Fehler: Duplikat '{new_filename}' entsteht.", is_error=True)
                        return None
                    if os.path.exists(new_path) and new_path != current_path:
                        self.update_log(f"Datei '{new_filename}' existiert bereits.", is_error=True)
                        return None

                    rename_list.append((current_path, new_path, filename, new_filename))
                    new_names_check.add(new_filename)
            
            return rename_list
        except Exception as e:
            self.update_log(f"Fehler beim Lesen: {e}", is_error=True)
            return None

    def preview_rename(self):
        self.clear_preview()
        rename_list = self.get_renames()
        if not rename_list:
            if rename_list is not None:
                self.update_log("Keine passenden Dateien gefunden.", is_error=True)
            return

        for _, _, old_name, new_name in rename_list:
            self.tree.insert("", tk.END, values=(old_name, new_name))
        
        self.update_log(f"{len(rename_list)} Änderungen vorbereitet.")

    def perform_rename(self):
        rename_list = self.get_renames()
        if not rename_list: return
        
        if not messagebox.askyesno("Bestätigen", f"{len(rename_list)} Dateien wirklich umbenennen?"):
            return

        count = 0
        try:
            for current_path, new_path, _, _ in rename_list:
                os.rename(current_path, new_path)
                count += 1
            
            self.update_log(f"Erfolg: {count} Dateien umbenannt.", is_error=False)
            messagebox.showinfo("Erfolg", f"{count} Dateien wurden erfolgreich umbenannt!")
            self.clear_preview()
        except Exception as e:
            self.update_log(f"Fehler: {e}", is_error=True)
            messagebox.showerror("Fehler", f"Fehler aufgetreten: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileRenameTool(root)
    root.mainloop()