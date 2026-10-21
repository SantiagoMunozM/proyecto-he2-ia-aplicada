# Bitácora — 2026-10-20: lectura, reconocimiento y limpieza de los datos

**Integrantes en la sesión:** Santiago Muñoz

## Resumen

Objetivo: escribir el primer script del pipeline, que lee el JSON crudo, lo
normaliza, hace un reconocimiento de la base (tipos frente al README de
columnas, faltantes, estadísticas, anomalías), elimina las observaciones con
N/A y guarda la base limpia en `01_Datos/02_Limpios/`.

El "Siguiente objetivo" que traía `HANDOFF.md` era `01_lectura_datos.py` (cargar
y normalizar el JSON, guardar en Limpios y reportar registros y faltantes por
columna). Se cumplió, con un alcance mayor, en un solo script llamado
`01_limpieza_datos.py` porque el equipo pidió lectura y limpieza juntas.

Desarrollo:

1. Se perfiló el JSON antes de escribir el script. Hallazgos que cambiaron el
   diseño:
   - Eliminar toda fila con algún N/A deja **0 filas**: `piso` y `closets` son
     100% N/A, `direccion` y `url` 98%, y `precio_arriendo` es N/A en toda venta.
   - Los numéricos vienen como números nativos, no como texto (lo que decía
     `CLAUDE.md`). Los faltantes sí vienen como `{'$numberDouble': 'NaN'}`.
   - El JSON trae 46 columnas. El README de columnas lista 3 que no existen
     (`centro_comercial_cercano`, `distancia_centro_comercial_m`,
     `is_cerca_centro_comercial`), y el JSON trae `_id` y `direccion`, que el
     README no menciona.
2. Se definió un alcance y una regla de N/A explícitos (ver abajo) y el equipo
   fue ajustándolos a medida que se revisaban los datos: se quitaron `compañia`,
   `administracion` y `estado`; `sector` y `barrio` en N/A pasaron a una
   categoría `SIN_DATO`; se agregaron filtros de validez.
3. Se revisaron los outliers de `precio_venta` y `area` y las viviendas sin
   baños, contrastando con el texto de `descripcion`. Se aplicó un filtro de
   precio por m² y otro de baños.

## Archivos

- Creados:
  - `02_Scripts/01_limpieza_datos.py`
  - `01_Datos/02_Limpios/apartamentos_venta_limpio.csv` (27,324 filas × 36
    columnas, 23.2 MB)
  - `03_Resultados/Tablas/01_resumen_columnas.csv`
  - `03_Resultados/Tablas/01_perdida_observaciones.csv`
  - `03_Resultados/Tablas/01_perdida_por_localidad_estrato.csv`
  - `03_Resultados/Tablas/01_estadisticas_numericas.csv`
  - `03_Resultados/Tablas/01_anomalias.csv`
  - `06_Bitacoras/2026-10-20_limpieza-datos.md` (este archivo)
- Modificados: `HANDOFF.md`, `README.md` (secciones Datos, Estructura del
  repositorio y Cómo reproducir), `CLAUDE.md` (corrección sobre el formato del
  JSON y tablas de decisiones, análisis descartados y restricciones de muestra).
- Eliminados: ninguno. Los crudos no se tocaron.

## Detalle por archivo

### `02_Scripts/01_limpieza_datos.py`

Un solo script, que se corre desde la raíz y lee solo de `01_Datos/01_Crudos/`.
Las rutas se anclan a la raíz del proyecto a partir de la ubicación del script.
Los parámetros de la limpieza son constantes al inicio.

Pasos y la intuición de cada decisión:

- **Lectura y normalización.** Convierte `$numberDouble`, `$oid` y `$date` a
  valores de Python y también acepta numéricos en texto. Las cadenas vacías en
  columnas de texto se tratan como faltante.
- **Contraste con el README.** Lee los nombres de columna directamente de la
  tabla de `README_columnas.md` (ignorando la tabla de imágenes comentada) y
  reporta las que están en un lado y no en el otro. Cada columna tiene un tipo
  esperado (texto, entero, decimal, binario, fecha) y el script falla si una
  columna no tiene tipo definido o si un valor no se puede convertir.
- **Alcance.** Se conservan `VENTA` y `VENTA Y ARRIENDO`, porque son las que
  tienen `precio_venta`, la variable objetivo. `precio_arriendo` es un problema
  aparte (decisión de la propuesta).
- **Columnas descartadas** (9): `_id` y `timeline` (no entran en un CSV plano
  ni están en el README), `direccion`, `url`, `precio_arriendo`, `piso` y
  `closets` (más de 50% de N/A dentro del alcance, regla del umbral), y por
  decisión del equipo `compañia`, `administracion` y `estado`.
  - `administracion` está en N/A en todos los proyectos nuevos (sobre planos, en
    construcción, para estrenar), que de otro modo se perderían. Los N/A de ahí
    tienen sentido: la cuota todavía no existe.
  - `compañia` es metadato del anuncio y habi.co no la reporta. `estado` es
    redundante con `antiguedad` (todos los `NUEVO` son exactamente `SOBRE
    PLANOS`, `EN CONSTRUCCION` o `PARA ESTRENAR`; el resto es `USADO`) y habi.co
    tampoco la reporta (las 796 filas con `estado` en N/A tienen `compañia` en
    N/A). Mantener estas tres columnas habría eliminado de la muestra todas las
    viviendas `NUEVO`, las casas y toda la fuente habi.co.
- **`sector` y `barrio` en N/A → `SIN_DATO`.** El N/A de ubicación categórica se
  conserva como categoría (constante, no aprendida de los datos, sin fuga de
  información). Eran 771 y 143 filas. Se prefirió a eliminar la fila o la
  variable porque `barrio` es la variable de ubicación con más poder
  explicativo y el N/A cae parejo entre localidades y estratos (2.4% a 5.4%).
- **Eliminación de N/A en el resto de columnas.** Pierde 13 filas (1 en
  `estrato`, 10 en `antiguedad`, 2 en `website`).
- **Corrección:** `parqueaderos` negativo se toma como 0 (era una fila con -2).
- **Filtros de validez:** `area > 0`, estrato entre 1 y 6 inclusive,
  `banos >= 1` (`banos == 0` se trata como faltante) y precio por m² entre 1 y
  40 millones de COP.
- **Tipos finales.** Enteros (`int64`), decimales (`float64`), binarios
  (`bool`) y fechas (`datetime64`). El script verifica que cada tipo coincida
  con el esperado y relee el CSV para comprobar forma, tipos y ausencia de N/A.
- **Anomalías.** Se reportan en una tabla; las que ya tienen filtro dan 0.
  Quedan `coords_modified == True` (566 filas), que no se filtran.

### `01_Datos/02_Limpios/apartamentos_venta_limpio.csv`

Base limpia que consumirán los scripts siguientes. Formato CSV UTF-8, 23.2 MB,
por debajo de los 50 MB que GitHub advierte. Los tipos se recuperan al leerla
con `parse_dates=['datetime', 'last_view']`.

### `README.md` y `CLAUDE.md`

- `README.md`: se actualizaron "Datos" (formato de los numéricos, base limpia,
  advertencias nuevas), "Estructura del repositorio" y "Cómo reproducir".
- `CLAUDE.md`: se corrigió la línea sobre el formato del JSON y se registraron
  las decisiones, el análisis descartado y las restricciones de muestra, con
  aprobación del equipo en la sesión.

## Resultados nuevos (tablas, figuras, métricas)

Todas salen de `02_Scripts/01_limpieza_datos.py` y están en
`03_Resultados/Tablas/`:

- `01_perdida_observaciones.csv`: embudo de la limpieza, paso a paso. Es la
  tabla que exige `CLAUDE.md` (cuántas observaciones se pierden en cada filtro).
- `01_perdida_por_localidad_estrato.csv`: observaciones del alcance y finales
  por localidad y por estrato. Sirve para ver si la limpieza sesga la
  composición, insumo de la sección de IA responsable.
- `01_resumen_columnas.csv`: por columna, presencia en el README y en el JSON,
  tipos crudos, tipo esperado y final, faltantes, valores únicos, columnas
  descartadas y observaciones (incluye la nota de que `chimenea`,
  `permite_mascotas` y `salon_comunal` son constantes en `False`).
- `01_estadisticas_numericas.csv`: estadísticas descriptivas de las variables
  numéricas de la base limpia.
- `01_anomalias.csv`: conteo de reglas de calidad sobre la base limpia.

Pérdida de observaciones (de `01_perdida_observaciones.csv`):

| Paso | Antes | Después | Pierde |
| --- | ---: | ---: | ---: |
| Registros leídos | 43,013 | 43,013 | 0 |
| Alcance: `VENTA` y `VENTA Y ARRIENDO` | 43,013 | 27,498 | 15,515 |
| N/A en `estrato`, `antiguedad` y `website` | 27,498 | 27,485 | 13 |
| `area > 0` | 27,485 | 27,466 | 19 |
| `1 <= estrato <= 6` | 27,466 | 27,459 | 7 |
| `banos >= 1` | 27,459 | 27,445 | 14 |
| Precio por m² entre 1 y 40 millones | 27,445 | 27,324 | 121 |
| **Total** | **43,013** | **27,324** | **15,689** |

Además, 914 valores de `sector`/`barrio` se pasaron a `SIN_DATO` (771 y 143) y 1
valor de `parqueaderos` se corrigió a 0, sin perder filas.

La pérdida por grupo es pequeña: por estrato va de 0% (estrato 1) a 0.8%
(estrato 6) y por localidad el máximo es 1.3% (Barrios Unidos, 2 de 155), sin
contar los 8 registros con estrato 0 o N/A, que se pierden por completo.

## Uso de IA

- **Herramienta:** Claude Code (Claude Sonnet 5.5).
- **Para qué:** perfilar el JSON, proponer el diseño de la limpieza, escribir y
  depurar `01_limpieza_datos.py`, revisar los outliers y las viviendas sin
  baños, y redactar esta bitácora, el `HANDOFF.md` y los cambios a `README.md` y
  `CLAUDE.md`.
- **Cómo se verificó:**
  - Los conteos salen de corridas del script, no se escribieron a mano; el
    script tiene verificaciones propias (tipos, ausencia de N/A, unicidad de
    `codigo`, relectura del CSV). La primera corrida falló en una verificación
    (una columna sin tipo definido) y la corrida posterior a un cambio falló por
    una regla que apuntaba a una columna ya excluida; ambas se corrigieron y se
    volvió a correr completo.
  - Una afirmación propia resultó incorrecta y se corrigió en la sesión: se
    había dicho que la pérdida desigual por localidad venía de `sector` y
    `barrio`; al medirla venía de `estado`.
  - Los outliers y los `banos == 0` se contrastaron con el texto de
    `descripcion`. La hipótesis de errores de escala en el precio (×1000) es
    consistente con los datos, pero **no se pudo verificar** porque las
    descripciones no mencionan el precio.
  - Santiago Muñoz decidió cada exclusión, el tratamiento de `SIN_DATO`, el
    estrato inclusivo hasta 6 y los dos últimos filtros. El umbral superior de
    40 millones de COP/m² lo fijó la IA, con los datos a la vista (cambiarlo
    entre 31.6 y 50 millones mueve entre 3 y 9 filas).

## Pendientes

- **Siguiente paso (elegido por el equipo): análisis descriptivo** de la base
  limpia, con tablas y figuras en `03_Resultados/`, desagregado por estrato y
  localidad.
- Supuestos sin confirmar:
  - Que los rangos de `antiguedad` signifiquen lo mismo en metrocuadrado.com y
    habi.co (la distribución difiere: habi.co concentra más en 10–20 años).
  - Que los 121 + 14 registros eliminados por los dos últimos filtros sean
    errores y no inmuebles reales muy caros o muy baratos.
- Decisiones aún abiertas para el modelado:
  - `barrio` tiene 1,387 categorías (muchas con pocas observaciones): definir
    cómo codificarlo dentro del `Pipeline`, ajustado solo con entrenamiento.
  - `website` como variable de control o no (habi.co es 792 filas, 2.9%).
  - Partición aleatoria o temporal: `datetime` cubre solo del 3 de julio al 3
    de septiembre de 2024.
  - `parqueaderos` llega a 30 y `habitaciones` a 7; no se filtraron.
  - Las 566 filas con `coords_modified` y las 3 columnas constantes siguen en
    la base.
- Definir el entorno de Python: `python` no existe en esta máquina; el script se
  corrió con `/usr/bin/python3` (3.9, pandas 2.2.0) y el `python3` de Homebrew
  (3.15) no tiene pandas. Falta `requirements.txt` y `00_main.py`.
- Completar roles y correos de Maria Paula Rivera y Angelo Di Marco en
  `CLAUDE.md`.
