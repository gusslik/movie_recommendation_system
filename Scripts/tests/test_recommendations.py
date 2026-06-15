# Scripts/test_recommendations.py
# Автор: Гордеева Анастасия
"""
Тестирование рекомендательной системы: популярные фильмы,
user‑based и item‑based рекомендации.
"""
import sys
import os


current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)


from Library.data_loader import load_all_data
from Library.recommendations import (
    build_user_item_matrix,
    cosine_similarity_matrix,
    get_user_based_recommendations,
    get_item_based_recommendations,
    get_popular_movies,
    build_item_item_similarity
)


def test_popular():
    """
    Проверяет функцию get_popular_movies: возвращает 3 самых популярных фильма.
    """
    print("1. Проверка популярных фильмов...")
    movies, _, ratings = load_all_data()
    pop = get_popular_movies(ratings, movies, top_n=3)
    assert len(pop) == 3, "Неверное количество"
    print("   OK")


def test_user_based():
    """
    Проверяет user‑based рекомендации.
    Убеждается, что ни один рекомендованный фильм
    не был уже оценён пользователем.
    """
    print("2. User-based рекомендации...")
    movies, _, ratings = load_all_data()
    matrix = build_user_item_matrix(ratings)
    sim = cosine_similarity_matrix(matrix)
    user_id = matrix.index[0]  # берём первого пользователя с оценками
    recs = get_user_based_recommendations(
        user_id=user_id,
        user_item_matrix=matrix,
        similarity_matrix=sim,
        movies_df=movies,
        top_n=5
    )
    user_rated = matrix.loc[user_id].dropna().index.tolist()
    for movie in recs['movieId']:
        assert movie not in user_rated, f"Рекомендован уже оценённый фильм {movie}"
    print("   OK")


def test_item_based():
    """
    Проверяет item‑based рекомендации.
    Убеждается, что в колонке score нет значений NaN.
    """
    print("3. Item-based рекомендации...")
    movies, _, ratings = load_all_data()
    matrix = build_user_item_matrix(ratings)
    item_sim = build_item_item_similarity(matrix)
    user_id = matrix.index[0]
    recs = get_item_based_recommendations(
        user_id=user_id,
        user_item_matrix=matrix,
        item_sim_matrix=item_sim,
        movies_df=movies,
        top_n=5
    )
    assert not recs['score'].isna().any(), "Есть NaN в score"
    print("   OK")


if __name__ == "__main__":
    test_popular()
    test_user_based()
    test_item_based()
    print("Все тесты рекомендаций пройдены!")
