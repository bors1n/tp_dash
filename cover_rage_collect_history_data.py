import pandas as pd
from flib import Db
from utils import load_sql

CATEGORY_1_CODES = ('AM18266', 'ID43922', 'AM24114', 'ID43921', 'EY74273', 'IW79893', 'IW79895', 'GH19556')
DATE_FROM = '2025-05-25'
DATE_TO = '2025-06-25'

def get_tp_wh_data(db: Db, date_from: str, date_to: str, category_1_codes: tuple) -> pd.DataFrame:
    category_1_codes_str = str(category_1_codes)  # для подстановки в SQL IN
    sql = load_sql(
        'tp_wh_coverage.sql',
        date_from=date_from,
        date_to=date_to,
        category_1_codes=category_1_codes_str
    )
    df = db.read_sql(sql)
    return df

def process_coverage_data(df: pd.DataFrame):
    # Агрегации по ТП и РРЦ
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

def main():
    ch = Db("formats")

    df = get_tp_wh_data(ch, DATE_FROM, DATE_TO, CATEGORY_1_CODES)
    tp_wh_coverage, div_coverage, dep_coverage, div_static_metrics = process_coverage_data(df)
    save_results(tp_wh_coverage, div_coverage, dep_coverage, div_static_metrics)

if __name__ == "__main__":
    main()