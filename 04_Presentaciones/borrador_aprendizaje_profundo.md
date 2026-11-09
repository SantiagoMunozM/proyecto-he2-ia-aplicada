# Borrador: aprendizaje profundo con la descripción de las viviendas

Borrador de las diapositivas de texto y aprendizaje profundo para la presentación de avance.
Después se pasa a la presentación de Canva. Corresponde a los pasos 1, 2, 3 y 5 del plan de
`05_Notas/alternativas_aprendizaje_profundo_descripcion.md`. El paso 4 (extracción con LLM)
va como propuesta.

**Convenciones**

- Cada diapositiva tiene cuatro partes: **mensaje** (lo que debe quedar escrito en la
  lámina), **sustento** (figura o tabla de `03_Resultados/`), **cifras** (cada una con su
  fuente) y **notas del expositor**.
- RMSE en millones de COP. "CV" es la validación cruzada de 5 folds sobre entrenamiento;
  "prueba" es el 20% reservado (5,380 viviendas). Todas las cifras son de la corrida del
  2026-11-09.
- Las rutas de tablas son relativas a `03_Resultados/Tablas/` y las de figuras a
  `03_Resultados/Figuras/`.
- Las cifras marcadas con ⚠ no salen de una tabla de `03_Resultados/`. Hay que generarlas
  con un script o quitarlas antes de pasar a Canva (ver la sección final).

---

## Diapositiva 1. Por qué la descripción: la estructura de los datos

**Mensaje.** Cada anuncio trae un texto libre que describe atributos que no tienen columna:
vista, balcón, remodelación, iluminación y piso. Es texto, y el texto es la estructura de
datos que justifica pasar a aprendizaje profundo.

**Sustento.** `07_perfil_descripcion.csv` y `09_variables_palabras_clave.csv`.

**Cifras.**

- Las 26,900 viviendas tienen descripción. La mediana es de 75 palabras (percentil 10: 33;
  percentil 90: 134). Fuente: `07_perfil_descripcion.csv`.
- Atributos sin columna mencionados en el texto: vista 44.1%, balcón 30.1%, cercanía a
  colegio, TransMilenio o centro comercial 21.2%, remodelado 14.8% e iluminación 13.7%.
  Fuente: `07_perfil_descripcion.csv`.
- El piso se menciona en el 41.1% de los anuncios, y la columna `piso` se había excluido por
  estar 100% vacía. Fuente: `09_variables_palabras_clave.csv` (`txt_menciona_piso`).

**Notas del expositor.**

- En la presentación de avance mostramos que el modelo tabular no tiene información de piso,
  vista ni estado de conservación. La descripción es el único lugar donde aparecen.
- Una sola frase de contexto: son anuncios de portales escritos por el vendedor o la
  inmobiliaria, no una ficha técnica.
- Ojo: la mención de "vista" de `07` (44.1%) es un conteo simple. La variable `txt_vista` de
  `09` (36.9%) descuenta las negaciones y la "vista interior". Si se citan las dos, aclarar
  la diferencia.

---

## Diapositiva 2. El texto también trae el precio: cómo se evitó la fuga

**Mensaje.** Antes de cualquier modelo se enmascararon en la descripción las cifras de dinero
(precio, administración, canon), los teléfonos y los correos. Ninguna descripción conserva
el precio publicado después de enmascarar, y no se eliminó ninguna fila.

**Sustento.** `09_enmascaramiento.csv` (se sugiere una tabla de dos columnas: antes y
después).

**Cifras** (fuente: `09_enmascaramiento.csv`).

| Medida | Viviendas | % |
| --- | --- | --- |
| Descripciones con el precio publicado (±2%), antes de enmascarar | 1,057 | 3.93 |
| Descripciones con el precio publicado, después de enmascarar | 0 | 0.00 |
| Descripciones con alguna cifra de dinero enmascarada | 1,956 | 7.27 |
| Descripciones con teléfono enmascarado | 546 | 2.03 |
| Descripciones con correo enmascarado | 4 | 0.01 |
| Descripciones modificadas por alguna regla | 2,471 | 9.19 |

**Notas del expositor.**

- Por qué importa: si el texto dice "venta $685 millones", un modelo de texto aprende a leer
  el precio, no a estimarlo a partir de las características. Eso es fuga del objetivo.
- La administración y el canon también se enmascaran: están atados al precio y no son
  características de la vivienda.
- Los teléfonos y correos se quitan por privacidad, antes de mostrar textos o enviarlos a
  un servicio externo.
- Pendiente con el equipo: los nombres de barrio **no** se enmascararon.
- Otra fuente de fuga: 219 viviendas de prueba tienen una descripción idéntica a una de
  entrenamiento (5,380 − 5,161 en `11_sensibilidad_duplicados.csv`). Se trata en la
  diapositiva 7.

---

## Diapositiva 3. Qué se estimó: tres formas de leer el texto

**Mensaje.** Se probaron tres representaciones del texto, de la más simple a la de
aprendizaje profundo. Cada una se comparó con una pareja sin texto estimada igual, para
atribuir la diferencia al texto y no a otra búsqueda de hiperparámetros.

**Sustento.** Diagrama propio (sin figura en `03_Resultados/`), con la tabla de parejas y
`10_embeddings_resumen.csv`.

| Representación | Qué es | Modelo con texto | Pareja sin texto |
| --- | --- | --- | --- |
| A1. Palabras clave | 17 variables de la vivienda (vista, balcón, piso, remodelado, dúplex, etc.) | RF + palabras clave | RF tabular |
| A2. TF-IDF | Frecuencia de palabras y bigramas, ajustada solo con entrenamiento | RF + PCA de TF-IDF; Ridge + TF-IDF | RF tabular; Ridge tabular |
| C1. Vectores e5 (Transformer preentrenado) | `multilingual-e5-base`, congelado, 768 dimensiones por descripción | RF + PCA de e5; MLP híbrido + e5 (con y sin PCA) | RF tabular; MLP tabular |

**Cifras.**

- e5 lee hasta 512 tokens. La descripción más larga tiene 382 (mediana 121) y ninguna se
  trunca. Fuente: `10_embeddings_resumen.csv`.
- Calcular los vectores de las 26,900 viviendas tomó 13.6 min (en un M1 con MPS). Se
  calculan una vez y se guardan. Fuente: `10_embeddings_resumen.csv`.
- Las variables de palabras clave están en `09_variables_palabras_clave.csv`, con la
  expresión regular de cada una.

**Notas del expositor.**

- MLP híbrido: red en PyTorch con capas (256, 64) que recibe las variables tabulares
  estandarizadas junto con el vector del texto. La CV elige el dropout y el weight decay.
  La parada temprana usa un 10% del entrenamiento de cada fold, nunca la prueba.
- e5 no ve el precio y no se entrena con nuestros datos, así que calcularlo para toda la base
  no filtra información.
- A propósito, las palabras clave describen solo la vivienda: no hay variables de
  negociación ("negociable", "remate") ni de barrio o estrato.
- Todos los modelos usan la misma partición de la presentación anterior (21,520 en
  entrenamiento, 5,380 en prueba) y se estiman con el objetivo en log y en niveles.

---

## Diapositiva 4. La propuesta de aprendizaje profundo: pros y contras

**Mensaje.** Los vectores de un Transformer preentrenado (C1) aportan conocimiento del idioma
que 21,520 anuncios no alcanzan a enseñar. A cambio, se pierde interpretabilidad y el modelo
pasa a depender de cómo esté redactado el anuncio.

**Sustento.** Sección 4 de `05_Notas/alternativas_aprendizaje_profundo_descripcion.md`
(cualitativo, sin cifras).

| Pros | Contras |
| --- | --- |
| Reconoce sinónimos y parte del contexto, sin entrenar un modelo de lenguaje | El vector no es interpretable y codifica todo, incluidos los nombres de barrio y las señales del vendedor |
| No usa nuestros precios, así que no hay fuga por el ajuste | Exige librerías nuevas (`torch`, `sentence-transformers`) |
| Se calcula una vez y se reutiliza en RF y MLP | Para predecir hace falta un texto libre: la predicción cambia según la redacción |
| Lee el anuncio completo (ninguno se trunca) | Una red sobre variables tabulares suele requerir más ajuste que un Random Forest |

**Notas del expositor.**

- Se descartaron tres alternativas. El ajuste fino de un Transformer: más de 100 millones de
  parámetros con 21,520 ejemplos, horas por configuración. Pedirle el precio directamente a
  un LLM: no es validable y el modelo pudo haber visto los anuncios. Una LSTM: los anuncios
  son listas de atributos, así que el orden de las palabras aporta poco.
- Esta lámina responde a la parte de la rúbrica que pide "pros" y "contras" de la nueva
  propuesta.

---

## Diapositiva 5. Todas las variantes contra la línea base

**Mensaje.** En las dos escalas, todos los modelos, con y sin texto, tienen un RMSE de CV
menor que la línea base lineal. El menor RMSE de CV es del XGBoost en log y del Random
Forest en niveles, ambos sin texto.

**Sustento.** Figura `13_rmse_todas_variantes.png` y tabla `13_comparacion_modelos.csv`.

**Cifras** (fuente: `13_comparacion_modelos.csv`; RMSE en millones de COP).

| Modelo | Escala | RMSE CV (desv. entre folds) | RMSE prueba | MAPE prueba (%) |
| --- | --- | --- | --- | --- |
| Lineal (base) | log | 462.9 (57.9) | 433.4 | 17.3 |
| XGBoost | log | 358.0 (59.2) | 321.2 | 12.2 |
| Random Forest | log | 365.0 (69.2) | 322.1 | 11.9 |
| RF + e5 PCA (C1) | log | 369.7 (68.4) | 328.3 | 12.2 |
| MLP + e5 PCA (C1) | log | 375.5 (39.9) | 344.0 | 14.3 |
| Lineal (base) | niveles | 508.9 (56.4) | 473.3 | 36.3 |
| Random Forest | niveles | 354.8 (65.2) | 310.1 | 12.7 |
| RF + e5 PCA (C1) | niveles | 361.4 (66.3) | 316.3 | 13.0 |
| MLP + e5 PCA (C1) | niveles | 378.9 (47.1) | 354.8 | 17.6 |

- Frente a la línea base de su escala, el RMSE de CV del Random Forest en niveles es 30.3%
  menor y el de RF + e5 PCA, 29.0% menor (`cambio_rmse_cv_vs_base_pct`).

**Notas del expositor.**

- La figura tiene 15 variantes por escala. Recomendamos mostrar la figura completa y citar
  solo las filas de la tabla de arriba.
- El orden se lee en CV, no en prueba: la prueba solo se usa para reportar.
- Los rombos (prueba) quedan a la izquierda de los círculos (CV) en casi todos los modelos.
  Es la misma diferencia CV–prueba que mostramos en la presentación anterior.

---

## Diapositiva 6. ¿Cuánto cambia el error al agregar el texto?

**Mensaje.** Frente a su propia pareja sin texto, el texto no reduce el RMSE de CV del Random
Forest (sube entre 0.3% y 1.9%) y sí lo reduce en Ridge (entre 9.6% y 12.1%) y en el MLP
con PCA de e5 (entre 2.9% y 5.1%). En el Random Forest, las diferencias son menores que la
desviación entre folds.

**Sustento.** Figura `13_cambio_texto_vs_pareja.png` (generada por
`13_comparacion_final.py` a partir de `13_comparacion_modelos.csv`, columna
`cambio_rmse_cv_vs_sin_texto_pct`), más `11_importancia_variables.csv` y `11_cv_grillas.csv`
para las notas. La tabla de abajo trae las mismas cifras de la figura; en la lámina basta con
la figura.

**Cifras.**

| Variante con texto | Cambio de RMSE de CV vs. pareja sin texto, log (%) | Ídem, niveles (%) |
| --- | --- | --- |
| RF + palabras clave (A1) | +0.3 | +0.8 |
| RF + TF-IDF PCA (A2) | +1.5 | +1.5 |
| RF + e5 PCA (C1) | +1.3 | +1.9 |
| Ridge + TF-IDF (A2) | −12.1 | −9.6 |
| MLP + e5 PCA (C1) | −5.1 | −2.9 |
| MLP + e5, sin PCA (C1) | +6.3 | +5.6 |

Fuente: `13_comparacion_modelos.csv`.

- Desviación del RMSE de CV entre folds del Random Forest tabular: 69.2 M (log) y 65.2 M
  (niveles). La diferencia entre RF + e5 PCA y RF es de 4.7 M (log) y 6.6 M (niveles).
  Fuente: `13_comparacion_modelos.csv`.
- En los RF, el texto suma entre 1.1% y 3.7% de la importancia total (RF + e5 PCA: 1.1% en
  log y 3.0% en niveles). Fuente: `11_importancia_variables.csv` (suma de `importancia_pct`
  con `de_texto == True`).
- El RMSE de CV del RF + e5 sube con el número de componentes del PCA: en log, 369.7 con k=2
  y 389.3 con k=50. Por eso la CV elige k=2, el valor más cercano a no usar texto. Fuente:
  `11_cv_grillas.csv`.

**Notas del expositor.**

- La lectura es por parejas: cada variante se compara con su modelo sin texto, estimado con
  la misma grilla y la misma CV.
- El texto reduce el error en los modelos que parten de más error (Ridge, MLP), pero ninguno
  de ellos queda por debajo del Random Forest tabular (diapositiva 5).
- En el Random Forest, las variables de área, baños, parqueaderos y ubicación ya capturan lo
  que el texto agrega.
- Pasar los 768 componentes sin PCA al MLP aumenta el error de CV en las dos escalas.
- No anticipamos que el texto bajara el error, y que no lo baje en el RF también se reporta.

---

## Diapositiva 7. ¿El texto memoriza anuncios repetidos?

**Mensaje.** Al quitar de la prueba las viviendas con una descripción idéntica en
entrenamiento o con un gemelo, el RMSE de prueba sube en todas las variantes. El orden entre
modelos se mantiene, salvo un cambio entre dos MLP en niveles.

**Sustento.** `11_sensibilidad_duplicados.csv`.

**Cifras** (fuente: `11_sensibilidad_duplicados.csv`).

- Prueba completa: 5,380 viviendas. Sin descripción duplicada: 5,161 (−219). Sin gemelo:
  5,139 (−241). Sin ninguna de las dos: 4,963 (−417).
- Sin duplicadas ni gemelos, el RMSE de prueba sube entre 1.8 M y 8.3 M según la variante.
  En el Random Forest en niveles pasa de 310.1 M a 317.4 M, y en RF + e5 PCA en niveles de
  316.3 M a 324.4 M.
- En niveles, el MLP + e5 y el MLP tabular intercambian el 8.º y el 9.º lugar. El resto del
  orden es igual en las dos escalas.

**Notas del expositor.**

- Un "gemelo" es una vivienda con la misma área, precio, coordenadas y habitaciones que otra
  del otro lado de la partición.
- Nota interna, no va a la lámina: la bitácora del 2026-11-09 dice "entre 1.8 y 8.1
  millones" y "el orden de los modelos no cambia". La tabla da 8.3 M y un intercambio entre
  los dos MLP en niveles. En este borrador se usa la tabla; hay que corregir la bitácora.

---

## Diapositiva 8. Errores por estrato

**Mensaje.** En el Random Forest, con o sin texto, el MAPE de prueba es menor en el estrato 2
y mayor en el estrato 6, en las dos escalas. En niveles, la línea base y el MLP + e5 PCA
tienen su mayor MAPE en los estratos 2 y 3.

**Sustento.** Figura `13_mape_estrato_texto.png` y tabla `13_errores_por_estrato.csv`.

**Cifras** (MAPE de prueba en %, fuente: `13_errores_por_estrato.csv`).

| Modelo | Escala | Estrato 2 (n=190) | Estrato 3 (n=669) | Estrato 6 (n=2,347) |
| --- | --- | --- | --- | --- |
| Lineal (base) | niveles | 80.7 | 72.9 | 23.6 |
| Random Forest | niveles | 8.2 | 10.7 | 14.7 |
| RF + e5 PCA (C1) | niveles | 8.6 | 11.1 | 15.0 |
| MLP + e5 PCA (C1) | niveles | 33.5 | 21.7 | 16.9 |
| Lineal (base) | log | 13.1 | 17.3 | 18.9 |
| Random Forest | log | 7.5 | 9.4 | 14.0 |
| RF + e5 PCA (C1) | log | 7.8 | 9.8 | 14.2 |

- Brecha de MAPE entre estratos (máximo − mínimo, estratos 2 a 6): RF 6.5 pp (log) y 6.6 pp
  (niveles); línea base en niveles 57.2 pp; MLP + e5 PCA en niveles 18.0 pp. Fuente:
  `13_resumen_sesgos.csv` (`brecha_mape_estrato_pp`).

**Notas del expositor.**

- El estrato 1 tiene 16 viviendas en prueba (sombreado en la figura). No apoyamos ninguna
  conclusión en él, por debajo del umbral de 30 que fijamos.
- Lo que debe quedar: el MAPE es relativo al precio, y en los modelos que no son árboles el
  error relativo es mayor justo en las viviendas más baratas. Esas son las de los hogares que
  dependen de créditos o subsidios.

---

## Diapositiva 9. Sesgo con signo: ¿a quién se sobrevalora o subvalora?

**Mensaje.** El Random Forest en niveles, con y sin texto, sobrevalora en promedio todos los
estratos de 2 a 6, entre 2.6% y 4.8%. La línea base en niveles subvalora los estratos 2 a 5
y sobrevalora el 6.

**Sustento.** Figura `13_sesgo_estrato_texto.png` y tabla `13_errores_por_estrato.csv`
(`error_relativo_medio_pct`; positivo = sobrevalora).

**Cifras** (error relativo medio con signo en prueba, %; fuente: `13_errores_por_estrato.csv`).

| Modelo | Escala | Estr. 2 | Estr. 3 | Estr. 4 | Estr. 5 | Estr. 6 |
| --- | --- | --- | --- | --- | --- | --- |
| Lineal (base) | niveles | −12.5 | −12.1 | −4.3 | −4.1 | +9.0 |
| Random Forest | niveles | +2.6 | +4.3 | +4.0 | +3.5 | +4.6 |
| RF + e5 PCA (C1) | niveles | +3.0 | +4.4 | +4.2 | +3.8 | +4.8 |
| MLP + e5 PCA (C1) | niveles | −7.5 | +0.6 | +3.5 | +4.9 | +4.0 |
| Random Forest | log | +0.5 | +1.4 | +2.0 | +1.7 | +1.6 |
| MLP + e5 PCA (C1) | log | +6.8 | +4.6 | +3.4 | +0.9 | +2.8 |

**Notas del expositor.**

- Para el usuario: sobrevalorar perjudica al comprador (paga de más o el crédito no cubre)
  y subvalorar perjudica al vendedor (vende por debajo). La línea base en niveles subvalora
  justamente los estratos bajos.
- Agregar el texto al RF no cambia el patrón de signo por estrato: las dos curvas casi se
  superponen en la figura.
- Las cifras por estrato de la tabla salen de `13_errores_por_estrato.csv`. El rango
  "2.6% a 4.8%" del mensaje combina RF y RF + e5 PCA en niveles.

---

## Diapositiva 10. Ablación sin estrato ni localidad: ¿el texto reintroduce la ubicación?

**Mensaje.** Al quitar estrato y localidad del Random Forest, la brecha de MAPE entre
estratos se reduce y el MAPE total de prueba sube menos de un punto. Agregar el texto al
modelo sin estrato ni localidad no reduce el RMSE de CV.

**Sustento.** Figura `13_ablacion_estrato_localidad.png` (generada por
`13_comparacion_final.py` a partir de `13_resumen_sesgos.csv`: MAPE de prueba y brecha de
MAPE entre estratos), más `13_comparacion_modelos.csv` para el RMSE de CV. La nota al pie de
la figura ya aclara que la ablación conserva latitud, longitud y distancias.

**Cifras.**

| Modelo | Escala | MAPE prueba (%) | Brecha de MAPE entre estratos 2–6 (pp) | RMSE CV (M) |
| --- | --- | --- | --- | --- |
| Random Forest | log | 11.94 | 6.46 | 365.0 |
| RF sin estrato ni localidad | log | 12.22 | 5.00 | 366.0 |
| RF + e5 PCA sin estrato ni localidad | log | 12.53 | 4.94 | 370.1 |
| Random Forest | niveles | 12.70 | 6.57 | 354.8 |
| RF sin estrato ni localidad | niveles | 13.22 | 3.54 | 357.0 |
| RF + e5 PCA sin estrato ni localidad | niveles | 13.49 | 3.39 | 362.2 |

Fuentes: MAPE y brecha de `13_resumen_sesgos.csv`; RMSE de CV de `13_comparacion_modelos.csv`.

- Frente al RF sin estrato ni localidad, el RMSE de CV del RF + e5 PCA sin estrato ni
  localidad sube 1.1% (log) y 1.5% (niveles). Fuente: `13_comparacion_modelos.csv`
  (`cambio_rmse_cv_vs_sin_texto_pct`).

**Notas del expositor.**

- **Aclarar en voz alta:** la ablación quita estrato y las dummies de localidad, pero **no**
  la latitud, la longitud ni las distancias (`02_Scripts/11_modelos_texto.py`, líneas
  438–440). La ubicación fina sigue en el modelo, y eso explica por qué el error casi no
  cambia.
- Lectura para IA responsable: con este diseño no vemos que el texto recupere el error que
  se pierde al quitar estrato y localidad. Pero los nombres de barrio siguen en el texto y la
  ubicación sigue en las coordenadas, así que la ablación no aísla toda la información de
  ubicación.
- Estrategias de mitigación que proponemos:
  1. reportar siempre el error por estrato y localidad, con el umbral de 30 viviendas;
  2. ofrecer la versión sin estrato ni localidad cuando el uso sea crediticio o de subsidios,
     y documentar su costo en MAPE;
  3. si se adopta la extracción con LLM, que su esquema excluya barrio, estrato y cifras de
     dinero;
  4. decidir con el equipo si se enmascaran los nombres de barrio.

---

## Diapositiva 11. Qué significa para quien usaría el modelo

**Mensaje.** Con la descripción, el modelo de menor RMSE de CV en niveles sigue siendo el
Random Forest tabular, que se alimenta con un formulario de características y no necesita un
anuncio escrito. El monitoreo se amplía con controles sobre el texto.

**Sustento.** `13_comparacion_modelos.csv` y el plan de evaluación de impacto de la
presentación anterior (`05_*`).

**Cifras.**

- En niveles, el RMSE de prueba es de 310.1 M en el RF tabular y de 316.3 M en el RF + e5
  PCA. Fuente: `13_comparacion_modelos.csv`.

**Plan de monitoreo actualizado (propuesta).**

1. Revalidación trimestral (sin cambios): RMSE y MAPE sobre datos nuevos, desagregados por
   estrato y localidad.
2. Si se usa texto, en cada revalidación se vuelve a correr el contador de `09` sobre los
   anuncios nuevos. El número de descripciones con el precio publicado después de enmascarar
   debe seguir en 0.
3. El modelo e5 se usa en una revisión fija (`10_embeddings_resumen.csv`). Si se cambia, se
   recalculan los vectores y se repite la comparación por parejas.
4. La prueba A/B propuesta (lineal vs. Random Forest) no cambia. Una variante con texto solo
   entraría si reduce el RMSE de CV frente a su pareja sin texto.

**Notas del expositor.**

- Esta lámina conecta con el criterio "Evaluación e impacto" y "Claridad en objetivos
  prácticos". Un comprador o vendedor describe la vivienda con un formulario; un modelo que
  exige el texto del anuncio cambia su predicción según cómo esté redactado.
- Si en la presentación anterior ya hay una lámina de costos por estrato (`06_costo_estrato.png`),
  aquí basta con remitir a ella.

---

## Diapositiva 12. Obstáculos

**Mensaje.** Hubo dos obstáculos técnicos: el tiempo de cómputo de las redes y del TF-IDF, y
el ruido entre folds, que es del mismo orden que las diferencias entre modelos. Además, el
MLP y los modelos lineales en niveles predicen precios negativos.

**Sustento.** `11_metricas_modelos_texto.csv` (`segundos_estimacion`), `11_cv_grillas.csv` y
`13_comparacion_modelos.csv` (`n_pred_negativas_prueba`).

**Cifras.**

- **Tiempo.**
  - La estimación de todas las variantes de `11` suma 32.6 min. La de mayor duración es el
    MLP + e5 sin PCA en log (5.1 min). Fuente: `11_metricas_modelos_texto.csv`.
  - El cálculo de los vectores e5 tomó 13.6 min. Fuente: `10_embeddings_resumen.csv`.
  - ⚠ La primera corrida con grillas amplias tardó 7.2 h. Fuente: bitácora 2026-11-09 y
    `CLAUDE.md`; no hay tabla en `03_Resultados/`.
- **Ruido entre folds.**
  - En la grilla del MLP tabular en log, el RMSE de CV va de 395.6 M a 442.4 M, con
    desviaciones entre folds de 40.6 M a 103.2 M. Fuente: `11_cv_grillas.csv`.
  - En el RF, la desviación entre folds (65–69 M) es mayor que cualquier diferencia entre
    sus variantes con y sin texto. Fuente: `13_comparacion_modelos.csv`.
- **Predicciones negativas en prueba, con el objetivo en niveles.**
  - MLP tabular 7, MLP + e5 5 y MLP + e5 PCA 2.
  - Ridge + TF-IDF 169 y línea base 218.
  - Con el objetivo en log no hay ninguna, y tampoco en los RF.

  Fuente: `13_comparacion_modelos.csv`.

**Qué hicimos al respecto.**

- Las grillas se recortaron con la evidencia de la corrida larga: weight decay 1e-2 fue el
  peor en todas las superficies del MLP, y en Ridge + TF-IDF los alpha menores a 0.1 dieron
  más error.
- A la parada temprana se le agregó una mejora mínima.
- Los vectores se guardan en disco para que `00_main.py` no los recalcule.
- La comparación se hace por parejas y se reporta la desviación entre folds junto a cada
  RMSE.

**Notas del expositor.**

- Con el ruido entre folds, una diferencia de 5 M entre dos variantes del RF no permite
  ordenarlas con confianza.
- Las predicciones negativas en niveles son una razón técnica para preferir el objetivo en
  log en los modelos que no son árboles.

---

## Diapositiva 13. Paso siguiente: IA generativa para extraer características (propuesta)

**Mensaje.** El siguiente paso es usar un LLM para convertir cada descripción, ya enmascarada,
en características definidas (vista exterior o interior, piso, remodelado, dúplex, balcón,
estado de conservación). Esas columnas entrarían al Random Forest como cualquier otra
variable.

**Sustento.** Sección D1 de `05_Notas/alternativas_aprendizaje_profundo_descripcion.md`. No
hay resultados todavía (`12_texto_llm.py` no existe).

**Por qué este paso.**

- Conserva el uso con formulario: las características extraídas se pueden llenar sin un
  anuncio escrito.
- Es interpretable: las columnas nuevas aparecen en la importancia de variables.
- Se calcula una vez, sin el precio. Las salidas se guardan en `01_Datos/02_Limpios/` para
  que la corrida sea reproducible sin volver a llamar a la API.

**Cómo se validaría.**

- 200 descripciones etiquetadas a mano por el equipo, con precisión y *recall* por campo.
- RF + atributos LLM contra el RF tabular, con la misma CV y la misma prueba (misma regla
  de parejas).

**Notas del expositor.**

- Riesgos: el LLM puede equivocarse o inventar (por eso las 200 etiquetas), y el texto se
  envía a un servicio externo (por eso se enmascaran teléfonos y correos).
- Abierto con el equipo: proveedor, presupuesto y SDK, y quién etiqueta las 200
  descripciones. El costo estimado está en la nota de alternativas, pero son precios de
  lista y no una corrida; no se pone en la lámina.

---

## Diapositiva 14 (o nota al pie). Uso de IA generativa en esta etapa

**Mensaje.** Usamos Claude Code para escribir los scripts 09, 10, 11 y 13 y este borrador.
Lo verificamos con controles en el código y revisión manual.

**Sustento.** Bitácora `06_Bitacoras/2026-11-09_modelos-texto-aprendizaje-profundo.md`
(sección "Uso de IA").

**Notas del expositor.**

- Verificaciones:
  1. contador del precio literal antes y después de enmascarar (1,057 → 0,
     `09_enmascaramiento.csv`);
  2. el RF tabular de `11` reproduce las métricas de `04` (control con `assert`);
  3. revisión manual de ejemplos de cada regla de enmascaramiento.
- `multilingual-e5-base` solo convierte texto en vectores: no genera texto ni ve el precio.

---

## Verificación del borrador

### Cobertura de la rúbrica de avance (`../Rubrica_Presentacion_Avance.xlsx`)

| Criterio | Diapositivas |
| --- | --- |
| Resultados con métodos clásicos (línea base, métricas, validación) | 3, 5, 6 |
| Diagnóstico de obstáculos | 7, 12 |
| Propuesta de aprendizaje profundo o IA generativa (estructura de datos, pros y contras) | 1, 3, 4, 13 |
| Evaluación e impacto (costos/beneficios, monitoreo) | 9, 11 |
| IA responsable (a quién afectan los errores, variables sensibles, mitigación) | 2, 8, 9, 10 |
| Claridad en objetivos prácticos | 11 |
| Trabajo en equipo | No aplica a estas láminas. Se evalúa con los commits y con quién expone cada parte |

### Cifras que no salen de `03_Resultados/`

- ⚠ "7.2 h" de la corrida con grillas amplias (diapositiva 12): solo aparece en la bitácora
  y en `CLAUDE.md`. Hay dos opciones: quitarla de la lámina, o dejarla en las notas del
  expositor citando la bitácora.

### Pendientes antes de pasar a Canva

- Corregir tres cifras en la bitácora del 2026-11-09:
  - el rango de sensibilidad es de hasta 8.3 M, no 8.1 M;
  - la frase "el orden de los modelos no cambia" (diapositiva 7);
  - Ridge + TF-IDF en niveles baja 9.6% frente a Ridge tabular, no 9.7% (el valor es −9.649%,
    diapositiva 6).
- Las figuras de las diapositivas 6 y 10 (`13_cambio_texto_vs_pareja.png` y
  `13_ablacion_estrato_localidad.png`) usan la misma paleta y fondo que las demás `13_*`. En
  Canva se insertan tal cual, sin rehacerlas a mano.
- Confirmar con el equipo si se enmascaran los nombres de barrio. La respuesta cambia las
  notas de las diapositivas 2 y 10.
- Decidir si la diapositiva 13 va como propuesta (este borrador) o si se espera a tener
  resultados del paso 4.
