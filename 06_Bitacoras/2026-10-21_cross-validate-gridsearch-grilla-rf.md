# Bitácora — 2026-10-21: `cross_validate`, `GridSearchCV` y ampliación de la grilla del Random Forest

**Integrantes en la sesión:** Santiago Muñoz (inferido del usuario de git; confirmar). La
sesión empezó la noche del 2026-10-20 y se cerró el 2026-10-21.

## Resumen

El "Siguiente objetivo" que traía `HANDOFF.md` era ampliar `GRILLA_RF` en
`02_Scripts/04_estimacion_modelos.py` (porque `min_samples_leaf=1` quedó en el borde), volver
a correr 04 y 05 y reportar cuánto cambian RMSE y MAPE de prueba frente a la línea base. Se
cumplió, con una salvedad sobre el criterio de terminado (ver abajo).

Antes de implementar se revisó la grilla y se encontró que la sugerencia del handoff (agregar
valores mayores de `min_samples_leaf`) no resolvía el borde: `min_samples_leaf=1` es el
mínimo posible y, en la grilla anterior, el RMSE de CV subía con cada valor mayor en las dos
escalas. Por eso la grilla se refinó donde sí había espacio (`max_features`) y se agregaron
valores cercanos al mínimo (2 y 5), quitando el 10.

A mitad de la sesión se pidió automatizar la validación cruzada con scikit-learn. Se evaluaron
las opciones (`cross_validate`, `GridSearchCV`, `RandomizedSearchCV`, búsquedas por halving,
`Pipeline` y compañía) y la decisión fue integrar `cross_validate` en todos los modelos y
`GridSearchCV` en las especificaciones con el objetivo en niveles. Esto contradecía la regla
previa del `CLAUDE.md` (que excluía `GridSearchCV`), así que se actualizó el `CLAUDE.md`.

Pérdida de observaciones: ninguna. La base limpia (27,324 viviendas), la partición (21,859
entrenamiento, 5,465 prueba) y el conjunto de prueba no se tocaron.

## Archivos

- Creados: esta bitácora.
- Modificados: `02_Scripts/04_estimacion_modelos.py`, `CLAUDE.md`, `HANDOFF.md`,
  `README.md` (fila "Validación" de la tabla de enfoque); tablas `04_*` y `05_*` y figuras
  `04_*` y `05_*` regeneradas por `00_main.py`. También se regeneraron las tablas y figuras
  `02_*`, sin cambios de contenido (diferencias de 1e-16 en el último dígito de unas pocas
  celdas).
- Eliminados: ninguno.

## Detalle por archivo

### `02_Scripts/04_estimacion_modelos.py`

1. **`cross_validate` reemplaza el ciclo manual sobre `KFold`** en `cv_en_pesos`, que ahora
   sirve a todos los modelos (lineales, Lasso, Random Forest y XGBoost en log). Se mantiene el
   mismo `KFold(5, shuffle=True, random_state=2026)`, de modo que los folds son los mismos.
2. **Puntaje propio en la escala log.** `cross_validate` recibe el objetivo ya transformado, y
   el puntaje estándar mediría el error en log(precio). Dos funciones
   (`puntaje_rmse_log`, `puntaje_mape_log`) aplican `exp` a lo real y a lo predicho y
   devuelven el error en pesos, con signo negativo como los puntajes de scikit-learn. La
   intuición: la selección de hiperparámetros sigue guiada por el mismo RMSE en pesos que
   antes; solo cambia quién hace la cuenta.
3. **`GridSearchCV` en la escala niveles** (`elegir_por_grid_search`): los puntajes estándar
   `neg_root_mean_squared_error` y `neg_mean_absolute_percentage_error` ya están en pesos, se
   elige por RMSE (`refit="rmse"`) y el modelo final es `best_estimator_`. En log se conserva
   el recorrido explícito de la grilla (`elegir_por_cv`), ahora midiendo cada combinación con
   `cross_validate`. Las dos funciones devuelven la misma tupla, y la tabla se reordena al
   orden de la grilla (`GridSearchCV` ordena los parámetros alfabéticamente) para que las
   tablas `04_cv_grilla_*.csv` conserven su forma.
4. **`GRILLA_RF`:** de `max_features` en [0.33, 0.5, 1.0] y `min_samples_leaf` en [1, 3, 10] a
   `max_features` en [0.2, 0.33, 0.4, 0.5, 0.6, 0.75, 1.0] y `min_samples_leaf` en [1, 2, 3, 5]
   (28 combinaciones en lugar de 9).

Supuestos: `GridSearchCV` y el recorrido manual producen las mismas desviaciones estándar
(ambos usan `ddof=0`).

### `CLAUDE.md`

- "Reglas de trabajo": `cross_validate` y `GridSearchCV` quedan autorizados; `Pipeline`,
  `ColumnTransformer` y `TransformedTargetRegressor` siguen excluidos.
- "Decisiones tomadas": se actualizó la fila de la estimación (ya no menciona el ciclo manual
  ni excluye `GridSearchCV`) y se agregaron dos filas: la de `cross_validate`/`GridSearchCV`
  (marcada como pedida por Santiago Muñoz y pendiente de confirmar con el equipo) y la de la
  nueva grilla del Random Forest.

### `README.md`

Solo la fila "Validación" de la tabla de enfoque, para nombrar `cross_validate` y
`GridSearchCV`. El resto del README no cambió.

## Resultados nuevos (tablas, figuras, métricas)

**Equivalencia del refactor.** Antes de ampliar la grilla se corrió 04 con la grilla anterior y
se comparó contra las tablas guardadas (emparejando por hiperparámetros, no por posición):
las tablas de CV de Random Forest y XGBoost, las métricas, los errores por estrato y por
localidad y las predicciones coinciden con diferencia relativa máxima de 6e-6 (en una
desviación estándar de XGBoost). Los hiperparámetros elegidos fueron los mismos.

**Hiperparámetros elegidos con la grilla ampliada** (`04_hiperparametros.csv`,
`04_cv_grilla_random_forest.csv`):

| Escala | Antes | Ahora |
|---|---|---|
| Log | `max_features=0.5`, `min_samples_leaf=1` | `max_features=0.5`, `min_samples_leaf=1` |
| Niveles | `max_features=0.5`, `min_samples_leaf=1` | `max_features=0.4`, `min_samples_leaf=1` |

`max_features` quedó en el interior de la grilla en las dos escalas. `min_samples_leaf=1`
sigue siendo el elegido y es el mínimo permitido: no puede estar en el interior de ninguna
grilla. El criterio de terminado del handoff ("valor elegido por CV en el interior de la
grilla, o anotado que sigue en el borde") se cumplió con la segunda opción para ese parámetro.

**Métricas (`04_metricas_modelos.csv`).** RMSE en millones de COP y MAPE en %, línea base
lineal frente a Random Forest y XGBoost de la misma escala. Entrenamiento, validación cruzada
(CV) y prueba:

| Modelo | Escala | RMSE train | RMSE CV | RMSE prueba | MAPE train | MAPE CV | MAPE prueba |
|---|---|---|---|---|---|---|---|
| Lineal (base) | Log | 467.1 | 466.8 | 421.5 | 16.94 | 16.97 | 16.89 |
| Random Forest | Log | 151.8 | 363.4 | 305.3 | 4.23 | 11.81 | 11.56 |
| XGBoost | Log | 196.1 | 360.4 | 302.0 | 8.64 | 12.19 | 11.87 |
| Lineal (base) | Niveles | 507.8 | 507.7 | 472.9 | 34.60 | 34.71 | 35.54 |
| Random Forest | Niveles | 127.1 | 346.5 | 291.2 | 4.49 | 12.45 | 12.18 |
| XGBoost | Niveles | 67.4 | 366.4 | 290.2 | 6.05 | 12.68 | 12.31 |

**Cambio del Random Forest frente a la grilla anterior** (la línea base no cambia):

| Escala | RMSE CV antes → ahora | RMSE prueba antes → ahora | Cambio de RMSE prueba vs. base antes → ahora | MAPE prueba antes → ahora |
|---|---|---|---|---|
| Log | 363.45 → 363.45 | 305.31 → 305.31 | −27.57% → −27.57% | 11.56 → 11.56 |
| Niveles | 348.47 → 346.48 | 288.53 → 291.17 | −38.98% → −38.42% | 12.13 → 12.18 |

En niveles, el RMSE de CV bajó 2.0 M y el de prueba subió 2.6 M. La selección es solo por CV
sobre entrenamiento; la prueba no se usó para elegir. Las tablas y figuras `05_*` se
regeneraron con el Random Forest en niveles nuevo, así que las cifras de la bitácora
`2026-10-20_analisis-errores-impacto.md` correspondientes a esa escala corresponden a la
grilla anterior; los valores vigentes están en `03_Resultados/Tablas/05_*.csv`.

**`00_main.py` completo.** Corrió de punta a punta sin intervención, sin errores: 14.2 min en
total (14.0 de estimación). Es la primera corrida encadenada verificada de los cinco scripts.
La única advertencia es una `MatplotlibDeprecationWarning` del parámetro `vert` en
`02_analisis_descriptivo.py`, que no se tocó.

## Uso de IA

Claude Code (Claude Sonnet 5.5) en el entorno de VS Code, para: revisar la grilla y el
handoff, explicar las herramientas de scikit-learn disponibles para automatizar la validación,
refactorizar `04_estimacion_modelos.py`, actualizar `CLAUDE.md` y correr el pipeline.
Verificación: (1) las tablas de la corrida con el refactor y la grilla anterior se compararon
con copias de las tablas previas, por hiperparámetros y por columna, y la diferencia máxima
fue de 6e-6; (2) las métricas de este informe se leyeron de los CSV regenerados, sin escribir
ningún número a mano; (3) se revisó la salida de `00_main.py` buscando errores y
advertencias. Las decisiones de fondo (usar `GridSearchCV` solo en niveles, qué grilla
probar) las tomó el usuario o se le propusieron antes de implementar.

## Pendientes

- **Siguiente objetivo (por decisión del usuario):** revisar si los resultados alcanzan para
  la presentación de avance, criterio por criterio de la rúbrica
  (`../Rubrica_Presentacion_Avance.xlsx`), e identificar lo que falta. Ya es claro que no hay
  nada hecho para la propuesta de aprendizaje profundo o IA generativa (criterio 4, 20% de la
  nota): el modelo de texto con `descripcion` sigue pendiente.
- Confirmar con el equipo la decisión de usar `cross_validate` y `GridSearchCV` (quedó
  registrada como pedida por Santiago Muñoz).
- Confirmar con el equipo el umbral de 30 viviendas en prueba (el estrato 1 tiene 16) y qué
  parte de la evaluación de impacto se calcula (error de precio) y cuál queda como propuesta
  (tiempo de compra/venta y ahorro).
- Completar roles y correos de Maria Paula Rivera y Angelo Di Marco en `CLAUDE.md`.
- Documentar la sesión del commit `bd96c50` (partición y estimación), que no tiene bitácora.
- Opcional: decidir si se usa `GridSearchCV` también en log (requeriría pasar el puntaje
  propio como `scoring`; hoy ahí se recorre la grilla a mano) y si se corrige la advertencia
  de `vert` en 02.
