from __future__ import annotations

import pandas as pd


class DataFrameDB:
    """Класс для работы с данными MovieLens через pandas DataFrame"""

    def __init__(self, movielens_data: dict) -> None:
        self.data = movielens_data

    def fetch_all(self, table: str, limit: int = None) -> list[dict]:
        """Возвращает все записи из таблицы в виде списка словарей"""
        table_map = {
            "Movies": "movies",
            "Users": "users",
            "Genres": "genres",
            "MovieGenre": "movie_genre",
            "Ratings": "ratings",
            "Tags": "tags"
        }

        df_key = table_map.get(table)
        if df_key and df_key in self.data:
            df = self.data[df_key]
            # Ограничиваем количество записей, если указан лимит
            if limit is not None:
                df = df.head(limit)
            # Конвертируем DataFrame в список словарей
            return df.to_dict('records')
        return []

    def stats(self) -> tuple[int, int]:
        """Возвращает количество фильмов и пользователей"""
        movies = len(self.data.get('movies', []))
        users = len(self.data.get('users', []))
        return movies, users

    def count(self, table: str) -> int:
        """Возвращает общее количество записей в таблице"""
        table_map = {
            "Movies": "movies",
            "Users": "users",
            "Genres": "genres",
            "MovieGenre": "movie_genre",
            "Ratings": "ratings",
            "Tags": "tags"
        }

        df_key = table_map.get(table)
        if df_key and df_key in self.data:
            return len(self.data[df_key])
        return 0

    def close(self) -> None:
        """Заглушка для совместимости с SQLite API"""
        pass
