# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# CLAUDE.md: reglas del proyecto

## Contexto del proyecto

Proyecto del curso HE2 Inteligencia Artificial Aplicada a la Economía (ECON-3527,
2026-2, Universidad de los Andes). Entregable final en GitHub más presentación
(Semana 16, 25 de noviembre de 2026).

- **Pregunta:** ¿cuál debería ser el precio de una vivienda en Bogotá dadas sus
  características como área, antigüedad y ubicación?
- **Tipo de problema:** aprendizaje supervisado, regresión. La variable objetivo
  es el precio publicado (`precio_venta`; `precio_arriendo` es un problema aparte).
- **Modelo propuesto:** Random Forest (elegido frente a XGBoost por menor
  necesidad de ajuste fino, menor riesgo de sobreajuste y por permitir analizar
  la importancia de las variables).
- **Línea base:** regresión lineal sencilla con área, antigüedad, ubicación,
  estrato y habitaciones. Todo modelo se reporta siempre contra esta línea base.
- **Métricas:** RMSE (principal) y MAPE (secundaria, error relativo al valor de
  la vivienda).
- **Evaluación de impacto (propuesta):** prueba A/B entre compradores/vendedores
  que usan el modelo lineal vs. el Random Forest, comparando tiempo de
  compra/venta y ganancia/ahorro; revisión trimestral con revalidación sobre
  datos nuevos.
- **IA responsable:** localidad/barrio y estrato son variables sensibles y muy
  correlacionadas entre sí. Riesgo de que el modelo perpetúe desigualdades
  históricas de inversión urbana; los más afectados por sub/sobrevaloración son
  hogares de estratos bajos o zonas periféricas (créditos hipotecarios,
  subsidios). Todo análisis de errores debe poder desagregarse por estrato y
  localidad.
- **Documentos de contexto** (carpeta padre del repo, `../`): propuesta
  presentada (`Presentación de Pregunta IA Aplicada.pdf`), enunciado de la
  Presentación 1 y rúbricas (`Rubrica_Presentacion1.xlsx`,
  `Rubrica_Presentacion_Avance.xlsx`). Diapositivas del curso en
  `../../Presentaciones/`.

### Hitos y lo que evalúa cada uno

- **Presentaciones de avance (Semanas 11 y 14):** resultados con métodos
  clásicos (varios modelos contra la línea base explícita, métricas coherentes
  con el costo de los errores, validación correcta), diagnóstico de obstáculos
  con evidencia técnica (calidad de datos, sobreajuste, variables faltantes),
  propuesta concreta de aprendizaje profundo o IA generativa justificada por la
  estructura de los datos (p. ej. el texto de `descripcion`), traducción de
  resultados a costos/beneficios para el usuario, y análisis de sesgos con
  estrategias de mitigación.
- **Proyecto final (Semana 16):** 50% presentación, 50% entregable en GitHub.
  Se evalúan contribuciones individuales verificables en GitHub (commits) y una
  sección de riesgos éticos y sesgos.
- **Política de IA del curso:** todo uso de IA generativa debe documentarse en
  los entregables (qué herramienta, para qué y cómo se verificó el resultado).
  Las bitácoras de sesión cumplen este papel.

## Estructura del proyecto

Misma estructura de los laboratorios y talleres de Ciencia de Datos, con solo
dos niveles de datos:

- `01_Datos/01_Crudos/`      datos originales. NUNCA se modifican
- `01_Datos/02_Limpios/`     datos limpios y transformados, listos para los modelos
- `02_Scripts/`              scripts de Python, numerados (`01_`, `02_`, ...)
- `03_Resultados/`           `Tablas/` y `Figuras/` generadas
- `04_Presentaciones/`       borradores y versiones de las presentaciones
- `05_Notas/`                notas e ideas preliminares
- `06_Bitacoras/`            documentación de cada sesión de trabajo
- `07_Recursos/`             artículos, enunciados y documentación externa
- `00_main.py`               (raíz) corre el pipeline completo en orden

Los crudos están en `01_Datos/01_Crudos/` (JSON principal,
`README_columnas.md` y `external/`). Las carpetas vacías llevan un `.gitkeep`
para que git las conserve; no lo borre al agregar archivos. El estado de avance
del proyecto se lleva en `HANDOFF.md`, no aquí.

## Datos

- **Base principal:** `processed_v2.0.0_august_2_2024.json` del proyecto
  `builker-col/bogota-apartments` (Kaggle: `erik172/bogota-apartments`), web
  scraping de portales inmobiliarios, 2024. Diccionario de columnas en
  `README_columnas.md` (junto al JSON).
  - 43,013 registros: 27,270 `VENTA`, 15,515 `ARRIENDO`, 228 `VENTA Y ARRIENDO`;
    casi todos `APARTAMENTO`.
  - **Formato MongoDB Extended JSON:** los faltantes vienen como
    `{'$numberDouble': 'NaN'}`, el id como `{'$oid': ...}`, y `timeline` es una
    lista anidada con el historial de precios. Los numéricos con valor vienen
    como números (verificado al perfilar el JSON), pero el script de lectura
    también acepta texto. Hay que normalizar esto explícitamente al cargar; no
    asuma tipos numéricos.
  - habi.co (794 de las ventas) no reporta `estado` ni `compañia`; `administracion`
    está en N/A en todos los proyectos nuevos.
  - `antiguedad` es categórica por rangos (p. ej. `ENTRE 10 Y 20 ANOS`), no años.
  - `coords_modified == True` indica coordenadas ajustadas: tratarlas con
    cautela en cualquier variable geográfica.
  - `last_view` se actualiza con cada corrida del scraper: no es fecha confiable
    de vigencia del anuncio.
  - El precio es el **publicado**, no el de transacción.
- **Datos externos** (`external/`, con su `README.MD`): barrios y localidades
  (GeoJSON/shapefile, WGS84), estaciones troncales de TransMilenio, paraderos
  SITP, centros comerciales y escenarios deportivos. La base principal ya trae
  distancias a TM, parques y centros comerciales calculadas por la fuente.
- El flujo es Crudos → Limpios. Nunca en sentido inverso.
- Reporte siempre cuántas observaciones se pierden en cada limpieza o filtro.
- Los crudos, incluido el JSON de ~81 MB, se versionan en git tal cual (sin
  Git LFS). GitHub advierte por archivos de más de 50 MB y rechaza los de más
  de 100 MB: si una base limpia supera ese límite, consulte antes de
  versionarla.

## Reglas de trabajo

- Lenguaje: Python. `pandas` para datos; `scikit-learn` para todos los métodos
  de machine learning, siguiendo lo visto en las diapositivas del curso
  (`train_test_split`, `KFold`/`cross_val_score`, `DecisionTree*`,
  `RandomForest*`, `LinearRegression`, `Pipeline`). Para regresión use las
  versiones `Regressor` de los estimadores. XGBoost (`xgboost`) solo como
  comparación, igual que en clase.
- **Un script por tarea**, numerado en orden de ejecución
  (`02_Scripts/01_limpieza_datos.py`, `02_...`). Cada script
  lee sus insumos de `01_Datos/` y escribe sus salidas en `01_Datos/` o
  `03_Resultados/`; no depende de variables en memoria de otro script.
- Los scripts se corren desde la raíz del repo (`python 02_Scripts/01_x.py`) y
  `python 00_main.py` debe reproducir todo el pipeline en una sesión limpia, sin
  intervención manual.
- Utilice rutas relativas ancladas a la raíz del proyecto (`01_Datos/...`).
  Nunca rutas absolutas del computador.
- Explique lo que va a hacer ANTES de editar o crear archivos.
- Redacte los comentarios del código en español.
- Fije la semilla (`random_state=2026`) en toda partición, validación cruzada y
  modelo con componente aleatorio.
- Ningún número se escribe a mano en tablas o presentaciones: todo sale de una
  corrida.

## Regla metodológica: evaluación

- El desempeño se evalúa siempre fuera de muestra: separe un conjunto de prueba
  al inicio y no lo toque hasta la evaluación final. Hiperparámetros y selección
  de modelo se hacen con validación cruzada solo sobre entrenamiento.
- Toda transformación aprendida de los datos (imputación, escalamiento,
  codificación, agregados por barrio/localidad) se ajusta solo con
  entrenamiento, idealmente dentro de un `Pipeline`, para evitar fuga de
  información.
- Reporte RMSE y MAPE de cada modelo junto a la línea base lineal, en
  entrenamiento y prueba (las diapositivas usan como regla práctica una
  diferencia < 10% entre ambos para diagnosticar sobreajuste).
- Si se usa la dimensión temporal (`datetime`, `timeline`), considere un split
  temporal en vez de uno aleatorio.
- Desagregue los errores por estrato y localidad para la sección de IA
  responsable.

## Registro de sesión de trabajo

- Cada sesión queda documentada en `06_Bitacoras/AAAA-MM-DD_<tema>.md`, con lo
  que se hizo, por qué, qué se descubrió y qué quedó pendiente, y con la lista
  de archivos creados, modificados o eliminados.
- La skill de proyecto `registrar-sesion`
  (`.claude/skills/registrar-sesion/SKILL.md`, versionada para todo el equipo)
  escribe la bitácora, actualiza `HANDOFF.md` y revisa `README.md` (lo edita
  solo si la sesión cambió algo que este documenta). Úsela al cerrar ("cerrar
  sesión", "registrar la sesión", "escribir la bitácora").
- Lea las bitácoras previas al iniciar una sesión para retomar lo pendiente.

### `HANDOFF.md`: resumen orientado a la acción siguiente

`HANDOFF.md` (raíz) resume las bitácoras para retomar el trabajo sin leerlas
todas. Las bitácoras explican el porqué; el handoff dice dónde estamos y qué
sigue.

- **Al iniciar una sesión:** lea `HANDOFF.md` antes que cualquier otro archivo
  y proponga trabajar en su "Siguiente objetivo", salvo que el usuario indique
  otra cosa. Consulte las bitácoras solo si necesita el detalle.
- **Al cerrar una sesión**, después de escribir la bitácora, actualice las tres
  secciones:
  - **Siguiente objetivo:** se reescribe. Una sola tarea concreta, con el
    archivo que debe producirse, un criterio de terminado verificable y los
    bloqueos o preguntas abiertas para el equipo.
  - **Estado actual:** se reescribe para reflejar qué existe y funciona hoy
    (datos, scripts, resultados). No es un historial.
  - **Registro de sesiones:** se agrega una entrada arriba (la más reciente
    primero), de tres a cinco líneas, con lo que se hizo y el enlace a la
    bitácora. Las entradas anteriores no se editan.
- Si una sesión no termina el objetivo, el objetivo se mantiene y se anota en
  el registro qué avanzó y qué lo impidió.

## Primero el diseño, después los resultados

- No emita juicios sobre si un resultado es "bueno" o "malo".
- No exprese entusiasmo por una métrica ni por un modelo.
- Mientras el diseño no esté resuelto, lo único relevante es si la
  especificación y la validación son correctas.

## Integrantes

| Nombre              | Rol / responsabilidad | Contacto                                                         |
| ------------------- | --------------------- | ---------------------------------------------------------------- |
| Maria Paula Rivera  |                       |                                                                  |
| Angelo Di Marco     |                       |                                                                  |
| Santiago Muñoz      |                       | [s.munozm234@uniandes.edu.co](mailto:s.munozm234@uniandes.edu.co) |

## Decisiones tomadas

<!-- Registro acumulado de decisiones metodológicas y su justificación. -->

| Fecha      | Decisión | Justificación |
| ---------- | -------- | ------------- |
| 2026-10-20 | Los datos crudos (incluido el JSON de ~81 MB) se versionan en git sin Git LFS. | Decisión del equipo; el archivo está por debajo del límite de 100 MB de GitHub. |
| 2026-10-20 | Solo dos niveles de datos: `01_Crudos/` y `02_Limpios/` (sin `Procesados/` ni `Listos/`). | Decisión del equipo para simplificar el flujo de datos. |
| 2026-10-20 | Base limpia solo con `VENTA` y `VENTA Y ARRIENDO` (`apartamentos_venta_limpio.csv`). | Son las que tienen `precio_venta`; `precio_arriendo` es un problema aparte. |
| 2026-10-20 | Se excluyen `compañia`, `administracion` y `estado` de la base limpia. | `administracion` es N/A en todos los proyectos nuevos; `compañia` es metadato y habi.co no la reporta; `estado` es redundante con `antiguedad` (NUEVO = `SOBRE PLANOS`, `EN CONSTRUCCION`, `PARA ESTRENAR`) y habi.co tampoco la reporta. Conservarlas eliminaba las viviendas nuevas, las casas y toda la fuente habi.co. |
| 2026-10-20 | También se excluyen `_id`, `timeline`, `direccion`, `url`, `precio_arriendo`, `piso` y `closets`. | `_id` y `timeline` no caben en un CSV plano; el resto tiene más de 50% de N/A dentro del alcance. |
| 2026-10-20 | `sector` y `barrio` en N/A se codifican como la categoría `SIN_DATO`, sin eliminar la fila. | El N/A cae parejo entre localidades y estratos y `barrio` es la variable de ubicación más informativa; la categoría es constante, no se aprende de los datos. |
| 2026-10-20 | `parqueaderos` negativo se toma como 0 (1 fila). | Decisión del equipo. |
| 2026-10-20 | `banos == 0` se trata como faltante y se elimina la fila. | Son apartamentos de 40 a 481 m² y la descripción de 12 de las 14 menciona baños. |
| 2026-10-20 | Filtro de precio por m² entre 1 y 40 millones de COP. | Fuera de ese rango hay errores de escala en precio o área. Umbral por plausibilidad, no por desempeño de un modelo; moverlo entre 31.6 y 50 millones cambia entre 3 y 9 filas. |
| 2026-10-20 | `chimenea`, `permite_mascotas` y `salon_comunal` se dejan en la base pero se anotan como constantes. | Siempre `False`: no aportan información; descartarlas en el modelado. |

## Análisis descartados

<!-- Especificaciones o enfoques probados y abandonados, con la razón. -->

| Fecha | Análisis/especificación descartada | Razón |
| ----- | ---------------------------------- | ----- |
| 2026-10-20 | Corregir los outliers de precio (×1000) y de área (decimal desplazado) en lugar de eliminarlos. | No se puede verificar el valor correcto: las descripciones no mencionan el precio y solo algunas dan los m². |
| 2026-10-20 | Eliminar toda fila con algún N/A. | Deja 0 filas: `piso` y `closets` son 100% N/A y `precio_arriendo` es N/A en toda venta. |
| 2026-10-20 | Estrato estrictamente menor a 6. | Eliminaba las 11,985 viviendas de estrato 6 del alcance (44%); el equipo eligió 1 a 6 inclusive. |

## Restricciones de muestra

<!-- Criterios de exclusión aplicados y el N resultante en cada paso. -->

| Criterio de exclusión | N antes | N después |
| --------------------- | ------- | --------- |
| `tipo_operacion` en `VENTA` o `VENTA Y ARRIENDO` | 43,013 | 27,498 |
| N/A en `estrato`, `antiguedad` o `website` | 27,498 | 27,485 |
| `area > 0` | 27,485 | 27,466 |
| `1 <= estrato <= 6` | 27,466 | 27,459 |
| `banos >= 1` | 27,459 | 27,445 |
| Precio por m² entre 1 y 40 millones de COP | 27,445 | 27,324 |

Fuente: `03_Resultados/Tablas/01_perdida_observaciones.csv`.

## Reglas estrictas

- No modificar ni sobrescribir archivos en `01_Datos/01_Crudos/`.
- No eliminar ni mover archivos fuera de la estructura del proyecto sin
  autorización.
- No evaluar modelos con datos de prueba usados en entrenamiento o ajuste.
