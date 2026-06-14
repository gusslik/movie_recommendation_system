# Library/data_loader.py
# Автор: Гордеева Анастасия
import pandas as pd
import os
import pickle
from Library.config_loader import load_config


def get_project_root():
    """
    Возвращает абсолютный путь к корню проекта (папке,
                                                где находится config.ini).

    Returns:
        str: Путь к корневой папке.

    Author:
        Gordeeva Anastasia
    """
    current = os.getcwd()
    while True:
        if os.path.exists(os.path.join(current, 'config.ini')):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return os.getcwd()


PROJECT_ROOT = get_project_root()
DATA_DIR = os.path.join(PROJECT_ROOT, 'Data')
CONFIG = load_config()


def load_movies():
    """
    Загружает справочник фильмов из CSV.

    Returns:
        pd.DataFrame: DataFrame с колонками movieId,
        title, genres (и др., зависит от файла).

    Raises:
        FileNotFoundError: Если файл не найден.

    Author:
        Gordeeva Anastasia
    """
    file_name = CONFIG["DATABASE_MOVIES_FILE"]
    file_path = os.path.join(DATA_DIR, file_name)
    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Файл {file_path} не найден. Проверьте, что файл {file_name} лежит в {DATA_DIR}"
        )
    return pd.read_csv(file_path)


def load_users():
    """
    Загружает справочник пользователей.
    Предполагается формат: userId|age|gender|occupation|zip
    (без заголовка, разделитель |).

    Returns:
        pd.DataFrame: DataFrame с колонками userId, age, gender,
        occupation, zip.

    Author:
        Gordeeva Anastasia
    """
    file_name = CONFIG["DATABASE_USERS_FILE"]
    file_path = os.path.join(DATA_DIR, file_name)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл {file_path} не найден")
    df = pd.read_csv(file_path, sep='|', header=None,
                     names=['userId', 'age', 'gender', 'occupation', 'zip'])
    df['age'] = pd.to_numeric(df['age'], errors='coerce')
    return df


def load_ratings():
    """
    Загружает таблицу оценок.

    Returns:
        pd.DataFrame: DataFrame с колонками userId,
        movieId, rating (и возможно timestamp).

    Author:
        Gordeeva Anastasia
    """
    file_name = CONFIG["DATABASE_RATINGS_FILE"]
    file_path = os.path.join(DATA_DIR, file_name)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл {file_path} не найден")
    return pd.read_csv(file_path)


def load_all_data():
    """
    Загружает все три справочника (фильмы, пользователи, оценки).

    Returns:
        tuple: (movies_df, users_df, ratings_df)

    Author:
        Gordeeva Anastasia
    """
    movies = load_movies()
    users = load_users()
    ratings = load_ratings()
    return movies, users, ratings


def save_binary(dataframe, filepath):
    """
    Сохраняет DataFrame в двоичный файл (pickle).

    Parameters:
        dataframe (pd.DataFrame): Данные для сохранения.
        filepath (str): Путь к файлу (включая имя).

    Returns:
        None

    Author:
        Gordeeva Anastasia
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'wb') as f:
        pickle.dump(dataframe, f)


def load_binary(filepath):
    """
    Загружает DataFrame из двоичного файла (pickle).

    Parameters:
        filepath (str): Путь к файлу.

    Returns:
        pd.DataFrame: Загруженные данные.

    Raises:
        FileNotFoundError: Если файл не существует.

    Author:
        Gordeeva Anastasia
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Файл {filepath} не найден")
    with open(filepath, 'rb') as f:
        return pickle.load(f)
