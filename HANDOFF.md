# HANDOFF

Resumen accionable del proyecto para retomar el trabajo. El detalle de cada
sesión está en `06_Bitacoras/`; aquí solo va lo necesario para saber dónde
estamos y qué sigue.

## Siguiente objetivo

<!-- Una sola tarea concreta, con el script o archivo que debe producirse y
     cómo se sabe que quedó terminada. Se reescribe al cerrar cada sesión. -->

**Objetivo:** ampliar la grilla del Random Forest en
`02_Scripts/04_estimacion_modelos.py` (`min_samples_leaf=1` quedó en el borde de
`GRILLA_RF`, p. ej. agregar valores menores de `max_features` y mayores de
`min_samples_leaf` sin tocar la partición) y volver a correr 04 y 05, antes de
interpretar o presentar los errores por estrato y localidad.

**Criterio de terminado:** `GRILLA_RF` ampliada con el valor elegido por CV en el
interior de la grilla (o anotado que sigue en el borde); `python 00_main.py` corre
completo sin intervención, incluido `05_analisis_errores_impacto.py`; las tablas
`04_*` y `05_*` quedan regeneradas y se reporta cuánto cambian RMSE y MAPE de
prueba del Random Forest frente a la línea base respecto de la grilla anterior.

**Bloqueos / preguntas abiertas:**

- Confirmar con el equipo el umbral de 30 viviendas en prueba para interpretar un
  grupo (estrato 1 tiene 16) y qué parte de la evaluación de impacto se calcula
  (error de precio) y cuál queda como propuesta (tiempo de compra/venta y ahorro).
- Completar roles y correos de Maria Paula Rivera y Angelo Di Marco en
  `CLAUDE.md`.
- Documentar la sesión del commit `bd96c50` (partición y estimación), que no
  tiene bitácora.
- Pendiente de fondo: modelo de texto con `descripcion` y sección de IA
  responsable para las presentaciones de avance.

## Estado actual

<!-- Qué existe y funciona hoy: datos, scripts, resultados. Se actualiza al
     cerrar cada sesión; no es un historial. -->

- `CLAUDE.md` con contexto, reglas, decisiones, análisis descartados y
  restricciones de muestra; `HANDOFF.md`; skill de proyecto `registrar-sesion`.
- Datos crudos versionados en `01_Datos/01_Crudos/`: JSON principal (43,013
  registros), `README_columnas.md` y `external/`.
- `02_Scripts/01_limpieza_datos.py`: lee el JSON, normaliza el Extended JSON,
  aplica el alcance (ventas), las exclusiones y los filtros de validez, y guarda
  `01_Datos/02_Limpios/apartamentos_venta_limpio.csv` (27,324 viviendas × 36
  columnas, sin N/A). Tablas `03_Resultados/Tablas/01_*.csv`.
- `02_Scripts/02_analisis_descriptivo.py`: describe la base limpia sin filtrarla.
  Tablas `02_*.csv` y figuras `02_*.png`.
- `02_Scripts/03_particion_muestra.py`: partición 80/20 estratificada por estrato
  (`random_state=2026`), guardada en `01_Datos/02_Limpios/particion_train_test.csv`
  (21,859 en entrenamiento, 5,465 en prueba); tabla `03_composicion_particion.csv`.
- `02_Scripts/04_estimacion_modelos.py`: línea base lineal, lineal completo,
  Lasso, Random Forest y XGBoost, cada uno con el objetivo en log y en niveles,
  con hiperparámetros por CV de 5 folds sobre entrenamiento. Reporta RMSE y MAPE
  en entrenamiento, CV y prueba, la diferencia entre prueba y CV (sin umbral), el
  cambio frente a la línea base, coeficientes, importancia de variables y errores
  por estrato y localidad. Tablas y figuras `04_*` en `03_Resultados/`. Tarda
  varios minutos por las grillas de Random Forest y XGBoost.
- `00_main.py` corre en orden todos los scripts numerados de `02_Scripts/`.
- `requirements.txt` fija el entorno (Python 3.13, `.venv/` local no versionado).
- `02_Scripts/05_analisis_errores_impacto.py`: lee las predicciones de prueba de
  04 y compara la línea base con el Random Forest por estrato y localidad (RMSE,
  MAE, sesgo, proporción sobre/subvalorada, grupos de menos de 30 viviendas
  marcados), calcula el costo esperado por vivienda para comprador y vendedor y
  dimensiona la prueba A/B del error de precio. Tablas y figuras `05_*`.
- Sin modelo de texto y sin evaluación de impacto con datos reales (tiempo de
  compra/venta y ahorro quedan como propuesta). Los resultados `04_*` y `05_*`
  dependen de la grilla actual del Random Forest.

## Registro de sesiones

<!-- Una entrada por sesión, la más reciente arriba. Tres a cinco líneas:
     qué se hizo y enlace a la bitácora. -->

### 2026-10-20: análisis de errores por estrato y localidad y evaluación de impacto

- Santiago Muñoz (inferido del usuario de git). Se escribió
  `02_Scripts/05_analisis_errores_impacto.py`: errores de prueba por estrato y
  localidad (línea base y Random Forest), costo esperado para comprador y vendedor
  y dimensionamiento de la prueba A/B del error de precio. Tablas y figuras `05_*`.
- Se fijó el umbral de 30 viviendas para marcar grupos; tiempo de compra/venta y
  ahorro quedan como propuesta. No se corrió `00_main.py` completo.
- Bitácora: [2026-10-20_analisis-errores-impacto.md](06_Bitacoras/2026-10-20_analisis-errores-impacto.md)

### 2026-10-20: revisión de las métricas de los modelos

- Santiago Muñoz (inferido del usuario de git). Se revisaron los resultados de
  `04_estimacion_modelos.py` (escrito en el commit `bd96c50`, sin bitácora).
- Se retiró la regla del 10% entre RMSE/MAPE de entrenamiento y prueba como
  diagnóstico de sobreajuste (está definida para predicciones binarias): se
  quitó del script y de `CLAUDE.md`, y se agregó la comparación descriptiva CV
  frente a prueba. Las métricas no cambiaron tras volver a correr.
- Se actualizaron `README.md` y el estado de este archivo, que no incluían la
  partición, los modelos ni `00_main.py`.
- Bitácora: [2026-10-20_revision-metricas-modelos.md](06_Bitacoras/2026-10-20_revision-metricas-modelos.md)

### 2026-10-20: análisis descriptivo de la base limpia

- Angelo Di Marco. Se escribió `02_Scripts/02_analisis_descriptivo.py`: tablas
  y figuras de precio, área y precio por m² desagregadas por estrato y
  localidad, composición de la muestra y asociación (Cramér's V) entre
  estrato, localidad y barrio.
- Se resolvió el bloqueo de entorno de Python (`requirements.txt` + entorno
  virtual local, Python 3.12).
- Un intento inicial de `01_lectura_datos.py` en una rama aparte se descartó
  al encontrar que `01_limpieza_datos.py` ya cubría lectura y limpieza juntas
  en `main`.
- Bitácora: [2026-10-20_analisis-descriptivo.md](06_Bitacoras/2026-10-20_analisis-descriptivo.md)

### 2026-10-20: lectura, reconocimiento y limpieza de los datos

- Santiago Muñoz. Se escribió `02_Scripts/01_limpieza_datos.py` y se generó la
  base limpia: de 43,013 registros a 27,324 viviendas en venta, 36 columnas, sin
  N/A.
- Decisiones: se excluyeron `compañia`, `administracion` y `estado`; `sector` y
  `barrio` en N/A pasan a `SIN_DATO`; filtros de `area`, estrato 1 a 6, baños y
  precio por m² entre 1 y 40 millones.
- Se revisaron los outliers y los `banos == 0` contra la descripción; se
  registraron decisiones y restricciones de muestra en `CLAUDE.md`.
- Bitácora: [2026-10-20_limpieza-datos.md](06_Bitacoras/2026-10-20_limpieza-datos.md)

### 2026-10-20: configuración inicial

- Santiago Muñoz. Se crearon `CLAUDE.md`, `HANDOFF.md` y la skill
  `registrar-sesion`.
- Se movieron los crudos a `01_Datos/01_Crudos/` sin modificarlos y se creó la
  estructura de carpetas (dos niveles de datos: crudos y limpios).
- Primer commit y push a `main`.
- Bitácora: [2026-10-20_configuracion-inicial.md](06_Bitacoras/2026-10-20_configuracion-inicial.md)
