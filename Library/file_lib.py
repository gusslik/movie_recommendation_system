import pandas as pd
import pickle

# Библиотека для работы с файлами

# Сохраняет данные из DataFrame-ов в бинарные файлы,
# чтобы новые данные можно было использовать при повторном запуске программы
def save_db(data, filepath: str):
    """Сохраняет DataFrame или словарь DataFrame-ов в pickle файл"""
    with open(filepath, 'wb') as f:
        pickle.dump(data, f)

# Загружает данные из бинарного файла
def load_db(filepath: str):
    """Загружает DataFrame или словарь DataFrame-ов из pickle файла"""
    with open(filepath, 'rb') as f:
        return pickle.load(f)
