SELECT DISTINCT
    b.territory_4_name AS div,
    b.name AS rrc_name,
    b.id AS rrc_id,
    p.category_1_name,
    p.category_4_name,
    p.category_4_id,
    sid.`Номенклатура` AS product,
    sid.`Количество` AS stock,
    p.federal_status_name,
    p.life_cycle_status_name,
    p.purchase_status_name
FROM RN.Schet_41_Itogi_day sid
JOIN dict.branch b ON sid.`Филиал` = b.id
JOIN dict.product p ON sid.`Номенклатура` = p.id
WHERE
    sid.`Период` = '{period}'
    AND sid.`Количество` > 0
    AND b.is_deleted = 0
    AND b.type_name = 'РРЦ'
    AND p.category_1_code IN {category_1_codes}
    AND lowerUTF8(b.name) NOT ILIKE '%сдх%'
    AND b.id <> '{excluded_id}'