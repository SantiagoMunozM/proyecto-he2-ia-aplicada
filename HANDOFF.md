# HANDOFF

Resumen accionable del proyecto para retomar el trabajo. El detalle de cada
sesión está en `06_Bitacoras/`; aquí solo va lo necesario para saber dónde
estamos y qué sigue.

## Siguiente objetivo

<!-- Una sola tarea concreta, con el script o archivo que debe producirse y
     cómo se sabe que quedó terminada. Se reescribe al cerrar cada sesión. -->

**Objetivo:** hacer un borrador de presentación con los resultados de aprendizaje
profundo y texto (pasos 1, 2, 3 y 5 del plan de
`05_Notas/alternativas_aprendizaje_profundo_descripcion.md`), para la presentación de
avance. Debe producirse `04_Presentaciones/borrador_aprendizaje_profundo.md`, con una
sección por diapositiva: mensaje, figura o tabla de `03_Resultados/` que la sustenta (ruta)
y notas del expositor. Luego se lleva a la presentación de Canva. Las diapositivas mínimas
son:

- por qué la descripción (estructura de los datos) y cómo se evitó la fuga del precio
  (`09_enmascaramiento.csv`);
- qué se estimó: palabras clave, TF-IDF, vectores e5 con RF y MLP híbrido, con su pareja
  sin texto;
- todas las variantes contra la línea base (`13_rmse_todas_variantes.png`,
  `13_comparacion_modelos.csv`);
- errores y sesgos por estrato y la ablación sin estrato ni localidad
  (`13_mape_estrato_texto.png`, `13_sesgo_estrato_texto.png`, `13_resumen_sesgos.csv`);
- obstáculos (tiempo de cómputo, ruido entre folds) y el paso siguiente (extracción con
  LLM).

**Criterio de terminado:** el archivo existe, cada cifra citada apunta a una tabla o figura
de `03_Resultados/` (ningún número escrito a mano sin fuente), cada criterio de la rúbrica
del avance (`../Rubrica_Presentacion_Avance.xlsx`) que toca el aprendizaje profundo tiene al
menos una diapositiva, y el texto no emite juicios de "bueno" o "malo" sobre los resultados.

**Bloqueos / preguntas abiertas:**

- Confirmar con el equipo:
  - las librerías nuevas, `torch` y `sentence-transformers`;
  - si se enmascaran los nombres de barrio en `descripcion`;
  - el uso de `cross_validate` y `GridSearchCV`;
  - la eliminación de anuncios repetidos;
  - el umbral de 30 viviendas en prueba para interpretar un grupo (estrato 1 tiene 16).
- Paso 4 (extracción con LLM, `12_texto_llm.py`): decidir proveedor, presupuesto y SDK, y
  quién etiqueta a mano las 200 descripciones de validación. ¿Entra en la presentación como
  propuesta o con resultados?
- Actualizar las cifras † de la nota de alternativas: dice 1,190 descripciones con el precio
  literal y la corrida da 1,057.
- Siguen abiertos de antes:
  - la revisión completa contra la rúbrica (`05_Notas/revision_resultados_avance.md`);
  - roles y correos de Maria Paula Rivera y Angelo Di Marco en `CLAUDE.md`;
  - la bitácora del commit `bd96c50`.

## Estado actual

<!-- Qué existe y funciona hoy: datos, scripts, resultados. Se actualiza al
     cerrar cada sesión; no es un historial. -->

- `CLAUDE.md` con contexto, reglas, decisiones, análisis descartados y
  restricciones de muestra; `HANDOFF.md`; skill de proyecto `registrar-sesion`.
- Datos crudos versionados en `01_Datos/01_Crudos/`: JSON principal (43,013
  registros), `README_columnas.md` y `external/`.
- `02_Scripts/01_limpieza_datos.py`: lee el JSON, normaliza el Extended JSON,
  aplica el alcance (ventas), las exclusiones y los filtros de validez, y guarda
  `01_Datos/02_Limpios/apartamentos_venta_limpio.csv` (26,900 viviendas × 36
  columnas, sin N/A). Elimina los anuncios repetidos (idénticos salvo `codigo` y
  fechas; 424 filas, lista en `01_duplicados_eliminados.csv`). Tablas
  `03_Resultados/Tablas/01_*.csv`.
- `02_Scripts/02_analisis_descriptivo.py`: describe la base limpia sin filtrarla.
  Tablas `02_*.csv` y figuras `02_*.png`.
- `02_Scripts/03_particion_muestra.py`: partición 80/20 estratificada por estrato
  (`random_state=2026`), guardada en `01_Datos/02_Limpios/particion_train_test.csv`
  (21,520 en entrenamiento, 5,380 en prueba); tabla `03_composicion_particion.csv`.
- `02_Scripts/04_estimacion_modelos.py`: línea base lineal, lineal completo,
  Lasso, Random Forest y XGBoost, cada uno con el objetivo en log y en niveles, con
  hiperparámetros por CV de 5 folds sobre entrenamiento (`cross_validate`;
  `GridSearchCV` para RF y XGBoost en niveles). El RF elige `min_samples_leaf=1` y
  `max_features` 0.5 (log) y 0.33 (niveles). Reporta RMSE y MAPE en entrenamiento, CV y
  prueba, importancia de variables y errores por estrato y localidad. Tablas y figuras
  `04_*`. Tarda unos 27 min.
- `02_Scripts/05_analisis_errores_impacto.py`: compara la línea base con el RF por
  estrato y localidad, costo esperado para comprador y vendedor, dimensionamiento de la
  prueba A/B del error de precio y sensibilidad a gemelos. Tablas y figuras `05_*`.
- `02_Scripts/06_figuras_presentacion.py` (figuras `06_*` con la paleta de las
  diapositivas), `07_perfil_descripcion.py` (perfil del texto de `descripcion`, tablas
  `07_*`) y `08_objetivos_practicos.py` (error típico por estrato en pesos y un ejemplo
  de vivienda, tablas `08_*`).
- **Modelos de texto (aprendizaje profundo):**
  - `09_texto_limpieza.py`: enmascara dinero, teléfonos y correos en `descripcion` y
    crea 17 variables por palabras clave. Escribe
    `01_Datos/02_Limpios/descripcion_limpia.csv` y las tablas `09_*`. En la corrida, 1,057
    descripciones tenían el precio literal antes de enmascarar y 0 después.
  - `10_texto_embeddings.py`: vectores de `intfloat/multilingual-e5-base` (revisión fija)
    en `01_Datos/02_Limpios/embeddings_e5_base.npz`. No recalcula si ya coinciden con la
    base; calcularlos tarda unos 14 min.
  - `11_modelos_texto.py`: RF con palabras clave, con PCA de TF-IDF y con PCA de e5;
    Ridge con TF-IDF; y MLP híbrido en PyTorch. Cada variante tiene su pareja sin texto, en
    log y en niveles, con ablación sin estrato ni localidad. Tablas `11_*`. Tarda unos
    33 min.
- `02_Scripts/13_comparacion_final.py`: las 15 variantes contra la línea base en
  `13_comparacion_modelos.csv`, resumen de sesgos por estrato y localidad y tres figuras
  `13_*` para la presentación. El número 12 está reservado para la extracción con LLM
  (paso 4), que no existe todavía.
- `00_main.py` corre en orden todos los scripts numerados; la corrida completa de 01 a 11
  está verificada (2026-11-09, 60 min, sin errores).
- `requirements.txt` fija el entorno (Python 3.13, con `torch` y `sentence-transformers`;
  `.venv/` local no versionado).
- Presentación de avance en Canva y su PDF en `04_Presentaciones/`, con las cifras de la
  corrida del 2026-10-21. Todavía no incluye los resultados de texto.
- Sin evaluación de impacto con datos reales (tiempo de compra/venta y ahorro quedan como
  propuesta).

## Registro de sesiones

<!-- Una entrada por sesión, la más reciente arriba. Tres a cinco líneas:
     qué se hizo y enlace a la bitácora. -->

### 2026-11-09: modelos de texto con la descripción y comparación final

- Santiago Muñoz (inferido del usuario de git). Pasos 1, 2, 3 y 5 del plan de la nota de
  alternativas:
  - `09` enmascara dinero, teléfonos y correos y crea las variables por palabras clave;
  - `10` calcula los vectores de `multilingual-e5-base`;
  - `11` estima RF, Ridge y un MLP híbrido en PyTorch con y sin texto;
  - `13` compara las 15 variantes contra la línea base y resume los sesgos.
- Las grillas se recortaron tras una corrida de 7.2 h. `00_main.py` corrió completo
  (60 min). Se agregaron seis decisiones a `CLAUDE.md` y las librerías de texto a
  `requirements.txt`.
- El objetivo anterior (revisión contra la rúbrica) no se trabajó. El siguiente es el
  borrador de la presentación con estos resultados. El paso 4 (extracción con LLM) queda
  pendiente.
- Bitácora: [2026-11-09_modelos-texto-aprendizaje-profundo.md](06_Bitacoras/2026-11-09_modelos-texto-aprendizaje-profundo.md)

### 2026-10-21: base de 2023 y eliminación de anuncios repetidos

- Santiago Muñoz (inferido del usuario de git). Se revisó la base de 2023 de la fuente y
  se descartó (35.4% de las ventas de 2024 reaparecen, faltan variables, 158 MB).
- Se eliminaron 424 anuncios repetidos (idénticos salvo `codigo` y fechas) en
  `01_limpieza_datos.py`: la base queda en 26,900 y la partición se reasignó. Se agregó
  la sensibilidad a gemelos en 05 y su figura en 06; `00_main.py` corrió completo (23 min).
- Se actualizó la presentación de Canva con las cifras nuevas y una diapositiva del
  obstáculo. El objetivo anterior (revisión contra la rúbrica) no se trabajó y se mantiene.
- Bitácora: [2026-10-21_anuncios-repetidos-datos-2023.md](06_Bitacoras/2026-10-21_anuncios-repetidos-datos-2023.md)

### 2026-10-21: `cross_validate`, `GridSearchCV` y grilla del Random Forest

- Santiago Muñoz (inferido del usuario de git). En `04_estimacion_modelos.py`,
  `cross_validate` reemplaza el ciclo manual de CV y `GridSearchCV` elige los
  hiperparámetros con el objetivo en niveles; `CLAUDE.md` se actualizó. Con la
  grilla anterior las tablas coinciden con las previas (diferencia máxima de 6e-6).
- Se amplió `GRILLA_RF`: `max_features` queda en el interior (0.5 en log, 0.4 en
  niveles) y `min_samples_leaf=1` sigue siendo el elegido (es el mínimo posible).
  `00_main.py` corrió completo (14.2 min) y se regeneraron las tablas `04_*` y `05_*`.
- Objetivo anterior cumplido; el siguiente es revisar los resultados contra la
  rúbrica del avance.
- Bitácora: [2026-10-21_cross-validate-gridsearch-grilla-rf.md](06_Bitacoras/2026-10-21_cross-validate-gridsearch-grilla-rf.md)

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
