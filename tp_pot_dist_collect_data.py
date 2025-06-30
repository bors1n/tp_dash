import pandas as pd
from flib import Db
from utils import load_sql

TOP_CATEGORY_CUMSUM_THRESHOLD = 0.7
STOCK_DEFAULT_MIN = 2
CATEGORY_1_CODES = ('AM18266', 'ID43922', 'AM24114', 'ID43921', 'EY74273', 'IW79893', 'IW79895', 'GH19556')
RRC_EXCLUDED_ID = '4a863ecc-7bcf-11ef-9273-0050569d9cb8'
TP_EXCLUDED_BRANCH_NAMES = [
    'Рыбинск ТП', 'Бийск Технопоинт на Советской', 'СПб Склад в Горелово ТП',
    'Иркутск Торг.Склад Мельниковский', 'Калининград Орудийная ТП', 'Барнаул Технопоинт СК',
    'Южно-Сахалинск Склад ТП', 'Волгоград Торг. Склад', 'Воронеж Торг. Склад',
    'Киров ТП на Щорса', 'Чита Торг. Склад ТП', 'Владивосток Днепровская ТП ',
    'Краснодар Магазин-склад ДНС', 'Тула Торг. Склад', 'Кра Торг. Склад ТП',
    'Владимир Технопоинт', 'Новосиб Технопоинт СК Сибирский', 'Ростов Магазин-склад Технопоинт new', 'Рыбинск ТП']
PERIOD = '2025-06-30'

def get_top_categories(db: Db, date_start: str = '2025-01-01', threshold: float = 0.7) -> pd.Series:
    sql = load_sql('top_categories.sql', date_start=date_start, threshold=threshold)
    df = db.read_sql(sql)
    return df['category_4_id'].astype(str)

def get_rrc_stock(db: Db, period: str = '2025-06-01') -> pd.DataFrame:
    sql = load_sql('rrc_stock.sql', period=period, category_1_codes=CATEGORY_1_CODES, excluded_id=RRC_EXCLUDED_ID)
    df = db.read_sql(sql)
    # Приведение типов по аналогии
    df['stock'] = pd.to_numeric(df['stock'])
    df['rrc_id'] = df['rrc_id'].astype(str)
    df['product'] = df['product'].astype(str)
    df['category_4_id'] = df['category_4_id'].astype(str)
    return df

def get_rrc_fix(db: Db) -> pd.DataFrame:
    sql = load_sql('rrc_fix.sql')
    df = db.read_sql(sql)
    df['rrc_id'] = df['rrc_id'].astype(str)
    df['product'] = df['product'].astype(str)
    return df

def get_tp_stock(db: Db, period: str = '2025-06-02') -> pd.DataFrame:
    excluded_names_str = ', '.join(f"'{name}'" for name in TP_EXCLUDED_BRANCH_NAMES)
    sql = load_sql('tp_stock.sql', period=period, category_1_codes=CATEGORY_1_CODES, excluded_branch_names=excluded_names_str)
    df = db.read_sql(sql)
    df['rrc_id'] = df['rrc_id'].astype(str)
    df['branch_id'] = df['branch_id'].astype(str)
    df['category_4_id'] = df['category_4_id'].astype(str)
    df['product'] = df['product'].astype(str)
    return df

def prepare_rrc_full_stock(rrc_stock: pd.DataFrame, rrc_fix: pd.DataFrame, top_category: pd.Series) -> pd.DataFrame:
    """
    Объеденить данные остатков и потребностей, посчитать доступность, отметить топовые категории.
    """
    merged = rrc_stock.merge(rrc_fix, on=['rrc_id', 'product'], how='left')
    merged['fix'] = merged['fix'].fillna(0)
    merged['max'] = merged['fix'].apply(lambda x: max(x, STOCK_DEFAULT_MIN))
    merged['access'] = merged['stock'] > merged['max']
    merged['top_category'] = merged['category_4_id'].isin(top_category)
    return merged

def aggregate_rrc_table(rrc_full_stock: pd.DataFrame) -> pd.DataFrame:
    """
    Группировка статистики по РРЦ и категориям.
    """
    agg_columns = [
        'div', 'rrc_name', 'rrc_id',
        'category_1_name', 'category_4_name', 'category_4_id',
        'federal_status_name', 'life_cycle_status_name', 'purchase_status_name', 'access', 'top_category'
    ]
    rrc_table = rrc_full_stock.groupby(agg_columns, as_index=False).agg(
        product_count=('product', 'nunique')
    )
    return rrc_table

def compute_tp_stock_group(tp_stock: pd.DataFrame, top_category: pd.Series) -> pd.DataFrame:
    """
    Подсчитать количество продуктов на ТП на уровне категорий.
    """
    tp_stock['top_category'] = tp_stock['category_4_id'].isin(top_category)
    grouped = tp_stock.groupby([
        'rrc_id', 'branch', 'branch_id', 'category_1_name', 'category_4_name', 'category_4_id', 'top_category'
    ], as_index=False)['product'].count().rename(columns={'product': 'product_count_tp'})
    return grouped

def compute_available_tp_stock(rrc_full_stock: pd.DataFrame, tp_stock: pd.DataFrame) -> pd.DataFrame:
    """
    Рассчитать доступные для наполнения товары для ТП (отсутствующие на филиале).
    """
    tp = tp_stock.copy()
    rrc = rrc_full_stock.query('access == True')[
        ['div', 'rrc_name', 'rrc_id', 'category_1_name', 'category_4_name', 'category_4_id', 'product',
         'federal_status_name', 'life_cycle_status_name', 'purchase_status_name', 'top_category']
    ]

    branches = tp[['rrc_id', 'branch', 'branch_id']].drop_duplicates()
    rrc_branches = pd.merge(rrc, branches, on='rrc_id', how='left')

    compare = pd.merge(
        rrc_branches,
        tp,
        how='left',
        on=['rrc_id', 'branch_id', 'category_4_id', 'product'],
        indicator=True,
        suffixes=('', '_tp')
    )

    missing_products = compare[compare['_merge'] == 'left_only']

    agg_columns = [
        'div', 'rrc_name', 'rrc_id', 'branch', 'branch_id',
        'category_1_name', 'category_4_name', 'category_4_id',
        'federal_status_name', 'life_cycle_status_name', 'purchase_status_name', 'top_category'
    ]
    available_tp_stock = missing_products.groupby(agg_columns, as_index=False).agg(
        product_count=('product', 'nunique')
    )
    return available_tp_stock

def save_dataframes(rrc_table: pd.DataFrame, tp_stock_group: pd.DataFrame, available_tp_stock: pd.DataFrame):
    """
    Сохранить результаты в сжатые csv файлы.
    """
    rrc_table.dropna().to_csv('rrc_table.csv.gz', index=False, compression='gzip')
    tp_stock_group.dropna().to_csv('tp_stock.csv.gz', index=False, compression='gzip')
    available_tp_stock.dropna().to_csv('available_tp_stock.csv.gz', index=False, compression='gzip')

def main():
    ch = Db("formats")
    pg = Db('db_postgresql_spb')

    top_category = get_top_categories(ch)
    rrc_stock = get_rrc_stock(ch, PERIOD)
    rrc_fix = get_rrc_fix(pg)

    rrc_full_stock = prepare_rrc_full_stock(rrc_stock, rrc_fix, top_category)
    rrc_table = aggregate_rrc_table(rrc_full_stock)

    tp_stock = get_tp_stock(ch, PERIOD)
    tp_stock_group = compute_tp_stock_group(tp_stock, top_category)
    available_tp_stock = compute_available_tp_stock(rrc_full_stock, tp_stock)

    save_dataframes(rrc_table, tp_stock_group, available_tp_stock)

if __name__ == "__main__":
    main()