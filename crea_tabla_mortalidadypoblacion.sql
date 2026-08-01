WITH t0 AS (

SELECT distritos_2026.cod_distrito, 
distritos_2026.distrito_nombre,
cantones_2026.cod_canton,
cantones_2026.canton_nombre,
cantones_2026.provincia_nombre
FROM distritos_2026 INNER JOIN
cantones_2026 ON distritos_2026.cod_canton = cantones_2026.cod_canton
),

t1 AS (
SELECT 
t0.cod_distrito,
t0.distrito_nombre,
t0.cod_canton,
t0.canton_nombre,
t0.provincia_nombre,
defunciones_todas.anho,
defunciones_todas.defunciones_total,
estimados_poblacion_inec2025.pob_total as poblacion_total
FROM defunciones_todas
INNER JOIN t0
ON defunciones_todas.cod_distrito = t0.cod_distrito
LEFT JOIN estimados_poblacion_inec2025
ON defunciones_todas.cod_distrito= estimados_poblacion_inec2025.cod_distrito AND
defunciones_todas.anho = estimados_poblacion_inec2025.anho
WHERE estimados_poblacion_inec2025.pob_total is NOT NULL
ORDER BY defunciones_todas.cod_distrito, defunciones_todas.anho
)

SELECT * FROM t1

