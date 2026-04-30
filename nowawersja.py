import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from pathlib import Path
import sqlite3
import csv
import sys

try:
    import pyodbc
except ImportError:
    pyodbc = None

try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_OK = True
except Exception:
    MATPLOTLIB_OK = False
    Figure = None
    FigureCanvasTkAgg = None

APP_DIR = Path(__file__).resolve().parent
DBFILE = APP_DIR / "gmsystem.db"
SQLFILE = APP_DIR / "gm_schema_and_data_extended.sql"

# Konfiguracja aktywnej bazy (zmieniona na sqlite jako domyślna)
ACTIVE_DB = "sqlite"

DB_CONFIG = {
    "sqlite": {
        "type": "sqlite",
        "database": DBFILE,
    },
    "sqlserver_1": {
        "type": "pyodbc",
        "driver": "ODBC Driver 17 for SQL Server",
        "server": r"localhost\SQLEXPRESS",
        "database": "GMSystem1",
        "trusted_connection": "yes",
        "uid": "",
        "pwd": "",
    }
}

def get_connection():
    cfg = DB_CONFIG[ACTIVE_DB]

    if cfg["type"] == "sqlite":
        conn = sqlite3.connect(cfg["database"])
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    if cfg["type"] == "pyodbc":
        if pyodbc is None:
            raise RuntimeError("Brak biblioteki pyodbc. Zainstaluj: pip install pyodbc")

        if str(cfg.get("trusted_connection", "yes")).lower() in ("yes", "true", "1"):
            conn_str = (
                f"DRIVER={{{cfg['driver']}}};"
                f"SERVER={cfg['server']};"
                f"DATABASE={cfg['database']};"
                "Trusted_Connection=yes;"
            )
        else:
            conn_str = (
                f"DRIVER={{{cfg['driver']}}};"
                f"SERVER={cfg['server']};"
                f"DATABASE={cfg['database']};"
                f"UID={cfg.get('uid', '')};"
                f"PWD={cfg.get('pwd', '')};"
            )

        return pyodbc.connect(conn_str)

    raise ValueError(f"Nieobsługiwany typ bazy: {cfg['type']}")


class MagazynApp:
    def __init__(self, root):
        self.root = root
        self.root.title("System GM - Gospodarka Magazynowa (Zintegrowany)")
        self.root.geometry("1200x800")

        self.materialy_dict = {}
        self.magazyny_dict = {}
        
        # Flagi/zmienne dla raportów Matplotlib
        self.current_chart_canvas = None
        self.current_figure = None
        self.chart_mode = "bar"

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Inicjalizacja zakładek
        self.create_przyjecia_tab()
        self.create_wydania_tab()
        self.create_kartoteka_tab()
        self.create_inwentaryzacja_tab()
        self.create_zapas_tab()
        self.create_raporty_tab()

    # ─────────────────────────────────────────────────────────────
    #  ZAKŁADKA: PRZYJĘCIA
    # ─────────────────────────────────────────────────────────────
    def create_przyjecia_tab(self):
        self.przyjecia_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.przyjecia_frame, text="Przyjęcia")

        form_frame = ttk.LabelFrame(self.przyjecia_frame, text="Dodaj nowe przyjęcie", padding=10)
        form_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(form_frame, text="Materiał").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.przyjecia_material_combo = ttk.Combobox(form_frame, state="readonly", width=40)
        self.przyjecia_material_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Ilość").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.przyjecia_ilosc_entry = ttk.Entry(form_frame, width=20)
        self.przyjecia_ilosc_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(form_frame, text="Data operacji").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.przyjecia_data_entry = ttk.Entry(form_frame, width=20)
        self.przyjecia_data_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        self.przyjecia_data_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ttk.Label(form_frame, text="Magazyn").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.przyjecia_magazyn_combo = ttk.Combobox(form_frame, state="readonly", width=30)
        self.przyjecia_magazyn_combo.grid(row=3, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(form_frame, text="Dostawca").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.przyjecia_dostawca_entry = ttk.Entry(form_frame, width=50)
        self.przyjecia_dostawca_entry.grid(row=4, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Uwagi").grid(row=5, column=0, sticky="nw", padx=5, pady=5)
        self.przyjecia_uwagi_text = tk.Text(form_frame, height=3, width=50)
        self.przyjecia_uwagi_text.grid(row=5, column=1, padx=5, pady=5)

        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=10)
        ttk.Button(button_frame, text="Dodaj przyjęcie", command=self.add_przyjecie).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Odśwież", command=self.refresh_przyjecia).pack(side="left", padx=5)

        table_frame = ttk.LabelFrame(self.przyjecia_frame, text="Historia przyjęć", padding=10)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side="right", fill="y")

        cols = ("ID", "Materiał", "Ilość", "Data", "Magazyn", "Dostawca", "Uwagi")
        self.przyjecia_tree = ttk.Treeview(table_frame, columns=cols, show="headings", yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.przyjecia_tree.yview)

        for col in cols:
            self.przyjecia_tree.heading(col, text=col)
            self.przyjecia_tree.column(col, width=120)

        self.przyjecia_tree.pack(fill="both", expand=True)

        self.load_combobox_data()
        self.refresh_przyjecia()

    # ─────────────────────────────────────────────────────────────
    #  ZAKŁADKA: WYDANIA
    # ─────────────────────────────────────────────────────────────
    def create_wydania_tab(self):
        self.wydania_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.wydania_frame, text="Wydania")

        form_frame = ttk.LabelFrame(self.wydania_frame, text="Dodaj nowe wydanie", padding=10)
        form_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(form_frame, text="Materiał").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.wydania_material_combo = ttk.Combobox(form_frame, state="readonly", width=40)
        self.wydania_material_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Ilość").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.wydania_ilosc_entry = ttk.Entry(form_frame, width=20)
        self.wydania_ilosc_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(form_frame, text="Data operacji").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.wydania_data_entry = ttk.Entry(form_frame, width=20)
        self.wydania_data_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        self.wydania_data_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ttk.Label(form_frame, text="Magazyn").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.wydania_magazyn_combo = ttk.Combobox(form_frame, state="readonly", width=30)
        self.wydania_magazyn_combo.grid(row=3, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(form_frame, text="Zlecenie/Pracownik").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.wydania_zlecenie_entry = ttk.Entry(form_frame, width=50)
        self.wydania_zlecenie_entry.grid(row=4, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Uwagi").grid(row=5, column=0, sticky="nw", padx=5, pady=5)
        self.wydania_uwagi_text = tk.Text(form_frame, height=3, width=50)
        self.wydania_uwagi_text.grid(row=5, column=1, padx=5, pady=5)

        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=10)
        ttk.Button(button_frame, text="Dodaj wydanie", command=self.add_wydanie).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Odśwież", command=self.refresh_wydania).pack(side="left", padx=5)

        table_frame = ttk.LabelFrame(self.wydania_frame, text="Historia wydań", padding=10)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side="right", fill="y")

        cols = ("ID", "Materiał", "Ilość", "Data", "Magazyn", "Zlecenie/Pracownik", "Uwagi")
        self.wydania_tree = ttk.Treeview(table_frame, columns=cols, show="headings", yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.wydania_tree.yview)

        for col in cols:
            self.wydania_tree.heading(col, text=col)
            self.wydania_tree.column(col, width=130)

        self.wydania_tree.pack(fill="both", expand=True)

        self.wydania_material_combo["values"] = list(self.materialy_dict.keys())
        self.wydania_magazyn_combo["values"] = list(self.magazyny_dict.keys())
        self.refresh_wydania()

    # ─────────────────────────────────────────────────────────────
    #  ZAKŁADKA: KARTOTEKA
    # ─────────────────────────────────────────────────────────────
    def create_kartoteka_tab(self):
        self.kartoteka_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.kartoteka_frame, text="Kartoteka")

        # Lewa strona: materiały
        left = ttk.Frame(self.kartoteka_frame)
        left.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        mat_form = ttk.LabelFrame(left, text="Nowy materiał", padding=10)
        mat_form.pack(fill="x", padx=5, pady=5)

        ttk.Label(mat_form, text="Nazwa").grid(row=0, column=0, sticky="w", padx=5, pady=3)
        self.kart_mat_nazwa = ttk.Entry(mat_form, width=30)
        self.kart_mat_nazwa.grid(row=0, column=1, padx=5, pady=3)

        ttk.Label(mat_form, text="Indeks").grid(row=1, column=0, sticky="w", padx=5, pady=3)
        self.kart_mat_indeks = ttk.Entry(mat_form, width=15)
        self.kart_mat_indeks.grid(row=1, column=1, sticky="w", padx=5, pady=3)

        ttk.Label(mat_form, text="Kategoria").grid(row=2, column=0, sticky="w", padx=5, pady=3)
        self.kart_mat_kategoria = ttk.Entry(mat_form, width=30)
        self.kart_mat_kategoria.grid(row=2, column=1, padx=5, pady=3)

        ttk.Label(mat_form, text="Cena jedn.").grid(row=3, column=0, sticky="w", padx=5, pady=3)
        self.kart_mat_cena = ttk.Entry(mat_form, width=15)
        self.kart_mat_cena.grid(row=3, column=1, sticky="w", padx=5, pady=3)

        ttk.Label(mat_form, text="Jednostka").grid(row=4, column=0, sticky="w", padx=5, pady=3)
        self.kart_mat_jednostka = ttk.Entry(mat_form, width=10)
        self.kart_mat_jednostka.insert(0, "szt")
        self.kart_mat_jednostka.grid(row=4, column=1, sticky="w", padx=5, pady=3)

        btn_mat = ttk.Frame(mat_form)
        btn_mat.grid(row=5, column=0, columnspan=2, pady=8)
        ttk.Button(btn_mat, text="Dodaj materiał", command=self.add_material).pack(side="left", padx=5)
        ttk.Button(btn_mat, text="Usuń zaznaczony", command=self.delete_material).pack(side="left", padx=5)

        mat_table = ttk.LabelFrame(left, text="Lista materiałów", padding=5)
        mat_table.pack(fill="both", expand=True, padx=5, pady=5)

        sb_mat = ttk.Scrollbar(mat_table)
        sb_mat.pack(side="right", fill="y")

        cols_m = ("ID", "Nazwa", "Indeks", "Kategoria", "Cena", "Jednostka")
        self.kart_mat_tree = ttk.Treeview(mat_table, columns=cols_m, show="headings", yscrollcommand=sb_mat.set, height=8)
        sb_mat.config(command=self.kart_mat_tree.yview)
        widths_m = (40, 200, 60, 100, 70, 60)
        for col, w in zip(cols_m, widths_m):
            self.kart_mat_tree.heading(col, text=col)
            self.kart_mat_tree.column(col, width=w)
        self.kart_mat_tree.pack(fill="both", expand=True)

        # Prawa strona: magazyny
        right = ttk.Frame(self.kartoteka_frame)
        right.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        mag_form = ttk.LabelFrame(right, text="Nowy magazyn", padding=10)
        mag_form.pack(fill="x", padx=5, pady=5)

        ttk.Label(mag_form, text="Kod").grid(row=0, column=0, sticky="w", padx=5, pady=3)
        self.kart_mag_kod = ttk.Entry(mag_form, width=15)
        self.kart_mag_kod.grid(row=0, column=1, sticky="w", padx=5, pady=3)

        ttk.Label(mag_form, text="Opis").grid(row=1, column=0, sticky="w", padx=5, pady=3)
        self.kart_mag_opis = ttk.Entry(mag_form, width=30)
        self.kart_mag_opis.grid(row=1, column=1, padx=5, pady=3)

        ttk.Label(mag_form, text="Lokalizacja").grid(row=2, column=0, sticky="w", padx=5, pady=3)
        self.kart_mag_lok = ttk.Entry(mag_form, width=30)
        self.kart_mag_lok.grid(row=2, column=1, padx=5, pady=3)

        btn_mag = ttk.Frame(mag_form)
        btn_mag.grid(row=3, column=0, columnspan=2, pady=8)
        ttk.Button(btn_mag, text="Dodaj magazyn", command=self.add_magazyn).pack(side="left", padx=5)
        ttk.Button(btn_mag, text="Usuń zaznaczony", command=self.delete_magazyn).pack(side="left", padx=5)

        mag_table = ttk.LabelFrame(right, text="Lista magazynów", padding=5)
        mag_table.pack(fill="both", expand=True, padx=5, pady=5)

        sb_mag = ttk.Scrollbar(mag_table)
        sb_mag.pack(side="right", fill="y")

        cols_mg = ("ID", "Kod", "Opis", "Lokalizacja")
        self.kart_mag_tree = ttk.Treeview(mag_table, columns=cols_mg, show="headings", yscrollcommand=sb_mag.set, height=8)
        sb_mag.config(command=self.kart_mag_tree.yview)
        for col in cols_mg:
            self.kart_mag_tree.heading(col, text=col)
            self.kart_mag_tree.column(col, width=100)
        self.kart_mag_tree.pack(fill="both", expand=True)

        self.refresh_kartoteka()

    # ─────────────────────────────────────────────────────────────
    #  ZAKŁADKA: INWENTARYZACJA
    # ─────────────────────────────────────────────────────────────
    def create_inwentaryzacja_tab(self):
        self.inw_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.inw_frame, text="Inwentaryzacja")

        form_frame = ttk.LabelFrame(self.inw_frame, text="Nowy wpis inwentaryzacyjny", padding=10)
        form_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(form_frame, text="Materiał").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.inw_material_combo = ttk.Combobox(form_frame, state="readonly", width=40)
        self.inw_material_combo.grid(row=0, column=1, padx=5, pady=4)

        ttk.Label(form_frame, text="Lokalizacja (ID)").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.inw_lok_combo = ttk.Combobox(form_frame, state="readonly", width=40)
        self.inw_lok_combo.grid(row=1, column=1, padx=5, pady=4)

        ttk.Label(form_frame, text="Pracownik").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        self.inw_pracownik_combo = ttk.Combobox(form_frame, state="readonly", width=30)
        self.inw_pracownik_combo.grid(row=2, column=1, sticky="w", padx=5, pady=4)

        ttk.Label(form_frame, text="Data").grid(row=3, column=0, sticky="w", padx=5, pady=4)
        self.inw_data_entry = ttk.Entry(form_frame, width=20)
        self.inw_data_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.inw_data_entry.grid(row=3, column=1, sticky="w", padx=5, pady=4)

        ttk.Label(form_frame, text="Ilość rzeczywista").grid(row=4, column=0, sticky="w", padx=5, pady=4)
        self.inw_ilosc_entry = ttk.Entry(form_frame, width=15)
        self.inw_ilosc_entry.grid(row=4, column=1, sticky="w", padx=5, pady=4)

        ttk.Label(form_frame, text="Status").grid(row=5, column=0, sticky="w", padx=5, pady=4)
        self.inw_status_combo = ttk.Combobox(form_frame, state="readonly", width=20, values=["Zatwierdzona", "Robocza", "Wyjasnienie"])
        self.inw_status_combo.set("Zatwierdzona")
        self.inw_status_combo.grid(row=5, column=1, sticky="w", padx=5, pady=4)

        ttk.Label(form_frame, text="Uwagi").grid(row=6, column=0, sticky="nw", padx=5, pady=4)
        self.inw_uwagi_text = tk.Text(form_frame, height=2, width=50)
        self.inw_uwagi_text.grid(row=6, column=1, padx=5, pady=4)

        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=8)
        ttk.Button(btn_frame, text="Zapisz inwentaryzację", command=self.add_inwentaryzacja).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Odśwież", command=self.refresh_inwentaryzacja).pack(side="left", padx=5)

        table_frame = ttk.LabelFrame(self.inw_frame, text="Historia inwentaryzacji", padding=10)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        sb = ttk.Scrollbar(table_frame)
        sb.pack(side="right", fill="y")

        cols = ("ID", "Materiał", "Lokalizacja", "Pracownik", "Data", "Stan system.", "Stan rzecz.", "Różnica", "Status", "Uwagi")
        self.inw_tree = ttk.Treeview(table_frame, columns=cols, show="headings", yscrollcommand=sb.set)
        sb.config(command=self.inw_tree.yview)
        widths_i = (40, 160, 120, 120, 90, 80, 80, 60, 90, 140)
        for col, w in zip(cols, widths_i):
            self.inw_tree.heading(col, text=col)
            self.inw_tree.column(col, width=w)
        self.inw_tree.pack(fill="both", expand=True)

        self.refresh_inwentaryzacja()

    # ─────────────────────────────────────────────────────────────
    #  ZAKŁADKA: AKTUALNY STAN ZAPASU
    # ─────────────────────────────────────────────────────────────
    def create_zapas_tab(self):
        self.zapas_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.zapas_frame, text="Aktualny stan zapasu")

        filter_frame = ttk.LabelFrame(self.zapas_frame, text="Filtrowanie", padding=8)
        filter_frame.pack(fill="x", padx=10, pady=8)

        ttk.Label(filter_frame, text="Magazyn (wszystkie jeśli puste):").pack(side="left", padx=5)
        self.zapas_mag_filter = ttk.Combobox(filter_frame, state="readonly", width=25)
        self.zapas_mag_filter.pack(side="left", padx=5)

        ttk.Button(filter_frame, text="Odśwież stan", command=self.refresh_zapas).pack(side="left", padx=10)
        ttk.Button(filter_frame, text="Eksportuj do pliku tekstowego", command=self.export_zapas).pack(side="left", padx=5)

        table_frame = ttk.LabelFrame(self.zapas_frame, text="Bieżący stan zapasów (suma przyjęć − suma wydań)", padding=10)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        sb = ttk.Scrollbar(table_frame)
        sb.pack(side="right", fill="y")

        cols = ("Materiał", "Magazyn", "Akt. ilość", "Jednostka", "Cena jedn.", "Wartość zapasu", "Lokalizacja")
        self.zapas_tree = ttk.Treeview(table_frame, columns=cols, show="headings", yscrollcommand=sb.set)
        sb.config(command=self.zapas_tree.yview)
        widths_z = (200, 80, 80, 70, 90, 110, 160)
        for col, w in zip(cols, widths_z):
            self.zapas_tree.heading(col, text=col)
            self.zapas_tree.column(col, width=w)
        self.zapas_tree.pack(fill="both", expand=True)

        self.zapas_summary_label = ttk.Label(self.zapas_frame, text="", font=("", 10, "bold"))
        self.zapas_summary_label.pack(anchor="e", padx=15, pady=4)

        self.refresh_zapas()

    # ─────────────────────────────────────────────────────────────
    #  ZAKŁADKA: RAPORTY (ze źródła 2)
    # ─────────────────────────────────────────────────────────────
    def create_raporty_tab(self):
        self.raporty_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.raporty_frame, text="Raporty")

        ctrl_frame = ttk.LabelFrame(self.raporty_frame, text="Opcje raportu", padding=10)
        ctrl_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(ctrl_frame, text="1. Stan zapasu", command=self.raport_stan_zapasu).pack(side="left", padx=5)
        ttk.Button(ctrl_frame, text="2. Analiza miesięczna", command=self.raport_miesieczny).pack(side="left", padx=5)
        ttk.Button(ctrl_frame, text="3. Ruchy magazynowe", command=self.raport_ruchy).pack(side="left", padx=5)
        ttk.Button(ctrl_frame, text="4. Ranking produktów", command=self.raport_ranking).pack(side="left", padx=5)
        ttk.Button(ctrl_frame, text="Tryb słupkowy", command=self.configure_bar_chart).pack(side="left", padx=5)
        ttk.Button(ctrl_frame, text="Tryb liniowy", command=self.configure_line_chart).pack(side="left", padx=5)
        ttk.Button(ctrl_frame, text="Eksportuj CSV", command=self.export_csv).pack(side="left", padx=5)

        self.chart_frame = ttk.LabelFrame(self.raporty_frame, text="Wykres", padding=10)
        self.chart_frame.pack(fill="both", expand=False, padx=10, pady=(0, 10))

        chart_controls = ttk.Frame(self.chart_frame)
        chart_controls.pack(fill="x", pady=(0, 8))

        ttk.Label(chart_controls, text="Metryka").grid(row=0, column=0, padx=4, pady=4, sticky="w")
        self.chart_metric_combo = ttk.Combobox(chart_controls, state="readonly", width=18, values=["Ilość", "Wartość", "Liczba operacji"])
        self.chart_metric_combo.grid(row=0, column=1, padx=4, pady=4)
        self.chart_metric_combo.set("Ilość")

        ttk.Label(chart_controls, text="Grupowanie").grid(row=0, column=2, padx=4, pady=4, sticky="w")
        self.chart_group_combo = ttk.Combobox(chart_controls, state="readonly", width=18, values=["Materiał", "Magazyn", "Miesiąc"])
        self.chart_group_combo.grid(row=0, column=3, padx=4, pady=4)
        self.chart_group_combo.set("Materiał")

        ttk.Label(chart_controls, text="Typ operacji").grid(row=0, column=4, padx=4, pady=4, sticky="w")
        self.chart_type_combo = ttk.Combobox(chart_controls, state="readonly", width=14, values=["Wszystkie", "Przyjcie", "Wydanie"])
        self.chart_type_combo.grid(row=0, column=5, padx=4, pady=4)
        self.chart_type_combo.set("Wszystkie")

        ttk.Label(chart_controls, text="Limit").grid(row=0, column=6, padx=4, pady=4, sticky="w")
        self.chart_limit_entry = ttk.Entry(chart_controls, width=6)
        self.chart_limit_entry.grid(row=0, column=7, padx=4, pady=4)
        self.chart_limit_entry.insert(0, "10")

        ttk.Button(chart_controls, text="Rysuj wykres", command=self.draw_embedded_chart).grid(row=0, column=8, padx=6, pady=4)
        ttk.Button(chart_controls, text="Wyczyść wykres", command=self.clear_chart).grid(row=0, column=9, padx=6, pady=4)

        self.chart_message = ttk.Label(self.chart_frame, text="Wybierz parametry i kliknij 'Rysuj wykres'.")
        self.chart_message.pack(anchor="w", pady=(0, 6))

        self.chart_canvas_holder = ttk.Frame(self.chart_frame, height=320)
        self.chart_canvas_holder.pack(fill="both", expand=True)
        self.chart_canvas_holder.pack_propagate(False)

        table_frame = ttk.LabelFrame(self.raporty_frame, text="Wyniki raportu", padding=10)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.raport_y_scroll = ttk.Scrollbar(table_frame)
        self.raport_y_scroll.pack(side="right", fill="y")
        self.raport_x_scroll = ttk.Scrollbar(table_frame, orient="horizontal")
        self.raport_x_scroll.pack(side="bottom", fill="x")

        cols = ("Lp.", "Materiał", "Magazyn", "Ilość", "Wartość", "Wyszczególnienie")
        self.raporty_tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=16, yscrollcommand=self.raport_y_scroll.set, xscrollcommand=self.raport_x_scroll.set)
        self.raport_y_scroll.config(command=self.raporty_tree.yview)
        self.raport_x_scroll.config(command=self.raporty_tree.xview)

        widths = {"Lp.": 50, "Materiał": 240, "Magazyn": 90, "Ilość": 140, "Wartość": 140, "Wyszczególnienie": 280}
        for col in cols:
            self.raporty_tree.heading(col, text=col)
            self.raporty_tree.column(col, width=widths[col], anchor="w")
        self.raporty_tree.pack(fill="both", expand=True)

    # ═════════════════════════════════════════════════════════════
    #  LOGIKA DANYCH I GŁÓWNE METODY
    # ═════════════════════════════════════════════════════════════

    def load_combobox_data(self):
        conn = get_connection()
        cursor = conn.cursor()

        # Materiały
        cursor.execute("SELECT MaterialID, Nazwa FROM Materialy ORDER BY Nazwa")
        materialy = cursor.fetchall()
        self.materialy_dict = {row[1]: row[0] for row in materialy}
        if hasattr(self, "przyjecia_material_combo"):
            self.przyjecia_material_combo["values"] = list(self.materialy_dict.keys())
        if hasattr(self, "wydania_material_combo"):
            self.wydania_material_combo["values"] = list(self.materialy_dict.keys())

        # Magazyny
        cursor.execute("SELECT MagazynID, Kod, Opis FROM Magazyny ORDER BY Kod")
        magazyny = cursor.fetchall()
        self.magazyny_dict = {f"{row[1]} - {row[2]}": row[0] for row in magazyny}
        if hasattr(self, "przyjecia_magazyn_combo"):
            self.przyjecia_magazyn_combo["values"] = list(self.magazyny_dict.keys())
        if hasattr(self, "wydania_magazyn_combo"):
            self.wydania_magazyn_combo["values"] = list(self.magazyny_dict.keys())

        conn.close()

        if hasattr(self, "inw_material_combo"):
            self._load_inwentaryzacja_combos()
        if hasattr(self, "zapas_mag_filter"):
            self._load_zapas_filter()

    # ── PRZYJĘCIA I WYDANIA ──────────────────────────────────────

    def add_przyjecie(self):
        try:
            material_name = self.przyjecia_material_combo.get()
            magazyn_name = self.przyjecia_magazyn_combo.get()

            if not material_name:
                messagebox.showerror("Błąd", "Wybierz materiał.")
                return
            if not magazyn_name:
                messagebox.showerror("Błąd", "Wybierz magazyn.")
                return

            ilosc = int(self.przyjecia_ilosc_entry.get())
            if ilosc <= 0:
                raise ValueError("Ilość musi być większa od zera.")

            data = self.przyjecia_data_entry.get().strip()
            datetime.strptime(data, "%Y-%m-%d")

            material_id = self.materialy_dict[material_name]
            magazyn_id = self.magazyny_dict[magazyn_name]
            dostawca = self.przyjecia_dostawca_entry.get().strip()
            uwagi = self.przyjecia_uwagi_text.get("1.0", "end-1c").strip()

            conn = get_connection()
            cursor = conn.cursor()

            # Pobierz id_dostawcy, jeśli tabela Dostawcy istnieje (ze zródła 1)
            try:
                cursor.execute("SELECT id_dostawcy FROM Dostawcy WHERE nazwa=?", (dostawca,))
                row = cursor.fetchone()
                id_dostawcy = row[0] if row else None
            except sqlite3.Error:
                id_dostawcy = None

            sql = (
                "INSERT INTO OperacjeMagazynowe "
                "(MaterialID, MagazynID, TypOperacji, Ilo, DataOperacji, Dostawca, ZlecPracownika, Uwagi, id_dostawcy) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
            )
            # W niektórych bazach id_dostawcy może nie występować, bezpieczniej jest użyć:
            try:
                cursor.execute(sql, (material_id, magazyn_id, "Przyjcie", ilosc, data, dostawca, None, uwagi, id_dostawcy))
            except sqlite3.OperationalError:
                sql_fallback = (
                    "INSERT INTO OperacjeMagazynowe "
                    "(MaterialID, MagazynID, TypOperacji, Ilo, DataOperacji, Dostawca, ZlecPracownika, Uwagi) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
                )
                cursor.execute(sql_fallback, (material_id, magazyn_id, "Przyjcie", ilosc, data, dostawca, None, uwagi))

            conn.commit()
            conn.close()

            messagebox.showinfo("OK", "Dodano przyjęcie.")
            self.clear_przyjecie_form()
            self.refresh_przyjecia()
            self.refresh_zapas()
        except ValueError as e:
            messagebox.showerror("Błąd danych", str(e))
        except sqlite3.Error as e:
            messagebox.showerror("Błąd bazy", str(e))
        except Exception as e:
            messagebox.showerror("Błąd", str(e))

    def clear_przyjecie_form(self):
        self.przyjecia_material_combo.set("")
        self.przyjecia_ilosc_entry.delete(0, tk.END)
        self.przyjecia_data_entry.delete(0, tk.END)
        self.przyjecia_data_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.przyjecia_magazyn_combo.set("")
        self.przyjecia_dostawca_entry.delete(0, tk.END)
        self.przyjecia_uwagi_text.delete("1.0", tk.END)

    def refresh_przyjecia(self):
        for item in self.przyjecia_tree.get_children():
            self.przyjecia_tree.delete(item)
        conn = get_connection()
        cursor = conn.cursor()
        sql = (
            "SELECT o.OperacjaID, m.Nazwa, o.Ilo, o.DataOperacji, mag.Kod, o.Dostawca, o.Uwagi "
            "FROM OperacjeMagazynowe o "
            "JOIN Materialy m ON o.MaterialID = m.MaterialID "
            "JOIN Magazyny mag ON o.MagazynID = mag.MagazynID "
            "WHERE o.TypOperacji = ? "
            "ORDER BY o.DataOperacji DESC, o.OperacjaID DESC"
        )
        cursor.execute(sql, ("Przyjcie",))
        for row in cursor.fetchall():
            self.przyjecia_tree.insert("", "end", values=row)
        conn.close()

    def get_available_stock(self, material_id, magazyn_id):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN TypOperacji='Przyjcie' THEN Ilo ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN TypOperacji='Wydanie' THEN Ilo ELSE 0 END), 0)
            FROM OperacjeMagazynowe
            WHERE MaterialID = ? AND MagazynID = ?
        """, (material_id, magazyn_id))
        row = cur.fetchone()
        conn.close()
        return int(row[0] or 0)

    def add_wydanie(self):
        try:
            material_name = self.wydania_material_combo.get()
            magazyn_name = self.wydania_magazyn_combo.get()

            if not material_name:
                messagebox.showerror("Błąd", "Wybierz materiał.")
                return
            if not magazyn_name:
                messagebox.showerror("Błąd", "Wybierz magazyn.")
                return

            ilosc = int(self.wydania_ilosc_entry.get())
            if ilosc <= 0:
                raise ValueError("Ilość musi być większa od zera.")

            data = self.wydania_data_entry.get().strip()
            datetime.strptime(data, "%Y-%m-%d")

            material_id = self.materialy_dict[material_name]
            magazyn_id = self.magazyny_dict[magazyn_name]
            zlecenie = self.wydania_zlecenie_entry.get().strip()
            uwagi = self.wydania_uwagi_text.get("1.0", "end-1c").strip()

            dostepny_stan = self.get_available_stock(material_id, magazyn_id)

            if dostepny_stan < ilosc:
                messagebox.showerror(
                    "Brak towaru",
                    f"Niewystarczający stan magazynowy!\nDostępne: {dostepny_stan} szt."
                )
                return

            conn = get_connection()
            cursor = conn.cursor()
            sql = (
                "INSERT INTO OperacjeMagazynowe "
                "(MaterialID, MagazynID, TypOperacji, Ilo, DataOperacji, Dostawca, ZlecPracownika, Uwagi) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            )
            cursor.execute(sql, (material_id, magazyn_id, "Wydanie", ilosc, data, None, zlecenie, uwagi))
            conn.commit()
            conn.close()

            messagebox.showinfo("OK", "Dodano wydanie.")
            self._clear_wydanie_form()
            self.refresh_wydania()
            self.refresh_zapas()
        except ValueError as e:
            messagebox.showerror("Błąd danych", str(e))
        except sqlite3.Error as e:
            messagebox.showerror("Błąd bazy", str(e))
        except Exception as e:
            messagebox.showerror("Błąd", str(e))

    def _clear_wydanie_form(self):
        self.wydania_material_combo.set("")
        self.wydania_ilosc_entry.delete(0, tk.END)
        self.wydania_data_entry.delete(0, tk.END)
        self.wydania_data_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.wydania_magazyn_combo.set("")
        self.wydania_zlecenie_entry.delete(0, tk.END)
        self.wydania_uwagi_text.delete("1.0", tk.END)

    def refresh_wydania(self):
        for item in self.wydania_tree.get_children():
            self.wydania_tree.delete(item)
        conn = get_connection()
        cursor = conn.cursor()
        sql = (
            "SELECT o.OperacjaID, m.Nazwa, o.Ilo, o.DataOperacji, mag.Kod, o.ZlecPracownika, o.Uwagi "
            "FROM OperacjeMagazynowe o "
            "JOIN Materialy m ON o.MaterialID = m.MaterialID "
            "JOIN Magazyny mag ON o.MagazynID = mag.MagazynID "
            "WHERE o.TypOperacji = ? "
            "ORDER BY o.DataOperacji DESC, o.OperacjaID DESC"
        )
        cursor.execute(sql, ("Wydanie",))
        for row in cursor.fetchall():
            self.wydania_tree.insert("", "end", values=row)
        conn.close()

    # ── KARTOTEKA I INWENTARYZACJA (ze źródła 1) ─────────────────
    def add_material(self):
        try:
            nazwa = self.kart_mat_nazwa.get().strip()
            indeks = int(self.kart_mat_indeks.get())
            kategoria = self.kart_mat_kategoria.get().strip()
            cena = float(self.kart_mat_cena.get())
            jednostka = self.kart_mat_jednostka.get().strip() or "szt"

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Materialy (Nazwa, Indeks, Kategoria, Cenajedn, Jednostka) VALUES (?,?,?,?,?)",
                           (nazwa, indeks, kategoria, cena, jednostka))
            conn.commit()
            conn.close()
            self.refresh_kartoteka()
            self.load_combobox_data()
        except Exception as e:
            messagebox.showerror("Błąd", str(e))

    def delete_material(self):
        sel = self.kart_mat_tree.selection()
        if not sel: return
        mat_id = self.kart_mat_tree.item(sel[0])["values"][0]
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Materialy WHERE MaterialID=?", (mat_id,))
            conn.commit()
            conn.close()
            self.refresh_kartoteka()
            self.load_combobox_data()
        except Exception as e:
            messagebox.showerror("Błąd", str(e))

    def add_magazyn(self):
        try:
            kod = self.kart_mag_kod.get().strip()
            opis = self.kart_mag_opis.get().strip()
            lok = self.kart_mag_lok.get().strip()
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Magazyny (Kod, Opis, Lokalizacja) VALUES (?,?,?)", (kod, opis, lok))
            conn.commit()
            conn.close()
            self.refresh_kartoteka()
            self.load_combobox_data()
        except Exception as e:
            messagebox.showerror("Błąd", str(e))

    def delete_magazyn(self):
        sel = self.kart_mag_tree.selection()
        if not sel: return
        mag_id = self.kart_mag_tree.item(sel[0])["values"][0]
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Magazyny WHERE MagazynID=?", (mag_id,))
            conn.commit()
            conn.close()
            self.refresh_kartoteka()
            self.load_combobox_data()
        except Exception as e:
            messagebox.showerror("Błąd", str(e))

    def refresh_kartoteka(self):
        for item in self.kart_mat_tree.get_children(): self.kart_mat_tree.delete(item)
        for item in self.kart_mag_tree.get_children(): self.kart_mag_tree.delete(item)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT MaterialID, Nazwa, Indeks, Kategoria, Cenajedn, Jednostka FROM Materialy ORDER BY Nazwa")
        for row in cursor.fetchall(): self.kart_mat_tree.insert("", "end", values=row)
        cursor.execute("SELECT MagazynID, Kod, Opis, Lokalizacja FROM Magazyny ORDER BY Kod")
        for row in cursor.fetchall(): self.kart_mag_tree.insert("", "end", values=row)
        conn.close()

    def _load_inwentaryzacja_combos(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT MaterialID, Nazwa FROM Materialy ORDER BY Nazwa")
            self.inw_materialy_dict = {row[1]: row[0] for row in cursor.fetchall()}
            self.inw_material_combo["values"] = list(self.inw_materialy_dict.keys())

            cursor.execute("""
                SELECT l.id_lokalizacji, mag.Kod, l.strefa, l.regal, l.polka 
                FROM LokalizacjeMagazynowe l JOIN Magazyny mag ON l.MagazynID = mag.MagazynID
            """)
            self.inw_lok_dict = {f"{row[1]}/{row[2]}-{row[3]}-{row[4]} (ID:{row[0]})": row[0] for row in cursor.fetchall()}
            self.inw_lok_combo["values"] = list(self.inw_lok_dict.keys())

            cursor.execute("SELECT id_pracownika, imie, nazwisko FROM Pracownicy WHERE aktywny=1")
            self.inw_prac_dict = {f"{row[1]} {row[2]}": row[0] for row in cursor.fetchall()}
            self.inw_pracownik_combo["values"] = list(self.inw_prac_dict.keys())
            conn.close()
        except sqlite3.OperationalError:
            pass # Tabela mogła nie zostać jeszcze wgrana

    def add_inwentaryzacja(self):
        try:
            mat_id = self.inw_materialy_dict[self.inw_material_combo.get()]
            lok_id = self.inw_lok_dict[self.inw_lok_combo.get()]
            prac_id = self.inw_prac_dict[self.inw_pracownik_combo.get()]
            data = self.inw_data_entry.get().strip()
            ilosc_rzecz = int(self.inw_ilosc_entry.get())
            status = self.inw_status_combo.get()
            uwagi = self.inw_uwagi_text.get("1.0", "end-1c").strip()
            ilosc_sys = self.get_available_stock(mat_id, lok_id) # W uproszczeniu pobieramy stan

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Inwentaryzacja (id_produktu, id_lokalizacji, id_pracownika, data_inwentaryzacji, ilosc_systemowa, ilosc_rzeczywista, status, uwagi)
                VALUES (?,?,?,?,?,?,?,?)
            """, (mat_id, lok_id, prac_id, data, ilosc_sys, ilosc_rzecz, status, uwagi))
            conn.commit()
            conn.close()
            self.refresh_inwentaryzacja()
        except Exception as e:
            messagebox.showerror("Błąd", str(e))

    def refresh_inwentaryzacja(self):
        for item in self.inw_tree.get_children(): self.inw_tree.delete(item)
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT i.id_inwentaryzacji, m.Nazwa, mag.Kod || '/' || l.strefa, p.imie || ' ' || p.nazwisko,
                       i.data_inwentaryzacji, i.ilosc_systemowa, i.ilosc_rzeczywista, 
                       (i.ilosc_rzeczywista - i.ilosc_systemowa), i.status, i.uwagi
                FROM Inwentaryzacja i
                JOIN Materialy m ON i.id_produktu = m.MaterialID
                JOIN LokalizacjeMagazynowe l ON i.id_lokalizacji = l.id_lokalizacji
                JOIN Magazyny mag ON l.MagazynID = mag.MagazynID
                JOIN Pracownicy p ON i.id_pracownika = p.id_pracownika
                ORDER BY i.data_inwentaryzacji DESC
            """)
            for row in cursor.fetchall():
                tag = "niedobor" if row[7] < 0 else ("nadwyzka" if row[7] > 0 else "")
                self.inw_tree.insert("", "end", values=row, tags=(tag,))
            self.inw_tree.tag_configure("niedobor", background="#ffe0e0")
            self.inw_tree.tag_configure("nadwyzka", background="#e0ffe0")
            conn.close()
        except sqlite3.OperationalError:
            pass

    def _load_zapas_filter(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Kod FROM Magazyny ORDER BY Kod")
        kody = ["(wszystkie)"] + [row[0] for row in cursor.fetchall()]
        conn.close()
        self.zapas_mag_filter["values"] = kody
        self.zapas_mag_filter.set("(wszystkie)")

    def refresh_zapas(self):
        for item in self.zapas_tree.get_children():
            self.zapas_tree.delete(item)

        filter_val = self.zapas_mag_filter.get() if hasattr(self, "zapas_mag_filter") else "(wszystkie)"
        mag_where = "AND mag.Kod = ?" if filter_val and filter_val != "(wszystkie)" else ""
        params = [filter_val] if mag_where else []

        conn = get_connection()
        cursor = conn.cursor()
        sql = f"""
            SELECT m.Nazwa, mag.Kod,
                (COALESCE(SUM(CASE WHEN o.TypOperacji='Przyjcie' THEN o.Ilo ELSE 0 END), 0) -
                 COALESCE(SUM(CASE WHEN o.TypOperacji='Wydanie'  THEN o.Ilo ELSE 0 END), 0)) AS akt_ilosc,
                m.Jednostka, m.Cenajedn,
                ROUND((COALESCE(SUM(CASE WHEN o.TypOperacji='Przyjcie' THEN o.Ilo ELSE 0 END), 0) -
                       COALESCE(SUM(CASE WHEN o.TypOperacji='Wydanie'  THEN o.Ilo ELSE 0 END), 0)) * m.Cenajedn, 2) AS wartosc,
                '—' AS lokalizacja
            FROM OperacjeMagazynowe o
            JOIN Materialy m ON o.MaterialID = m.MaterialID
            JOIN Magazyny mag ON o.MagazynID = mag.MagazynID
            WHERE 1=1 {mag_where}
            GROUP BY m.MaterialID, mag.MagazynID
            ORDER BY m.Nazwa, mag.Kod
        """
        cursor.execute(sql, params)
        total_wartosc = 0.0
        for row in cursor.fetchall():
            akt_ilosc = max(0, row[2])
            wartosc = max(0.0, row[5] or 0.0)
            total_wartosc += wartosc
            tag = "zero" if akt_ilosc == 0 else ""
            self.zapas_tree.insert("", "end", values=(row[0], row[1], akt_ilosc, row[3], f"{row[4]:.2f}", f"{wartosc:.2f}", row[6]), tags=(tag,))
        self.zapas_tree.tag_configure("zero", background="#fff3cd")
        self.zapas_summary_label.config(text=f"Łączna wartość zapasów: {total_wartosc:,.2f} PLN")
        conn.close()

    def export_zapas(self):
        try:
            path = APP_DIR / f"stan_zapasu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            lines = [f"STAN ZAPASÓW — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "=" * 80]
            for child in self.zapas_tree.get_children():
                v = self.zapas_tree.item(child)["values"]
                lines.append(f"{str(v[0]):<30} {str(v[1]):^5} {str(v[2]):>8} {str(v[3]):^6} {str(v[4]):>10} {str(v[5]):>12}")
            lines.append(self.zapas_summary_label.cget("text"))
            path.write_text("\n".join(lines), encoding="utf-8")
            messagebox.showinfo("Eksport", f"Zapisano do:\n{path}")
        except Exception as e:
            messagebox.showerror("Błąd eksportu", str(e))

    # ── LOGIKA RAPORTÓW (ZADANIE 1 - Rozwiązane zapytania SQL) ──

    def clear_report_table(self):
        for item in self.raporty_tree.get_children():
            self.raporty_tree.delete(item)

    def raport_stan_zapasu(self):
        self.clear_report_table()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
         SELECT m.Nazwa, mag.Kod,
                   SUM(CASE WHEN o.TypOperacji='Przyjcie' THEN o.Ilo ELSE -o.Ilo END) AS IloscAktualna,
                   SUM(CASE WHEN o.TypOperacji='Przyjcie' THEN o.Ilo * m.Cenajedn ELSE -o.Ilo * m.Cenajedn END) AS WartoscAktualna,
                   m.Cenajedn
            FROM OperacjeMagazynowe o
            JOIN Materialy m ON o.MaterialID = m.MaterialID
            JOIN Magazyny mag ON o.MagazynID = mag.MagazynID
            GROUP BY m.MaterialID, mag.MagazynID, m.Nazwa, mag.Kod, m.Cenajedn
            HAVING SUM(CASE WHEN o.TypOperacji='Przyjcie' THEN o.Ilo ELSE -o.Ilo END) > 0
            ORDER BY mag.Kod, m.Nazwa
        """)
        total = 0.0
        for lp, row in enumerate(cur.fetchall(), 1):
            nazwa, magazyn, ilosc, wartosc, cena = row
            wartosc = float(wartosc or 0)
            total += wartosc
            self.raporty_tree.insert("", "end", values=(lp, nazwa, magazyn, f"{ilosc} szt.", f"{wartosc:.2f} PLN", f"Cena jedn. {cena:.2f} PLN"))
        self.raporty_tree.insert("", "end", values=("", "RAZEM", "", "", f"{total:.2f} PLN", ""))
        conn.close()

    def raport_miesieczny(self):
        self.clear_report_table()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                strftime('%Y-%m', o.DataOperacji) AS Miesiac,
                m.Nazwa, 
                mag.Kod,
                SUM(CASE WHEN o.TypOperacji='Przyjcie' THEN o.Ilo ELSE 0 END) AS Przyjecia,
                SUM(CASE WHEN o.TypOperacji='Wydanie' THEN o.Ilo ELSE 0 END) AS Wydania,
                SUM(CASE WHEN o.TypOperacji='Przyjcie' THEN o.Ilo ELSE -o.Ilo END) AS Saldo
            FROM OperacjeMagazynowe o
            JOIN Materialy m ON o.MaterialID = m.MaterialID
            JOIN Magazyny mag ON o.MagazynID = mag.MagazynID
            WHERE o.DataOperacji IS NOT NULL
            GROUP BY Miesiac, m.Nazwa, mag.Kod
            ORDER BY Miesiac DESC, mag.Kod, m.Nazwa
        """)
        for lp, row in enumerate(cur.fetchall(), 1):
            miesiac, nazwa, magazyn, przyjecia, wydania, saldo = row
            self.raporty_tree.insert("", "end", values=(lp, nazwa, magazyn, f"P:{przyjecia} / W:{wydania}", f"Saldo: {saldo}", miesiac))
        conn.close()

    def raport_ruchy(self):
        self.clear_report_table()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                o.DataOperacji,
                m.Nazwa,
                mag.Kod,
                o.TypOperacji,
                o.Ilo,
                m.Cenajedn,
                (o.Ilo * m.Cenajedn) AS Wartosc,
                COALESCE(o.Dostawca, o.ZlecPracownika, '-') AS Szczegoly
            FROM OperacjeMagazynowe o
            JOIN Materialy m ON o.MaterialID = m.MaterialID
            JOIN Magazyny mag ON o.MagazynID = mag.MagazynID
            ORDER BY o.DataOperacji DESC, o.OperacjaID DESC
        """)
        for lp, row in enumerate(cur.fetchall(), 1):
            data, nazwa, magazyn, typ, ilosc, cena, wartosc, szczegoly = row
            self.raporty_tree.insert("", "end", values=(lp, nazwa, magazyn, f"{typ}: {ilosc} szt.", f"{float(wartosc or 0):.2f} PLN", f"{data}; {szczegoly}"))
        conn.close()

    def raport_ranking(self):
        self.clear_report_table()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                m.Nazwa,
                COUNT(o.OperacjaID) AS LiczbaOperacji,
                SUM(o.Ilo) AS LacznaIlosc,
                SUM(o.Ilo * m.Cenajedn) AS LacznaWartosc
            FROM OperacjeMagazynowe o
            JOIN Materialy m ON o.MaterialID = m.MaterialID
            WHERE o.TypOperacji = 'Wydanie'
            GROUP BY m.MaterialID, m.Nazwa
            ORDER BY LacznaIlosc DESC, m.Nazwa
        """)
        for lp, row in enumerate(cur.fetchall(), 1):
            nazwa, liczba_op, laczna_ilosc, laczna_wartosc = row
            self.raporty_tree.insert("", "end", values=(lp, nazwa, "-", f"{laczna_ilosc} szt.", f"{float(laczna_wartosc or 0):.2f} PLN", f"Liczba operacji: {liczba_op}"))
        conn.close()

    def export_csv(self):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
            SELECT 
                m.Nazwa,
                mag.Kod,
                SUM(CASE WHEN o.TypOperacji='Przyjcie' THEN o.Ilo ELSE -o.Ilo END) AS Ilosc,
                SUM(CASE WHEN o.TypOperacji='Przyjcie' THEN o.Ilo * m.Cenajedn ELSE -o.Ilo * m.Cenajedn END) AS WartoscPLN
            FROM OperacjeMagazynowe o
            JOIN Materialy m ON o.MaterialID = m.MaterialID
            JOIN Magazyny mag ON o.MagazynID = mag.MagazynID
            GROUP BY m.MaterialID, m.Nazwa, mag.MagazynID, mag.Kod
            ORDER BY mag.Kod, m.Nazwa
            """)
            filename = APP_DIR / f"raport_zapasu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Materiał", "Magazyn", "Ilość", "Wartość PLN"])
                writer.writerows(cur.fetchall())
            conn.close()
            messagebox.showinfo("Sukces", f"Raport wyeksportowany do:\n{filename}")
        except Exception as e:
            messagebox.showerror("Błąd", str(e))

    # ── LOGIKA WYKRESÓW ──────────────────────────────────────────

    def configure_bar_chart(self):
        self.chart_mode = "bar"
        self.chart_message.config(text="Wybrano tryb słupkowy. Kliknij 'Rysuj wykres'.")

    def configure_line_chart(self):
        self.chart_mode = "line"
        self.chart_message.config(text="Wybrano tryb liniowy. Kliknij 'Rysuj wykres'.")

    def clear_chart(self):
        if self.current_chart_canvas is not None:
            try:
                self.current_chart_canvas.get_tk_widget().pack_forget()
                self.current_chart_canvas.get_tk_widget().destroy()
            except Exception:
                pass
            self.current_chart_canvas = None
        if self.current_figure is not None:
            try:
                self.current_figure.clear()
            except Exception:
                pass
            self.current_figure = None
        for child in self.chart_canvas_holder.winfo_children():
            child.destroy()
        self.chart_message.config(text="Wykres wyczyszczony.")
        self.root.update_idletasks()

    def draw_embedded_chart(self):
        if not MATPLOTLIB_OK:
            messagebox.showerror("Brak biblioteki", "Matplotlib nie jest dostępny. Zainstaluj pakiet matplotlib.")
            return

        metric_label = self.chart_metric_combo.get()
        group_label = self.chart_group_combo.get()
        type_label = self.chart_type_combo.get()
        try:
            limit = max(1, int(self.chart_limit_entry.get().strip()))
        except Exception:
            limit = 10

        metric_map = {"Ilość": "Ilo", "Wartość": "wartosc", "Liczba operacji": "liczba"}
        metric = metric_map.get(metric_label, "Ilo")

        if group_label == "Miesiąc":
            xexpr = "strftime('%Y-%m', o.DataOperacji)"
            xlabel = "Miesiąc"
            order_expr = "x ASC"
        elif group_label == "Magazyn":
            xexpr = "mag.Kod"
            xlabel = "Magazyn"
            order_expr = "y DESC, x ASC"
        else:
            xexpr = "m.Nazwa"
            xlabel = "Materiał"
            order_expr = "y DESC, x ASC"

        if metric == "Ilo":
            agg = "SUM(o.Ilo)"
            ylabel = "Ilość"
        elif metric == "wartosc":
            agg = "SUM(o.Ilo * m.Cenajedn)"
            ylabel = "Wartość"
        else:
            agg = "COUNT(o.OperacjaID)"
            ylabel = "Liczba operacji"

        where_clause = ""
        params = []
        if type_label in ("Przyjcie", "Wydanie"):
            where_clause = "WHERE o.TypOperacji = ?"
            params.append(type_label)

        query = f"""
            SELECT {xexpr} AS x, {agg} AS y
            FROM OperacjeMagazynowe o
            JOIN Materialy m ON m.MaterialID = o.MaterialID
            JOIN Magazyny mag ON mag.MagazynID = o.MagazynID
            {where_clause}
            GROUP BY x
            ORDER BY {order_expr}
            LIMIT ?
        """
        params.append(limit)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()

        if not rows:
            messagebox.showwarning("Brak danych", "Brak danych do wygenerowania wykresu.")
            return

        self.clear_chart()

        x_values = [r[0] for r in rows]
        y_values = [float(r[1] or 0) for r in rows]

        fig = Figure(figsize=(8.8, 3.6), dpi=100)
        ax = fig.add_subplot(111)

        if self.chart_mode == "bar":
            ax.bar(x_values, y_values, color="#2a6fdb")
            ax.set_title(f"Wykres słupkowy: {metric_label} wg {group_label}")
        else:
            ax.plot(x_values, y_values, marker="o", linewidth=2.0, color="#0f766e")
            ax.set_title(f"Wykres liniowy: {metric_label} wg {group_label}")

        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", alpha=0.25)
        for label in ax.get_xticklabels():
            label.set_rotation(35)
            label.set_horizontalalignment("right")

        fig.tight_layout()
        self.current_figure = fig
        self.current_chart_canvas = FigureCanvasTkAgg(fig, master=self.chart_canvas_holder)
        self.current_chart_canvas.draw_idle()
        widget = self.current_chart_canvas.get_tk_widget()
        widget.pack(fill="both", expand=True)
        widget.update_idletasks()
        self.chart_message.config(text=f"Wyświetlono wykres {self.chart_mode} dla: {metric_label} / {group_label}.")
        self.root.update_idletasks()

def main():
    root = tk.Tk()
    app = MagazynApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()