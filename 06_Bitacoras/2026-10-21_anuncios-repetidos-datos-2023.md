# Bitácora — 2026-10-21: revisión de la base de 2023 y eliminación de anuncios repetidos

**Integrantes en la sesión:** Santiago Muñoz (inferido del usuario de git; confirmar).

## Resumen

La sesión no trabajó en el "Siguiente objetivo" que traía `HANDOFF.md` (revisar los
resultados contra la rúbrica de la presentación de avance); ese objetivo se mantiene. Se
trabajó en tres temas pedidos por el usuario.

1. **Base de 2023.** La fuente (`builker-col/bogota-apartments`) publica en Dropbox un JSON
   de 2023. Se descargó a una carpeta temporal fuera del repo y se comparó con la base de
   2024. Decisión del usuario: no se incluye (ver "Análisis descartados" en `CLAUDE.md`).
   Al revisarla apareció el tema de los anuncios repetidos.
2. **Anuncios repetidos en la base de 2024.** El mismo inmueble aparece con códigos
   distintos, y una parte de esas copias quedaba a ambos lados de la partición. Por la
   preocupación del usuario de borrar apartamentos distintos de un mismo edificio, se
   eliminan solo las filas idénticas en todas las columnas salvo `codigo` y fechas. Para
   el resto se reporta una sensibilidad de las métricas de prueba. Se volvió a correr
   `00_main.py` completo.
3. **Presentación de avance en Canva.** Se actualizaron todas las cifras y figuras con la
   corrida nueva y se agregó una diapositiva sobre los anuncios repetidos como obstáculo.

Pérdida de observaciones: la base limpia pasa de 27,324 a 26,900 viviendas (−424 por
anuncios repetidos). La partición se reasignó completa (21,520 en entrenamiento, 5,380 en
prueba), porque `train_test_split` reparte de nuevo cuando cambia el número de filas.

## Archivos

- Creados: esta bitácora; `03_Resultados/Tablas/01_duplicados_eliminados.csv`,
  `03_Resultados/Tablas/05_sensibilidad_gemelos.csv`,
  `03_Resultados/Figuras/06_sensibilidad_gemelos.png`.
- Modificados: `02_Scripts/01_limpieza_datos.py`, `02_Scripts/05_analisis_errores_impacto.py`,
  `02_Scripts/06_figuras_presentacion.py`, `CLAUDE.md`, `HANDOFF.md`, `README.md`;
  `01_Datos/02_Limpios/apartamentos_venta_limpio.csv` y `particion_train_test.csv`; todas las
  tablas y figuras `01_*` a `07_*` regeneradas por `00_main.py`. Fuera del repo: la
  presentación "Presentación Avance IA Aplicada" en Canva.
- Eliminados: ninguno. El JSON de 2023 quedó solo en la carpeta temporal de la sesión, no en
  el repo.

## Detalle por archivo

### Revisión de la base de 2023 (sin archivos en el repo)

`2023_bogota_apartments_processed.json`, 158 MB, enlace de Dropbox de la fuente. Lo que se
encontró (scripts de exploración fuera del repo):

- 85,310 registros (56,798 ventas), con `datetime` de junio a diciembre de 2023. Todo es
  vivienda usada: no hay proyectos sobre planos ni en construcción.
- Faltan columnas que hoy usa el modelo completo: `piscina`, `terraza`, `vigilancia`,
  `salon_comunal` y la distancia a parques. Esa distancia no se puede recalcular, porque
  `external/` no trae parques. A cambio trae `piso` (59% con dato en ventas) y `closets`.
- 9,673 de las 27,324 viviendas limpias de 2024 (35.4%) tienen el mismo `codigo` en 2023,
  y 1,898 de ellas estaban en prueba. En esos pares, el 96% tiene las mismas coordenadas y
  el 79% el mismo precio. Sumar 2023 al entrenamiento sin quitarlas habría metido fuga.
- Llevar los precios a 2024: la mediana del cociente de precios entre años en los anuncios
  repetidos es 1.000 (el precio publicado casi no cambia). Con una regresión hedónica de
  log(precio), sin los repetidos, el factor 2024/2023 es 1.063, y va de 1.056 (estrato 6)
  a 1.115 (estrato 1). Las alternativas consideradas fueron el índice de vivienda usada del
  Banco de la República o el año como variable.
- 158 MB supera el límite de 100 MB de GitHub, y el equipo decidió no usar Git LFS.

Usos posibles que se dejaron anotados, sin implementar: validación temporal (entrenar con
2023 y evaluar en la prueba de 2024) y más texto para el modelo de `descripcion`.

### `02_Scripts/01_limpieza_datos.py`

Paso 3g nuevo, después del filtro de precio por m². Elimina las filas idénticas en todas las
columnas salvo `codigo`, `datetime` y `last_view` (constante `COLUMNAS_IGNORADAS_DUPLICADOS`)
y conserva la publicación con el `datetime` más reciente. La pérdida queda en el embudo
(`01_perdida_observaciones.csv`). `01_duplicados_eliminados.csv` lista cada código
eliminado, el código que se conservó en su lugar y la fecha del eliminado.

Intuición: si dos anuncios coinciden en todo, incluida la descripción letra por letra, son el
mismo anuncio publicado otra vez. Aunque fueran dos unidades distintas, la segunda copia no
aporta información. Los que difieren en cualquier otra columna (descripción, baños,
amenidades, estrato) se conservan, porque pueden ser apartamentos distintos de un mismo
edificio. La información de los vecinos sí estaría disponible al usar el modelo, así que
aprender de ellos no es fuga.

Antes de decidir la regla se exploró la base limpia anterior (fuera del repo). Con la clave
área + precio + coordenadas + habitaciones había 844 grupos y 1,166 filas sobrantes.
Clasificados por grupo:

- 227 grupos tenían la misma descripción y los mismos atributos;
- 178 tenían los mismos atributos y otra descripción;
- 432 diferían en algún atributo;
- 7 mencionaban pisos distintos en el texto.

En el 58% de los grupos todas las filas eran de la misma inmobiliaria (prefijo del
`codigo`). La regla fila por fila elimina 424, más que las 337 sobrantes del primer tipo,
porque también encuentra pares idénticos dentro de grupos mixtos.

### `02_Scripts/05_analisis_errores_impacto.py`

Sección 5 nueva, de sensibilidad a gemelos (las figuras pasan a ser la sección 6). Lee la
base limpia y la partición. Marca como "con gemelo" cada vivienda de prueba que tiene en
entrenamiento otra con igual área, precio, latitud, longitud y habitaciones. Luego calcula
RMSE y MAPE de prueba de todos los modelos y escalas para tres subconjuntos: todas, sin
gemelo y con gemelo. No elimina nada: mide cuánto cambiarían las métricas si esos casos
ambiguos fueran duplicados. La clave usa el precio, pero solo para el diagnóstico; no entra
a ningún modelo.

### `02_Scripts/06_figuras_presentacion.py`

Sección 9 nueva: `06_sensibilidad_gemelos.png`, con barras de MAPE de prueba por modelo,
sin gemelo y con gemelo, un panel por escala y la paleta de las diapositivas. Lee
`05_sensibilidad_gemelos.csv`.

### `CLAUDE.md`

- "Decisiones tomadas": fila nueva sobre los anuncios repetidos, y nota en la fila de la
  grilla del Random Forest (`max_features` elegido: 0.5 en log y 0.33 en niveles tras el
  cambio).
- "Restricciones de muestra": fila nueva, 27,324 → 26,900.
- "Análisis descartados": fila nueva sobre la base de 2023.

### `README.md`

- Sección "Datos": la base limpia excluye los anuncios repetidos, y hay una advertencia
  nueva sobre ellos.
- "Cómo reproducir": el paso 5 menciona la sensibilidad a gemelos, y se agregaron los pasos
  6 (`06_figuras_presentacion.py`) y 7 (`07_perfil_descripcion.py`), que ya existían en el
  repo y corre `00_main.py`, pero el README no listaba.

### Presentación en Canva (fuera del repo)

"Presentación Avance IA Aplicada": se reemplazaron las 7 figuras `06_*` y todas las cifras
de texto con valores de las tablas nuevas. Antes se verificó que, con las tablas del commit
anterior, el mismo script reproducía las cifras que tenía la presentación. Se agregó la
diapositiva 7 "Anuncios repetidos: el mismo inmueble con otro código", con
`06_sensibilidad_gemelos.png` y notas del presentador. Esa diapositiva quedó con la
tipografía por defecto de Canva y falta igualarla a mano.

## Resultados nuevos (tablas, figuras, métricas)

**Métricas con la base sin repetidos (`04_metricas_modelos.csv`).** RMSE en millones de COP,
MAPE en %. Entrenamiento (solo descriptivo), validación cruzada (CV) y prueba:

| Modelo | Escala | RMSE train | RMSE CV | RMSE prueba | MAPE train | MAPE CV | MAPE prueba |
|---|---|---|---|---|---|---|---|
| Lineal (base) | Log | 465.8 | 462.9 | 433.4 | 16.87 | 16.90 | 17.29 |
| Random Forest | Log | 148.8 | 365.0 | 322.1 | 4.27 | 11.96 | 11.94 |
| XGBoost | Log | 194.7 | 358.0 | 321.2 | 8.55 | 12.22 | 12.25 |
| Lineal (base) | Niveles | 510.5 | 508.9 | 473.3 | 35.17 | 35.25 | 36.27 |
| Random Forest | Niveles | 127.2 | 354.8 | 310.1 | 4.58 | 12.66 | 12.70 |
| XGBoost | Niveles | 135.3 | 361.4 | 327.6 | 9.84 | 13.41 | 13.52 |

Frente a la corrida anterior (bitácora `2026-10-21_cross-validate-gridsearch-grilla-rf.md`),
el conjunto de prueba es otro, así que las diferencias mezclan el efecto de quitar los
repetidos con el de la nueva partición. RMSE de CV del Random Forest: 363.4 → 365.0 (log) y
346.5 → 354.8 (niveles); de la línea base: 466.8 → 462.9 (log) y 507.7 → 508.9 (niveles).
Cambiaron dos hiperparámetros: `max_features` del Random Forest en niveles (0.4 → 0.33) y
`max_depth` de XGBoost en niveles (8 → 6). `min_samples_leaf=1` sigue elegido en las dos
escalas. El modelo con menor RMSE de CV sigue siendo el Random Forest en niveles.
`00_main.py` corrió completo en 23.0 min, sin errores (22.7 min de estimación).

**`01_duplicados_eliminados.csv`.** 424 filas en 288 grupos. Hace verificable cada
eliminación: para cada anuncio eliminado dice qué anuncio quedó en su lugar.

**`05_sensibilidad_gemelos.csv` y `06_sensibilidad_gemelos.png`.** 241 de 5,380 viviendas de
prueba (4.5%) tienen un gemelo en entrenamiento. MAPE de prueba (todas / sin gemelo / con
gemelo):

| Modelo | Log | Niveles |
|---|---|---|
| Lineal (base) | 17.3 / 17.4 / 14.9 | 36.3 / 36.1 / 40.9 |
| Random Forest | 11.9 / 12.3 / 3.9 | 12.7 / 13.1 / 4.5 |
| XGBoost | 12.2 / 12.5 / 6.9 | 13.5 / 13.8 / 8.1 |

En las viviendas con gemelo, los árboles tienen un error mucho menor que en el resto y los
lineales no. Con la base anterior la exploración daba 341 viviendas de prueba (6.2%) con
gemelo. Esta tabla sustenta el diagnóstico de obstáculos (calidad de datos y posible fuga)
en la presentación de avance.

## Uso de IA

Claude Code (Claude Opus 5.5) en VS Code, para: descargar y perfilar la base de 2023,
diagnosticar los duplicados y clasificarlos, implementar los cambios en 01, 05 y 06, correr
el pipeline, recalcular las cifras de la presentación y editar la presentación en Canva a
través de su conector. Verificación:

1. Las cifras de esta bitácora y de la presentación se leyeron de los CSV regenerados, sin
   escribir ningún número a mano.
2. Para la presentación, un script calculó cada cifra con las tablas del commit anterior y
   con las nuevas; con las anteriores reprodujo lo que decía la presentación, lo que
   confirma que la fuente de cada cifra es la correcta.
3. Cada diapositiva editada se revisó en miniatura antes de guardar, y el usuario aprobó
   guardar.
4. La regla de eliminación se ajustó a la objeción del usuario (no borrar posibles unidades
   distintas) antes de implementarla.

## Pendientes

- **Siguiente objetivo (sin cambios):** revisión de los resultados contra la rúbrica de la
  presentación de avance (`05_Notas/revision_resultados_avance.md`). Ahora el diagnóstico de
  obstáculos tiene evidencia adicional (anuncios repetidos).
- Confirmar con el equipo la regla de eliminación de anuncios repetidos y que la partición
  cambió (todo resultado anterior al 2026-10-21 corresponde a otra partición).
- Igualar la tipografía de la diapositiva 7 en Canva.
- Hipótesis sin comprobar: que `min_samples_leaf=1` en el borde se deba en parte a los
  gemelos que quedan entre folds de la CV.
- Siguen abiertos los pendientes anteriores: confirmar `cross_validate`/`GridSearchCV` y el
  umbral de 30 viviendas, completar roles en `CLAUDE.md` y documentar la sesión del commit
  `bd96c50`.
