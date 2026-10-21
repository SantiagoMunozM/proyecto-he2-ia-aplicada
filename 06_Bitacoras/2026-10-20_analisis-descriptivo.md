# Bitácora — 2026-10-20: análisis descriptivo de la base limpia

**Integrantes en la sesión:** Angelo Di Marco

## Resumen

El "Siguiente objetivo" que traía `HANDOFF.md` al iniciar la sesión era
`01_lectura_datos.py` (cargar el JSON crudo y normalizar el formato MongoDB
Extended JSON). Se escribió esa versión en una rama local (`Angelo`), pero al
revisar `main` se encontró que Santiago Muñoz ya había subido
`01_limpieza_datos.py`, que hace lectura y limpieza en un solo script (así lo
pidió el equipo, según la bitácora de esa sesión) y ya estaba en `main` junto
con `apartamentos_venta_limpio.csv`. Se descartó el trabajo de la rama
`Angelo` (queda respaldado en un `git stash` local, no en el historial de
`main`) y se actualizó a la versión de `main`.

Con la base limpia ya disponible, el objetivo pasó a ser el análisis
descriptivo que la bitácora de limpieza había dejado como "siguiente paso
elegido por el equipo": tablas y figuras desagregadas por estrato y
localidad. Se escribió `02_Scripts/02_analisis_descriptivo.py` y se corrió
sobre `apartamentos_venta_limpio.csv` (27,324 viviendas; este script no
filtra ni pierde observaciones). Se cumplió el objetivo.

De paso se resolvió el bloqueo de entorno de Python que señalaban
`HANDOFF.md` y la bitácora anterior (`python` no existía en esa máquina, sin
`requirements.txt`): se creó un entorno virtual local (`.venv/`, Python 3.12,
no versionado) y `requirements.txt` con las versiones exactas usadas.

## Archivos

- Creados:
  - `02_Scripts/02_analisis_descriptivo.py`
  - `03_Resultados/Tablas/02_distribucion_precio_area.csv`
  - `03_Resultados/Tablas/02_precio_m2_por_estrato.csv`
  - `03_Resultados/Tablas/02_precio_m2_por_localidad.csv`
  - `03_Resultados/Tablas/02_composicion_localidad_estrato.csv`
  - `03_Resultados/Tablas/02_composicion_website.csv`
  - `03_Resultados/Tablas/02_antiguedad_estrato_precio_m2.csv`
  - `03_Resultados/Tablas/02_asociacion_variables_sensibles.csv`
  - `03_Resultados/Figuras/02_histograma_precio_venta.png`
  - `03_Resultados/Figuras/02_histograma_area.png`
  - `03_Resultados/Figuras/02_histograma_precio_m2.png`
  - `03_Resultados/Figuras/02_boxplot_precio_m2_por_estrato.png`
  - `03_Resultados/Figuras/02_boxplot_precio_m2_por_localidad.png`
  - `requirements.txt`, `.gitignore`
  - `06_Bitacoras/2026-10-20_analisis-descriptivo.md` (este archivo)
- Modificados: `HANDOFF.md` (este cierre de sesión).
- Descartados sin llegar a `main`: `02_Scripts/01_lectura_datos.py`,
  `01_Datos/02_Limpios/apartamentos_normalizado.parquet` y
  `03_Resultados/Tablas/01_resumen_lectura.csv`, escritos primero en la rama
  `Angelo` y luego descartados al encontrar `01_limpieza_datos.py` ya en
  `main`. Quedan en un `git stash` local, no en el historial de `main`.
- Eliminados de la base: ninguno. No se tocaron los crudos ni la base limpia.

## Detalle por archivo

### `02_Scripts/02_analisis_descriptivo.py`

No filtra ni modifica la base limpia; solo la describe. Agrega una columna
derivada `precio_m2 = precio_venta / area` en memoria (no se guarda en el
CSV: ya se había usado en `01_limpieza_datos.py` para filtrar, pero no quedó
como columna en `apartamentos_venta_limpio.csv`, ver `CLAUDE.md`).

Produce, en una sola corrida:

- Estadísticas descriptivas (n, media, desviación estándar, min, p25,
  mediana, p75, max) de `precio_venta`, `area` y `precio_m2`, con un
  histograma de cada una.
- `precio_m2` (n, media, mediana, desviación estándar) por `estrato` y por
  `localidad`, ordenado por mediana.
- Composición de la muestra: conteos `localidad` × `estrato`, y conteo /
  porcentaje por `website`.
- `precio_m2` cruzando `antiguedad` × `estrato` (n, media, mediana).
- Asociación entre las variables sensibles (`estrato`, `localidad`,
  `barrio`), con el coeficiente de Cramér's V. Se usa Cramér's V y no una
  correlación porque las tres son categóricas (`estrato` es ordinal, pero se
  trata como categórica para compararla en la misma escala que `localidad` y
  `barrio`).
- Boxplots horizontales de `precio_m2` por `estrato` y por `localidad`,
  ordenados por mediana, sin mostrar valores atípicos (para que la caja sea
  legible con outliers ya filtrados en la limpieza).

### `requirements.txt` / `.gitignore` / `.venv/`

`requirements.txt` fija `pandas==2.2.3`, `numpy==2.1.3`, `pyarrow==18.1.0`,
`scikit-learn==1.5.2`, `xgboost==2.1.3`, `matplotlib==3.9.3`, probado con
Python 3.12 en un entorno virtual local (`.venv/`, excluido por
`.gitignore`). `pyarrow`, `scikit-learn` y `xgboost` no los usa todavía este
script (son para los pasos de modelado que siguen); se incluyeron de una vez
para fijar un único entorno para todo el pipeline en vez de ir agregando
`requirements.txt` por script.

## Resultados nuevos (tablas, figuras, métricas)

Todas salen de `02_Scripts/02_analisis_descriptivo.py` y están en
`03_Resultados/`:

- `02_distribucion_precio_area.csv`: estadísticas descriptivas de
  `precio_venta`, `area` y `precio_m2` sobre las 27,324 viviendas. Primer
  punto de referencia para cualquier métrica de error que se calcule después
  (p. ej. para poner el RMSE en la escala del precio).
- `02_precio_m2_por_estrato.csv` / `02_precio_m2_por_localidad.csv`: insumo
  directo para la desagregación de errores por estrato y localidad que exige
  `CLAUDE.md` en la sección de IA responsable — da el punto de comparación
  (cuánto varía el precio por m² entre grupos) antes de tener un modelo.
- `02_composicion_localidad_estrato.csv` / `02_composicion_website.csv`:
  composición de la muestra. Relevante para interpretar los resultados por
  grupo: el estrato 1 tiene 80 observaciones de 27,324, y 8 de las 19
  localidades tienen menos de 200.
- `02_antiguedad_estrato_precio_m2.csv`: cruce de `antiguedad` y `estrato`
  frente a `precio_m2`, para la línea base del curso que usa estas mismas
  variables (área, antigüedad, ubicación, estrato, habitaciones).
- `02_asociacion_variables_sensibles.csv`: matriz de Cramér's V entre
  `estrato`, `localidad` y `barrio`. Valores: estrato–localidad 0.467,
  estrato–barrio 0.803, localidad–barrio 0.999. Cuantifica, para la sección
  de IA responsable de `CLAUDE.md`, que `barrio` determina `localidad` casi
  por completo y que `estrato` está fuertemente asociado con ambas: las tres
  variables aportan información muy redundante entre sí.
- Figuras: histogramas de `precio_venta`, `area` y `precio_m2`; boxplots de
  `precio_m2` por `estrato` y por `localidad`.

## Uso de IA

- **Herramienta:** Claude Code (Claude Sonnet 5).
- **Para qué:** perfilar la estructura real del JSON crudo antes de escribir
  el primer script (`01_lectura_datos.py`, luego descartado), escribir y
  depurar `02_analisis_descriptivo.py`, resolver el conflicto entre la rama
  local y lo ya subido a `main` (`git stash`, `pull`, restauración selectiva
  de `requirements.txt` y `.gitignore`), y redactar esta bitácora y el
  `HANDOFF.md`.
- **Cómo se verificó:**
  - Todas las cifras de las tablas salen de corridas del script, no se
    escribieron a mano.
  - Se revisó manualmente una figura (boxplot por localidad) para confirmar
    que el orden y las etiquetas fueran correctos.
  - Se verificó a nivel de bytes que la columna `compañía` del JSON crudo
    está en UTF-8 válido: el carácter mal mostrado en la consola de Windows
    era un problema de la terminal, no de los datos ni de los archivos
    guardados.
  - Los commits de esta sesión (`Descriptivos`, `Resdultados Script
    Descritivos`) los hizo el usuario directamente desde el IDE, no esta
    sesión de Claude Code.

## Pendientes

- **Siguiente objetivo (elegido por el usuario en esta sesión):** línea base
  de regresión lineal, `03_modelo_baseline.py` — partición train/test,
  `Pipeline` con área, antigüedad, ubicación, estrato y habitaciones, RMSE y
  MAPE en entrenamiento y en prueba, `random_state=2026`.
- Decisiones de modelado que ese script va a tener que resolver (no
  bloquearon el descriptivo, sí al modelo):
  - Cómo codificar `barrio` (1,387 categorías) y `localidad`/`sector` dentro
    del `Pipeline`, ajustado solo con entrenamiento.
  - Si `website` entra como variable de control (`habi.co` es 2.9% de la
    muestra).
  - Partición aleatoria o temporal (`datetime` cubre solo del 3 de julio al 3
    de septiembre de 2024).
- Completar roles y correos de Maria Paula Rivera y Angelo Di Marco en
  `CLAUDE.md` (pendiente de sesiones anteriores).
- Queda un `git stash` local ("respaldo antes de resetear a main...") con el
  `01_lectura_datos.py` descartado y archivos relacionados. No se eliminó por
  si el equipo quiere revisarlo; se puede borrar con `git stash drop`.
- Sin cambios a `CLAUDE.md`: la sesión no tomó decisiones metodológicas
  nuevas, no descartó ningún análisis ni aplicó restricciones de muestra
  (el script solo describe, no filtra).
