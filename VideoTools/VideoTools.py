import tkinter as tk
from tkinter import ttk
import subprocess
import os
import sys

class VideoToolHub:
    def __init__(self, root):
        self.root = root
        self.root.title("🎬 Video Tool Hub")
        self.root.geometry("600x450")
        self.root.configure(bg="#1a1a1a")

        # Styling
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Design-Konfiguration
        self.colors = {
            "bg": "#1a1a1a",
            "card": "#2a2a2a",
            "text": "#f0f0f0",
            "accent": "#3b82f6", # Blau
            "hover": "#2563eb"
        }

        self.setup_ui()

    def setup_ui(self):
        # Header
        header = tk.Label(
            self.root, text="Video Processing Dashboard",
            font=("Inter", 18, "bold"), bg=self.colors["bg"], fg=self.colors["accent"],
            pady=20
        )
        header.pack()

        # Container für die Buttons
        container = tk.Frame(self.root, bg=self.colors["bg"])
        container.pack(expand=True, fill="both", padx=40)

        # Definition deiner Tools (Dateiname muss im gleichen Ordner liegen)
        tools = [
            ("🎥 Movie Converter", "movie_converter.py", "Konvertiert Formate für optimale Kompatibilität"),            
            ("📺 Serien Renamer", "serien_renamer.py", "S01E01 Schema für Serien-Dateien"),
            ("📝 File Renamer", "file_renamer.py", "Säubert Dateinamen für Filme"),
            ("⚙️ Metadaten Editor", "metadaten_editor.py", "Editiere Einträge des Videohubs (metadaten.json)"),
        ]

        for title, script, desc in tools:
            self.create_tool_card(container, title, script, desc)

        # Footer
        footer = tk.Label(
            self.root, text="Status: Bereit",
            font=("Inter", 9), bg=self.colors["bg"], fg="#666", pady=10
        )
        footer.pack(side="bottom")

    def create_tool_card(self, parent, title, script, desc):
        # Rahmen für ein Tool
        card = tk.Frame(parent, bg=self.colors["card"], bd=0, highlightthickness=1, highlightbackground="#444")
        card.pack(fill="x", pady=10, ipady=5)

        # Text-Bereich
        info_frame = tk.Frame(card, bg=self.colors["card"])
        info_frame.pack(side="left", padx=15, fill="y")

        tk.Label(info_frame, text=title, font=("Inter", 12, "bold"), 
                 bg=self.colors["card"], fg=self.colors["text"]).pack(anchor="w")
        tk.Label(info_frame, text=desc, font=("Inter", 9), 
                 bg=self.colors["card"], fg="#aaa").pack(anchor="w")

        # Start-Button
        btn = tk.Button(
            card, text="Starten", 
            command=lambda s=script: self.launch_tool(s),
            bg=self.colors["accent"], fg="white",
            font=("Inter", 10, "bold"), relief="flat",
            activebackground=self.colors["hover"], activeforeground="white",
            cursor="hand2", width=10
        )
        btn.pack(side="right", padx=15)

    def launch_tool(self, script_name):
        """Startet das Skript in einem separaten Prozess."""
        script_path = os.path.join(os.path.dirname(__file__), script_name)
        
        if os.path.exists(script_path):
            # Nutzt den aktuellen Python-Interpreter für den Start
            subprocess.Popen([sys.executable, script_path])
        else:
            print(f"Fehler: {script_name} wurde im Ordner nicht gefunden!")

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoToolHub(root)
    root.mainloop()