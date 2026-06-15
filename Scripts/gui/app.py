from __future__ import annotations

import tkinter as tk
from configparser import ConfigParser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable

from Scripts.config import save_config
from Scripts.database import DB


class CrudWindow(tk.Toplevel):
    def __init__(self, master: tk.Tk, db: DB, table: str) -> None:
        super().__init__(master)
        self.db = db
        self.table = table
        self.title(f"Справочник: {table}")
        self.geometry("900x460")

        self.tree = ttk.Treeview(self, show="headings")
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)

        if table == "Movies":
            self.columns = ["movieId", "title"]
            self.labels = ["ID фильма", "Название"]
        elif table == "Users":
            self.columns = ["userId"]
            self.labels = ["ID пользователя"]
        elif table == "Genres":
            self.columns = ["genreId", "genreName"]
            self.labels = ["ID жанра", "Название жанра"]
        elif table == "Ratings":
            self.columns = ["ratingId", "userId", "movieId", "rating"]
            self.labels = ["ID рейтинга", "ID пользователя", "ID фильма", "Рейтинг"]
        elif table == "Tags":
            self.columns = ["tagId", "userId", "movieId", "tag"]
            self.labels = ["ID тега", "ID пользователя", "ID фильма", "Тег"]
        else:  # MovieGenre
            self.columns = ["movieId", "genreId"]
            self.labels = ["ID фильма", "ID жанра"]

        self.tree["columns"] = self.columns
        for col, label in zip(self.columns, self.labels):
            self.tree.heading(col, text=label)
            self.tree.column(col, width=130, stretch=True)

        controls = ttk.Frame(self)
        controls.pack(fill="x", padx=8, pady=(0, 8))

        ttk.Button(controls, text="Обновить", command=self.refresh).pack(side="left", padx=4)

        self.refresh()

    def refresh(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in self.db.fetch_all(self.table):
            # row теперь словарь, получаем значения по ключам колонок
            values = [row.get(col, '') for col in self.columns]
            self.tree.insert("", "end", values=values)


class MovieApp(tk.Tk):
    def __init__(self, db: DB, config: ConfigParser, paths: dict[str, Path]) -> None:
        super().__init__()
        self.db = db
        self.config_data = config
        self.paths = paths
        self.current_photo = None
        self.is_fullscreen = False
        self.current_section = "dashboard"

        ui = config["ui"]
        self.title(ui["title"])
        self.geometry(f"{ui['window_width']}x{ui['window_height']}")

        self._build_menu()
        self._build_layout()
        self._bind_hotkeys()
        self._refresh_status()

        # Разворачиваем окно на весь экран (для macOS)
        self.state('zoomed')  # Максимизация окна на текущем экране

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Выход", command=self.destroy)
        menubar.add_cascade(label="Файл", menu=file_menu)

        dict_menu = tk.Menu(menubar, tearoff=0)
        dict_menu.add_command(label="Фильмы", command=lambda: CrudWindow(self, self.db, "Movies"))
        dict_menu.add_command(label="Пользователи", command=lambda: CrudWindow(self, self.db, "Users"))
        dict_menu.add_command(label="Жанры", command=lambda: CrudWindow(self, self.db, "Genres"))
        dict_menu.add_command(label="Фильм-Жанр", command=lambda: CrudWindow(self, self.db, "MovieGenre"))
        dict_menu.add_command(label="Рейтинги", command=lambda: CrudWindow(self, self.db, "Ratings"))
        dict_menu.add_command(label="Теги", command=lambda: CrudWindow(self, self.db, "Tags"))
        menubar.add_cascade(label="Справочники", menu=dict_menu)

        rep_menu = tk.Menu(menubar, tearoff=0)
        rep_menu.add_command(label="Текстовые отчёты", command=lambda: self.show_reports("output"))
        rep_menu.add_command(label="Графические отчёты", command=lambda: self.show_reports("graphics"))
        menubar.add_cascade(label="Отчёты", menu=rep_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Полный экран (F11)", command=self.toggle_fullscreen)
        view_menu.add_command(label="Выйти из полного экрана (Esc)", command=self.exit_fullscreen)
        menubar.add_cascade(label="Вид", menu=view_menu)

        set_menu = tk.Menu(menubar, tearoff=0)
        set_menu.add_command(label="Настройки", command=self.show_settings)
        menubar.add_cascade(label="Настройки", menu=set_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=lambda: messagebox.showinfo("О программе", "GUI слой"))
        menubar.add_cascade(label="Справка", menu=help_menu)

        self.config(menu=menubar)

    def _bind_hotkeys(self) -> None:
        self.bind("<F11>", lambda _event: self.toggle_fullscreen())
        self.bind("<Escape>", lambda _event: self.exit_fullscreen())

    def toggle_fullscreen(self) -> None:
        self.is_fullscreen = not self.is_fullscreen
        self.attributes("-fullscreen", self.is_fullscreen)

    def exit_fullscreen(self) -> None:
        self.is_fullscreen = False
        self.attributes("-fullscreen", False)

    def _build_layout(self) -> None:
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        left = ttk.Frame(container, width=260)
        left.pack(side="left", fill="y")

        ttk.Label(left, text="Навигация").pack(anchor="w", padx=8, pady=(10, 8))
        nav_items = [
            ("Обзор", self.show_dashboard),
            ("Фильмы", self.show_movies),
            ("Пользователи", self.show_users),
            ("Жанры", self.show_genres),
            ("Рейтинги", self.show_ratings),
            ("Теги", self.show_tags),
            ("Рекомендации", self.show_recommendations),
            ("Отчёты", self.show_reports_overview),
            ("Настройки", self.show_settings),
        ]
        for label, callback in nav_items:
            ttk.Button(left, text=label, command=callback).pack(fill="x", padx=8, pady=4)

        ttk.Separator(left).pack(fill="x", padx=8, pady=10)
        ttk.Label(left, text="Панель управления").pack(anchor="w", padx=8, pady=(0, 8))
        ttk.Button(left, text="Регистрация пользователя", command=self.register_user).pack(fill="x", padx=8, pady=4)
        ttk.Button(left, text="Открыть текстовые отчёты", command=lambda: self.show_reports("output")).pack(fill="x", padx=8, pady=4)
        ttk.Button(left, text="Открыть графические отчёты", command=lambda: self.show_reports("graphics")).pack(fill="x", padx=8, pady=4)

        right = ttk.Frame(container)
        right.pack(side="left", fill="both", expand=True)

        header = ttk.Frame(right)
        header.pack(fill="x", padx=12, pady=(12, 0))
        self.content_title = ttk.Label(header, text="Рекомендательная система фильмов", font=("Segoe UI", 16, "bold"))
        self.content_title.pack(anchor="w")

        self.content_subtitle = ttk.Label(header, text="Выберите раздел в навигации слева")
        self.content_subtitle.pack(anchor="w", pady=(4, 0))

        self.cards_area = ttk.Frame(right)
        self.cards_area.pack(fill="x", padx=12, pady=12)

        body = ttk.Frame(right)
        body.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.content_text = tk.Text(body, height=15, wrap="word")
        self.content_text.pack(fill="both", expand=True)
        self.content_text.insert("1.0", "Здесь будет отображаться справочная информация, отчёты и карточки рекомендаций.")
        self.content_text.config(state="disabled")

        self.image_label = ttk.Label(body)
        self.image_label.pack(anchor="center", padx=12, pady=(10, 0))

        self.status = ttk.Label(self, text="", relief="sunken", anchor="w")
        self.status.pack(fill="x", side="bottom")

    def _refresh_status(self) -> None:
        movies, users = self.db.stats()
        self.status.config(text=f"Фильмов: {movies}    Пользователей: {users}    База загружена")

    def _set_text_content(self, title: str, body: str) -> None:
        self.current_section = "text"
        self.content_title.config(text=title)
        self.content_subtitle.config(text="")
        self._clear_cards()
        self.content_text.config(state="normal")
        self.content_text.delete("1.0", "end")
        self.content_text.insert("1.0", body)
        self.content_text.config(state="disabled")
        self.image_label.config(image="")

    def _clear_cards(self) -> None:
        for widget in self.cards_area.winfo_children():
            widget.destroy()

    def _render_cards(self, cards: list[tuple[str, str, str, Callable[[], None] | None]]) -> None:
        self._clear_cards()
        for idx, (title, subtitle, action_text, command) in enumerate(cards):
            card = ttk.Frame(self.cards_area, padding=10, relief="ridge")
            card.grid(row=0, column=idx, padx=6, sticky="nsew")
            ttk.Label(card, text=title, font=("Segoe UI", 11, "bold")).pack(anchor="w")
            ttk.Label(card, text=subtitle, wraplength=200).pack(anchor="w", pady=(4, 8))
            ttk.Button(card, text=action_text, command=command).pack(anchor="w")
        for idx in range(max(1, len(cards))):
            self.cards_area.columnconfigure(idx, weight=1)

    def register_user(self) -> None:
        """Заглушка для регистрации пользователя - будет реализовано позже"""
        pass

    def show_dashboard(self) -> None:
        self.current_section = "dashboard"
        self.content_title.config(text="Обзор системы")
        self.content_subtitle.config(text="Состояние данных, быстрые действия и следующее, что стоит сделать")
        self._render_cards([
            ("Фильмы", "Откройте справочник фильмов и проверьте данные.", "Открыть", self.open_movies_window),
            ("Пользователи", "Зарегистрируйте нового пользователя или отредактируйте существующего.", "Открыть", self.open_users_window),
            ("Отчёты", "Текстовые и графические отчёты отображаются внутри приложения.", "Открыть", self.show_reports_overview),
        ])
        self._set_text_body(
            "Статус проекта",
            "Фронтенд открывет справочники, показывает отчёты, работает с настройками.",
        )

    def _set_text_body(self, title: str, body: str) -> None:
        self.content_title.config(text=title)
        self.content_text.config(state="normal")
        self.content_text.delete("1.0", "end")
        self.content_text.insert("1.0", body)
        self.content_text.config(state="disabled")
        self.image_label.config(image="")

    def _show_table_in_content(self, table_name: str, title: str) -> None:
        """Отображает справочник в основной области приложения"""
        self.current_section = f"table_{table_name}"
        self.content_title.config(text=title)

        # Получаем общее количество записей
        total_count = self.db.count(table_name)
        display_limit = 1000

        if total_count > display_limit:
            self.content_subtitle.config(text=f"Показано первых {display_limit} из {total_count} записей")
        else:
            self.content_subtitle.config(text=f"Всего записей: {total_count}")

        self._clear_cards()

        # Скрываем текстовое поле и показываем таблицу
        self.content_text.pack_forget()
        self.image_label.config(image="")

        # Создаём таблицу, если её ещё нет
        if not hasattr(self, 'main_tree') or self.main_tree is None:
            tree_frame = ttk.Frame(self.content_text.master)
            tree_frame.pack(fill="both", expand=True)

            scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical")
            scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal")

            self.main_tree = ttk.Treeview(
                tree_frame,
                show="headings",
                yscrollcommand=scrollbar_y.set,
                xscrollcommand=scrollbar_x.set
            )

            scrollbar_y.config(command=self.main_tree.yview)
            scrollbar_x.config(command=self.main_tree.xview)

            scrollbar_y.pack(side="right", fill="y")
            scrollbar_x.pack(side="bottom", fill="x")
            self.main_tree.pack(fill="both", expand=True)

        # Определяем колонки для таблицы
        if table_name == "Movies":
            columns = ["movieId", "title"]
            labels = ["ID фильма", "Название"]
        elif table_name == "Users":
            columns = ["userId"]
            labels = ["ID пользователя"]
        elif table_name == "Genres":
            columns = ["genreId", "genreName"]
            labels = ["ID жанра", "Название жанра"]
        elif table_name == "Ratings":
            columns = ["ratingId", "userId", "movieId", "rating"]
            labels = ["ID рейтинга", "ID пользователя", "ID фильма", "Рейтинг"]
        elif table_name == "Tags":
            columns = ["tagId", "userId", "movieId", "tag"]
            labels = ["ID тега", "ID пользователя", "ID фильма", "Тег"]
        else:  # MovieGenre
            columns = ["movieId", "genreId"]
            labels = ["ID фильма", "ID жанра"]

        # Настраиваем колонки
        self.main_tree["columns"] = columns
        for col, label in zip(columns, labels):
            self.main_tree.heading(col, text=label)
            self.main_tree.column(col, width=150, stretch=True)

        # Очищаем старые данные
        for row in self.main_tree.get_children():
            self.main_tree.delete(row)

        # Загружаем данные с лимитом
        for row in self.db.fetch_all(table_name, limit=display_limit):
            values = [row.get(col, '') for col in columns]
            self.main_tree.insert("", "end", values=values)

    def show_movies(self) -> None:
        self._show_table_in_content("Movies", "Справочник фильмов")

    def show_users(self) -> None:
        self._show_table_in_content("Users", "Справочник пользователей")

    def show_genres(self) -> None:
        self._show_table_in_content("Genres", "Справочник жанров")

    def show_ratings(self) -> None:
        self._show_table_in_content("Ratings", "Справочник рейтингов")

    def show_tags(self) -> None:
        self._show_table_in_content("Tags", "Справочник тегов")

    def show_recommendations(self) -> None:
        self.current_section = "recommendations"
        self.content_title.config(text="Рекомендации")
        self.content_subtitle.config(text="Пока используются mock-карточки, но сценарий уже похож на реальную выдачу")
        self._render_recommendation_feed()
        self.content_text.config(state="normal")
        self.content_text.delete("1.0", "end")
        self.content_text.insert(
            "1.0",
            "На этом экране будут показываться карточки фильмов, которые можно лайкнуть или скрыть. "
            "Сейчас это демонстрационный набор, который помогает отладить UI-поток без готового бэкенда.",
        )
        self.content_text.config(state="disabled")
        self.image_label.config(image="")

    def show_reports_overview(self) -> None:
        self.current_section = "reports"
        self._set_text_body(
            "Отчёты",
            "Используйте кнопки слева или пункты верхнего меню для просмотра текстовых и графических отчётов. "
            "Файлы берутся из каталогов Output/ и Graphics/.",
        )
        self._render_cards([
            ("Текстовые", "Список и просмотр текстовых отчётов.", "Открыть", lambda: self.show_reports("output")),
            ("Графические", "Список графиков и изображений отчётов.", "Открыть", lambda: self.show_reports("graphics")),
            ("Экспорт", "Позже можно добавить экспорт и печать.", "Открыть", self._show_reports_placeholder),
        ])

    def open_movies_window(self) -> None:
        CrudWindow(self, self.db, "Movies")

    def open_users_window(self) -> None:
        CrudWindow(self, self.db, "Users")

    def _show_recommendations_placeholder(self) -> None:
        self.show_recommendations()

    def _render_recommendation_feed(self) -> None:
        self._clear_cards()
        for idx, movie in enumerate(self.mock_recommendations):
            card = ttk.Frame(self.cards_area, padding=12, relief="ridge")
            card.grid(row=0, column=idx, padx=6, sticky="nsew")
            ttk.Label(card, text=movie["title"], font=("Segoe UI", 11, "bold")).pack(anchor="w")
            ttk.Label(card, text=f"{movie['year']}  •  {movie['genres']}").pack(anchor="w", pady=(4, 0))
            ttk.Label(card, text=movie["reason"], wraplength=220).pack(anchor="w", pady=(8, 10))
            buttons = ttk.Frame(card)
            buttons.pack(anchor="w")
            ttk.Button(buttons, text="Лайк", command=lambda m=movie: self._handle_recommendation_action(m, "like")).pack(side="left", padx=(0, 6))
            ttk.Button(buttons, text="Скрыть", command=lambda m=movie: self._handle_recommendation_action(m, "hide")).pack(side="left")
        for idx in range(max(1, len(self.mock_recommendations))):
            self.cards_area.columnconfigure(idx, weight=1)

    def _handle_recommendation_action(self, movie: dict, action: str) -> None:
        action_label = "лайкнули" if action == "like" else "скрыли"
        self.content_subtitle.config(text=f"Последнее действие: {action_label} {movie['title']}")
        self.status.config(text=f"{movie['title']} -> {action_label}")
        messagebox.showinfo("Действие сохранено", f"Вы {action_label} фильм {movie['title']}.")

    def _show_reports_placeholder(self) -> None:
        self._set_text_body(
            "Отчёты",
            "Раздел экспорта пока не подключён. Сейчас отчёты просматриваются прямо из Output/ и Graphics/.",
        )

    def show_reports(self, report_type: str) -> None:
        base = self.paths[report_type]
        files = sorted([p for p in base.iterdir() if p.is_file()])
        if not files:
            self._set_text_content("Отчёты", f"В папке {base} пока нет файлов.")
            return

        picker = tk.Toplevel(self)
        picker.title("Выбор отчёта")
        picker.geometry("620x360")

        lst = tk.Listbox(picker)
        lst.pack(fill="both", expand=True, padx=8, pady=8)
        for f in files:
            lst.insert("end", f.name)

        def open_selected() -> None:
            if not lst.curselection():
                return
            path = base / lst.get(lst.curselection()[0])
            if report_type == "output":
                self._set_text_content(f"Текстовый отчёт: {path.name}", path.read_text(encoding="utf-8", errors="ignore"))
            else:
                self._show_image(path)
            picker.destroy()

        ttk.Button(picker, text="Открыть", command=open_selected).pack(pady=6)

    def _show_image(self, path: Path) -> None:
        self.content_title.config(text=f"Графический отчёт: {path.name}")
        suffix = path.suffix.lower()
        if suffix not in {".png", ".gif"}:
            self._set_text_content("Графический отчёт", f"Формат {suffix} не поддерживается встроенным просмотром Tkinter.\nФайл: {path}")
            self.image_label.config(image="")
            return
        try:
            photo = tk.PhotoImage(file=str(path))
            self.current_photo = photo
            self.image_label.config(image=photo)
            self._set_text_content("Графический отчёт", f"Открыт файл: {path.name}")
        except tk.TclError as err:
            self._set_text_content("Ошибка изображения", str(err))

    def show_settings(self) -> None:
        win = tk.Toplevel(self)
        win.title("Настройки")
        win.geometry("720x360")

        keys = [
            ("ui", "title"),
            ("ui", "font_family"),
            ("ui", "font_size"),
            ("paths", "data_dir"),
            ("paths", "graphics_dir"),
            ("paths", "output_dir"),
        ]
        entries: dict[tuple[str, str], ttk.Entry] = {}

        for i, (section, key) in enumerate(keys):
            ttk.Label(win, text=f"{section}.{key}").grid(row=i, column=0, padx=8, pady=6, sticky="w")
            ent = ttk.Entry(win, width=80)
            ent.insert(0, self.config_data[section][key])
            ent.grid(row=i, column=1, padx=8, pady=6)
            entries[(section, key)] = ent

        def choose_dir(target: tuple[str, str]) -> None:
            selected = filedialog.askdirectory(initialdir=entries[target].get() or "/")
            if selected:
                entries[target].delete(0, "end")
                entries[target].insert(0, selected)

        ttk.Button(win, text="Выбрать graphics_dir", command=lambda: choose_dir(("paths", "graphics_dir"))).grid(row=7, column=1, sticky="w", padx=8)
        ttk.Button(win, text="Выбрать output_dir", command=lambda: choose_dir(("paths", "output_dir"))).grid(row=8, column=1, sticky="w", padx=8)

        def save() -> None:
            for (section, key), ent in entries.items():
                self.config_data[section][key] = ent.get().strip()
            save_config(self.config_data)
            messagebox.showinfo("Настройки", "Настройки сохранены. Перезапустите приложение для полного применения.")
            win.destroy()

        ttk.Button(win, text="Сохранить", command=save).grid(row=9, column=0, columnspan=2, pady=12)
