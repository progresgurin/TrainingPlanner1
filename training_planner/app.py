"""Modern Tkinter user interface for Training Planner."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from .model import Training, TrainingBook, ValidationError, validate_date, validate_duration, validate_training_type
from .storage import JsonStorage, StorageError

APP_NAME = "Training Planner"
AUTHOR = "Roberto Gatti"
DEFAULT_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "trainings.json"


class TrainingPlannerApp:
    """Desktop application for planning and filtering workouts."""

    def __init__(self, root: tk.Tk, data_path: str | Path = DEFAULT_DATA_PATH) -> None:
        self.root = root
        self.storage = JsonStorage(data_path)
        self.book = TrainingBook()
        self.current_rows: list[Training] = []
        self.selected_id: str | None = None

        self.date_var = tk.StringVar()
        self.type_var = tk.StringVar()
        self.duration_var = tk.StringVar()
        self.filter_date_var = tk.StringVar()
        self.filter_type_var = tk.StringVar()
        self.total_var = tk.StringVar(value="0")
        self.filtered_var = tk.StringVar(value="0")
        self.minutes_var = tk.StringVar(value="0")
        self.status_var = tk.StringVar(value="Готово")

        self._configure_root()
        self._configure_style()
        self._create_menu()
        self._create_layout()
        self.reload_from_disk(show_success=False)

    def _configure_root(self) -> None:
        self.root.title(APP_NAME)
        self.root.geometry("1080x720")
        self.root.minsize(960, 620)
        self.root.configure(bg="#EEF2F7")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

    def _configure_style(self) -> None:
        self.style = ttk.Style(self.root)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self.colors = {
            "bg": "#EEF2F7",
            "card": "#FFFFFF",
            "primary": "#2563EB",
            "primary_dark": "#1E40AF",
            "text": "#111827",
            "muted": "#6B7280",
            "border": "#D8DEE9",
            "danger": "#DC2626",
            "success": "#059669",
            "soft_blue": "#DBEAFE",
            "soft_green": "#D1FAE5",
            "soft_orange": "#FFEDD5",
        }

        default_font = ("Segoe UI", 10)
        title_font = ("Segoe UI", 22, "bold")
        section_font = ("Segoe UI", 13, "bold")

        self.style.configure(".", font=default_font, background=self.colors["bg"], foreground=self.colors["text"])
        self.style.configure("App.TFrame", background=self.colors["bg"])
        self.style.configure("Card.TFrame", background=self.colors["card"], relief="flat")
        self.style.configure("Hero.TFrame", background=self.colors["primary"])
        self.style.configure("Title.TLabel", font=title_font, background=self.colors["primary"], foreground="white")
        self.style.configure("HeroText.TLabel", background=self.colors["primary"], foreground="#DBEAFE")
        self.style.configure("Section.TLabel", font=section_font, background=self.colors["card"], foreground=self.colors["text"])
        self.style.configure("CardText.TLabel", background=self.colors["card"], foreground=self.colors["text"])
        self.style.configure("Muted.TLabel", background=self.colors["card"], foreground=self.colors["muted"])
        self.style.configure("Stat.TLabel", font=("Segoe UI", 20, "bold"), background=self.colors["card"], foreground=self.colors["primary_dark"])
        self.style.configure("StatCaption.TLabel", background=self.colors["card"], foreground=self.colors["muted"])
        self.style.configure("TEntry", fieldbackground="white", bordercolor=self.colors["border"], lightcolor=self.colors["border"], darkcolor=self.colors["border"], padding=8)
        self.style.configure("Primary.TButton", background=self.colors["primary"], foreground="white", padding=(14, 9), borderwidth=0)
        self.style.map("Primary.TButton", background=[("active", self.colors["primary_dark"]), ("pressed", self.colors["primary_dark"])] )
        self.style.configure("Secondary.TButton", background="#F8FAFC", foreground=self.colors["text"], padding=(14, 9), borderwidth=1)
        self.style.map("Secondary.TButton", background=[("active", "#E5E7EB"), ("pressed", "#E5E7EB")])
        self.style.configure("Danger.TButton", background="#FEF2F2", foreground=self.colors["danger"], padding=(14, 9), borderwidth=1)
        self.style.map("Danger.TButton", background=[("active", "#FEE2E2"), ("pressed", "#FEE2E2")])
        self.style.configure("Treeview", background="white", fieldbackground="white", foreground=self.colors["text"], rowheight=34, borderwidth=0)
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#F1F5F9", foreground="#334155", padding=8)
        self.style.map("Treeview", background=[("selected", self.colors["soft_blue"])], foreground=[("selected", self.colors["text"])])

    def _create_menu(self) -> None:
        menu = tk.Menu(self.root)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="Сохранить", command=self.save_to_disk)
        file_menu.add_command(label="Загрузить заново", command=self.reload_from_disk)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.destroy)
        menu.add_cascade(label="Файл", menu=file_menu)

        help_menu = tk.Menu(menu, tearoff=False)
        help_menu.add_command(label="О программе", command=self.show_about)
        menu.add_cascade(label="Справка", menu=help_menu)
        self.root.config(menu=menu)

    def _card(self, parent: ttk.Widget, row: int, column: int, **grid_options: object) -> ttk.Frame:
        frame = ttk.Frame(parent, style="Card.TFrame", padding=20)
        frame.grid(row=row, column=column, **grid_options)
        return frame

    def _create_layout(self) -> None:
        main = ttk.Frame(self.root, style="App.TFrame", padding=18)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(2, weight=1)

        self._create_hero(main)
        self._create_input_and_filters(main)
        self._create_table(main)
        self._create_status_bar(main)

    def _create_hero(self, parent: ttk.Frame) -> None:
        hero = ttk.Frame(parent, style="Hero.TFrame", padding=24)
        hero.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        hero.columnconfigure(0, weight=1)

        ttk.Label(hero, text=APP_NAME, style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            hero,
            text="Планирование тренировок, фильтрация по дате и типу, сохранение данных в JSON",
            style="HeroText.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        stats = ttk.Frame(hero, style="Hero.TFrame")
        stats.grid(row=0, column=1, rowspan=2, sticky="e")

        self._hero_stat(stats, "Записей", self.total_var, 0)
        self._hero_stat(stats, "В фильтре", self.filtered_var, 1)
        self._hero_stat(stats, "Минут", self.minutes_var, 2)

    def _hero_stat(self, parent: ttk.Frame, title: str, variable: tk.StringVar, column: int) -> None:
        box = tk.Frame(parent, bg="#1D4ED8", padx=18, pady=12, highlightthickness=0)
        box.grid(row=0, column=column, padx=(10, 0))
        tk.Label(box, textvariable=variable, font=("Segoe UI", 20, "bold"), bg="#1D4ED8", fg="white").pack()
        tk.Label(box, text=title, font=("Segoe UI", 9), bg="#1D4ED8", fg="#BFDBFE").pack()

    def _create_input_and_filters(self, parent: ttk.Frame) -> None:
        area = ttk.Frame(parent, style="App.TFrame")
        area.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        area.columnconfigure(0, weight=3)
        area.columnconfigure(1, weight=2)

        form = self._card(area, 0, 0, sticky="nsew", padx=(0, 12))
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)
        form.columnconfigure(5, weight=1)

        ttk.Label(form, text="Новая тренировка", style="Section.TLabel").grid(row=0, column=0, columnspan=6, sticky="w")
        ttk.Label(form, text="Заполните поля и нажмите кнопку добавления.", style="Muted.TLabel").grid(row=1, column=0, columnspan=6, sticky="w", pady=(2, 18))

        self._field(form, "Дата", self.date_var, "30.04.2026", 2, 0)
        self._field(form, "Тип тренировки", self.type_var, "Бег", 2, 2)
        self._field(form, "Длительность", self.duration_var, "45", 2, 4)

        buttons = ttk.Frame(form, style="Card.TFrame")
        buttons.grid(row=4, column=0, columnspan=6, sticky="w", pady=(18, 0))
        ttk.Button(buttons, text="Добавить тренировку", style="Primary.TButton", command=self.add_training).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(buttons, text="Сохранить изменения", style="Secondary.TButton", command=self.update_selected).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(buttons, text="Удалить", style="Danger.TButton", command=self.delete_selected).grid(row=0, column=2, padx=(0, 8))
        ttk.Button(buttons, text="Очистить", style="Secondary.TButton", command=self.clear_form).grid(row=0, column=3)

        filters = self._card(area, 0, 1, sticky="nsew")
        filters.columnconfigure(1, weight=1)
        ttk.Label(filters, text="Фильтрация", style="Section.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(filters, text="Поиск по дате и типу тренировки.", style="Muted.TLabel").grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 18))
        self._field(filters, "Дата", self.filter_date_var, "30.04.2026", 2, 0, columns=2)
        self._field(filters, "Тип", self.filter_type_var, "бег", 3, 0, columns=2)

        filter_buttons = ttk.Frame(filters, style="Card.TFrame")
        filter_buttons.grid(row=4, column=0, columnspan=2, sticky="w", pady=(18, 0))
        ttk.Button(filter_buttons, text="Применить фильтр", style="Primary.TButton", command=self.apply_filter).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(filter_buttons, text="Сбросить", style="Secondary.TButton", command=self.reset_filter).grid(row=0, column=1)

    def _field(
        self,
        parent: ttk.Frame,
        label: str,
        variable: tk.StringVar,
        placeholder: str,
        row: int,
        column: int,
        columns: int = 1,
    ) -> None:
        ttk.Label(parent, text=label, style="CardText.TLabel").grid(row=row, column=column, sticky="w", padx=(0, 8), pady=4)
        entry = ttk.Entry(parent, textvariable=variable)
        entry.grid(row=row + 1, column=column, columnspan=columns, sticky="ew", padx=(0, 12), pady=(0, 4))
        entry.insert(0, "")
        entry.configure()
        if placeholder:
            entry.bind("<FocusIn>", lambda event: self._set_status(f"Пример: {placeholder}"))

    def _create_table(self, parent: ttk.Frame) -> None:
        card = self._card(parent, 2, 0, sticky="nsew")
        card.columnconfigure(0, weight=1)
        card.rowconfigure(2, weight=1)

        top = ttk.Frame(card, style="Card.TFrame")
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(0, weight=1)
        ttk.Label(top, text="Таблица тренировок", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(top, text="Кликните по строке, чтобы выбрать запись для редактирования.", style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 16))

        columns = ("date", "type", "duration")
        self.table = ttk.Treeview(card, columns=columns, show="headings", selectmode="browse")
        self.table.heading("date", text="Дата")
        self.table.heading("type", text="Тип тренировки")
        self.table.heading("duration", text="Длительность, мин")
        self.table.column("date", width=160, anchor="center")
        self.table.column("type", width=520, anchor="w")
        self.table.column("duration", width=180, anchor="center")
        self.table.grid(row=2, column=0, sticky="nsew")
        self.table.bind("<<TreeviewSelect>>", self.on_table_select)

        scrollbar = ttk.Scrollbar(card, orient="vertical", command=self.table.yview)
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.table.configure(yscrollcommand=scrollbar.set)

    def _create_status_bar(self, parent: ttk.Frame) -> None:
        status = ttk.Frame(parent, style="App.TFrame")
        status.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        status.columnconfigure(0, weight=1)
        label = tk.Label(
            status,
            textvariable=self.status_var,
            bg="#E0E7FF",
            fg="#1E3A8A",
            padx=12,
            pady=8,
            anchor="w",
            font=("Segoe UI", 10, "bold"),
        )
        label.grid(row=0, column=0, sticky="ew")

    def _set_status(self, text: str) -> None:
        self.status_var.set(text)

    def add_training(self) -> None:
        try:
            training = Training.create(self.date_var.get(), self.type_var.get(), self.duration_var.get())
            self.book.add(training)
            self.save_to_disk(show_success=False)
            self.clear_form(update_status=False)
            self.refresh_table()
            self._set_status("Тренировка добавлена и сохранена в JSON.")
        except ValidationError as exc:
            messagebox.showerror("Ошибка ввода", str(exc))
            self._set_status(str(exc))
        except StorageError as exc:
            messagebox.showerror("Ошибка сохранения", str(exc))
            self._set_status(str(exc))

    def update_selected(self) -> None:
        if not self.selected_id:
            messagebox.showwarning("Нет выбранной записи", "Выберите тренировку в таблице.")
            return

        try:
            updated = Training(
                id=self.selected_id,
                date=validate_date(self.date_var.get()),
                training_type=validate_training_type(self.type_var.get()),
                duration=validate_duration(self.duration_var.get()),
            )
            self.book.replace(self.selected_id, updated)
            self.save_to_disk(show_success=False)
            self.clear_form(update_status=False)
            self.refresh_table()
            self._set_status("Изменения сохранены.")
        except ValidationError as exc:
            messagebox.showerror("Ошибка ввода", str(exc))
            self._set_status(str(exc))
        except StorageError as exc:
            messagebox.showerror("Ошибка сохранения", str(exc))
            self._set_status(str(exc))

    def delete_selected(self) -> None:
        if not self.selected_id:
            messagebox.showwarning("Нет выбранной записи", "Выберите тренировку в таблице.")
            return

        training = self.book.get(self.selected_id)
        if not training:
            return

        confirmed = messagebox.askyesno("Удаление", f"Удалить тренировку: {training.date}, {training.training_type}?")
        if not confirmed:
            return

        self.book.remove(self.selected_id)
        self.save_to_disk(show_success=False)
        self.clear_form(update_status=False)
        self.refresh_table()
        self._set_status("Тренировка удалена.")

    def clear_form(self, update_status: bool = True) -> None:
        self.selected_id = None
        self.date_var.set("")
        self.type_var.set("")
        self.duration_var.set("")
        self.table.selection_remove(self.table.selection())
        if update_status:
            self._set_status("Форма очищена.")

    def on_table_select(self, _event: tk.Event[tk.Widget]) -> None:
        selection = self.table.selection()
        if not selection:
            return
        item_id = selection[0]
        try:
            index = int(item_id)
            training = self.current_rows[index]
        except (ValueError, IndexError):
            return

        self.selected_id = training.id
        self.date_var.set(training.date)
        self.type_var.set(training.training_type)
        self.duration_var.set(str(training.duration))
        self._set_status("Запись выбрана для редактирования.")

    def apply_filter(self) -> None:
        try:
            rows = self.book.filter(self.filter_date_var.get(), self.filter_type_var.get())
            self.refresh_table(rows)
            self._set_status(f"Фильтр применён. Найдено записей: {len(rows)}.")
        except ValidationError as exc:
            messagebox.showerror("Ошибка фильтра", str(exc))
            self._set_status(str(exc))

    def reset_filter(self) -> None:
        self.filter_date_var.set("")
        self.filter_type_var.set("")
        self.refresh_table()
        self._set_status("Фильтры сброшены.")

    def refresh_table(self, rows: list[Training] | None = None) -> None:
        for item in self.table.get_children():
            self.table.delete(item)

        self.current_rows = rows if rows is not None else self.book.all()
        for index, training in enumerate(self.current_rows):
            tag = "even" if index % 2 == 0 else "odd"
            self.table.insert("", "end", iid=str(index), values=(training.date, training.training_type, training.duration), tags=(tag,))

        self.table.tag_configure("even", background="#FFFFFF")
        self.table.tag_configure("odd", background="#F8FAFC")
        self.total_var.set(str(len(self.book.all())))
        self.filtered_var.set(str(len(self.current_rows)))
        self.minutes_var.set(str(self.book.total_duration(self.current_rows)))

    def save_to_disk(self, show_success: bool = True) -> None:
        self.storage.save(self.book)
        if show_success:
            messagebox.showinfo("Сохранено", "Данные сохранены в JSON.")
            self._set_status("Данные сохранены в JSON.")

    def reload_from_disk(self, show_success: bool = True) -> None:
        try:
            self.book = self.storage.load()
            self.clear_form(update_status=False)
            self.refresh_table()
            if show_success:
                messagebox.showinfo("Загружено", "Данные загружены из JSON.")
            self._set_status("Данные загружены. Готово к работе.")
        except StorageError as exc:
            messagebox.showerror("Ошибка загрузки", str(exc))
            self.book = TrainingBook()
            self.refresh_table()
            self._set_status(str(exc))

    def show_about(self) -> None:
        messagebox.showinfo(
            "О программе",
            f"{APP_NAME}\n\nАвтор: {AUTHOR}\nНазначение: планирование тренировок с фильтрацией и JSON-хранением.",
        )


def run() -> None:
    root = tk.Tk()
    app = TrainingPlannerApp(root)
    root.mainloop()
