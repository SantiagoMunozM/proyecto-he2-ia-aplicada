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
| Validación | Conjunto de prueba separado al inicio; hiperparámetros con validación cruzada (`cross_validate`, y `GridSearchCV` para el objetivo en niveles) solo sobre entrenamiento |
| Semilla | `random_state=2026` en toda partición, validación y modelo aleatorio |

Todo modelo se reporta junto a la línea base, en entrenamiento, validación
cruzada y prueba. Los errores se desagregan por estrato y localidad.

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
- **Base limpia:** `01_Datos/02_Limpios/apartamentos_venta_limpio.csv`, solo con
  ventas (`VENTA` y `VENTA Y ARRIENDO`), sin N/A y con los tipos del diccionario
  de columnas. Las columnas y observaciones que se descartaron, y por qué, están
  en `CLAUDE.md` y en
  [03_Resultados/Tablas/01_perdida_observaciones.csv](03_Resultados/Tablas/01_perdida_observaciones.csv).

Cuidados al usar la base:

- Está en formato MongoDB Extended JSON: los faltantes vienen como
  `{'$numberDouble': 'NaN'}` y los ids como `$oid`. Hay que normalizarlo al
  cargar (lo hace `02_Scripts/01_limpieza_datos.py`).
- El diccionario de columnas lista 3 columnas de centro comercial que no
  existen en el JSON.
- habi.co no reporta `estado` ni `compañia`, y `administracion` no existe en los
  proyectos nuevos. Por eso esas columnas no están en la base limpia.
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
00_main.py          corre el pipeline completo en orden
```

El flujo de datos va en un solo sentido: Crudos → Limpios.

## Cómo reproducir

Entorno (probado con Python 3.13):

```
python -m venv .venv
.venv/Scripts/activate   # En Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

Scripts, en orden de ejecución (desde la raíz del repositorio):

1. `python 02_Scripts/01_limpieza_datos.py`: lee el JSON crudo, normaliza el
   formato, hace el reconocimiento y la limpieza, y escribe la base limpia en
   `01_Datos/02_Limpios/` y las tablas `01_*.csv` en `03_Resultados/Tablas/`.
2. `python 02_Scripts/02_analisis_descriptivo.py`: describe la base limpia
   (sin filtrarla) y escribe las tablas `02_*.csv` en `03_Resultados/Tablas/`
   y las figuras `02_*.png` en `03_Resultados/Figuras/`.
3. `python 02_Scripts/03_particion_muestra.py`: separa el conjunto de prueba
   (80/20 estratificado por estrato) y escribe la partición en
   `01_Datos/02_Limpios/` y la tabla `03_*.csv`.
4. `python 02_Scripts/04_estimacion_modelos.py`: estima la línea base, Lasso,
   Random Forest y XGBoost (objetivo en log y en niveles), y escribe las tablas
   `04_*.csv` y las figuras `04_*.png`. Tarda varios minutos.
5. `python 02_Scripts/05_analisis_errores_impacto.py`: desagrega por estrato y
   localidad los errores de prueba de la línea base y el Random Forest, los traduce
   a costo para comprador y vendedor y dimensiona la prueba A/B. Escribe las tablas
   `05_*.csv` y las figuras `05_*.png`.

`python 00_main.py` corre estos scripts en orden. Si se usa el entorno virtual:
`.venv/bin/python 00_main.py`.

Convenciones del proyecto:

- Python, con `pandas` para datos y `scikit-learn` para los modelos.
- Cada tarea es un script numerado en `02_Scripts/` que lee de `01_Datos/` y
  escribe en `01_Datos/` o `03_Resultados/`.
- Los scripts se corren desde la raíz del repositorio
  (`python3 02_Scripts/01_limpieza_datos.py`) y usan rutas relativas.
- `python 00_main.py` debe reproducir todo el pipeline en una sesión limpia.
- Ningún número de tablas o presentaciones se escribe a mano: todo sale de una
  corrida.

## IA responsable

La localidad, el barrio y el estrato son variables sensibles y están muy
correlacionadas entre sí (coeficiente de Cramér's V entre 0.47 y 0.999 según
el par, ver
[03_Resultados/Tablas/02_asociacion_variables_sensibles.csv](03_Resultados/Tablas/02_asociacion_variables_sensibles.csv)).
Existe el riesgo de que el modelo perpetúe
desigualdades históricas de inversión urbana, y los más afectados por una
sub o sobrevaloración serían los hogares de estratos bajos y de zonas
periféricas (créditos hipotecarios, subsidios). Por eso el análisis de errores
se desagrega por estrato y localidad (tablas `05_errores_por_*.csv` y
`05_costo_esperado_por_estrato.csv` en `03_Resultados/Tablas/`, con los grupos de
menos de 30 viviendas en prueba marcados), y el proyecto incluye una sección de
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
