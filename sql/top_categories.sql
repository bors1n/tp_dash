WITH category_sales AS (
        SELECT
            p.category_4_id,
            SUM(cost) AS cost
        FROM formats.product_movements_by_type pmbt
        JOIN dict.product p ON pmbt.product = p.id
        WHERE
            date_day >= '{date_start}'
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
    WHERE (cum_sum / total_sum) <= {threshold}
    ORDER BY cost DESC;