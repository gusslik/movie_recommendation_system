# Library/recommendations.py
# Автор: Гордеева Анастасия
import pandas as pd
import numpy as np


def build_user_item_matrix(ratings_df):
    """
    Создаёт матрицу: строки = userId, столбцы = movieId, значения = rating.

    Parameters:
        ratings_df (pd.DataFrame): колонки 'userId', 'movieId', 'rating'.

    Returns:
        pd.DataFrame: матрица оценок (пропуски = NaN).

    Author:
        Gordeeva Anastasia
    """
    matrix = ratings_df.pivot_table(index='userId', columns='movieId',
                                    values='rating')
    return matrix


def cosine_similarity_matrix(user_item_matrix):
    """
    Вычисляет косинусное сходство между всеми парами пользователей.

    Parameters:
        user_item_matrix (pd.DataFrame): матрица оценок (индекс = userId,
                                                         столбцы = movieId).

    Returns:
        pd.DataFrame: квадратная матрица сходства (индексы = userId).

    Author:
        Gordeeva Anastasia
    """
    mat = user_item_matrix.fillna(0).values
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    mat_norm = mat / np.where(norms == 0, 1, norms)
    similarity = np.dot(mat_norm, mat_norm.T)
    sim_df = pd.DataFrame(similarity,
                          index=user_item_matrix.index,
                          columns=user_item_matrix.index)
    return sim_df


def get_user_based_recommendations(user_id, user_item_matrix,
                                   similarity_matrix,
                                   movies_df, top_n=5, ratings_df=None):
    """
    Возвращает user‑based рекомендации для пользователя.

    Parameters:
        user_id (int): ID пользователя.
        user_item_matrix (pd.DataFrame): матрица оценок.
        similarity_matrix (pd.DataFrame): матрица сходства пользователей.
        movies_df (pd.DataFrame): справочник фильмов (колонки 'movieId',
                                                      'title').
        top_n (int): количество рекомендаций.
        ratings_df (pd.DataFrame, optional): исходные оценки (для fallback).

    Returns:
        pd.DataFrame: колонки ['movieId', 'title', 'score'].

    Author:
        Gordeeva Anastasia
    """
    user_ratings = user_item_matrix.loc[user_id]
    already_rated = user_ratings.dropna().index.tolist()

    sim_series = similarity_matrix[user_id].drop(index=user_id)
    sim_series = sim_series[sim_series > 0].sort_values(ascending=False).head(20)

    recs = {}
    for other_id, sim in sim_series.items():
        other_ratings = user_item_matrix.loc[other_id].dropna()
        good_movies = other_ratings[other_ratings >= 4].index.tolist()
        for movie in good_movies:
            if movie in already_rated:
                continue
            if movie not in recs:
                recs[movie] = 0.0
            recs[movie] += sim * other_ratings[movie]

    if not recs:
        if ratings_df is None:
            from library.data_loader import load_all_data
            _, _, ratings_df = load_all_data()
        return get_popular_movies(ratings_df, movies_df, top_n)

    sorted_recs = sorted(recs.items(),
                         key=lambda x: x[1], reverse=True)[:top_n]
    rec_df = pd.DataFrame(sorted_recs, columns=['movieId', 'score'])
    rec_df = rec_df.merge(movies_df[['movieId', 'title']], on='movieId')
    return rec_df[['movieId', 'title', 'score']]


def build_item_item_similarity(user_item_matrix):
    """
    Строит матрицу косинусного сходства между фильмами (item‑based).

    Parameters:
        user_item_matrix (pd.DataFrame): матрица оценок.

    Returns:
        pd.DataFrame: квадратная матрица сходства фильмов (индексы = movieId).

    Author:
        Gordeeva Anastasia
    """
    item_matrix = user_item_matrix.T
    return cosine_similarity_matrix(item_matrix)


def get_item_based_recommendations(user_id, user_item_matrix, item_sim_matrix,
                                   movies_df, top_n=5):
    """
    Возвращает item‑based рекомендации для пользователя.

    Parameters:
        user_id (int): ID пользователя.
        user_item_matrix (pd.DataFrame): матрица оценок.
        item_sim_matrix (pd.DataFrame): матрица сходства фильмов.
        movies_df (pd.DataFrame): справочник фильмов.
        top_n (int): количество рекомендаций.

    Returns:
        pd.DataFrame: колонки ['movieId', 'title', 'score'].

    Author:
        Gordeeva Anastasia
    """
    user_ratings = user_item_matrix.loc[user_id].dropna()
    liked_movies = user_ratings[user_ratings >= 4].index.tolist()

    scores = {}
    for movie in liked_movies:
        similar = item_sim_matrix[movie].drop(index=movie).sort_values(ascending=False).head(10)
        for sim_movie, sim in similar.items():
            if sim_movie in user_ratings.index:
                continue
            scores[sim_movie] = scores.get(sim_movie, 0.0) + sim * user_ratings[movie]

    if not scores:
        from library.data_loader import load_all_data
        _, _, ratings = load_all_data()
        return get_popular_movies(ratings, movies_df, top_n)

    sorted_recs = sorted(scores.items(),
                         key=lambda x: x[1], reverse=True)[:top_n]
    rec_df = pd.DataFrame(sorted_recs, columns=['movieId', 'score'])
    rec_df = rec_df.merge(movies_df[['movieId', 'title']], on='movieId')
    return rec_df


def get_popular_movies(ratings_df, movies_df, top_n=5):
    """
    Возвращает топ‑N самых популярных фильмов (по количеству оценок).

    Parameters:
        ratings_df (pd.DataFrame): оценки.
        movies_df (pd.DataFrame): фильмы.
        top_n (int): количество.

    Returns:
        pd.DataFrame: колонки ['movieId', 'title', 'score'] (score = 0).

    Author:
        Gordeeva Anastasia
    """
    pop = ratings_df.groupby('movieId').size().reset_index(name='count')
    pop = pop.sort_values('count', ascending=False).head(top_n)
    pop = pop.merge(movies_df[['movieId', 'title']], on='movieId')
    pop['score'] = 0.0
    return pop[['movieId', 'title', 'score']]


def user_similarity_matrix(ratings_matrix: pd.DataFrame) -> pd.DataFrame:
    """
    Обёртка: вычисляет матрицу косинусного сходства пользователей.

    Parameters:
        ratings_matrix (pd.DataFrame): матрица оценок.

    Returns:
        pd.DataFrame: матрица сходства пользователей.

    Author:
        Gordeeva Anastasia
    """
    return cosine_similarity_matrix(ratings_matrix)


def item_similarity_matrix(ratings_matrix: pd.DataFrame) -> pd.DataFrame:
    """
    Обёртка: вычисляет матрицу сходства фильмов (item‑based).

    Parameters:
        ratings_matrix (pd.DataFrame): матрица оценок.

    Returns:
        pd.DataFrame: матрица сходства фильмов.

    Author:
        Gordeeva Anastasia
    """
    return build_item_item_similarity(ratings_matrix)


def get_recommendations(user_id: int, top_n: int = 5,
                        method: str = 'user') -> pd.DataFrame:
    """
    Главная функция для получения рекомендаций.

    Parameters:
        user_id (int): ID пользователя.
        top_n (int): количество рекомендаций.
        method (str): 'user' или 'item'.

    Returns:
        pd.DataFrame: колонки ['movieId', 'title', 'score'].
        При ошибке загрузки данных возвращает пустой DataFrame с сообщением.

    Author:
        Gordeeva Anastasia
    """
    try:
        from library.data_loader import load_all_data
        movies, _, ratings = load_all_data()
    except Exception as e:
        print(f"Ошибка загрузки данных: {e}")
        return pd.DataFrame(columns=['movieId', 'title', 'score'])

    if movies.empty or ratings.empty:
        print("Нет данных для формирования рекомендаций.")
        return pd.DataFrame(columns=['movieId', 'title', 'score'])

    matrix = build_user_item_matrix(ratings)

    if method == 'user':
        sim_matrix = cosine_similarity_matrix(matrix)
        return get_user_based_recommendations(
            user_id=user_id,
            user_item_matrix=matrix,
            similarity_matrix=sim_matrix,
            movies_df=movies,
            top_n=top_n
        )
    elif method == 'item':
        item_sim = build_item_item_similarity(matrix)
        return get_item_based_recommendations(
            user_id=user_id,
            user_item_matrix=matrix,
            item_sim_matrix=item_sim,
            movies_df=movies,
            top_n=top_n
        )
    else:
        raise ValueError("method должен быть 'user' или 'item'")
