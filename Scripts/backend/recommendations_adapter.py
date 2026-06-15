"""
Адаптер для интеграции системы рекомендаций в GUI приложение
Использует функции из Library/recommendations.py
Оптимизирован для работы с большими датасетами
"""
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix


def sample_active_users(ratings_df, min_ratings=20, max_users=10000):
    """Выбирает активных пользователей для ускорения расчётов"""
    user_counts = ratings_df.groupby('userId').size()
    active_users = user_counts[user_counts >= min_ratings].index

    if len(active_users) > max_users:
        active_users = active_users[:max_users]

    return ratings_df[ratings_df['userId'].isin(active_users)]


def build_sparse_matrix(ratings_df):
    """Создаёт разреженную матрицу пользователь-фильм"""
    user_ids = ratings_df['userId'].unique()
    movie_ids = ratings_df['movieId'].unique()

    user_to_idx = {uid: idx for idx, uid in enumerate(user_ids)}
    movie_to_idx = {mid: idx for idx, mid in enumerate(movie_ids)}

    rows = ratings_df['userId'].map(user_to_idx).values
    cols = ratings_df['movieId'].map(movie_to_idx).values
    data = ratings_df['rating'].values

    sparse_matrix = csr_matrix((data, (rows, cols)),
                               shape=(len(user_ids), len(movie_ids)))

    return sparse_matrix, user_ids, movie_ids


def cosine_similarity_numpy(matrix1, matrix2):
    """
    Вычисляет косинусное сходство на чистом NumPy
    """
    # Нормализуем векторы
    norms1 = np.linalg.norm(matrix1, axis=1, keepdims=True)
    norms2 = np.linalg.norm(matrix2, axis=1, keepdims=True)

    mat1_norm = matrix1 / np.where(norms1 == 0, 1, norms1)
    mat2_norm = matrix2 / np.where(norms2 == 0, 1, norms2)

    # Вычисляем скалярное произведение
    similarity = np.dot(mat1_norm, mat2_norm.T)

    return similarity


def get_user_based_recommendations_sparse(user_id, sparse_matrix, user_ids,
                                         movie_ids, movies_df, ratings_df, top_n=5):
    """
    Возвращает user-based рекомендации
    """
    user_in_sample = user_id in user_ids

    # Получаем все оценённые фильмы
    user_rated_movies = set(ratings_df[ratings_df['userId'] == user_id]['movieId'].values)
    print(f"Пользователь {user_id} уже оценил {len(user_rated_movies)} фильмов")

    if not user_in_sample or len(user_rated_movies) == 0:
        print(f"Пользователь не в выборке или нет оценок, показываем популярные фильмы")
        return get_popular_movies(ratings_df, movies_df, top_n, exclude_movies=user_rated_movies)

    user_idx = np.where(user_ids == user_id)[0][0]

    # Вычисляем косинусное сходство
    user_vector = sparse_matrix[user_idx:user_idx+1].toarray()
    all_users = sparse_matrix.toarray()
    similarities = cosine_similarity_numpy(user_vector, all_users).flatten()

    # Находим похожих пользователей
    similar_indices = np.argsort(similarities)[::-1][1:21]
    similar_scores = similarities[similar_indices]

    positive_mask = similar_scores > 0
    similar_indices = similar_indices[positive_mask]
    similar_scores = similar_scores[positive_mask]

    if len(similar_indices) == 0:
        return get_popular_movies(ratings_df, movies_df, top_n, exclude_movies=user_rated_movies)

    # Собираем рекомендации
    recommendations = {}
    for sim_idx, sim_score in zip(similar_indices, similar_scores):
        sim_user_movies = sparse_matrix[sim_idx].toarray().flatten()
        good_movies_idx = np.where(sim_user_movies >= 4.0)[0]

        for movie_idx in good_movies_idx:
            movie_id = movie_ids[movie_idx]
            if movie_id in user_rated_movies:
                continue

            if movie_id not in recommendations:
                recommendations[movie_id] = 0.0
            recommendations[movie_id] += sim_score * sim_user_movies[movie_idx]

    print(f"Найдено {len(recommendations)} кандидатов для рекомендаций")

    if not recommendations:
        return get_popular_movies(ratings_df, movies_df, top_n, exclude_movies=user_rated_movies)

    sorted_recs = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)[:top_n]
    rec_df = pd.DataFrame(sorted_recs, columns=['movieId', 'score'])
    rec_df = rec_df.merge(movies_df[['movieId', 'title']], on='movieId')

    print(f"Возвращаем {len(rec_df)} рекомендаций")
    return rec_df[['movieId', 'title', 'score']]


def get_popular_movies(ratings_df, movies_df, top_n=5, exclude_movies=None):
    """
    Возвращает популярные фильмы
    """
    if exclude_movies is None:
        exclude_movies = set()

    pop = ratings_df.groupby('movieId').agg({
        'rating': ['count', 'mean']
    }).reset_index()
    pop.columns = ['movieId', 'count', 'avg_rating']

    pop = pop[~pop['movieId'].isin(exclude_movies)]
    pop = pop[(pop['count'] >= 100) & (pop['avg_rating'] >= 4.0)]
    pop = pop.sort_values(['count', 'avg_rating'], ascending=False).head(top_n)

    pop = pop.merge(movies_df[['movieId', 'title']], on='movieId')
    pop['score'] = 0.0
    return pop[['movieId', 'title', 'score']]


def get_recommendations_from_db(db, user_id, top_n=5, method='user'):
    """
    Главная функция для получения рекомендаций из DataFrameDB
    """
    try:
        print(f"Загрузка рекомендаций для пользователя {user_id}...")

        movies_data = db.data.get('movies')
        ratings_data = db.data.get('ratings')
        genres_data = db.data.get('genres')
        movie_genre_data = db.data.get('movie_genre')

        if movies_data.empty or ratings_data.empty:
            print("Нет данных для рекомендаций")
            return []

        print(f"Датасет: {len(ratings_data)} оценок, {ratings_data['userId'].nunique()} пользователей")

        # Сэмплируем активных пользователей
        sampled_ratings = sample_active_users(ratings_data, min_ratings=20, max_users=5000)
        print(f"Отобрано активных пользователей: {sampled_ratings['userId'].nunique()}")

        if method == 'user' and user_id in sampled_ratings['userId'].values:
            print("Построение разреженной матрицы...")
            sparse_matrix, user_ids, movie_ids = build_sparse_matrix(sampled_ratings)

            print("Вычисление рекомендаций...")
            rec_df = get_user_based_recommendations_sparse(
                user_id=user_id,
                sparse_matrix=sparse_matrix,
                user_ids=user_ids,
                movie_ids=movie_ids,
                movies_df=movies_data,
                ratings_df=ratings_data,
                top_n=top_n
            )
        else:
            print("Использование популярных фильмов...")
            rec_df = get_popular_movies(ratings_data, movies_data, top_n,
                                       exclude_movies=set(ratings_data[ratings_data['userId'] == user_id]['movieId'].values))

        # Добавляем информацию о жанрах
        recommendations = []
        for _, row in rec_df.iterrows():
            movie_id = row['movieId']

            movie_genres = movie_genre_data[movie_genre_data['movieId'] == movie_id]
            genre_ids = movie_genres['genreId'].tolist()
            genre_names = genres_data[genres_data['genreId'].isin(genre_ids)]['genreName'].tolist()
            genres_str = ', '.join(genre_names[:3]) if genre_names else 'Unknown'

            title = row['title']
            year = 'N/A'
            if '(' in title and ')' in title:
                year = title[title.rfind('(')+1:title.rfind(')')]

            reason = "Высокий рейтинг у похожих пользователей" if method == 'user' else "Популярный фильм"

            recommendations.append({
                'movieId': int(movie_id),
                'title': title.rsplit('(', 1)[0].strip() if '(' in title else title,
                'year': year,
                'genres': genres_str,
                'score': float(row['score']) if 'score' in row else 0.0,
                'reason': reason
            })

        print(f"Сформировано {len(recommendations)} рекомендаций")
        return recommendations

    except Exception as e:
        print(f"Ошибка при формировании рекомендаций: {e}")
        import traceback
        traceback.print_exc()
        return []
