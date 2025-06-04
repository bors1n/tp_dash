SELECT
    fix."Филиал" AS rrc_id,
    fix."Товар" AS product,
    MAX(fix."Количество") AS fix
FROM reg.total_product_fixes_by_stage fix
JOIN dim.dim_branches db ON fix."Филиал" = db."Ссылка" AND db."ВидФилиала" = 'РРЦ'
WHERE fix."Количество" > 0
GROUP BY rrc_id, product