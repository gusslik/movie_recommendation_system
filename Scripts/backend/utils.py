import pandas as pd
from os import path, getcwd

DATA_DIR_PATH = path.join(getcwd(), "Data")

#Формирует DataFrame-ы с сырыми данными из csv файлов в папке Data/
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
        "genres": sorted(genres_split)
    })

    genre_map = dict(zip(genres["genres"], genres["genreId"]))

    movie_genre_rows = []

    for row in movies_raw.itertuples(index=False):
        for genre_name in row.genres.split('|'):
            movie_genre_rows.append({
                "movieId": row.movieId,
                "genreId": genre_map[genre_name]
            })

    movie_genre = pd.DataFrame(movie_genre_rows)

    ratings: pd.DataFrame = ratings_raw
    ratings["ratingId"] = range(1, len(ratings_raw) + 1)

    tags: pd.DataFrame = tags_raw
    tags["tagId"] = range(1, len(tags_raw) + 1)

    print(movie_genre) 

    
    
convert_to_3nf(load_data_csv(DATA_DIR_PATH))