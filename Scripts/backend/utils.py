import pandas as pd
import csv
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

print(load_data_csv(DATA_DIR_PATH))