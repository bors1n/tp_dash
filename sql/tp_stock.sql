SELECT DISTINCT
    b.rrc_id AS rrc_id,
    b.name AS branch,
    b.id AS branch_id,
    p.category_1_name as category_1_name,
    p.category_4_name as category_4_name,
    p.category_4_id as category_4_id,
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
    sid.`Период` = '{period}'
    AND sid.`Количество` > 0
    AND b.is_deleted = 0
    AND b.type_name = 'Дисконт центр'
    AND p.category_1_code IN {category_1_codes}
    AND mkf.BranchConfModel NOT IN ('Не задана', 'ПВЗ')
    AND lowerUTF8(b.name) NOT ILIKE '%достав%'
    AND lowerUTF8(b.name) NOT ILIKE '%точк%'
    AND b.name NOT IN ({excluded_branch_names})