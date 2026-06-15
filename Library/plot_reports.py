# Library/plot_reports.py
# Автор: Гордеева Анастасия
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os


def clustered_bar(df, cat_col1, cat_col2, title=None, xlabel=None,
                  ylabel=None, save_path=None):
    """
    Строит кластеризованную столбчатую диаграмму
    для двух категориальных переменных.

    Parameters:
        df (pd.DataFrame): Исходные данные.
        cat_col1 (str): Название столбца для оси X
        (первая категориальная переменная).
        cat_col2 (str): Название столбца для группировки
        (вторая категориальная переменная).
        title (str, optional): Заголовок графика.
        xlabel (str, optional): Подпись оси X.
        ylabel (str, optional): Подпись оси Y.
        save_path (str, optional): Путь для сохранения графика
        (если None – только отображение).

    Returns:
        None

    Author:
        Gordeeva Anastasia
    """

    if cat_col1 not in df.columns or cat_col2 not in df.columns:
        print(f"Ошибка: отсутствуют колонки '{cat_col1}' или '{cat_col2}'")
        return

    crosstab = pd.crosstab(df[cat_col1], df[cat_col2])

    if crosstab.empty:
        print("Нет данных для построения столбчатой диаграммы.")
        return

    ax = crosstab.plot(kind='bar', figsize=(10, 6))

    ax.set_title(title if title else f'Распределение {cat_col2} по {cat_col1}')
    ax.set_xlabel(xlabel if xlabel else cat_col1)
    ax.set_ylabel(ylabel if ylabel else 'Количество')
    ax.legend(title=cat_col2)

    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=100)
        plt.close()
    else:
        plt.show()


def categorized_hist(df, quant_col, cat_col, bins=10, alpha=0.5,
                     title=None, xlabel=None, ylabel=None, save_path=None):
    """
    Категоризированная гистограмма: распределение количественной
    переменной по группам.

    Parameters:
        df (pd.DataFrame): Данные.
        quant_col (str): Имя количественного столбца.
        cat_col (str): Имя категориального столбца.
        bins (int): Количество интервалов гистограммы.
        alpha (float): Прозрачность заливки.
        title, xlabel, ylabel, save_path – аналогично clustered_bar.

    Returns:
        None

    Author:
        Gordeeva Anastasia
    """
    if quant_col not in df.columns or cat_col not in df.columns:
        print(f"Ошибка: отсутствуют колонки '{quant_col}' или '{cat_col}'")
        return

    data = df[[quant_col, cat_col]].dropna()
    if data.empty:
        print("Нет данных для построения гистограммы.")
        return

    categories = data[cat_col].unique()
    if len(categories) == 0:
        print("Нет категорий для гистограммы.")
        return

    plt.figure(figsize=(10, 6))
    for cat in categories:
        subset = data[data[cat_col] == cat][quant_col]
        plt.hist(subset, bins=bins, alpha=alpha, label=str(cat))

    plt.legend()
    plt.title(title if title else f'Распределение {quant_col} по {cat_col}')
    plt.xlabel(xlabel if xlabel else quant_col)
    plt.ylabel(ylabel if ylabel else 'Частота')
    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=100)
        plt.close()
    else:
        plt.show()


def categorized_boxplot(df, quant_col, cat_col, title=None,
                        ylabel=None, save_path=None):
    """
    Категоризированный ящик с усами (boxplot) для количественной
    переменной по категориям.

    Parameters:
        df (pd.DataFrame): Данные.
        quant_col (str): Количественный столбец.
        cat_col (str): Категориальный столбец.
        title, ylabel, save_path – аналогично.

    Returns:
        None

    Author:
        Gordeeva Anastasia
    """
    if quant_col not in df.columns or cat_col not in df.columns:
        print(f"Ошибка: отсутствуют колонки '{quant_col}' или '{cat_col}'")
        return

    # Удаляем пропуски в обоих столбцах
    data = df[[quant_col, cat_col]].dropna()
    if data.empty:
        print("Нет данных для построения boxplot.")
        return

    categories = data[cat_col].unique()
    if len(categories) == 0:
        print("Нет категорий для boxplot.")
        return

    plt.figure(figsize=(10, 6))
    # Построение boxplot с группировкой
    data.boxplot(column=quant_col, by=cat_col, grid=False)

    plt.suptitle(title if title else f'Распределение {quant_col} по {cat_col}')
    plt.ylabel(ylabel if ylabel else quant_col)
    plt.xlabel(cat_col)
    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=100)
        plt.close()
    else:
        plt.show()


def categorized_scatter(df, x_col, y_col, cat_col,
                        title=None, xlabel=None, ylabel=None, save_path=None):
    """
    Диаграмма рассеяния (scatter) с цветовой маркировкой по категории.

    Parameters:
        df (pd.DataFrame): Данные.
        x_col (str): Столбец для оси X (количественный).
        y_col (str): Столбец для оси Y (количественный).
        cat_col (str): Столбец для цветовой маркировки (категориальный).
        title, xlabel, ylabel, save_path – аналогично.

    Returns:
        None

    Author:
        Gordeeva Anastasia
    """
    if x_col not in df.columns or y_col not in df.columns or cat_col not in df.columns:
        print(f"Ошибка: отсутствуют колонки {x_col}, {y_col} или {cat_col}")
        return

    df_clean = df[[x_col, y_col, cat_col]].dropna()
    if df_clean.empty:
        print("Нет данных для построения scatter plot.")
        return

    categories = df_clean[cat_col].unique()
    if len(categories) == 0:
        print("Нет категорий для построения scatter plot.")
        return

    if len(df_clean) < 2:
        print("Недостаточно данных для построения scatter plot (меньше 2 точек).")
        return

    plt.figure(figsize=(10, 6))
    colors = plt.cm.tab10(np.linspace(0, 1, len(categories)))

    for cat, color in zip(categories, colors):
        subset = df_clean[df_clean[cat_col] == cat]
        plt.scatter(subset[x_col], subset[y_col],
                    label=str(cat), alpha=0.6, color=color)

    plt.legend()
    plt.title(title if title else f'{y_col} vs {x_col} по категориям {cat_col}')
    plt.xlabel(xlabel if xlabel else x_col)
    plt.ylabel(ylabel if ylabel else y_col)
    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=100)
        plt.close()
    else:
        plt.show()
