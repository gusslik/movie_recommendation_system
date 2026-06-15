# Руководство разработчика: backend

## Обзор

Модуль предоставляет две вспомогательные функции для сохранения и загрузки `DataFrame`-ов pandas на диск в бинарном формате (pickle). Это позволяет сохранять изменения базы данных между запусками программы.

---

## Зависимости

Все зависимости проекта перечислены в файле `requirements.txt`. Для установки выполните:

```bash
pip install -r requirements.txt
```

---

## API

### `save_db(df, filepath)`

Сохраняет `DataFrame` в бинарный файл формата pickle.

**Сигнатура:**
```python
def save_db(df: pd.DataFrame, filepath: str) -> None
```

**Параметры:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `df` | `pd.DataFrame` | DataFrame для сохранения |
| `filepath` | `str` | Путь к файлу на диске (например, `"data/users.pkl"`) |

**Возвращает:** `None`

**Пример использования:**
```python
import pandas as pd
from persistence import save_db

db = {
    "users": pd.DataFrame({"userId": [1, 2, 3]}),
    "movies": pd.DataFrame({"movieId": [10, 20], "title": ["Inception", "Dune"]}),
}

# Сохраняем каждую таблицу отдельно
save_db(db["users"], "data/users.pkl")
save_db(db["movies"], "data/movies.pkl")
```

---

### `load_db(filepath)`

Загружает `DataFrame` из бинарного файла pickle.

**Сигнатура:**
```python
def load_db(filepath: str) -> pd.DataFrame
```

**Параметры:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `filepath` | `str` | Путь к файлу на диске (например, `"data/users.pkl"`) |

**Возвращает:** `pd.DataFrame`

**Пример использования:**
```python
from persistence import load_db

users = load_db("data/users.pkl")
movies = load_db("data/movies.pkl")

# Восстанавливаем словарь db
db = {
    "users": users,
    "movies": movies,
}
```

---

## Интеграция с основным модулем

Функции предназначены для совместной работы со словарём `db`, который формируется функцией `convert_to_3nf()`. Рекомендуемый паттерн — сохранять и загружать каждую таблицу отдельно.

### Сохранение всей базы данных

```python
import os

TABLES = ["users", "movies", "genres", "movie-genre", "ratings", "tags"]
DATA_DIR = "data"

def save_all(db: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    for table_name in TABLES:
        filepath = os.path.join(DATA_DIR, f"{table_name}.pkl")
        save_db(db[table_name], filepath)
    print("База данных сохранена.")
```

### Загрузка всей базы данных

```python
def load_all() -> dict:
    db = {}
    for table_name in TABLES:
        filepath = os.path.join(DATA_DIR, f"{table_name}.pkl")
        db[table_name] = load_db(filepath)
    print("База данных загружена.")
    return db
```

### Типичный сценарий запуска

```python
DATA_DIR = "data"

if os.path.exists(os.path.join(DATA_DIR, "users.pkl")):
    # Файлы уже есть — загружаем с диска
    db = load_all()
else:
    # Первый запуск — скачиваем и инициализируем
    raw = load_data_csv(DATA_DIR_PATH)
    db = convert_to_3nf(raw)
    save_all(db)
```

---

## Формат файлов

Функции используют `pandas.DataFrame.to_pickle` / `pandas.read_pickle`, которые сериализуют данные в бинарный формат pickle.

**Особенности:**
- Файлы бинарные и не читаются как CSV/JSON.
- Рекомендуется использовать расширение `.pkl`.
- Формат зависит от версии pandas — файлы, созданные в одной версии, могут не читаться в другой (актуально при обновлении окружения).
- Файлы не подходят для передачи данных между разными системами; для этого лучше использовать CSV или Parquet.

---

## Обработка ошибок

Функции не содержат явной обработки исключений. При работе с ними возможны следующие ошибки:

| Ситуация | Исключение | Рекомендация |
|----------|------------|--------------|
| Файл не найден при загрузке | `FileNotFoundError` | Проверять наличие файла перед загрузкой |
| Нет прав на запись | `PermissionError` | Проверять права доступа к директории |
| Несовместимая версия pickle | `UnpicklingError` | Пересоздать файлы после обновления pandas |

Пример защитной загрузки:

```python
def safe_load(filepath: str) -> pd.DataFrame | None:
    try:
        return load_db(filepath)
    except FileNotFoundError:
        print(f"Файл не найден: {filepath}")
        return None
    except Exception as e:
        print(f"Ошибка загрузки {filepath}: {e}")
        return None
```

---

## Связанные модули

| Функция | Модуль | Описание |
|---------|--------|----------|
| `convert_to_3nf(raw)` | `main` | Формирует словарь `db` из сырых CSV-данных |
| `add_new_user(db)` | `main` | Добавляет пользователя; после вызова рекомендуется `save_db` |
| `delete_user(db, user_id)` | `main` | Удаляет пользователя; после вызова рекомендуется `save_db` |
| `add_new_rating(db, ...)` | `main` | Добавляет оценку; после вызова рекомендуется `save_db` |
| `delete_rating(db, rating_id)` | `main` | Удаляет оценку; после вызова рекомендуется `save_db` |
