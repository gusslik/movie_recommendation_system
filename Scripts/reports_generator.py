"""
Генератор отчетов для рекомендательной системы
Использует функции из Library/stats_reports.py и Library/plot_reports.py
"""
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from Library.stats_reports import freq_table, descriptive_stats
from Library.plot_reports import clustered_bar


def generate_text_reports(db, output_dir: Path):
    """
    Генерирует текстовые отчеты и сохраняет в папку Output/

    Parameters:
        db: экземпляр DataFrameDB
        output_dir: путь к папке Output/
    """
    output_dir.mkdir(exist_ok=True)

    movies = db.data['movies']
    ratings = db.data['ratings']
    genres = db.data['genres']
    movie_genre = db.data['movie_genre']

    # Отчет 1: Общая статистика
    report1 = []
    report1.append("=" * 60)
    report1.append("ОБЩАЯ СТАТИСТИКА СИСТЕМЫ")
    report1.append("=" * 60)
    report1.append(f"\nВсего фильмов: {len(movies)}")
    report1.append(f"Всего пользователей: {ratings['userId'].nunique()}")
    report1.append(f"Всего оценок: {len(ratings)}")
    report1.append(f"Всего жанров: {len(genres)}")
    report1.append(f"\nСредняя оценка: {ratings['rating'].mean():.2f}")
    report1.append(f"Медианная оценка: {ratings['rating'].median():.2f}")
    report1.append(f"Стандартное отклонение: {ratings['rating'].std():.2f}")

    with open(output_dir / "01_общая_статистика.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(report1))

    # Отчет 2: Топ-20 самых популярных фильмов
    popular = ratings.groupby('movieId').size().reset_index(name='count')
    popular = popular.sort_values('count', ascending=False).head(20)
    popular = popular.merge(movies[['movieId', 'title']], on='movieId')

    report2 = []
    report2.append("=" * 60)
    report2.append("ТОП-20 САМЫХ ПОПУЛЯРНЫХ ФИЛЬМОВ")
    report2.append("(по количеству оценок)")
    report2.append("=" * 60)
    report2.append("")

    for idx, row in popular.iterrows():
        report2.append(f"{row['title']:<50} {row['count']:>8} оценок")

    with open(output_dir / "02_популярные_фильмы.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(report2))

    # Отчет 3: Топ-20 лучших фильмов (по среднему рейтингу, минимум 100 оценок)
    best = ratings.groupby('movieId').agg({'rating': ['mean', 'count']}).reset_index()
    best.columns = ['movieId', 'avg_rating', 'count']
    best = best[best['count'] >= 100]
    best = best.sort_values('avg_rating', ascending=False).head(20)
    best = best.merge(movies[['movieId', 'title']], on='movieId')

    report3 = []
    report3.append("=" * 60)
    report3.append("ТОП-20 ЛУЧШИХ ФИЛЬМОВ")
    report3.append("(средний рейтинг, минимум 100 оценок)")
    report3.append("=" * 60)
    report3.append("")

    for idx, row in best.iterrows():
        report3.append(f"{row['title']:<45} {row['avg_rating']:>6.2f} ★  ({int(row['count'])} оценок)")

    with open(output_dir / "03_лучшие_фильмы.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(report3))

    # Отчет 4: Распределение жанров
    genre_counts = movie_genre.groupby('genreId').size().reset_index(name='count')
    genre_counts = genre_counts.merge(genres[['genreId', 'genreName']], on='genreId')
    genre_counts = genre_counts.sort_values('count', ascending=False)

    report4 = []
    report4.append("=" * 60)
    report4.append("РАСПРЕДЕЛЕНИЕ ФИЛЬМОВ ПО ЖАНРАМ")
    report4.append("=" * 60)
    report4.append("")

    for idx, row in genre_counts.iterrows():
        report4.append(f"{row['genreName']:<30} {row['count']:>8} фильмов")

    with open(output_dir / "04_жанры.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(report4))

    # Отчет 5: Описательная статистика оценок
    stats = descriptive_stats(ratings, ['rating'])

    report5 = []
    report5.append("=" * 60)
    report5.append("ОПИСАТЕЛЬНАЯ СТАТИСТИКА ОЦЕНОК")
    report5.append("=" * 60)
    report5.append("")
    report5.append(stats.to_string())

    with open(output_dir / "05_статистика_оценок.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(report5))

    print(f"✓ Создано 5 текстовых отчетов в {output_dir}")


def generate_graphics_reports(db, graphics_dir: Path):
    """
    Генерирует графические отчеты и сохраняет в папку Graphics/

    Parameters:
        db: экземпляр DataFrameDB
        graphics_dir: путь к папке Graphics/
    """
    graphics_dir.mkdir(exist_ok=True)

    ratings = db.data['ratings']
    movies = db.data['movies']
    genres = db.data['genres']
    movie_genre = db.data['movie_genre']

    # График 1: Распределение оценок
    plt.figure(figsize=(10, 6))
    ratings['rating'].value_counts().sort_index().plot(kind='bar', color='steelblue')
    plt.title('Распределение оценок фильмов', fontsize=14, fontweight='bold')
    plt.xlabel('Оценка')
    plt.ylabel('Количество')
    plt.xticks(rotation=0)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(graphics_dir / '01_распределение_оценок.png', dpi=150)
    plt.close()

    # График 2: Топ-15 жанров по количеству фильмов
    genre_counts = movie_genre.groupby('genreId').size().reset_index(name='count')
    genre_counts = genre_counts.merge(genres[['genreId', 'genreName']], on='genreId')
    genre_counts = genre_counts.sort_values('count', ascending=True).tail(15)

    plt.figure(figsize=(10, 8))
    plt.barh(genre_counts['genreName'], genre_counts['count'], color='coral')
    plt.title('Топ-15 жанров по количеству фильмов', fontsize=14, fontweight='bold')
    plt.xlabel('Количество фильмов')
    plt.ylabel('Жанр')
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig(graphics_dir / '02_топ_жанры.png', dpi=150)
    plt.close()

    # График 3: Активность пользователей (количество оценок)
    user_activity = ratings.groupby('userId').size()

    plt.figure(figsize=(10, 6))
    plt.hist(user_activity, bins=50, color='green', alpha=0.7, edgecolor='black')
    plt.title('Распределение активности пользователей', fontsize=14, fontweight='bold')
    plt.xlabel('Количество оценок на пользователя')
    plt.ylabel('Количество пользователей')
    plt.yscale('log')
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(graphics_dir / '03_активность_пользователей.png', dpi=150)
    plt.close()

    # График 4: Box plot оценок
    plt.figure(figsize=(8, 6))
    ratings.boxplot(column='rating', vert=True, patch_artist=True)
    plt.title('Box Plot распределения оценок', fontsize=14, fontweight='bold')
    plt.ylabel('Оценка')
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(graphics_dir / '04_boxplot_оценок.png', dpi=150)
    plt.close()

    print(f"✓ Создано 4 графических отчета в {graphics_dir}")


def generate_all_reports(db, output_dir: Path, graphics_dir: Path):
    """
    Генерирует все отчеты (текстовые и графические)

    Parameters:
        db: экземпляр DataFrameDB
        output_dir: путь к папке Output/
        graphics_dir: путь к папке Graphics/
    """
    print("Генерация отчетов...")
    generate_text_reports(db, output_dir)
    generate_graphics_reports(db, graphics_dir)
    print("✓ Все отчеты успешно созданы!")
