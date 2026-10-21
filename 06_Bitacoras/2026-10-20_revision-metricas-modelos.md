# Bitácora — 2026-10-20: revisión de las métricas de los modelos y retiro de la regla del 10%

**Integrantes en la sesión:** Santiago Muñoz (inferido del usuario de git; confirmar)

## Resumen

El "Siguiente objetivo" que traía `HANDOFF.md` era la línea base lineal
(`03_modelo_baseline.py`, con `Pipeline`). Ese objetivo ya no aplicaba: el commit
`bd96c50` ("modelos"), anterior a esta sesión y sin bitácora propia, había
agregado `03_particion_muestra.py`, `04_estimacion_modelos.py` y `00_main.py`,
con la línea base, Lasso, Random Forest y XGBoost en dos escalas del objetivo
(log y niveles). Esta sesión no escribió esos scripts: revisó sus resultados.

Se consultaron `04_metricas_modelos.csv`, `04_hiperparametros.csv` y
`04_importancia_variables.csv` para responder cuáles fueron los mejores
modelos. La primera lectura diagnosticó sobreajuste con la regla de las
diapositivas (diferencia entre RMSE de entrenamiento y de prueba menor a 10%),
que el script aplicaba en la columna `brecha_supera_10pct`. El usuario señaló
que esa regla está definida para predicciones binarias y no para variables
continuas: con RMSE o MAPE, el cambio porcentual puede ser muy grande si el
error de entrenamiento es pequeño, sin que eso diga nada sobre si el error
fuera de muestra es aceptable. También se corrigió una lectura errónea de la
primera respuesta: la brecha negativa (error de prueba menor que el de
entrenamiento) se había contado como si fuera sobreajuste, porque la bandera
usaba el valor absoluto.

Se retiró la regla del script y de `CLAUDE.md`, y se reemplazó por una
comparación descriptiva entre CV y prueba, sin umbral. Se volvió a correr
`04_estimacion_modelos.py` para regenerar las tablas.

## Archivos

- Creados: `06_Bitacoras/2026-10-20_revision-metricas-modelos.md`.
- Modificados: `02_Scripts/04_estimacion_modelos.py`, `CLAUDE.md`, `HANDOFF.md`,
  `README.md`, y las tablas regeneradas
  `03_Resultados/Tablas/04_metricas_modelos.csv`, `04_cv_grilla_random_forest.csv`,
  `04_cv_grilla_xgboost.csv`, `04_errores_por_estrato.csv`,
  `04_errores_por_localidad.csv` y `04_predicciones_prueba.csv`.
- Eliminados: ninguno.

## Detalle por archivo

### `02_Scripts/04_estimacion_modelos.py`

- Se eliminaron `UMBRAL_BRECHA_PCT`, la columna `brecha_train_prueba_pct` y la
  bandera `brecha_supera_10pct`.
- Se agregaron dos columnas descriptivas, sin umbral, a
  `04_metricas_modelos.csv`: `dif_rmse_prueba_vs_cv_pct` (RMSE de prueba frente
  al de CV, en %) y `dif_mape_prueba_vs_cv_pp` (MAPE de prueba menos MAPE de CV,
  en puntos porcentuales). La intuición: CV y prueba son dos medidas del error
  sobre datos que el modelo no usó para ajustarse; si coinciden, el error
  fuera de muestra es consistente. Las métricas de entrenamiento se siguen
  reportando como dato descriptivo.
- Se actualizaron el docstring y la salida impresa en consola.

### `CLAUDE.md`

En "Regla metodológica: evaluación" se reemplazó la mención de la regla del
10% por una nota: no se usa umbral entre entrenamiento y prueba; se compara CV
frente a prueba y el error de entrenamiento es solo descriptivo.

### `README.md`

Se alineó con el estado del repo: el Enfoque ahora dice que los modelos se
reportan en entrenamiento, validación cruzada y prueba; se quitó el marcador
"pendiente" de `00_main.py`; "Cómo reproducir" lista `03_particion_muestra.py`,
`04_estimacion_modelos.py` y `00_main.py`, y el entorno pasa a Python 3.13
(el de `.venv/` y `requirements.txt`).

### `HANDOFF.md`

Se reescribieron "Siguiente objetivo" y "Estado actual" (este último estaba
desactualizado: no incluía la partición, los modelos ni `00_main.py`) y se
agregó la entrada de esta sesión.

## Resultados nuevos (tablas, figuras, métricas)

Las métricas no cambiaron respecto de la corrida anterior (diferencia relativa
máxima de 1e-15 en RMSE y MAPE de entrenamiento, CV y prueba). Algunas
predicciones del Random Forest cambiaron en el decimal 14 entre corridas, por
lo que git marca como modificadas las tablas que las contienen; no se encontró
otro cambio y no se revisó cada archivo.

RMSE en millones de COP, MAPE en %. Cada modelo se compara con la línea base
lineal de su misma escala. CV es la media de 5 folds sobre entrenamiento.

| Modelo | Escala | RMSE CV | RMSE prueba | MAPE CV | MAPE prueba | Dif. RMSE prueba vs CV | Dif. MAPE prueba vs CV (pp) |
|---|---|---|---|---|---|---|---|
| Línea base | log | 466.8 | 421.5 | 16.97 | 16.89 | −9.7% | −0.09 |
| Lineal completo | log | 450.8 | 382.6 | 15.51 | 15.40 | −15.1% | −0.11 |
| Lasso | log | 452.9 | 384.6 | 15.55 | 15.44 | −15.1% | −0.11 |
| Random Forest | log | 363.4 | 305.3 | 11.81 | 11.56 | −16.0% | −0.25 |
| XGBoost | log | 360.4 | 302.0 | 12.19 | 11.87 | −16.2% | −0.32 |
| Línea base | niveles | 507.7 | 472.9 | 34.71 | 35.54 | −6.9% | +0.83 |
| Lineal completo | niveles | 496.0 | 459.8 | 36.02 | 36.95 | −7.3% | +0.93 |
| Lasso | niveles | 496.2 | 459.9 | 35.63 | 36.49 | −7.3% | +0.85 |
| Random Forest | niveles | 348.5 | 288.5 | 12.45 | 12.13 | −17.2% | −0.32 |
| XGBoost | niveles | 366.4 | 290.2 | 12.68 | 12.31 | −20.8% | −0.37 |

Observaciones (descriptivas): el RMSE de prueba es menor que el de CV en todos
los modelos, lineales incluidos, lo que apunta a la composición del conjunto de
prueba más que a un modelo en particular (no se verificó, p. ej. revisando los
folds con precios extremos). El MAPE de CV y el de prueba difieren en menos de
1 punto porcentual. Los lineales en niveles producen entre 205 y 232
predicciones negativas en prueba. Las diferencias entre Random Forest y
XGBoost en RMSE de prueba están dentro de una desviación estándar entre folds
de CV (14 a 29 millones). El Random Forest queda con `min_samples_leaf=1`, el
borde inferior de su grilla (ver `04_hiperparametros.csv`).

## Uso de IA

- **Herramienta:** Claude Code (Claude Sonnet 5.5).
- **Para qué:** leer las tablas de métricas, hiperparámetros e importancia y
  resumirlas; editar el script, `CLAUDE.md`, `README.md` y `HANDOFF.md`; correr
  de nuevo el script; redactar esta bitácora.
- **Cómo se verificó:** la lectura inicial de la IA (sobreajuste según la regla
  del 10% y lectura de la brecha negativa) fue corregida por el usuario, que
  señaló que la regla no aplica a variables continuas. Tras el cambio se
  comparó la tabla de métricas regenerada con la versión versionada en `HEAD`
  (diferencia relativa máxima de 1e-15) y se confirmó con `grep` que no queda
  ninguna referencia a `UMBRAL_BRECHA_PCT` ni a `brecha_*` en el script. No se
  consultaron las diapositivas del curso: la afirmación de que la regla es para
  predicciones binarias es del usuario.

## Pendientes

- **Siguiente objetivo (elegido por el usuario):** análisis de errores por
  estrato y localidad y evaluación de impacto, en
  `02_Scripts/05_analisis_errores_impacto.py`. Las tablas
  `04_errores_por_estrato.csv` y `04_errores_por_localidad.csv` existen pero
  no se han leído ni interpretado.
- Preguntas para el equipo: qué tamaño mínimo de grupo se acepta para
  interpretar errores (el script marca los grupos con menos de 30 viviendas en
  prueba; estrato 1 tiene 16), y qué parte de la evaluación de impacto (prueba
  A/B) se diseña ahora y cuál queda como propuesta.
- Posible ampliación de la grilla del Random Forest (`min_samples_leaf`), por el
  valor en el borde de la grilla. No se hizo.
- Completar roles y correos de Maria Paula Rivera y Angelo Di Marco en
  `CLAUDE.md` (pendiente de sesiones anteriores).
- El commit `bd96c50` (partición, estimación y `00_main.py`) no tiene bitácora;
  corresponde al equipo documentarlo.
- Decisión metodológica propuesta para la tabla "Decisiones tomadas" de
  `CLAUDE.md`: no se diagnostica sobreajuste con un umbral entre RMSE o MAPE de
  entrenamiento y de prueba; se compara CV con prueba (la regla de las
  diapositivas es para predicciones binarias).
