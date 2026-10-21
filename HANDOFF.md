# HANDOFF

Resumen accionable del proyecto para retomar el trabajo. El detalle de cada
sesión está en `06_Bitacoras/`; aquí solo va lo necesario para saber dónde
estamos y qué sigue.

## Siguiente objetivo

<!-- Una sola tarea concreta, con el script o archivo que debe producirse y
     cómo se sabe que quedó terminada. Se reescribe al cerrar cada sesión. -->

**Objetivo:** análisis descriptivo de la base limpia, en
`02_Scripts/02_analisis_descriptivo.py`. Lee
`01_Datos/02_Limpios/apartamentos_venta_limpio.csv` (con
`parse_dates=['datetime', 'last_view']`) y escribe tablas en
`03_Resultados/Tablas/` y figuras en `03_Resultados/Figuras/`, con prefijo `02_`.

**Criterio de terminado:** el script corre desde la raíz sin intervención y
produce, desde la misma corrida (sin números a mano):

- distribución de `precio_venta`, `area` y precio por m²;
- precio por m² (conteo, media, mediana) por estrato y por localidad;
- composición de la muestra por localidad × estrato y por `website`;
- relación entre `antiguedad`, `estrato` y precio por m²;
- tabla de las variables sensibles (estrato, localidad, barrio) y su asociación
  entre sí, como insumo de la sección de IA responsable.

**Bloqueos / preguntas abiertas:**

- Definir el entorno de Python: `python` no existe en esta máquina; el script de
  limpieza se corrió con `/usr/bin/python3` (3.9, pandas 2.2.0). Falta
  `requirements.txt` y `00_main.py`.
- Decidir si los gráficos se hacen con matplotlib (requiere instalarlo; no se
  verificó si está disponible).
- Completar roles y correos de Maria Paula Rivera y Angelo Di Marco en
  `CLAUDE.md`.
- Abiertas para el modelado, no bloquean el descriptivo: cómo codificar `barrio`
  (1,387 categorías), si `website` entra como variable (habi.co es 2.9%) y
  partición aleatoria o temporal (`datetime` cubre solo 3 jul–3 sep de 2024).

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
- Sin particiones train/test, modelos ni figuras. Sin `00_main.py` ni
  `requirements.txt`.
- Los archivos de la sesión del 2026-10-20 (limpieza) están en `main` en GitHub.

## Registro de sesiones

<!-- Una entrada por sesión, la más reciente arriba. Tres a cinco líneas:
     qué se hizo y enlace a la bitácora. -->

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
