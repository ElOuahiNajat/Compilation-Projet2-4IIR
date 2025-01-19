import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import re
from typing import Dict
from ttkthemes import ThemedTk
from tkinter import font as tkfont
import pyperclip
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import time

# Définition du thème de couleurs
THEME = {
    'bg_primary': "#1a1a1a",        # Fond principal très sombre
    'bg_secondary': "#252525",      # Fond secondaire
    'bg_tertiary': "#2d2d2d",       # Fond tertiaire pour les éléments interactifs
    'fg_primary': "#ffffff",        # Texte principal
    'fg_secondary': "#b3b3b3",      # Texte secondaire
    'accent_primary': "#007acc",    # Accent principal (bleu)
    'accent_secondary': "#0098ff",  # Accent secondaire (bleu clair)
    'success': "#28a745",          # Vert pour les succès
    'warning': "#ffc107",          # Jaune pour les avertissements
    'error': "#dc3545",            # Rouge pour les erreurs
    'border': "#404040",           # Couleur de bordure
}

# Définition des styles de police
FONTS = {
    'title': ('Segoe UI', 16, 'bold'),
    'subtitle': ('Segoe UI', 14, 'bold'),
    'text': ('Consolas', 12),
    'button': ('Segoe UI', 11),
}

class SQLGeneratorDSL:
    def __init__(self):
        # Mapping des types pour les colonnes
        self.type_mapping = {
            'entier': 'INTEGER',
            'texte': 'VARCHAR(255)',
            'date': 'DATE'
        }

    def parse_table(self, description: str) -> Dict:
        tables = {}
        current_table = None
        lines = description.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith('table '):
                table_match = re.match(r'table\s+(\w+):', line)
                if table_match:
                    current_table = table_match.group(1)
                    tables[current_table] = {'columns': [], 'constraints': []}
                continue

            if line.startswith('- ') and current_table:
                column = self.parse_column(line[2:])
                if column:
                    tables[current_table]['columns'].append(column)
                    if 'reference' in column:
                        ref = column['reference']
                        constraint = f"FOREIGN KEY ({column['name']}) REFERENCES {ref['table']}({ref['column']})"
                        tables[current_table]['constraints'].append(constraint)
        return tables

    def parse_column(self, column_def: str) -> Dict:
        parts = column_def.split('(')
        if not parts:
            return None

        name = parts[0].strip()
        properties = []
        if len(parts) > 1:
            properties = [p.strip(' )') for p in parts[1].split(',')]

        column = {
            'name': name,
            'type': None,
            'constraints': []
        }

        for prop in properties:
            prop = prop.strip()
            if prop in self.type_mapping:
                column['type'] = self.type_mapping[prop]
            elif prop == 'clé primaire':
                column['constraints'].append('PRIMARY KEY')
            elif prop == 'auto':
                column['constraints'].append('AUTO_INCREMENT')
            elif prop == 'requis':
                column['constraints'].append('NOT NULL')
            elif prop == 'unique':
                column['constraints'].append('UNIQUE')
            elif prop.startswith('par défaut:'):
                default_value = prop.split(':', 1)[1].strip()
                if default_value == 'aujourd\'hui':
                    column['constraints'].append("DEFAULT CURRENT_DATE")
                elif default_value == 'maintenant':
                    column['constraints'].append("DEFAULT CURRENT_TIMESTAMP")
                else:
                    column['constraints'].append(f"DEFAULT '{default_value}'")
            elif prop.startswith('référence:'):
                ref = prop.split(':', 1)[1].strip()
                table, column_name = ref.split('.')
                column['reference'] = {'table': table, 'column': column_name}
        return column

    def generate_sql(self, tables: Dict, db_type: str = "MySQL") -> str:
        sql_parts = []
        for table_name, table in tables.items():
            create_table = f"CREATE TABLE {table_name} (\n"
            column_defs = []
            for column in table['columns']:
                col_def = f"    {column['name']} {column['type']}"
                if column['constraints']:
                    col_def += ' ' + ' '.join(column['constraints'])
                column_defs.append(col_def)
            if table['constraints']:
                column_defs.extend([f"    {constraint}" for constraint in table['constraints']])
            create_table += ',\n'.join(column_defs)
            create_table += "\n);"
            sql_parts.append(create_table)

        return '\n\n'.join(sql_parts)


class ModernButton(tk.Button):
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            bg=THEME['bg_tertiary'],
            fg=THEME['fg_primary'],
            activebackground=THEME['accent_primary'],
            activeforeground=THEME['fg_primary'],
            font=FONTS['button'],
            relief=tk.FLAT,
            borderwidth=0,
            padx=15,
            pady=8,
            cursor="hand2",
            **kwargs
        )
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)

    def _on_enter(self, e):
        self['background'] = THEME['accent_primary']

    def _on_leave(self, e):
        self['background'] = THEME['bg_tertiary']


class SQLGeneratorGUI:
    def __init__(self, root, welcome_screen):
        self.root = root
        self.welcome_screen = welcome_screen
        self.generator = SQLGeneratorDSL()

        # Configuration de la fenêtre principale
        self.root.configure(bg=THEME['bg_primary'])

        # Navbar
        self.navbar = tk.Frame(
            root,
            bg=THEME['bg_secondary'],
            height=50,
            relief=tk.FLAT
        )
        self.navbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.navbar.grid_propagate(False)

        # Boutons dans la navbar
        buttons = [
            ("Générer SQL", self.generate),
            ("Effacer", self.clear),
            ("Exporter", self.export_sql),
            ("Copier", self.copy_to_clipboard),
            ("Importer", self.import_dsl),
            ("Aperçu", self.show_table_preview),
            ("Statistiques", self.show_statistics),
            ("Rechercher", self.show_search_replace),
            ("Valider", self.validate_syntax),
            ("Annuler", self.undo),
            ("Rétablir", self.redo),
            ("Retour", self.go_back),
            ("Quitter", self.exit_application)
        ]

        for text, command in buttons:
            btn = ModernButton(
                self.navbar,
                text=text,
                command=command
            )
            btn.pack(side="left", padx=2)

        # Frame de description
        self.description_frame = tk.LabelFrame(
            root,
            text="Description DSL",
            bg=THEME['bg_secondary'],
            fg=THEME['fg_primary'],
            font=FONTS['subtitle'],
            relief=tk.FLAT,
            bd=2
        )
        self.description_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Zone de texte de description
        self.description_text = scrolledtext.ScrolledText(
            self.description_frame,
            width=50,
            height=20,
            font=FONTS['text'],
            bg=THEME['bg_tertiary'],
            fg=THEME['fg_primary'],
            insertbackground=THEME['fg_primary'],
            selectbackground=THEME['accent_primary'],
            selectforeground=THEME['fg_primary'],
            relief=tk.FLAT,
            pady=5,
            padx=5
        )
        self.description_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Exemple prédéfini
        example = """table utilisateurs:
- id (entier, clé primaire, auto)
- nom (texte, requis)
- email (texte, unique)
- date_creation (date, par défaut: aujourd'hui)

table articles:
- id (entier, clé primaire, auto)
- utilisateur_id (entier, requis, référence: utilisateurs.id)
- titre (texte, requis)
- contenu (texte)
- date_publication (date, par défaut: maintenant)"""
        self.description_text.insert("1.0", example)

        # Compteur de lignes
        self.line_count_label = tk.Label(
            self.description_frame,
            text="Lignes : 0",
            bg=THEME['bg_secondary'],
            fg=THEME['fg_secondary'],
            font=FONTS['text']
        )
        self.line_count_label.pack(side="bottom", pady=5)

        # Frame SQL généré
        self.sql_frame = tk.LabelFrame(
            root,
            text="Script SQL",
            bg=THEME['bg_secondary'],
            fg=THEME['fg_primary'],
            font=FONTS['subtitle'],
            relief=tk.FLAT,
            bd=2
        )
        self.sql_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        self.sql_text = tk.Text(
            self.sql_frame,
            width=50,
            height=20,
            font=FONTS['text'],
            bg=THEME['bg_tertiary'],
            fg=THEME['fg_primary'],
            insertbackground=THEME['fg_primary'],
            selectbackground=THEME['accent_primary'],
            selectforeground=THEME['fg_primary'],
            relief=tk.FLAT,
            pady=5,
            padx=5
        )
        self.sql_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Sauvegarde automatique
        self.autosave_file = "autosave_dsl.txt"
        self.root.after(300000, self.autosave)  # Sauvegarde toutes les 5 minutes

    def generate(self):
        description = self.description_text.get("1.0", tk.END)
        tables = self.generator.parse_table(description)
        sql = self.generator.generate_sql(tables)
        self.sql_text.delete("1.0", tk.END)
        self.sql_text.insert("1.0", sql)
        self.color_sql()

    def clear(self):
        self.description_text.delete("1.0", tk.END)
        self.sql_text.delete("1.0", tk.END)

    def export_sql(self):
        sql_content = self.sql_text.get("1.0", tk.END)
        file_path = filedialog.asksaveasfilename(
            defaultextension=".sql",
            filetypes=[("Fichiers SQL", "*.sql"), ("Tous les fichiers", "*.*")],
            title="Enregistrer le fichier SQL"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(sql_content)
                messagebox.showinfo("Succès", f"Le fichier a été enregistré sous : {file_path}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Une erreur s'est produite lors de l'enregistrement : {e}")

    def copy_to_clipboard(self):
        sql_content = self.sql_text.get("1.0", tk.END)
        pyperclip.copy(sql_content)
        messagebox.showinfo("Succès", "Le SQL a été copié dans le presse-papiers.")

    def import_dsl(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")],
            title="Importer un fichier DSL"
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                self.description_text.delete("1.0", tk.END)
                self.description_text.insert("1.0", content)
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de lire le fichier : {e}")

    def show_table_preview(self):
        description = self.description_text.get("1.0", tk.END)
        tables = self.generator.parse_table(description)

        preview_window = tk.Toplevel(self.root)
        preview_window.title("Aperçu des tables")
        preview_window.configure(bg=THEME['bg_primary'])

        tree = ttk.Treeview(preview_window, columns=("Colonne", "Type", "Contraintes"), show="headings")
        tree.heading("Colonne", text="Colonne")
        tree.heading("Type", text="Type")
        tree.heading("Contraintes", text="Contraintes")
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        for table_name, table in tables.items():
            tree.insert("", "end", values=(f"Table: {table_name}", "", ""))
            for column in table['columns']:
                constraints = ", ".join(column['constraints'])
                tree.insert("", "end", values=(column['name'], column['type'], constraints))

    def show_statistics(self):
        description = self.description_text.get("1.0", tk.END)
        tables = self.generator.parse_table(description)

        # Préparation des données pour les graphiques
        table_names = list(tables.keys())
        column_counts = [len(table['columns']) for table in tables.values()]

        # Création des graphiques
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))  # Deux sous-graphiques côte à côte

        # Graphique en barres
        ax1.bar(table_names, column_counts, color=THEME['accent_primary'])
        ax1.set_xlabel("Tables")
        ax1.set_ylabel("Nombre de colonnes")
        ax1.set_title("Nombre de colonnes par table")

        # Graphique en camembert
        ax2.pie(column_counts, labels=table_names, autopct='%1.1f%%', colors=plt.cm.Paired.colors)
        ax2.set_title("Répartition des colonnes par table")

        # Affichage des graphiques dans une nouvelle fenêtre
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Statistiques")
        stats_window.configure(bg=THEME['bg_primary'])

        canvas = FigureCanvasTkAgg(fig, master=stats_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def show_search_replace(self):
        search_window = tk.Toplevel(self.root)
        search_window.title("Rechercher et Remplacer")
        search_window.configure(bg=THEME['bg_primary'])

        tk.Label(search_window, text="Rechercher:", bg=THEME['bg_primary'], fg=THEME['fg_primary']).grid(row=0, column=0, padx=5, pady=5)
        self.search_entry = tk.Entry(search_window, width=30, bg=THEME['bg_tertiary'], fg=THEME['fg_primary'])
        self.search_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(search_window, text="Remplacer par:", bg=THEME['bg_primary'], fg=THEME['fg_primary']).grid(row=1, column=0, padx=5, pady=5)
        self.replace_entry = tk.Entry(search_window, width=30, bg=THEME['bg_tertiary'], fg=THEME['fg_primary'])
        self.replace_entry.grid(row=1, column=1, padx=5, pady=5)

        ModernButton(search_window, text="Rechercher", command=self.search_text).grid(row=2, column=0, padx=5, pady=5)
        ModernButton(search_window, text="Remplacer", command=self.replace_text).grid(row=2, column=1, padx=5, pady=5)

    def search_text(self):
        search_term = self.search_entry.get()
        if search_term:
            start_index = self.description_text.search(search_term, "1.0", stopindex=tk.END)
            if start_index:
                end_index = f"{start_index}+{len(search_term)}c"
                self.description_text.tag_remove("search", "1.0", tk.END)
                self.description_text.tag_add("search", start_index, end_index)
                self.description_text.tag_config("search", background="yellow", foreground="black")
                self.description_text.mark_set(tk.INSERT, start_index)
                self.description_text.see(start_index)
            else:
                messagebox.showinfo("Rechercher", "Aucune correspondance trouvée.")

    def replace_text(self):
        search_term = self.search_entry.get()
        replace_term = self.replace_entry.get()
        if search_term and replace_term:
            start_index = self.description_text.search(search_term, "1.0", stopindex=tk.END)
            if start_index:
                end_index = f"{start_index}+{len(search_term)}c"
                self.description_text.delete(start_index, end_index)
                self.description_text.insert(start_index, replace_term)
                self.description_text.tag_remove("search", "1.0", tk.END)
                self.description_text.tag_add("search", start_index, f"{start_index}+{len(replace_term)}c")
                self.description_text.tag_config("search", background="yellow", foreground="black")
                self.description_text.mark_set(tk.INSERT, start_index)
                self.description_text.see(start_index)
            else:
                messagebox.showinfo("Remplacer", "Aucune correspondance trouvée.")

    def validate_syntax(self):
        description = self.description_text.get("1.0", tk.END)
        try:
            self.generator.parse_table(description)
            messagebox.showinfo("Validation", "La syntaxe DSL est correcte.")
        except Exception as e:
            messagebox.showerror("Erreur de syntaxe", f"Erreur détectée : {e}")

    def autosave(self):
        description = self.description_text.get("1.0", tk.END)
        try:
            with open(self.autosave_file, "w", encoding="utf-8") as file:
                file.write(description)
        except Exception as e:
            messagebox.showerror("Erreur de sauvegarde", f"Impossible de sauvegarder : {e}")
        self.root.after(300000, self.autosave)  # Répéter toutes les 5 minutes

    def undo(self):
        self.description_text.edit_undo()

    def redo(self):
        self.description_text.edit_redo()

    def update_line_count(self):
        line_count = self.description_text.get("1.0", tk.END).count("\n")
        self.line_count_label.config(text=f"Lignes : {line_count}")

    def go_back(self):
        self.description_frame.grid_forget()
        self.sql_frame.grid_forget()
        self.navbar.grid_forget()
        self.welcome_screen.description_label.pack(pady=20)
        self.welcome_screen.explore_button.pack(pady=10)

    def exit_application(self):
        if messagebox.askyesno("Quitter", "Êtes-vous sûr de vouloir quitter ?"):
            self.root.quit()

    def color_sql(self):
        self.sql_text.tag_config("keyword", foreground="#569CD6")    # Bleu
        self.sql_text.tag_config("type", foreground="#4EC9B0")      # Turquoise
        self.sql_text.tag_config("string", foreground="#CE9178")    # Orange
        self.sql_text.tag_config("number", foreground="#B5CEA8")    # Vert clair
        self.sql_text.tag_config("comment", foreground="#6A9955")   # Vert

        keywords = r"\b(CREATE|TABLE|FOREIGN|KEY|REFERENCES|NOT NULL|DEFAULT|PRIMARY KEY|AUTO_INCREMENT|UNIQUE)\b"
        types = r"\b(INTEGER|VARCHAR|DATE)\b"
        constraints = r"\b(FOREIGN KEY|PRIMARY KEY|REFERENCES|NOT NULL|AUTO_INCREMENT|UNIQUE|DEFAULT)\b"

        sql_text = self.sql_text.get("1.0", tk.END)

        for match in re.finditer(keywords, sql_text, re.IGNORECASE):
            self.sql_text.tag_add("keyword", f"1.0 + {match.start()}c", f"1.0 + {match.end()}c")
        for match in re.finditer(types, sql_text, re.IGNORECASE):
            self.sql_text.tag_add("type", f"1.0 + {match.start()}c", f"1.0 + {match.end()}c")
        for match in re.finditer(constraints, sql_text, re.IGNORECASE):
            self.sql_text.tag_add("constraint", f"1.0 + {match.start()}c", f"1.0 + {match.end()}c")


class WelcomeScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("SQL Generator")
        self.root.configure(bg=THEME['bg_primary'])

        # Frame principale
        main_frame = tk.Frame(
            root,
            bg=THEME['bg_primary'],
            padx=40,
            pady=40
        )
        main_frame.pack(expand=True, fill="both")

        # Titre
        title_label = tk.Label(
            main_frame,
            text="SQL Generator",
            font=('Segoe UI', 32, 'bold'),
            bg=THEME['bg_primary'],
            fg=THEME['accent_primary']
        )
        title_label.pack(pady=(0, 20))

        # Description
        description = """
        Bienvenue dans l'outil de génération de scripts SQL.

        Cet outil vous permet de décrire votre base de données
        en utilisant un langage simple et de générer
        automatiquement le script SQL correspondant.
        """
        self.description_label = tk.Label(
            main_frame,
            text=description,
            bg=THEME['bg_primary'],
            fg=THEME['fg_secondary'],
            font=FONTS['text'],
            justify="center"
        )
        self.description_label.pack(pady=20)

        # Bouton Explorer
        self.explore_button = ModernButton(
            main_frame,
            text="Commencer",
            command=self.show_sql_generator,
            width=20
        )
        self.explore_button.pack(pady=20)

    def show_sql_generator(self):
        self.root.configure(bg=THEME['bg_primary'])
        for widget in self.root.winfo_children():
            widget.destroy()
        self.sql_generator = SQLGeneratorGUI(self.root, self)


def main():
    root = ThemedTk(theme="equilux")
    root.title("SQL Generator")
    root.geometry("1200x800")
    welcome_screen = WelcomeScreen(root)
    root.mainloop()


if __name__ == "__main__":
    main()