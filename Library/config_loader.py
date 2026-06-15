# Library/config_loader.py
# Автор: Гордеева Анастасия
import configparser
import os


def load_config(config_path="config.ini"):
    """
    Загружает конфигурационный файл .ini.
    Сначала ищет в текущей папке, затем в родительской.

    Parameters:
        config_path (str): Имя файла конфигурации (по умолчанию config.ini).

    Returns:
        dict: Словарь настроек с ключами вида 'SECTION_KEY' и короткими
        ссылками 'DATA_DIR', 'OUTPUT_DIR', 'GRAPHICS_DIR'.

    Raises:
        FileNotFoundError: Если файл не найден ни в текущей,
        ни в родительской папке.
        KeyError: Если отсутствуют обязательные секции или ключи.

    Author:
        Gordeeva Anastasia
    """
    search_dirs = [
        os.getcwd(),
        os.path.dirname(os.getcwd())
    ]

    found_path = None
    for d in search_dirs:
        candidate = os.path.join(d, config_path)
        if os.path.exists(candidate):
            found_path = candidate
            break

    if found_path is None:
        raise FileNotFoundError(
            f"Файл конфигурации '{config_path}' не найден ни в {os.getcwd()}, "
            f"ни в {os.path.dirname(os.getcwd())}.\n"
            "Убедитесь, что config.ini лежит в папке Work или в текущей папке."
        )

    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(found_path, encoding='utf-8')

    if not config.has_section('DATABASE'):
        raise KeyError("В config.ini отсутствует секция [DATABASE]")

    required_db = ['MOVIES_FILE', 'USERS_FILE', 'RATINGS_FILE']
    missing_db = [k for k in required_db if not config.has_option('DATABASE', k)]
    if missing_db:
        raise KeyError(f"В секции [DATABASE] отсутствуют ключи: {', '.join(missing_db)}")

    required_default = ['DATA_DIR', 'OUTPUT_DIR', 'GRAPHICS_DIR']
    missing_default = [k for k in required_default if not config.has_option('DEFAULT', k)]
    if missing_default:
        raise KeyError(f"В секции [DEFAULT] отсутствуют ключи: {', '.join(missing_default)}")

    settings = {}
    for section in config.sections():
        for key, value in config.items(section):
            settings[f"{section}_{key}"] = value

    settings["DATA_DIR"] = config.get('DEFAULT', 'DATA_DIR')
    settings["OUTPUT_DIR"] = config.get('DEFAULT', 'OUTPUT_DIR')
    settings["GRAPHICS_DIR"] = config.get('DEFAULT', 'GRAPHICS_DIR')

    return settings


def get_file_path(filename, base_dir_key="DATA_DIR", config=None):
    """
    Формирует полный путь к файлу,
    используя базовую директорию из конфигурации.

    Parameters:
        filename (str): Имя файла.
        base_dir_key (str): Ключ в словаре конфигурации, указывающий на
        базовую папку.
        config (dict, optional): Словарь настроек. Если не передан,
        загружается автоматически.

    Returns:
        str: Полный путь к файлу.

    Author:
        Gordeeva Anastasia
    """
    if config is None:
        config = load_config()
    return os.path.join(config[base_dir_key], filename)
