import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from pathlib import Path
import sqlite3
import sys

APP_DIR = Path(__file__).resolve().parent
DBFILE = APP_DIR / "gmsystem.db"
SQLFILE = APP_DIR / "gm_schema_and_data_extended.sql"


def get_connection():
    conn = sqlite3.connect(DBFILE, timeout =20)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def database_has_required_tables():
    if not DBFILE.exists():
        return False
    try:
        conn = sqlite3.connect(DBFILE)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Materialy'")
        ok = cur.fetchone() is not None
        conn.close()
        return ok
    except sqlite3.Error:
        return False


class MagazynApp:
    def __init__(self, root):
        self.root = root
        self.root.title("System GM - Gospodarka Magazynowa")
        self.root.geometry("1100x750")

        self.materialy_dict = {}
        self.magazyny_dict = {}

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.create_przyjecia_tab()
        self.create_wydania_tab()
        self.create_kartoteka_tab()
        self.create_inwentaryzacja_tab()
        self.create_zapas_tab()

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

        # Załaduj comboboxy — zakładka już istnieje, więc materialy_dict jest gotowy
        self.wydania_material_combo["values"] = list(self.materialy_dict.keys())
        self.wydania_magazyn_combo["values"] = list(self.magazyny_dict.keys())
        self.refresh_wydania()

    # ─────────────────────────────────────────────────────────────
    #  ZAKŁADKA: KARTOTEKA
    # ─────────────────────────────────────────────────────────────
    def create_kartoteka_tab(self):
        self.kartoteka_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.kartoteka_frame, text="Kartoteka")

        # ── Lewa strona: materiały ──────────────────────────────
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
        self.kart_mat_tree = ttk.Treeview(mat_table, columns=cols_m, show="headings",
                                          yscrollcommand=sb_mat.set, height=8)
        sb_mat.config(command=self.kart_mat_tree.yview)
        widths_m = (40, 200, 60, 100, 70, 60)
        for col, w in zip(cols_m, widths_m):
            self.kart_mat_tree.heading(col, text=col)
            self.kart_mat_tree.column(col, width=w)
        self.kart_mat_tree.pack(fill="both", expand=True)

        # ── Prawa strona: magazyny ──────────────────────────────
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
        self.kart_mag_tree = ttk.Treeview(mag_table, columns=cols_mg, show="headings",
                                          yscrollcommand=sb_mag.set, height=8)
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
        self.inw_status_combo = ttk.Combobox(form_frame, state="readonly", width=20,
                                              values=["Zatwierdzona", "Robocza", "Wyjasnienie"])
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

        cols = ("ID", "Materiał", "Lokalizacja", "Pracownik", "Data",
                "Stan system.", "Stan rzecz.", "Różnica", "Status", "Uwagi")
        self.inw_tree = ttk.Treeview(table_frame, columns=cols, show="headings",
                                     yscrollcommand=sb.set)
        sb.config(command=self.inw_tree.yview)
        widths_i = (40, 160, 120, 120, 90, 80, 80, 60, 90, 140)
        for col, w in zip(cols, widths_i):
            self.inw_tree.heading(col, text=col)
            self.inw_tree.column(col, width=w)
        self.inw_tree.pack(fill="both", expand=True)

        self._load_inwentaryzacja_combos()
        self.refresh_inwentaryzacja()

    # ─────────────────────────────────────────────────────────────
    #  ZAKŁADKA: AKTUALNY STAN ZAPASU
    # ─────────────────────────────────────────────────────────────
    def create_zapas_tab(self):
        self.zapas_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.zapas_frame, text="Aktualny stan zapasu")

        # Filtr
        filter_frame = ttk.LabelFrame(self.zapas_frame, text="Filtrowanie", padding=8)
        filter_frame.pack(fill="x", padx=10, pady=8)

        ttk.Label(filter_frame, text="Magazyn (wszystkie jeśli puste):").pack(side="left", padx=5)
        self.zapas_mag_filter = ttk.Combobox(filter_frame, state="readonly", width=25)
        self.zapas_mag_filter.pack(side="left", padx=5)

        ttk.Button(filter_frame, text="Odśwież stan", command=self.refresh_zapas).pack(side="left", padx=10)
        ttk.Button(filter_frame, text="Eksportuj do pliku tekstowego", command=self.export_zapas).pack(side="left", padx=5)

        # Tabela
        table_frame = ttk.LabelFrame(self.zapas_frame, text="Bieżący stan zapasów (suma przyjęć − suma wydań)", padding=10)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        sb = ttk.Scrollbar(table_frame)
        sb.pack(side="right", fill="y")

        cols = ("Materiał", "Magazyn", "Akt. ilość", "Jednostka",
                "Cena jedn.", "Wartość zapasu", "Lokalizacja")
        self.zapas_tree = ttk.Treeview(table_frame, columns=cols, show="headings",
                                       yscrollcommand=sb.set)
        sb.config(command=self.zapas_tree.yview)
        widths_z = (200, 80, 80, 70, 90, 110, 160)
        for col, w in zip(cols, widths_z):
            self.zapas_tree.heading(col, text=col)
            self.zapas_tree.column(col, width=w)
        self.zapas_tree.pack(fill="both", expand=True)

        # Etykieta podsumowania
        self.zapas_summary_label = ttk.Label(self.zapas_frame, text="", font=("", 10, "bold"))
        self.zapas_summary_label.pack(anchor="e", padx=15, pady=4)

        self._load_zapas_filter()
        self.refresh_zapas()

    # ═════════════════════════════════════════════════════════════
    #  LOGIKA DANYCH
    # ═════════════════════════════════════════════════════════════

    def load_combobox_data(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT MaterialID, Nazwa FROM Materialy ORDER BY Nazwa")
        materialy = cursor.fetchall()
        self.materialy_dict = {row[1]: row[0] for row in materialy}
        self.przyjecia_material_combo["values"] = list(self.materialy_dict.keys())
        if hasattr(self, "wydania_material_combo"):
            self.wydania_material_combo["values"] = list(self.materialy_dict.keys())

        cursor.execute("SELECT MagazynID, Kod, Opis FROM Magazyny ORDER BY Kod")
        magazyny = cursor.fetchall()
        self.magazyny_dict = {f"{row[1]} - {row[2]}": row[0] for row in magazyny}
        self.przyjecia_magazyn_combo["values"] = list(self.magazyny_dict.keys())
        if hasattr(self, "wydania_magazyn_combo"):
            self.wydania_magazyn_combo["values"] = list(self.magazyny_dict.keys())

        conn.close()

        if hasattr(self, "inw_material_combo"):
            self._load_inwentaryzacja_combos()
        if hasattr(self, "zapas_mag_filter"):
            self._load_zapas_filter()

    # ── Przyjęcia ──────────────────────────────────────────────

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

            # Pobierz id_dostawcy (wymagane przez CHECK w DB)
            try:
                cursor.execute("SELECT id_dostawcy FROM Dostawcy WHERE nazwa=?", (dostawca,))
                row = cursor.fetchone()
                id_dostawcy = row[0] if row else None
                sql = (
                    "INSERT INTO OperacjeMagazynowe "
                    "(MaterialID, MagazynID, TypOperacji, Ilo, DataOperacji, Dostawca, ZlecPracownika, Uwagi, id_dostawcy) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
                )
                cursor.execute(sql, (material_id, magazyn_id, "Przyjcie", ilosc, data, dostawca, None, uwagi, id_dostawcy))
                conn.commit()
                messagebox.showinfo("OK", "Dodano przyjęcie.")
                self.clear_przyjecie_form()
                self.refresh_przyjecia()
                self.refresh_zapas()
            except sqlite3.Error as e:
                messagebox.showerror("ok", "coś nie działa, elo \n" + str(e))
                conn.close()
            finally:
                conn.close()

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

    # ── Wydania ────────────────────────────────────────────────

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

            # Sprawdź dostępność materiału w danym magazynie
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT (COALESCE(SUM(CASE WHEN TypOperacji='Przyjcie' THEN Ilo ELSE 0 END), 0) -
                        COALESCE(SUM(CASE WHEN TypOperacji='Wydanie'  THEN Ilo ELSE 0 END), 0)) AS stan
                FROM OperacjeMagazynowe
                WHERE MaterialID=? AND MagazynID=?
            """, (material_id, magazyn_id))
            dostepny_stan = cursor.fetchone()[0] or 0

            if dostepny_stan < ilosc:
                messagebox.showerror(
                    "Brak towaru",
                    f"Niewystarczający stan magazynowy!\nDostępne: {dostepny_stan} szt."
                )
                conn.close()
                return

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

    # ── Kartoteka ──────────────────────────────────────────────

    def add_material(self):
        try:
            nazwa = self.kart_mat_nazwa.get().strip()
            if not nazwa:
                raise ValueError("Podaj nazwę materiału.")
            indeks = int(self.kart_mat_indeks.get())
            kategoria = self.kart_mat_kategoria.get().strip()
            cena = float(self.kart_mat_cena.get())
            if cena < 0:
                raise ValueError("Cena nie może być ujemna.")
            jednostka = self.kart_mat_jednostka.get().strip() or "szt"

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Materialy (Nazwa, Indeks, Kategoria, Cenajedn, Jednostka) VALUES (?,?,?,?,?)",
                (nazwa, indeks, kategoria, cena, jednostka)
            )
            conn.commit()
            conn.close()

            messagebox.showinfo("OK", f"Materiał '{nazwa}' dodany.")
            self.kart_mat_nazwa.delete(0, tk.END)
            self.kart_mat_indeks.delete(0, tk.END)
            self.kart_mat_kategoria.delete(0, tk.END)
            self.kart_mat_cena.delete(0, tk.END)
            self.kart_mat_jednostka.delete(0, tk.END)
            self.kart_mat_jednostka.insert(0, "szt")
            self.refresh_kartoteka()
            self.load_combobox_data()
        except ValueError as e:
            messagebox.showerror("Błąd danych", str(e))
        except sqlite3.IntegrityError:
            messagebox.showerror("Błąd", "Materiał o tym indeksie już istnieje.")
        except sqlite3.Error as e:
            messagebox.showerror("Błąd bazy", str(e))

    def delete_material(self):
        sel = self.kart_mat_tree.selection()
        if not sel:
            messagebox.showwarning("Brak wyboru", "Zaznacz materiał do usunięcia.")
            return
        mat_id = self.kart_mat_tree.item(sel[0])["values"][0]
        mat_name = self.kart_mat_tree.item(sel[0])["values"][1]
        if not messagebox.askyesno("Potwierdzenie", f"Usunąć materiał '{mat_name}'?"):
            return
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Materialy WHERE MaterialID=?", (mat_id,))
            conn.commit()
            conn.close()
            self.refresh_kartoteka()
            self.load_combobox_data()
        except sqlite3.Error as e:
            messagebox.showerror("Błąd bazy", f"Nie można usunąć: {e}")

    def add_magazyn(self):
        try:
            kod = self.kart_mag_kod.get().strip()
            if not kod:
                raise ValueError("Podaj kod magazynu.")
            opis = self.kart_mag_opis.get().strip()
            lok = self.kart_mag_lok.get().strip()

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Magazyny (Kod, Opis, Lokalizacja) VALUES (?,?,?)",
                (kod, opis, lok)
            )
            conn.commit()
            conn.close()

            messagebox.showinfo("OK", f"Magazyn '{kod}' dodany.")
            self.kart_mag_kod.delete(0, tk.END)
            self.kart_mag_opis.delete(0, tk.END)
            self.kart_mag_lok.delete(0, tk.END)
            self.refresh_kartoteka()
            self.load_combobox_data()
        except ValueError as e:
            messagebox.showerror("Błąd danych", str(e))
        except sqlite3.IntegrityError:
            messagebox.showerror("Błąd", "Magazyn o tym kodzie już istnieje.")
        except sqlite3.Error as e:
            messagebox.showerror("Błąd bazy", str(e))

    def delete_magazyn(self):
        sel = self.kart_mag_tree.selection()
        if not sel:
            messagebox.showwarning("Brak wyboru", "Zaznacz magazyn do usunięcia.")
            return
        mag_id = self.kart_mag_tree.item(sel[0])["values"][0]
        mag_kod = self.kart_mag_tree.item(sel[0])["values"][1]
        if not messagebox.askyesno("Potwierdzenie", f"Usunąć magazyn '{mag_kod}'?"):
            return
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Magazyny WHERE MagazynID=?", (mag_id,))
            conn.commit()
            conn.close()
            self.refresh_kartoteka()
            self.load_combobox_data()
        except sqlite3.Error as e:
            messagebox.showerror("Błąd bazy", f"Nie można usunąć: {e}")

    def refresh_kartoteka(self):
        for item in self.kart_mat_tree.get_children():
            self.kart_mat_tree.delete(item)
        for item in self.kart_mag_tree.get_children():
            self.kart_mag_tree.delete(item)

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT MaterialID, Nazwa, Indeks, Kategoria, Cenajedn, Jednostka FROM Materialy ORDER BY Nazwa")
        for row in cursor.fetchall():
            self.kart_mat_tree.insert("", "end", values=row)

        cursor.execute("SELECT MagazynID, Kod, Opis, Lokalizacja FROM Magazyny ORDER BY Kod")
        for row in cursor.fetchall():
            self.kart_mag_tree.insert("", "end", values=row)

        conn.close()

    # ── Inwentaryzacja ─────────────────────────────────────────

    def _load_inwentaryzacja_combos(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT MaterialID, Nazwa FROM Materialy ORDER BY Nazwa")
        rows = cursor.fetchall()
        self.inw_materialy_dict = {row[1]: row[0] for row in rows}
        self.inw_material_combo["values"] = list(self.inw_materialy_dict.keys())

        cursor.execute(
            "SELECT l.id_lokalizacji, mag.Kod, l.strefa, l.regal, l.polka "
            "FROM LokalizacjeMagazynowe l "
            "JOIN Magazyny mag ON l.MagazynID = mag.MagazynID "
            "ORDER BY mag.Kod, l.strefa, l.regal"
        )
        rows = cursor.fetchall()
        self.inw_lok_dict = {
            f"{row[1]}/{row[2]}-{row[3]}-{row[4]} (ID:{row[0]})": row[0]
            for row in rows
        }
        self.inw_lok_combo["values"] = list(self.inw_lok_dict.keys())

        cursor.execute("SELECT id_pracownika, imie, nazwisko FROM Pracownicy WHERE aktywny=1 ORDER BY nazwisko")
        rows = cursor.fetchall()
        self.inw_prac_dict = {f"{row[1]} {row[2]}": row[0] for row in rows}
        self.inw_pracownik_combo["values"] = list(self.inw_prac_dict.keys())

        conn.close()

    def _get_stan_systemowy(self, material_id):
        """Oblicza bieżący stan systemowy materiału (wszystkie magazyny)."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(CASE WHEN TypOperacji='Przyjcie' THEN Ilo ELSE 0 END), 0) -
                   COALESCE(SUM(CASE WHEN TypOperacji='Wydanie'  THEN Ilo ELSE 0 END), 0)
            FROM OperacjeMagazynowe WHERE MaterialID=?
        """, (material_id,))
        result = cursor.fetchone()[0]
        conn.close()
        return result or 0

    def add_inwentaryzacja(self):
        try:
            mat_name = self.inw_material_combo.get()
            lok_name = self.inw_lok_combo.get()
            prac_name = self.inw_pracownik_combo.get()

            if not mat_name:
                raise ValueError("Wybierz materiał.")
            if not lok_name:
                raise ValueError("Wybierz lokalizację.")
            if not prac_name:
                raise ValueError("Wybierz pracownika.")

            data = self.inw_data_entry.get().strip()
            datetime.strptime(data, "%Y-%m-%d")

            ilosc_rzecz = int(self.inw_ilosc_entry.get())
            if ilosc_rzecz < 0:
                raise ValueError("Ilość rzeczywista nie może być ujemna.")

            status = self.inw_status_combo.get()
            uwagi = self.inw_uwagi_text.get("1.0", "end-1c").strip()

            mat_id = self.inw_materialy_dict[mat_name]
            lok_id = self.inw_lok_dict[lok_name]
            prac_id = self.inw_prac_dict[prac_name]
            ilosc_sys = self._get_stan_systemowy(mat_id)

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Inwentaryzacja "
                "(id_produktu, id_lokalizacji, id_pracownika, data_inwentaryzacji, "
                "ilosc_systemowa, ilosc_rzeczywista, status, uwagi) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (mat_id, lok_id, prac_id, data, ilosc_sys, ilosc_rzecz, status, uwagi)
            )
            conn.commit()
            conn.close()

            messagebox.showinfo("OK", f"Zapisano inwentaryzację.\nStan systemu: {ilosc_sys}, Rzeczywisty: {ilosc_rzecz}, Różnica: {ilosc_rzecz - ilosc_sys}")
            self.inw_material_combo.set("")
            self.inw_lok_combo.set("")
            self.inw_pracownik_combo.set("")
            self.inw_ilosc_entry.delete(0, tk.END)
            self.inw_uwagi_text.delete("1.0", tk.END)
            self.inw_status_combo.set("Zatwierdzona")
            self.refresh_inwentaryzacja()
        except ValueError as e:
            messagebox.showerror("Błąd danych", str(e))
        except sqlite3.Error as e:
            messagebox.showerror("Błąd bazy", str(e))

    def refresh_inwentaryzacja(self):
        for item in self.inw_tree.get_children():
            self.inw_tree.delete(item)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.id_inwentaryzacji,
                   m.Nazwa,
                   mag.Kod || '/' || l.strefa || '-' || l.regal || '-' || l.polka,
                   p.imie || ' ' || p.nazwisko,
                   i.data_inwentaryzacji,
                   i.ilosc_systemowa,
                   i.ilosc_rzeczywista,
                   (i.ilosc_rzeczywista - i.ilosc_systemowa),
                   i.status,
                   i.uwagi
            FROM Inwentaryzacja i
            JOIN Materialy m ON i.id_produktu = m.MaterialID
            JOIN LokalizacjeMagazynowe l ON i.id_lokalizacji = l.id_lokalizacji
            JOIN Magazyny mag ON l.MagazynID = mag.MagazynID
            JOIN Pracownicy p ON i.id_pracownika = p.id_pracownika
            ORDER BY i.data_inwentaryzacji DESC, i.id_inwentaryzacji DESC
        """)
        for row in cursor.fetchall():
            # Kolorowanie wierszy z różnicą
            roznica = row[7]
            tag = ""
            if roznica < 0:
                tag = "niedobor"
            elif roznica > 0:
                tag = "nadwyzka"
            self.inw_tree.insert("", "end", values=row, tags=(tag,))

        self.inw_tree.tag_configure("niedobor", background="#ffe0e0")
        self.inw_tree.tag_configure("nadwyzka", background="#e0ffe0")
        conn.close()

    # ── Aktualny stan zapasu ───────────────────────────────────

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

        conn = get_connection()
        cursor = conn.cursor()

        mag_where = ""
        params = []
        if filter_val and filter_val != "(wszystkie)":
            mag_where = "AND mag.Kod = ?"
            params.append(filter_val)

        sql = f"""
            SELECT
                m.Nazwa,
                mag.Kod,
                (COALESCE(SUM(CASE WHEN o.TypOperacji='Przyjcie' THEN o.Ilo ELSE 0 END), 0) -
                 COALESCE(SUM(CASE WHEN o.TypOperacji='Wydanie'  THEN o.Ilo ELSE 0 END), 0)) AS akt_ilosc,
                m.Jednostka,
                m.Cenajedn,
                ROUND(
                    (COALESCE(SUM(CASE WHEN o.TypOperacji='Przyjcie' THEN o.Ilo ELSE 0 END), 0) -
                     COALESCE(SUM(CASE WHEN o.TypOperacji='Wydanie'  THEN o.Ilo ELSE 0 END), 0))
                    * m.Cenajedn, 2
                ) AS wartosc,
                COALESCE(
                    (SELECT mag2.Kod || '/' || lm.strefa || '-' || lm.regal || '-' || lm.polka
                     FROM ProduktyLokalizacje pl
                     JOIN LokalizacjeMagazynowe lm ON pl.id_lokalizacji = lm.id_lokalizacji
                     JOIN Magazyny mag2 ON lm.MagazynID = mag2.MagazynID
                     WHERE pl.id_produktu = m.MaterialID
                     LIMIT 1),
                    '—'
                ) AS lokalizacja
            FROM OperacjeMagazynowe o
            JOIN Materialy m ON o.MaterialID = m.MaterialID
            JOIN Magazyny mag ON o.MagazynID = mag.MagazynID
            WHERE 1=1 {mag_where}
            GROUP BY m.MaterialID, mag.MagazynID
            ORDER BY m.Nazwa, mag.Kod
        """
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        total_wartosc = 0.0
        for row in rows:
            akt_ilosc = max(0, row[2])          # nigdy ujemny
            wartosc = max(0.0, row[5] or 0.0)   # wartość też nie ujemna
            total_wartosc += wartosc
            # Kolorowanie zerowych stanów
            tag = "zero" if akt_ilosc == 0 else ""
            self.zapas_tree.insert("", "end", values=(
                row[0], row[1], akt_ilosc, row[3],
                f"{row[4]:.2f}", f"{wartosc:.2f}", row[6]
            ), tags=(tag,))

        self.zapas_tree.tag_configure("zero", background="#fff3cd")
        self.zapas_summary_label.config(
            text=f"Łączna wartość zapasów: {total_wartosc:,.2f} PLN"
        )

    def export_zapas(self):
        """Zapisuje aktualny stan do pliku tekstowego."""
        try:
            path = APP_DIR / f"stan_zapasu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            lines = [
                f"STAN ZAPASÓW — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "=" * 80,
                f"{'Materiał':<30} {'Mag':^5} {'Ilość':>8} {'Jedn':^6} {'Cena':>10} {'Wartość':>12} {'Lokalizacja'}",
                "-" * 80,
            ]
            for child in self.zapas_tree.get_children():
                v = self.zapas_tree.item(child)["values"]
                lines.append(f"{str(v[0]):<30} {str(v[1]):^5} {str(v[2]):>8} {str(v[3]):^6} {str(v[4]):>10} {str(v[5]):>12}  {v[6]}")
            lines.append("-" * 80)
            lines.append(self.zapas_summary_label.cget("text"))
            path.write_text("\n".join(lines), encoding="utf-8")
            messagebox.showinfo("Eksport", f"Zapisano do:\n{path}")
        except Exception as e:
            messagebox.showerror("Błąd eksportu", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    root.deiconify()
    app = MagazynApp(root)
    root.mainloop()