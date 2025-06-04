# utils.py для загрузки sql
from pathlib import Path

def load_sql(filename: str, **params) -> str:
    """
    Загружает SQL-запрос из файла и форматирует его строкой с переданными параметрами.

    :param filename: имя файла с SQL внутри папки 'sql'
    :param params: параметры для подстановки в SQL
    :return: сформированный SQL запрос
    """
    sql_path = Path(__file__).parent / 'sql' / filename
    sql_template = sql_path.read_text(encoding='utf-8')
    return sql_template.format(**params)