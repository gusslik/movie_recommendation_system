# Scripts/test_integration.py
# Автор: Гордеева Анастасия
"""
Интеграционное тестирование модулей: конфигурация, загрузка данных,
построение матрицы.
"""

import sys
import os
import pandas as pd


current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)


from Library.config_loader import load_config
from Library.data_loader import load_all_data
from Library.recommendations import build_user_item_matrix


def test_config():
    """
    Проверяет загрузку конфигурационного файла.
    Убеждается, что присутствует ключ DATA_DIR и его значение равно 'data/'.
    """
    print("1. Тестирование конфигурации...")
    config = load_config()
    assert 'DATA_DIR' in config, "Нет DATA_DIR"
    assert config['DATA_DIR'] == 'Data/', "DATA_DIR не data/"
    print("   OK")


def test_data_loading():
    """
    Проверяет загрузку всех трёх справочников (фильмы, пользователи, оценки).
    Убеждается, что загружены DataFrame и присутствуют обязательные колонки.
    """
    print("2. Тестирование загрузки данных...")
    movies, users, ratings = load_all_data()
    assert isinstance(movies, pd.DataFrame), "movies не DataFrame"
    assert isinstance(users, pd.DataFrame), "users не DataFrame"
    assert isinstance(ratings, pd.DataFrame), "ratings не DataFrame"
    assert 'movieId' in movies.columns, "movies нет movieId"
    assert 'userId' in ratings.columns, "ratings нет userId"
    print(f"   Загружено: фильмов {len(movies)}, пользователей {len(users)}, "
          f"оценок {len(ratings)}")


def test_matrix_build():
    """
    Проверяет построение матрицы пользователь–фильм.
    Сравнивает размерность матрицы с количеством уникальных userId и movieId.
    """
    print("3. Тестирование построения матрицы...")
    _, _, ratings = load_all_data()
    matrix = build_user_item_matrix(ratings)
    assert (matrix.shape[0] == ratings['userId'].nunique()
            ), "Неверное число строк"
    assert (matrix.shape[1] == ratings['movieId'].nunique()
            ), "Неверное число столбцов"
    print(f"   Матрица {matrix.shape}")


if __name__ == "__main__":
    test_config()
    test_data_loading()
    test_matrix_build()
    print("Все интеграционные тесты пройдены!")
