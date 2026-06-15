# Scripts/test_stats_plots.py
# Автор: Гордеева Анастасия
"""
Тестирование статистических и графических отчётов.
Проверяет работу freq_table, descriptive_stats, pivot_report,
а также всех четырёх типов графиков.
"""
import sys
import os


current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)


from Library.data_loader import load_all_data, get_project_root
from Library.stats_reports import freq_table, descriptive_stats,pivot_report, save_text_report
from Library.plot_reports import clustered_bar, categorized_hist, categorized_boxplot, categorized_scatter


PROJECT_ROOT = get_project_root()
GRAPHICS_DIR = os.path.join(PROJECT_ROOT, 'Graphics')
os.makedirs(GRAPHICS_DIR, exist_ok=True)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'Output')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def test_stats():
    """
    Тестирует текстовые отчёты:
    - таблицу частот для пола (если есть),
    - описательные статистики для возраста,
    - сводную таблицу по полу и профессии (если есть).
    """
    print("1. Статистические отчёты...")
    movies, users, ratings = load_all_data()

    if 'gender' in users.columns:
        freq = freq_table(users, 'gender')
        assert len(freq) > 0, "freq_table пуста"
        save_text_report(freq, 'freq_gender.csv', output_dir=OUTPUT_DIR)
        print("   freq_table OK")

    if 'age' in users.columns:
        stats_age = descriptive_stats(users, ['age'])
        assert stats_age.iloc[0]['Min'] > 0, "Возраст не может быть 0"
        print("   descriptive_stats OK")

    if 'gender' in users.columns and 'occupation' in users.columns:
        pivot = pivot_report(users, 'gender', 'occupation',
                             'userId', aggfunc='count')
        assert pivot.shape[0] > 0, "pivot пуста"
        print("   pivot_report OK")


def test_plots():
    """
    Тестирует графические отчёты, сохраняя их в GRAPHICS_DIR.
    Проверяет вызов каждой функции (clustered_bar, categorized_hist,
    categorized_boxplot, categorized_scatter) без ошибок.
    """
    print("2. Графические отчёты (проверка вызова с абсолютными путями)...")
    movies, users, ratings = load_all_data()

    avg_rating = ratings.groupby('userId')['rating'].mean().reset_index()
    avg_rating.columns = ['userId', 'avg_rating']
    user_avg = users.merge(avg_rating, on='userId')

    if 'gender' in users.columns and 'occupation' in users.columns:
        path_bar = os.path.join(GRAPHICS_DIR, 'test_bar.png')
        clustered_bar(users, 'gender', 'occupation', save_path=path_bar)
        print("   clustered_bar OK")

    if 'age' in users.columns and 'gender' in users.columns:
        path_hist = os.path.join(GRAPHICS_DIR, 'test_hist.png')
        categorized_hist(users, 'age', 'gender', save_path=path_hist)
        print("   categorized_hist OK")

    if 'age' in users.columns and 'occupation' in users.columns:
        path_box = os.path.join(GRAPHICS_DIR, 'test_boxplot.png')
        categorized_boxplot(users, 'age', 'occupation', save_path=path_box)
        print("   categorized_boxplot OK")

    if ('gender' in user_avg.columns and 'age' in user_avg.columns
            and 'avg_rating' in user_avg.columns):
        path_scatter = os.path.join(GRAPHICS_DIR, 'test_scatter.png')
        categorized_scatter(user_avg, 'age', 'avg_rating', 'gender',
                            save_path=path_scatter)
        print("   categorized_scatter OK")


if __name__ == "__main__":
    test_stats()
    test_plots()
    print("Все тесты пройдены!")
