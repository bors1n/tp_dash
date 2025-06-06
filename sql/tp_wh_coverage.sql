WITH tp_stock AS (
    SELECT
        toDate(sid.`Период`) AS date_,
        b.territory_4_name AS div,
        b.rrc_name as rrc_name,
        b.rrc_id as rrc_id,
        b.name AS branch,
        p.category_1_name as dep,
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
        sid.`Период` BETWEEN '{date_from}' AND '{date_to}'
        AND sid.`Количество` > 0
        AND b.is_deleted = 0
        AND b.type_name = 'Дисконт центр'
        AND p.category_1_code IN {category_1_codes}
        AND mkf.BranchConfModel NOT IN ('Не задана', 'ПВЗ')
        AND lowerUTF8(b.name)  NOT ILIKE '%достав%'
        AND lowerUTF8(b.name)  NOT ILIKE '%точк%'
    GROUP BY date_, rrc_name, div, rrc_id, dep, branch
),
rrc_stock AS (
    SELECT
        toDate(sid.`Период`) AS date_,
        b.id AS rrc_id,
        b.name AS rrc_name,
        p.category_1_name as dep,
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
        sid.`Период` BETWEEN '{date_from}' AND '{date_to}'
        AND sid.`Количество` > 0
        AND b.is_deleted = 0
        AND b.type_name = 'РРЦ'
        AND p.category_1_code IN {category_1_codes}
        AND mkf.BranchConfModel NOT IN ('Не задана', 'ПВЗ')
    GROUP BY date_, rrc_id, dep, rrc_name
)
SELECT
    tp_stock.date_, tp_stock.div, tp_stock.rrc_name, tp_stock.dep, tp_stock.branch,
    tp_stock.ass sku_tp, rrc_stock.ass sku_wh
FROM tp_stock
JOIN rrc_stock ON tp_stock.rrc_id = rrc_stock.rrc_id
              AND tp_stock.date_ = rrc_stock.date_
              AND tp_stock.dep = rrc_stock.dep