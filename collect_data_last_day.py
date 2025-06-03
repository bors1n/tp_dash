import pandas as pd
from flib import Db

def main():

    ch = Db("formats")
    pg = Db('db_postgresql_spb')

    #получаем топ 70 категорий
    top_category = ch.read_sql('''
    WITH category_sales AS (
        SELECT 
            p.category_4_id,
            SUM(cost) AS cost
        FROM formats.product_movements_by_type pmbt
        JOIN dict.product p ON pmbt.product = p.id
        WHERE 
            date_day >= '2025-01-01'
            AND pmbt.type_of_movement IN ('Продажа и выдача с себя', 'Отгрузка под клиента', 'Продажа + Доставка с себя')
            AND count > 0
        GROUP BY 
            p.category_4_id
    ),
    ordered_sales AS (
        SELECT
            category_4_id,
            cost,
            SUM(cost) OVER (ORDER BY cost DESC ROWS UNBOUNDED PRECEDING) AS cum_sum,
            SUM(cost) OVER () AS total_sum
        FROM category_sales
    )
    SELECT
        category_4_id
    FROM ordered_sales
    WHERE (cum_sum / total_sum) <= 0.7
    ORDER BY cost DESC;
    ''')

    top_category['category_4_id'] = top_category['category_4_id'].apply(lambda x: str(x))

    #Получаем все остатки по РРЦ
    rrc_stock = ch.read_sql('''
   SELECT DISTINCT 
	b.territory_4_name AS div,
	b.name as rrc_name,
	b.id AS rrc_id,
	p.category_1_name category_1_name,
	p.category_4_name category_4_name,
	p.category_4_id category_4_id,
	sid.`Номенклатура` AS product, 
	sid.`Количество` stock,
	p.federal_status_name federal_status_name, 
	p.life_cycle_status_name life_cycle_status_name,
	p.purchase_status_name purchase_status_name
FROM RN.Schet_41_Itogi_day sid
	JOIN dict.branch b ON sid.`Филиал` = b.id
	JOIN dict.product p ON sid.`Номенклатура` = p.id
WHERE 
	1=1 
	AND sid.`Период` = '2025-06-01'
	AND sid.`Количество` > 0
	AND b.is_deleted = 0
	AND b.type_name = 'РРЦ'
	AND p.category_1_code IN ('AM18266', 'ID43922', 'AM24114', 'ID43921', 'EY74273', 'IW79893', 'IW79895', 'GH19556')
	AND lowerUTF8(b.name)  NOT ILIKE '%сдх%'  
	and b.id <> '4a863ecc-7bcf-11ef-9273-0050569d9cb8'
    	--and b.id IN ('60a4be06-4c74-11e9-a206-00155d03332b', 'd1053f78-128b-44ff-8a6b-4b2cbd0a1a15')
    ''')

    # получаем потребности РРЦ.
    rrc_fix = pg.read_sql('''
    SELECT 
    	fix."Филиал" rrc_id, fix."Товар" product, max(fix."Количество") fix
    FROM reg.total_product_fixes_by_stage fix
    	JOIN dim.dim_branches db ON fix."Филиал" = db."Ссылка"
    							 AND db."ВидФилиала" = 'РРЦ'
    WHERE 
    	fix."Количество" > 0
    	---and fix."Филиал" IN ('60a4be06-4c74-11e9-a206-00155d03332b', 'd1053f78-128b-44ff-8a6b-4b2cbd0a1a15')
    GROUP BY 
    	rrc_id, product
    ''')

    # приводим столбцы в нужные форматы
    rrc_stock['stock'] = pd.to_numeric(rrc_stock.stock)
    rrc_stock['rrc_id'] = rrc_stock['rrc_id'].apply(lambda x: str(x))
    rrc_stock['product'] = rrc_stock['product'].apply(lambda x: str(x))
    rrc_stock['category_4_id'] = rrc_stock['category_4_id'].apply(lambda x: str(x))

    #обьединяем потребности и остатки, рассчитываем доступность, добавляем пометку о топовости категории

    rrc_full_stock = rrc_stock.merge(rrc_fix, on=['rrc_id', 'product'], how='left')
    rrc_full_stock['fix'] = rrc_full_stock.fix.fillna(0)
    rrc_full_stock['max'] = rrc_full_stock['fix'].apply(lambda x: max(x, 2))
    rrc_full_stock['access'] = rrc_full_stock['stock'] > rrc_full_stock['max']
    rrc_full_stock['top_category'] = rrc_full_stock['category_4_id'].isin(top_category.category_4_id)

    # группируем до категории.
    rrc_table = rrc_full_stock.groupby([
        'div', 'rrc_name', 'rrc_id',
        'category_1_name', 'category_4_name', 'category_4_id',
        'federal_status_name', 'life_cycle_status_name', 'purchase_status_name', 'access', 'top_category'
    ],
        as_index=False).agg(
        product_count=('product', 'nunique')
    )

    # получаю остаток для тп
    tp_stock = ch.read_sql('''
  SELECT DISTINCT 
	b.rrc_id rrc_id,
	b.name AS branch,
	b.id AS branch_id,
	p.category_4_id category_4_id,
	sid.`Номенклатура` AS product
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
	AND sid.`Период` = '2025-06-02'
	AND sid.`Количество` > 0
	AND b.is_deleted = 0
	AND b.type_name = 'Дисконт центр'
	AND p.category_1_code IN ('AM18266', 'ID43922', 'AM24114', 'ID43921', 'EY74273', 'IW79893', 'IW79895', 'GH19556')
	AND mkf.BranchConfModel NOT IN ('Не задана', 'ПВЗ')
	AND lowerUTF8(b.name)  NOT ILIKE '%достав%' --- убираем: доставка, точка выдачи достаток
	AND lowerUTF8(b.name)  NOT ILIKE '%точк%'  
	and b.name not in ('Рыбинск ТП', 'Бийск Технопоинт на Советской', 'СПб Склад в Горелово ТП', 'Иркутск Торг.Склад Мельниковский', 'Калининград Орудийная ТП',
	                    'Барнаул Технопоинт СК', 'Южно-Сахалинск Склад ТП', 'Волгоград Торг. Склад', 'Воронеж Торг. Склад', 'Киров ТП на Щорса', 'Чита Торг. Склад ТП', 
	                    'Владивосток Днепровская ТП ', 'Краснодар Магазин-склад ДНС', 'Тула Торг. Склад', 'Кра Торг. Склад ТП', 'Владимир Технопоинт', 'Новосиб Технопоинт СК Сибирский', 
	                    'Ростов Магазин-склад Технопоинт new', 'Рыбинск ТП')
	--and b.rrc_id IN ('60a4be06-4c74-11e9-a206-00155d03332b', 'd1053f78-128b-44ff-8a6b-4b2cbd0a1a15')
    ''')

    tp_stock['rrc_id'] = tp_stock['rrc_id'].apply(lambda x: str(x))
    tp_stock['branch_id'] = tp_stock['branch_id'].apply(lambda x: str(x))
    tp_stock['category_4_id'] = tp_stock['category_4_id'].apply(lambda x: str(x))
    tp_stock['product'] = tp_stock['product'].apply(lambda x: str(x))

    #считаю асс для тп
    tp_stock_group = tp_stock.groupby(['rrc_id', 'branch', 'branch_id', 'category_4_id'], as_index=False)[
        'product'].count().rename(columns={'product': 'product_count_tp'})

    # потенциальный остаток для ТП
    tp = tp_stock.copy()
    rrc = rrc_full_stock.query('access == True')[
        ['div', 'rrc_name', 'rrc_id', 'category_1_name', 'category_4_name', 'category_4_id', 'product',
         'federal_status_name', 'life_cycle_status_name', 'purchase_status_name', 'top_category']]

    # Получаем уникальные филиалы с привязкой к РРЦ
    branches = tp[['rrc_id', 'branch', 'branch_id']].drop_duplicates()
    # Делаем полное соединение товаров РРЦ с филиалами по rrc_id
    rrc_branches = pd.merge(rrc, branches, on='rrc_id', how='left')
    # Далее left merge с tp для выявления, есть ли товар на филиале
    compare = pd.merge(
        rrc_branches,
        tp,
        on=['rrc_id', 'branch_id', 'category_4_id', 'product'],
        how='left',
        indicator=True,
        suffixes=('', '_tp')
    )
    # Выбираем товары, отсутствующие на филиалах (left_only)
    missing_products = compare[compare['_merge'] == 'left_only']
    # датафрем с количеством ску доступных для наполнения по каждому ТП - Категории
    available_tp_stock = missing_products.groupby([
        'div', 'rrc_name', 'rrc_id', 'branch', 'branch_id',
        'category_1_name', 'category_4_name', 'category_4_id',
        'federal_status_name', 'life_cycle_status_name', 'purchase_status_name', 'top_category'
    ], as_index=False) \
        .agg(
        product_count=('product', 'nunique')
    )

    #сохраняю данные
    # rrc_table.dropna().to_csv('rrc_table.csv', index=False)
    # tp_stock_group.dropna().to_csv('tp_stock.csv', index=False)
    # available_tp_stock.dropna().to_csv('available_tp_stock.csv', index=False)
    rrc_table.dropna().to_csv('rrc_table.csv.gz', index=False, compression='gzip')
    tp_stock_group.dropna().to_csv('tp_stock.csv.gz', index=False, compression='gzip')
    available_tp_stock.dropna().to_csv('available_tp_stock.csv.gz', index=False, compression='gzip')

if __name__ == "__main__":
    main()