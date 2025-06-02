import pandas as pd
from flib import Db


def main():
    query = f'''
    WITH tp_stock AS (
    ---- асс ТП
    SELECT
        toDate(sid.`Период`) AS date_,
        b.territory_4_name AS div,
        b.rrc_name as rrc_name,
        b.rrc_id rrc_id,
        b.name AS branch,
        p.category_1_name dep, 
        count(DISTINCT sid.`Номенклатура`) AS ass
    FROM RN.Schet_41_Itogi_day sid
        JOIN dict.branch b ON sid.`Филиал` = b.id
        JOIN dict.product p ON sid.`Номенклатура` = p.id
        JOIN (
            SELECT BranchId, BranchConfModel
            FROM formats_bi.GroupOfMeasuresOnBranchStats
            ORDER BY Period DESC 
            LIMIT 1 BY BranchId, BranchConfModel
            ) mkf ON b.id = mkf.BranchId
    WHERE 
        1=1 
        AND sid.`Период` BETWEEN '2025-05-01' AND '2025-06-01'
        AND sid.`Количество` > 0
        AND b.is_deleted = 0
        AND b.type_name = 'Дисконт центр'
        AND p.category_1_code IN ('AM18266', 'ID43922', 'AM24114', 'ID43921', 'EY74273', 'IW79893', 'IW79895', 'GH19556')
        AND mkf.BranchConfModel NOT IN ('Не задана', 'ПВЗ')
        AND lowerUTF8(b.name)  NOT ILIKE '%достав%' --- убираем: доставка, точка выдачи достаток
        AND lowerUTF8(b.name)  NOT ILIKE '%точк%'   
    GROUP BY date_, rrc_name, div, rrc_id, dep, branch
    ),
    --- acc РРЦ
    rrc_stock AS (
    SELECT
        toDate(sid.`Период`) AS date_,
        b.id AS rrc_id,
        b.name AS rrc_name,
        p.category_1_name dep,
        count(DISTINCT sid.`Номенклатура`) AS ass
    FROM RN.Schet_41_Itogi_day sid
        JOIN dict.branch b ON sid.`Филиал` = b.id
        JOIN dict.product p ON sid.`Номенклатура` = p.id
        JOIN (
            SELECT BranchId, BranchConfModel
            FROM formats_bi.GroupOfMeasuresOnBranchStats
            ORDER BY Period DESC 
            LIMIT 1 BY BranchId, BranchConfModel
        ) mkf ON b.id = mkf.BranchId
    WHERE 
        1=1 
        AND sid.`Период` BETWEEN '2025-05-01' AND '2025-06-01'
        AND sid.`Количество` > 0
        AND b.is_deleted = 0
        AND b.type_name = 'РРЦ'
        AND p.category_1_code IN ('AM18266', 'ID43922', 'AM24114', 'ID43921', 'EY74273', 'IW79893', 'IW79895', 'GH19556')
        AND mkf.BranchConfModel NOT IN ('Не задана', 'ПВЗ')
    GROUP BY date_, rrc_id, dep, rrc_name
    )
    SELECT 
        tp_stock.date_, tp_stock.div, tp_stock.rrc_name, tp_stock.dep, tp_stock.branch, tp_stock.ass sku_tp, rrc_stock.ass sku_wh 
    FROM tp_stock 
        JOIN rrc_stock ON tp_stock.rrc_id = rrc_stock.rrc_id
                      AND tp_stock.date_ = rrc_stock.date_
                      AND tp_stock.dep = rrc_stock.dep 
    -- WHERE 
    -- 	tp_stock.ass >= 1000
    '''
    ch = Db("formats")

    df = ch.read_sql(query)  # запрос данных

    tp = df.groupby(['date_', 'div', 'rrc_name', 'branch'], as_index=False)['sku_tp'].sum()
    wh = df[['date_', 'div', 'rrc_name', 'dep', 'sku_wh']].drop_duplicates().groupby(['date_', 'div', 'rrc_name'], as_index=False)['sku_wh'].sum()

    tp_wh_coverage = tp.merge(wh, on=['date_', 'div', 'rrc_name']).query('sku_tp >= 1000')
    tp_wh_coverage['coverage_rate'] = (tp_wh_coverage['sku_tp'] / tp_wh_coverage['sku_wh'] * 100).round(2)
    # tp_wh_coverage - динамика доли для каждого ТП.

    div_coverage = tp_wh_coverage.groupby(['date_', 'div'], as_index=False).agg({'coverage_rate': 'mean'})
    # div_coverage - динамика доля для дивизионов

    dep_coverage = df.merge(tp_wh_coverage['branch'].drop_duplicates(), on='branch', how='inner')
    dep_coverage['coverage_rate'] = dep_coverage['sku_tp'] / dep_coverage['sku_wh']
    dep_coverage = dep_coverage.groupby(['date_', 'dep'], as_index=False)['coverage_rate'].mean()
    dep_coverage['coverage_rate'] = dep_coverage.coverage_rate.mul(100).round(2)
    # dep_coverage - динамика доля по деп.

    div_static_metrics = tp_wh_coverage.groupby(['div'], as_index=False).agg({
        'sku_tp': ['mean', 'median', 'min', 'max'],
        'branch': 'nunique'
    })

    div_static_metrics.columns = ['_'.join(col).strip() for col in div_static_metrics.columns.values]
    div_static_metrics['sku_tp_mean'] = div_static_metrics.sku_tp_mean.round(2)
    # div_static_metrics - мин, макс, средний и медианный ассортимент. Количество тп в дивизионе.

    tp_wh_coverage.to_csv('tp_wh_coverage.csv', index=False)
    div_coverage.to_csv('div_coverage.csv', index=False)
    dep_coverage.to_csv('dep_coverage.csv', index=False)
    div_static_metrics.to_csv('div_static_metrics.csv', index=False)

if __name__ == "__main__":
    main()