import pandas as pd
from os import path, getcwd, getenv, remove
import requests
import zipfile
from dotenv import load_dotenv

load_dotenv()


ORIGIN_DATASET_URL = getenv("ORIGIN_DATASET_URL")
ARCHIVE_NAME = getenv("ARCHIVE_NAME")

# Путь до директории с датасетом
DATA_DIR_PATH = path.join(getcwd(), "Data", ARCHIVE_NAME)

# Скачивает csv файлы, обращаясь по url
def fetch_csv(filepath: str, url: str):
    print("Идет скачивание архива...")
    res = requests.get(url)

    archive_name = "archive.zip"
    with open(archive_name, "wb") as archive:
        archive.write(res.content)

    print("Распаковка архива...")
    with zipfile.ZipFile(archive_name, "r") as zip:
        zip.extractall(filepath)

    print("Архив распакован...")
    remove(archive_name)

# Формирует DataFrame-ы с сырыми данными из csv файлов в папке Data/
def load_data_csv(filepath: str) -> dict:
    FILEPATH_MOVIES_CSV = path.join(filepath, 'movies.csv')
    FILEPATH_RATINGS_CSV = path.join(filepath, 'ratings.csv')
    FILEPATH_TAGS_CSV = path.join(filepath, 'tags.csv')

    movies_csv_raw = pd.read_csv(FILEPATH_MOVIES_CSV)
    ratings_csv_raw = pd.read_csv(FILEPATH_RATINGS_CSV)
    tags_csv_raw = pd.read_csv(FILEPATH_TAGS_CSV)

    raw = {
        "movies": movies_csv_raw,
        "ratings": ratings_csv_raw,
        "tags" : tags_csv_raw
    }

    return raw

# Форматирует сырые данные из load_data_csv и формирует таблицы в 3нф
def convert_to_3nf(raw: dict) -> dict:
    movies_raw = raw['movies']
    ratings_raw = raw['ratings']
    tags_raw = raw['tags']

    unique_users = set()
    for value in ratings_raw["userId"]:
        unique_users.add(value)

    users = pd.DataFrame({
        "userId": sorted(unique_users)
    })

    movies = movies_raw[["movieId", "title"]]

    genres_split = set()
    for value in movies_raw["genres"]:
        genres_split.update(value.split('|'))

    genres = pd.DataFrame({
        "genreId": range(1, len(genres_split) + 1),
        "genreName": sorted(genres_split)
    })

    genre_map = dict(zip(genres["genreName"], genres["genreId"]))

    movie_genre_rows = []

    for row in movies_raw.itertuples(index=False):
        for genre_name in row.genres.split('|'):
            movie_genre_rows.append({
                "movieId": row.movieId,
                "genreId": genre_map[genre_name]
            })

    movie_genre = pd.DataFrame(movie_genre_rows)

    ratings: pd.DataFrame = ratings_raw[["userId", "movieId", "rating"]]
    ratings["ratingId"] = range(1, len(ratings_raw) + 1)

    tags: pd.DataFrame = tags_raw[["userId", "movieId", "tag"]]
    tags["tagId"] = range(1, len(tags_raw) + 1)


    db = {
        "users": users,
        "movies": movies,
        "genres": genres,
        "movie_genre": movie_genre,
        "ratings": ratings,
        "tags": tags
    }

    return db

def add_new_user(db: dict) -> int:
    users = db["users"]

    new_user_id = users["userId"].max() + 1

    if new_user_id in users["userId"].values:
        raise ValueError(f"Пользователь с ID {new_user_id} уже существует")

    new_user = pd.DataFrame({"userId": [new_user_id]})

    db["users"] = pd.concat([users, new_user], ignore_index=True)

    print(f"Пользователь с ID {new_user_id} успешно добавлен")

    return new_user_id

def delete_user(db: dict, user_id: int) -> bool:
    users = db["users"]

    if user_id not in users["userId"].values:
        raise ValueError(f"Пользователь с ID {user_id} не найден")

    db["users"] = users[users["userId"] != user_id]
    db["ratings"] = db["ratings"][db["ratings"]["userId"] != user_id]
    db["tags"] = db["tags"][db["tags"]["userId"] != user_id]

    print(f"Пользователь с ID {user_id} успешно удален")

    return True

def add_new_rating(db: dict, user_id: int, movie_id: int, rating: float) -> bool:
    if(rating < 0 or rating > 5):
        raise ValueError(f"Оценка фильам должна быть в диапозоне значений 0-5")

    ratings = db["ratings"]

    if user_id not in ratings["userId"].values:
        raise ValueError(f"Пользователь с ID {user_id} не найден")

    if movie_id not in ratings["movieId"].values:
        raise ValueError(f"Пользователь с ID {user_id} не найден")

    new_rating_id = ratings["ratingId"].max() + 1

    if new_rating_id in ratings["ratingId"].values:
        raise ValueError(f"Оценка с ID {new_rating_id} уже существует")

    new_rating = pd.DataFrame({
        "ratingId": [new_rating_id],
        "userId": [user_id],
        "movieId": [movie_id],
        "rating": [rating]
    })

    db["ratings"] = pd.concat([ratings, new_rating], ignore_index=True)

    print(f"Оценка с ID {new_rating_id} успешно добавлена")

    return True

def delete_rating(db: dict, rating_id: int) -> bool:
    ratings = db["ratings"]

    if rating_id not in ratings["ratingId"].values:
        raise ValueError(f"Оценка с ID {rating_id} не найдена")

    db["ratings"] = ratings[ratings["ratingId"] != rating_id]

    print(f"Оценка с ID {rating_id} успешно удалена")

    return True
