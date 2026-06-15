# Руководство разработчика фронтенда

Документ описывает архитектуру GUI-слоя рекомендательной системы фильмов и правила работы с ним.

## 1. Общая архитектура

### Структура GUI-слоя

```
Scripts/
├── gui/
│   ├── __init__.py
│   └── app.py              # Основное GUI приложение
├── backend/
│   ├── utils.py            # Загрузка и обработка данных
│   └── recommendations_adapter.py  # Адаптер системы рекомендаций
├── dataframe_db.py         # Обёртка над pandas DataFrame
├── config.py               # Управление конфигурацией
├── bootstrap.py            # Инициализация окружения
├── reports_generator.py    # Генерация отчётов
└── main.py                 # Точка входа
```

### Технологический стек

- **GUI Framework:** Tkinter (встроенный в Python)
- **Данные:** pandas DataFrame (в памяти)
- **Конфигурация:** ConfigParser (INI файлы)
- **Изображения:** PIL/Pillow
- **Графики:** matplotlib

## 2. Основные компоненты

### 2.1 MovieApp (главное окно)

**Файл:** `Scripts/gui/app.py`

**Класс:** `MovieApp(tk.Tk)`

**Основные атрибуты:**
- `self.db: DataFrameDB` — доступ к данным
- `self.config_data: ConfigParser` — конфигурация приложения
- `self.paths: dict[str, Path]` — пути к директориям
- `self.app_user_id: int` — ID персонального пользователя
- `self.recommendations_cache: list[dict]` — кэш рекомендаций
- `self.current_section: str` — текущий активный раздел

**Жизненный цикл:**
1. Инициализация окна и конфигурации
2. Создание персонального пользователя (`_create_app_user()`)
3. Построение меню (`_build_menu()`)
4. Построение layout (`_build_layout()`)
5. Привязка горячих клавиш (`_bind_hotkeys()`)
6. Обновление статуса (`_refresh_status()`)
7. Максимизация окна (кроссплатформенная)

### 2.2 CrudWindow (окна справочников)

**Класс:** `CrudWindow(tk.Toplevel)`

**Назначение:** Отображение данных таблиц в отдельном окне

**Поддерживаемые таблицы:**
- Movies (movieId, title)
- Users (userId)
- Genres (genreId, genreName)
- Ratings (ratingId, userId, movieId, rating)
- Tags (tagId, userId, movieId, tag)
- MovieGenre (movieId, genreId)

**Методы:**
- `refresh()` — обновление данных из БД

## 3. Компоновка интерфейса

### Layout структура

```
┌─────────────────────────────────────────────────────┐
│ Меню: Файл | Справочники | Отчёты | Вид | ...       │
├──────────┬──────────────────────────────────────────┤
│          │  Header (title + subtitle)               │
│ Навига-  ├──────────────────────────────────────────┤
│ ция      │  Cards Area (карточки рекомендаций)      │
│          ├──────────────────────────────────────────┤
│ - Обзор  │  Content Area:                           │
│ - Фильмы │   - Text widget OR                       │
│ - ...    │   - Treeview (таблицы) OR                │
│          │   - Image label (графики)                │
│──────────┤                                          │
│ Панель   │                                          │
│ управл.  │                                          │
│          │                                          │
│ Ваш ID:  │                                          │
│ #162542|                                          │
├──────────┴──────────────────────────────────────────┤
│ Status bar: Фильмов: 62423  Пользователей: 162542   │
└─────────────────────────────────────────────────────┘
```

### Основные зоны

**Left Panel (навигация):**
- Ширина: 260px
- Кнопки навигации (fill="x")
- Разделитель
- Панель управления
- Информация о пользователе

**Right Panel (контент):**
- Header: title (16pt bold) + subtitle
- Cards area: горизонтальная сетка карточек
- Content area: текст/таблица/изображение
- Динамически переключается в зависимости от раздела

## 4. Разделы интерфейса

### 4.1 Обзор (Dashboard)

**Метод:** `show_dashboard()`

**Содержимое:**
- 3 карточки: Фильмы, Пользователи, Отчёты
- Текстовое описание статуса проекта

### 4.2 Справочники (Movies, Users, Genres, ...)

**Методы:** `show_movies()`, `show_users()`, etc.

**Реализация:** `_show_table_in_content(table_name, title)`

**Особенности:**
- Отображает первые 1000 записей (производительность)
- Показывает общее количество записей в subtitle
- Использует `ttk.Treeview` для табличного отображения
- Вертикальная и горизонтальная прокрутка

### 4.3 Рекомендации

**Метод:** `show_recommendations()`

**Workflow:**
1. Проверка кэша рекомендаций
2. Если кэш пуст — загрузка через `get_recommendations_from_db()`
3. Отображение карточек через `_render_recommendation_feed()`
4. При действии (лайк/скрыть):
   - Добавление оценки через `_add_rating()`
   - Удаление карточки из кэша
   - Перерисовка карточек
   - Если карточки закончились — загрузка новых

**Карточка рекомендации:**
```python
{
    'movieId': int,
    'title': str,
    'year': str,
    'genres': str,
    'score': float,
    'reason': str
}
```

### 4.4 Отчёты

**Просмотр отчётов:**
- `show_reports(report_type)` — выбор отчёта из списка
- Текстовые: читаются из `Output/`
- Графические: читаются из `Graphics/`

**Генерация отчётов:**
- `generate_reports()` — вызывает `reports_generator.py`
- Создаёт 5 текстовых + 4 графических отчёта
- Показывает уведомление об успехе/ошибке

## 5. Работа с данными

### DataFrameDB

**Файл:** `Scripts/dataframe_db.py`

**Интерфейс:**
```python
class DataFrameDB:
    def fetch_all(self, table: str, limit: int = None) -> list[dict]
    def stats(self) -> tuple[int, int]  # (movies, users)
    def count(self, table: str) -> int
    def close(self) -> None
```

**Доступ к данным:**
```python
# Прямой доступ к DataFrame
self.db.data['movies']     # pd.DataFrame
self.db.data['ratings']    # pd.DataFrame
self.db.data['genres']     # pd.DataFrame
...
```

### Добавление оценок

**Метод:** `_add_rating(user_id, movie_id, rating)`

**Логика:**
1. Проверка существующей оценки
2. Если есть — обновление `rating`
3. Если нет — создание новой записи с уникальным `ratingId`
4. Конкатенация через `pd.concat()`

**Важно:** Изменения в `db.data` сохраняются только в памяти. Для постоянного сохранения нужно вызвать `save_db()` при выходе.

## 6. Система рекомендаций

### Адаптер

**Файл:** `Scripts/backend/recommendations_adapter.py`

**Главная функция:**
```python
get_recommendations_from_db(
    db: DataFrameDB,
    user_id: int,
    top_n: int = 5,
    method: str = 'user'
) -> list[dict]
```

**Алгоритм:**
1. Сэмплирование активных пользователей (мин. 20 оценок, макс. 5000)
2. Построение разреженной матрицы (scipy.sparse.csr_matrix)
3. Вычисление косинусного сходства (NumPy)
4. Поиск топ-20 похожих пользователей
5. Сбор рекомендаций (фильмы с рейтингом ≥4.0)
6. Исключение уже оценённых фильмов
7. Возврат топ-N рекомендаций

**Fallback:** Если пользователь новый или нет похожих — популярные фильмы.

### Интеграция в GUI

**Кэширование:**
- `self.recommendations_cache = None` — сброс кэша
- Загрузка при первом открытии раздела
- Обновление после действий пользователя

**Удаление карточки:**
```python
self.recommendations_cache = [
    rec for rec in self.recommendations_cache
    if rec['movieId'] != movie['movieId']
]
self._render_recommendation_feed()
```

## 7. Конфигурация

### Файлы конфигурации

**app_settings.ini:**
```ini
[ui]
title = Рекомендательная система фильмов
theme = dark
font_family = Segoe UI
font_size = 11
window_width = 1200
window_height = 760

[paths]
data_dir = Data
graphics_dir = Graphics
output_dir = Output
notes_dir = Notes
```

**Загрузка:**
```python
from Scripts.config import load_config, save_config

config = load_config()  # Создаёт файл, если не существует
title = config['ui']['title']
data_dir = config['paths']['data_dir']
```

**Редактирование в GUI:**
- Окно настроек: `show_settings()`
- Сохранение: `save_config(self.config_data)`
- Требует перезапуск для полного применения

## 8. Работа с изображениями

### Отображение графиков

**Метод:** `_show_image(path: Path)`

**Использует PIL/Pillow:**
```python
from PIL import Image, ImageTk

img = Image.open(path)
img.thumbnail((1000, 600), Image.Resampling.LANCZOS)
photo = ImageTk.PhotoImage(img)
self.image_label.config(image=photo)
self.current_photo = photo  # Сохраняем ссылку!
```

**Важно:** Нужно сохранять ссылку на `PhotoImage` в атрибуте класса, иначе изображение будет удалено garbage collector'ом.

**Поддерживаемые форматы:** PNG, JPG, JPEG, GIF

### Пути к файлам

Всегда используйте `Path` из `pathlib`:
```python
from pathlib import Path

output_dir = Path(config['paths']['output_dir'])
report_path = output_dir / 'report.txt'
```

### Шрифты

Используйте кроссплатформенные семейства:
- `Segoe UI` (Windows)
- `Helvetica` (macOS)
- `Arial` (универсальный fallback)

## 9. Добавление новых функций

### Новый раздел навигации

1. **Добавить кнопку в nav_items:**
```python
nav_items = [
    ...,
    ("Мой раздел", self.show_my_section),
]
```

2. **Создать метод отображения:**
```python
def show_my_section(self) -> None:
    self.current_section = "my_section"
    self.content_title.config(text="Мой раздел")
    self.content_subtitle.config(text="Описание")
    # Ваш контент здесь
```

### Новая таблица в справочниках

1. **Обновить `CrudWindow.__init__()`:**
```python
elif table == "MyTable":
    self.columns = ["id", "name"]
    self.labels = ["ID", "Название"]
```

2. **Добавить маппинг в `DataFrameDB.fetch_all()`:**
```python
table_map = {
    ...,
    "MyTable": "my_table",
}
```

### Новый отчёт

1. **Добавить функцию генерации в `reports_generator.py`**
2. **Вызвать в `generate_text_reports()` или `generate_graphics_reports()`**
3. Отчёт автоматически появится в списке

**Автор:** Воронков Илья  


