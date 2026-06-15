# Library/stats_reports.py
# Автор: Гордеева Анастасия
import pandas as pd
import os


def freq_table(df, column):
    """
    Строит таблицу частот для качественной переменной.

    Parameters:
        df (pd.DataFrame): Исходные данные.
        column (str): Имя категориального столбца.

    Returns:
        pd.DataFrame: Три колонки: Category, Frequency, Percentage.

    Author:
        Gordeeva Anastasia
    """
    if column not in df.columns:
        raise KeyError(f"Столбец '{column}' отсутствует в DataFrame")
    freq = df[column].value_counts().reset_index()
    freq.columns = ['Category', 'Frequency']
    total = len(df)
    freq['Percentage'] = (freq['Frequency'] / total) * 100
    return freq


def descriptive_stats(df, columns):
    """
    Возвращает описательные статистики для количественных переменных.

    Parameters:
        df (pd.DataFrame): Данные.
        columns (list): Список имён числовых столбцов.

    Returns:
        pd.DataFrame: Строки – переменные,
        столбцы – статистики (Min, Max, Mean, Variance, Std).

    Author:
        Gordeeva Anastasia
    """
    stats_list = []
    for col in columns:
        if col not in df.columns:
            continue
        data = df[col].dropna()
        if data.empty:
            stats = {
                'Variable': col,
                'Min': None,
                'Max': None,
                'Mean': None,
                'Variance': None,
                'Std': None
            }
        else:
            stats = {
                'Variable': col,
                'Min': data.min(),
                'Max': data.max(),
                'Mean': data.mean(),
                'Variance': data.var(ddof=1),
                'Std': data.std(ddof=1)
            }
        stats_list.append(stats)
    return pd.DataFrame(stats_list)


def pivot_report(df, index_col, columns_col, values_col, aggfunc='mean'):
    """
    Строит сводную таблицу для двух качественных атрибутов.

    Parameters:
        df (pd.DataFrame): Данные.
        index_col (str): Столбец, который станет строками.
        columns_col (str): Столбец, который станет столбцами.
        values_col (str): Столбец со значениями (числовой).
        aggfunc (str): Функция агрегации ('mean', 'sum', 'count', ...).

    Returns:
        pd.DataFrame: Сводная таблица.

    Author:
        Gordeeva Anastasia
    """
    required = [index_col, columns_col, values_col]
    for col in required:
        if col not in df.columns:
            raise KeyError(f"Столбец '{col}' отсутствует в данных")
    pivot = pd.pivot_table(df,
                           index=index_col,
                           columns=columns_col,
                           values=values_col,
                           aggfunc=aggfunc)
    return pivot


def prepare_joined_data(ratings_df, users_df, movies_df):
    """
    Объединяет три таблицы (оценки, пользователи, фильмы) в одну для аналитики.

    Parameters:
        ratings_df (pd.DataFrame): Оценки.
        users_df (pd.DataFrame): Пользователи.
        movies_df (pd.DataFrame): Фильмы.

    Returns:
        pd.DataFrame: Объединённая таблица.

    Author:
        Gordeeva Anastasia
    """
    joined = ratings_df.merge(users_df, on='userId')
    joined = joined.merge(movies_df, on='movieId')
    return joined


def save_text_report(dataframe, filename, output_dir='Output/'):
    """
    Сохраняет DataFrame в CSV-файл (в папку output).

    Parameters:
        dataframe (pd.DataFrame): Данные для сохранения.
        filename (str): Имя файла (например, 'report.csv').
        output_dir (str): Путь к папке для сохранения (по умолчанию 'output/').

    Returns:
        str: Полный путь к сохранённому файлу.

    Author:
        Gordeeva Anastasia
    """
    os.makedirs(output_dir, exist_ok=True)
    full_path = os.path.join(output_dir, filename)
    dataframe.to_csv(full_path, index=False, encoding='utf-8-sig')
    return full_path
