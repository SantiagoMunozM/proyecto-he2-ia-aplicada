# Precios de vivienda en Bogotá

Proyecto final del curso **HE2 Inteligencia Artificial Aplicada a la Economía**
(ECON-3527, 2026-2, Universidad de los Andes).

## Pregunta de investigación

¿Cuál debería ser el precio de una vivienda en Bogotá dadas sus características,
como área, antigüedad y ubicación?

Es un problema de **aprendizaje supervisado (regresión)**. La variable objetivo
es el precio de venta publicado (`precio_venta`). El precio de arriendo
(`precio_arriendo`) es un problema aparte.

## Enfoque

| Elemento | Definición |
| --- | --- |
| Línea base | Regresión lineal con área, antigüedad, ubicación, estrato y habitaciones |
| Modelo propuesto | Random Forest (`RandomForestRegressor`), comparado contra la línea base |
| Comparación adicional | XGBoost, solo como referencia |
| Métricas | RMSE (principal) y MAPE (secundaria) |
| Validación | Conjunto de prueba separado al inicio; hiperparámetros con validación cruzada solo sobre entrenamiento |
| Semilla | `random_state=2026` en toda partición, validación y modelo aleatorio |

Todo modelo se reporta junto a la línea base, en entrenamiento y en prueba. Los
errores se desagregan por estrato y localidad.

**Evaluación de impacto (propuesta):** prueba A/B entre usuarios del modelo
lineal y del Random Forest, comparando tiempo de compra/venta y ganancia o
ahorro, con revisión trimestral sobre datos nuevos.

## Datos

- **Base principal:** `processed_v2.0.0_august_2_2024.json`, del proyecto
  [`builker-col/bogota-apartments`](https://www.kaggle.com/datasets/erik172/bogota-apartments)
  (Kaggle), obtenida por web scraping de portales inmobiliarios en 2024. El
  diccionario de columnas está en
  [01_Datos/01_Crudos/README_columnas.md](01_Datos/01_Crudos/README_columnas.md).
- **Tamaño:** 43,013 registros (27,270 `VENTA`, 15,515 `ARRIENDO`, 228
  `VENTA Y ARRIENDO`), casi todos apartamentos.
- **Datos externos** (en `01_Datos/01_Crudos/external/`): barrios y localidades,
  estaciones troncales de TransMilenio, paraderos del SITP, centros comerciales
  y escenarios deportivos.

Cuidados al usar la base:

- Está en formato MongoDB Extended JSON: los numéricos vienen como texto, los
  faltantes como `{'$numberDouble': 'NaN'}` y las fechas e ids como objetos
  `$date` / `$oid`. Hay que normalizarlo al cargar.
- `antiguedad` es categórica por rangos, no años.
- `coords_modified == True` marca coordenadas ajustadas; usarlas con cautela.
- `last_view` no es una fecha confiable de vigencia del anuncio.
- El precio es el **publicado**, no el de transacción.

## Estructura del repositorio

```
01_Datos/
  01_Crudos/        datos originales (nunca se modifican)
  02_Limpios/       datos limpios y transformados, listos para los modelos
02_Scripts/         scripts de Python numerados (01_, 02_, ...)
03_Resultados/
  Tablas/           tablas generadas
  Figuras/          figuras generadas
04_Presentaciones/  borradores y versiones de las presentaciones
05_Notas/           notas e ideas preliminares
06_Bitacoras/       documentación de cada sesión de trabajo
07_Recursos/        artículos, enunciados y documentación externa
00_main.py          corre el pipeline completo en orden (pendiente)
```

El flujo de datos va en un solo sentido: Crudos → Limpios.

## Cómo reproducir

> Pendiente: aún no hay scripts, `00_main.py` ni `requirements.txt`. Esta
> sección se completa cuando existan.

Convenciones del proyecto:

- Python, con `pandas` para datos y `scikit-learn` para los modelos.
- Cada tarea es un script numerado en `02_Scripts/` que lee de `01_Datos/` y
  escribe en `01_Datos/` o `03_Resultados/`.
- Los scripts se corren desde la raíz del repositorio
  (`python 02_Scripts/01_lectura_datos.py`) y usan rutas relativas.
- `python 00_main.py` debe reproducir todo el pipeline en una sesión limpia.
- Ningún número de tablas o presentaciones se escribe a mano: todo sale de una
  corrida.

## IA responsable

La localidad, el barrio y el estrato son variables sensibles y están muy
correlacionadas entre sí. Existe el riesgo de que el modelo perpetúe
desigualdades históricas de inversión urbana, y los más afectados por una
sub o sobrevaloración serían los hogares de estratos bajos y de zonas
periféricas (créditos hipotecarios, subsidios). Por eso el análisis de errores
se desagrega por estrato y localidad, y el proyecto incluye una sección de
riesgos éticos, sesgos y estrategias de mitigación.

## Uso de IA generativa

Siguiendo la política del curso, todo uso de IA generativa (herramienta,
propósito y verificación del resultado) queda documentado en las bitácoras de
`06_Bitacoras/`.

## Estado y documentación del equipo

- [HANDOFF.md](HANDOFF.md): dónde está el proyecto y cuál es el siguiente
  objetivo.
- [06_Bitacoras/](06_Bitacoras/): qué se hizo en cada sesión y por qué.
- [CLAUDE.md](CLAUDE.md): reglas de trabajo, decisiones y restricciones de
  muestra.

## Integrantes

- Maria Paula Rivera
- Angelo Di Marco
- Santiago Muñoz
