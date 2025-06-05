import pandas as pd
from flib import Db
from utils import load_sql
from datetime import datetime, timedelta

CATEGORY_1_CODES = ('AM18266', 'ID43922', 'AM24114', 'ID43921', 'EY74273', 'IW79893', 'IW79895', 'GH19556')
DATE_FROM_DEFAULT = '2025-05-01'
DATE_TO_DEFAULT = datetime.today().strftime('%Y-%m-%d')  # Можно заменить на текущую дату при автоматизации

def get_tp_wh_data(db: Db, date_from: str, date_to: str, category_1_codes: tuple) -> pd.DataFrame:
    category_1_codes_str = str(category_1_codes)
    sql = load_sql(
        'tp_wh_coverage.sql',
        date_from=date_from,
        date_to=date_to,
        category_1_codes=category_1_codes_str
    )
    df = db.read_sql(sql)
    return df

def process_coverage_data(df: pd.DataFrame):
    tp = df.groupby(['date_', 'div', 'rrc_name', 'branch'], as_index=False)['sku_tp'].sum()
    wh = df[['date_', 'div', 'rrc_name', 'dep', 'sku_wh']].drop_duplicates().groupby(
        ['date_', 'div', 'rrc_name'], as_index=False)['sku_wh'].sum()

    tp_wh_coverage = tp.merge(wh, on=['date_', 'div', 'rrc_name']).query('sku_tp >= 1000')
    tp_wh_coverage['coverage_rate'] = (tp_wh_coverage['sku_tp'] / tp_wh_coverage['sku_wh'] * 100).round(2)

    div_coverage = tp_wh_coverage.groupby(['date_', 'div'], as_index=False).agg({'coverage_rate': 'mean'})

    dep_coverage = df.merge(tp_wh_coverage['branch'].drop_duplicates(), on='branch', how='inner')
    dep_coverage['coverage_rate'] = dep_coverage['sku_tp'] / dep_coverage['sku_wh']
    dep_coverage = dep_coverage.groupby(['date_', 'dep'], as_index=False)['coverage_rate'].mean()
    dep_coverage['coverage_rate'] = dep_coverage.coverage_rate.mul(100).round(2)

    div_static_metrics = tp_wh_coverage.groupby(['div'], as_index=False).agg({
        'sku_tp': ['mean', 'median', 'min', 'max'],
        'branch': 'nunique'
    })
    div_static_metrics.columns = ['_'.join(col).strip() for col in div_static_metrics.columns.values]
    div_static_metrics['sku_tp_mean'] = div_static_metrics.sku_tp_mean.round(2)

    return tp_wh_coverage, div_coverage, dep_coverage, div_static_metrics

def save_results(tp_wh_coverage, div_coverage, dep_coverage, div_static_metrics):
    tp_wh_coverage.to_csv('tp_wh_coverage.csv', index=False)
    div_coverage.to_csv('div_coverage.csv', index=False)
    dep_coverage.to_csv('dep_coverage.csv', index=False)
    div_static_metrics.to_csv('div_static_metrics.csv', index=False)

def get_last_date_from_csv(path: str) -> pd.Timestamp | None:
    try:
        df = pd.read_csv(path, usecols=['date_'])
        df['date_'] = pd.to_datetime(df['date_'])
        last_date = df['date_'].max()
        return last_date
    except FileNotFoundError:
        return None

def main():
    ch = Db("formats")

    last_date = get_last_date_from_csv('tp_wh_coverage.csv')
    if last_date is None:
        # Если файлов нет - выгружаем всё с дефолтной даты
        date_from = DATE_FROM_DEFAULT
    else:
        # Берём минус 1 день для подстраховки на возможные обновления
        date_from = (last_date - timedelta(days=2)).strftime('%Y-%m-%d')
    # Текущая дата — допустим сегодня, или можно передавать параметром
    date_to = datetime.today().strftime('%Y-%m-%d')

    print(f"Загружаем данные с {date_from} по {date_to}")

    df_new = get_tp_wh_data(ch, date_from, date_to, CATEGORY_1_CODES)

    if df_new.empty:
        print("Новых данных нет.")
        return

    # Читаем старые данные, если они есть
    try:
        df_old = pd.read_csv('tp_wh_coverage.csv')
        # Объединяем, удаляя дублирующиеся строки
        df_all = pd.concat([df_old, df_new], ignore_index=True)
        df_all.drop_duplicates(subset=['date_', 'div', 'rrc_name', 'dep', 'branch', 'sku_tp', 'sku_wh'], inplace=True)
    except FileNotFoundError:
        df_all = df_new

    tp_wh_coverage, div_coverage, dep_coverage, div_static_metrics = process_coverage_data(df_all)
    save_results(tp_wh_coverage, div_coverage, dep_coverage, div_static_metrics)

    print("Данные обновлены успешно.")

if __name__ == "__main__":
    main()