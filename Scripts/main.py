from __future__ import annotations

import sys
from pathlib import Path

# Позволяет запускать приложение как: python3 Scripts/main.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Scripts.bootstrap import bootstrap_environment
from Scripts.config import load_config
from Scripts.dataframe_db import DataFrameDB
from Scripts.gui.app import MovieApp
from Scripts.backend.utils import DATA_DIR_PATH, ORIGIN_DATASET_URL, fetch_csv, load_data_csv, convert_to_3nf
from Library.file_lib import save_db, load_db
from os import path


def run() -> None:
    cfg = load_config()
    paths = bootstrap_environment()

    # Путь к pickle файлам с обработанными данными
    db_pickle_path = Path(cfg["paths"]["data_dir"]) / "movielens_db.pkl"

    # Проверяем, есть ли уже обработанные данные
    if path.exists(db_pickle_path):
        print("Загрузка обработанных данных MovieLens из кэша...")
        movielens_data = load_db(db_pickle_path)
    else:
        # Проверяем наличие датасета MovieLens
        if not path.exists(DATA_DIR_PATH):
            print("Датасет MovieLens не найден. Начинаю загрузку...")
            parent_dir = path.dirname(DATA_DIR_PATH)
            fetch_csv(parent_dir, ORIGIN_DATASET_URL)

        # Загружаем данные из CSV
        print("Загрузка данных из CSV файлов...")
        raw_data = load_data_csv(DATA_DIR_PATH)

        # Преобразуем в 3НФ
        print("Преобразование данных в 3НФ...")
        movielens_data = convert_to_3nf(raw_data)

        # Сохраняем обработанные данные
        print("Сохранение обработанных данных в кэш...")
        save_db(movielens_data, db_pickle_path)

    # Создаём обёртку для работы с DataFrame
    db = DataFrameDB(movielens_data)

    print(f"Загружено: {len(movielens_data['movies'])} фильмов, {len(movielens_data['users'])} пользователей")

    app = MovieApp(db=db, config=cfg, paths=paths)
    app.mainloop()
    db.close()


if __name__ == "__main__":
    run()
