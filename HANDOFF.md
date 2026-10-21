# HANDOFF

Resumen accionable del proyecto para retomar el trabajo. El detalle de cada
sesión está en `06_Bitacoras/`; aquí solo va lo necesario para saber dónde
estamos y qué sigue.

## Siguiente objetivo

<!-- Una sola tarea concreta, con el script o archivo que debe producirse y
     cómo se sabe que quedó terminada. Se reescribe al cerrar cada sesión. -->

**Objetivo:** línea base de regresión lineal, en `02_Scripts/03_modelo_baseline.py`.
Lee `01_Datos/02_Limpios/apartamentos_venta_limpio.csv` (con
`parse_dates=['datetime', 'last_view']`), separa un conjunto de prueba al
inicio y entrena, dentro de un `Pipeline`, una `LinearRegression` con área,
antigüedad, ubicación, estrato y habitaciones.

**Criterio de terminado:** el script corre desde la raíz sin intervención,
con `random_state=2026` en la partición, y reporta desde la misma corrida
(sin números a mano), en `03_Resultados/Tablas/` con prefijo `03_`:

- RMSE y MAPE en entrenamiento y en prueba;
- los mismos errores desagregados por estrato y por localidad.

**Bloqueos / preguntas abiertas:**

- Cómo codificar `barrio` (1,387 categorías) y `localidad`/`sector` dentro del
  `Pipeline`, ajustado solo con entrenamiento.
- Si `website` entra como variable de control (`habi.co` es 2.9% de la
  muestra).
- Partición aleatoria o temporal (`datetime` cubre solo del 3 de julio al 3 de
  septiembre de 2024).
- Completar roles y correos de Maria Paula Rivera y Angelo Di Marco en
  `CLAUDE.md`.
- Falta `00_main.py` que corra el pipeline completo (lectura+limpieza →
  descriptivo → modelo) en una sesión limpia.

## Estado actual

<!-- Qué existe y funciona hoy: datos, scripts, resultados. Se actualiza al
     cerrar cada sesión; no es un historial. -->

- `CLAUDE.md` con contexto, reglas, decisiones, análisis descartados y
  restricciones de muestra; `HANDOFF.md`; skill de proyecto `registrar-sesion`.
- Datos crudos versionados en `01_Datos/01_Crudos/`: JSON principal (43,013
  registros), `README_columnas.md` y `external/`.
- `02_Scripts/01_limpieza_datos.py`: lee el JSON, normaliza el Extended JSON,
  contrasta columnas y tipos con el README, aplica el alcance (ventas), las
  exclusiones, `SIN_DATO` en `sector`/`barrio` y los filtros de validez, y
  guarda la base limpia. Corre desde la raíz con `python3`.
- `01_Datos/02_Limpios/apartamentos_venta_limpio.csv`: 27,324 viviendas × 36
  columnas, sin N/A, tipos verificados (23.2 MB).
- `03_Resultados/Tablas/01_*.csv`: resumen de columnas, embudo de pérdida de
  observaciones, pérdida por localidad y estrato, estadísticas numéricas y
  anomalías.
- `02_Scripts/02_analisis_descriptivo.py`: no filtra, describe la base limpia.
  Produce distribución de precio/área/precio por m², precio por m² por
  estrato y por localidad, composición de la muestra (localidad × estrato,
  `website`), cruce antigüedad × estrato, y la asociación (Cramér's V) entre
  estrato, localidad y barrio. Corre desde la raíz.
- `03_Resultados/Tablas/02_*.csv` y `03_Resultados/Figuras/02_*.png`: tablas y
  figuras del análisis descriptivo (ver bitácora para el detalle de cada una).
- `requirements.txt` fija el entorno (`pandas`, `numpy`, `pyarrow`,
  `scikit-learn`, `xgboost`, `matplotlib`), probado con Python 3.12 en un
  entorno virtual local (`.venv/`, no versionado). `.gitignore` lo excluye.
- Sin particiones train/test, modelos ni `00_main.py` todavía.
- Los archivos de las sesiones del 2026-10-20 (limpieza y descriptivo) están
  en `main` en GitHub.

## Registro de sesiones

<!-- Una entrada por sesión, la más reciente arriba. Tres a cinco líneas:
     qué se hizo y enlace a la bitácora. -->

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
