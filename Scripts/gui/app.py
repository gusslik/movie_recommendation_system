from __future__ import annotations

import tkinter as tk
import pandas as pd
from configparser import ConfigParser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable
from PIL import Image, ImageTk

from Scripts.config import save_config
from Scripts.dataframe_db import DataFrameDB
from Scripts.backend.recommendations_adapter import get_recommendations_from_db
from Scripts.reports_generator import generate_all_reports


class CrudWindow(tk.Toplevel):
    def __init__(self, master: tk.Tk, db: DataFrameDB, table: str) -> None:
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
    def __init__(self, db: DataFrameDB, config: ConfigParser, paths: dict[str, Path]) -> None:
        super().__init__()
        self.db = db
        self.config_data = config
        self.paths = paths
        self.current_photo = None
        self.is_fullscreen = False
        self.current_section = "dashboard"

        # Создаём нового пользователя приложения (не из датасета)
        self.app_user_id = self._create_app_user()
        self.recommendations_cache = None  # Кэш рекомендаций

        ui = config["ui"]
        self.title(ui["title"])
        self.geometry(f"{ui['window_width']}x{ui['window_height']}")

        self._build_menu()
        self._build_layout()
        self._bind_hotkeys()
        self._refresh_status()

        # Максимизация окна (кроссплатформенно)
        try:
            self.state('zoomed')  # Windows/macOS
        except tk.TclError:
            self.attributes('-zoomed', True)  # Linux

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

        # Показываем ID текущего пользователя
        user_info = ttk.Frame(left)
        user_info.pack(fill="x", padx=8, pady=4)
        ttk.Label(user_info, text="Ваш ID:", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.user_id_label = ttk.Label(user_info, text=f"#{self.app_user_id}", font=("Segoe UI", 10))
        self.user_id_label.pack(anchor="w", pady=(2, 0))

        ttk.Button(left, text="Регистрация пользователя", command=self.register_user).pack(fill="x", padx=8, pady=4)
        ttk.Button(left, text="Сгенерировать отчёты", command=self.generate_reports).pack(fill="x", padx=8, pady=4)
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

    def _create_app_user(self) -> int:
        """Создаёт нового пользователя приложения (не из датасета)"""
        users_df = self.db.data['users']

        # Находим максимальный ID и создаём нового пользователя
        max_user_id = users_df['userId'].max() if len(users_df) > 0 else 0
        new_user_id = max_user_id + 1

        new_user = pd.DataFrame([{'userId': new_user_id}])
        self.db.data['users'] = pd.concat([users_df, new_user], ignore_index=True)

        print(f"Создан пользователь приложения с ID: {new_user_id}")
        return new_user_id

    def _refresh_status(self) -> None:
        movies, users = self.db.stats()
        self.status.config(text=f"Фильмов: {movies}    Пользователей: {users}    Ваш ID: {self.app_user_id}")

    def _set_text_content(self, title: str, body: str) -> None:
        self.current_section = "text"
        self.content_title.config(text=title)
        self.content_subtitle.config(text="")
        self._clear_cards()

        # Скрываем изображение и показываем текстовое поле
        self.image_label.pack_forget()
        self.content_text.pack(fill="both", expand=True)

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
        """Регистрирует нового пользователя в системе"""
        try:
            from Scripts.backend.utils import add_new_user

            # Добавляем нового пользователя
            new_user_id = add_new_user(self.db.data)

            # Показываем уведомление
            messagebox.showinfo(
                "Успешно",
                f"Новый пользователь зарегистрирован!\n\nID пользователя: {new_user_id}\n\n"
                f"Теперь этот пользователь может оценивать фильмы и получать рекомендации."
            )

            # Обновляем статус
            self._refresh_status()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось зарегистрировать пользователя:\n{str(e)}")
            print(f"Ошибка регистрации: {e}")
            import traceback
            traceback.print_exc()

    def generate_reports(self) -> None:
        """Генерирует все отчёты (текстовые и графические)"""
        try:
            self.status.config(text="Генерация отчётов...")
            self.update()

            generate_all_reports(
                self.db,
                self.paths['output'],
                self.paths['graphics']
            )

            messagebox.showinfo(
                "Отчёты созданы",
                "Все отчёты успешно сгенерированы!\n\n"
                "Текстовые отчёты: Output/\n"
                "Графические отчёты: Graphics/"
            )
            self.status.config(text="Отчёты успешно созданы")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать отчёты:\n{str(e)}")
            self.status.config(text="Ошибка при создании отчётов")
            print(f"Ошибка генерации отчётов: {e}")
            import traceback
            traceback.print_exc()

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

        # Загружаем рекомендации, если ещё не загружены
        if self.recommendations_cache is None:
            self.content_subtitle.config(text="Загрузка рекомендаций...")
            self.update()

            try:
                self.recommendations_cache = get_recommendations_from_db(
                    self.db,
                    self.app_user_id,
                    top_n=5,
                    method='user'
                )
                if not self.recommendations_cache:
                    self.recommendations_cache = []
                    self.content_subtitle.config(text="Не удалось загрузить рекомендации")
                else:
                    self.content_subtitle.config(text=f"Персональные рекомендации")
            except Exception as e:
                print(f"Ошибка загрузки рекомендаций: {e}")
                self.recommendations_cache = []
                self.content_subtitle.config(text="Ошибка при загрузке рекомендаций")
        else:
            self.content_subtitle.config(text=f"Персональные рекомендации")

        self._render_recommendation_feed()
        self.content_text.config(state="normal")
        self.content_text.delete("1.0", "end")

        if self.recommendations_cache:
            self.content_text.insert(
                "1.0",
                "Рекомендации на основе анализа ваших оценок и предпочтений похожих пользователей. "
                "Лайкайте фильмы, чтобы улучшить качество рекомендаций.",
            )
        else:
            self.content_text.insert(
                "1.0",
                "К сожалению, сейчас нет доступных рекомендаций. "
                "Попробуйте оценить несколько фильмов, чтобы система могла подобрать персональные рекомендации.",
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

        # Используем реальные рекомендации или показываем пустое состояние
        recommendations = self.recommendations_cache if self.recommendations_cache else []

        if not recommendations:
            # Показываем сообщение, если нет рекомендаций
            card = ttk.Frame(self.cards_area, padding=12, relief="ridge")
            card.grid(row=0, column=0, padx=6, sticky="nsew")
            ttk.Label(card, text="Нет рекомендаций", font=("Segoe UI", 11, "bold")).pack(anchor="w")
            ttk.Label(card, text="Попробуйте оценить несколько фильмов", wraplength=220).pack(anchor="w", pady=(4, 0))
            self.cards_area.columnconfigure(0, weight=1)
            return

        for idx, movie in enumerate(recommendations):
            card = ttk.Frame(self.cards_area, padding=12, relief="ridge")
            card.grid(row=0, column=idx, padx=6, sticky="nsew")
            ttk.Label(card, text=movie["title"], font=("Segoe UI", 11, "bold")).pack(anchor="w")
            ttk.Label(card, text=f"{movie['year']}  •  {movie['genres']}").pack(anchor="w", pady=(4, 0))
            ttk.Label(card, text=movie["reason"], wraplength=220).pack(anchor="w", pady=(8, 10))
            buttons = ttk.Frame(card)
            buttons.pack(anchor="w")
            ttk.Button(buttons, text="Лайк", command=lambda m=movie: self._handle_recommendation_action(m, "like")).pack(side="left", padx=(0, 6))
            ttk.Button(buttons, text="Скрыть", command=lambda m=movie: self._handle_recommendation_action(m, "hide")).pack(side="left")

        for idx in range(max(1, len(recommendations))):
            self.cards_area.columnconfigure(idx, weight=1)

    def _handle_recommendation_action(self, movie: dict, action: str) -> None:
        action_label = "лайкнули" if action == "like" else "скрыли"
        movie_title = movie['title']

        try:
            # Добавляем оценку в базу данных
            if action == "like":
                self._add_rating(self.app_user_id, movie['movieId'], 5.0)
                message = f"Добавлена оценка 5.0 для фильма '{movie_title}'"
            else:
                self._add_rating(self.app_user_id, movie['movieId'], 1.0)
                message = f"Фильм '{movie_title}' скрыт из рекомендаций"

            # Удаляем фильм из кэша рекомендаций
            if self.recommendations_cache:
                self.recommendations_cache = [
                    rec for rec in self.recommendations_cache
                    if rec['movieId'] != movie['movieId']
                ]

            # Обновляем интерфейс
            self.content_subtitle.config(text=f"✓ {message}")
            self.status.config(text=f"{movie_title} → {action_label}")

            # Перерисовываем карточки рекомендаций
            self._render_recommendation_feed()

            # Если рекомендации закончились, загружаем новые
            if not self.recommendations_cache:
                self.content_subtitle.config(text="Загрузка новых рекомендаций...")
                self.recommendations_cache = None
                self.after(500, self.show_recommendations)

        except Exception as e:
            self.content_subtitle.config(text=f"Ошибка: {str(e)}")
            print(f"Ошибка при обработке действия: {e}")

    def _add_rating(self, user_id: int, movie_id: int, rating: float) -> None:
        """Добавляет новую оценку в базу данных"""
        ratings_df = self.db.data['ratings']

        # Проверяем, не оценивал ли пользователь этот фильм ранее
        existing = ratings_df[
            (ratings_df['userId'] == user_id) &
            (ratings_df['movieId'] == movie_id)
        ]

        if not existing.empty:
            # Обновляем существующую оценку
            ratings_df.loc[existing.index, 'rating'] = rating
        else:
            # Создаём новую оценку
            new_rating_id = ratings_df['ratingId'].max() + 1 if len(ratings_df) > 0 else 1

            new_rating = pd.DataFrame([{
                'ratingId': new_rating_id,
                'userId': user_id,
                'movieId': movie_id,
                'rating': rating
            }])

            self.db.data['ratings'] = pd.concat([ratings_df, new_rating], ignore_index=True)

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
        if suffix not in {".png", ".gif", ".jpg", ".jpeg"}:
            self._set_text_content("Графический отчёт", f"Формат {suffix} не поддерживается.\nФайл: {path}")
            self.image_label.config(image="")
            return
        try:
            # Используем PIL для загрузки изображения
            img = Image.open(path)

            # Масштабируем изображение, если оно слишком большое
            max_width = 1000
            max_height = 600
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            # Конвертируем в PhotoImage
            photo = ImageTk.PhotoImage(img)
            self.current_photo = photo
            self.image_label.config(image=photo)

            # Скрываем текстовое поле и показываем изображение
            self.content_text.pack_forget()
            self.image_label.pack(fill="both", expand=True, padx=12, pady=12)

        except Exception as err:
            self._set_text_content("Ошибка изображения", f"Не удалось загрузить изображение:\n{str(err)}")
            self.image_label.config(image="")

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
