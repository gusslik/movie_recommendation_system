import pandas as pd

# Библиотека для работы с файлами

# Сохраняет данные из DataFrame-ов в бинарные файлы, 
# чтобы новые данные можно было использовать при повторном запуске программы
def save_db(df: pd.DataFrame, filepath: str):
    df.to_pickle(filepath)

# Загружает данные из бинарного файла
def load_db(filepath: str) -> pd.DataFrame:
    df = pd.read_pickle(filepath)

    return df
