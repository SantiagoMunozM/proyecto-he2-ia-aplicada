# Bitácora — 2026-11-09: modelos de texto con la descripción (aprendizaje profundo) y comparación final

**Integrantes en la sesión:** Santiago Muñoz (inferido del usuario de git; confirmar).

## Resumen

La sesión no trabajó en el "Siguiente objetivo" que traía `HANDOFF.md` (revisar los
resultados contra la rúbrica de la presentación de avance). El usuario pidió seguir el plan
de la sección 7 de `05_Notas/alternativas_aprendizaje_profundo_descripcion.md`, que responde
a la brecha de mayor peso de esa revisión: la propuesta de aprendizaje profundo o IA
generativa (peso 0.20). Se hicieron los pasos 1, 2, 3 y 5 del plan; el paso 4 (extracción
con LLM) quedó pendiente.

1. **Paso 1. Limpieza del texto y palabras clave (A1).** `09_texto_limpieza.py` enmascara en
   `descripcion` las cifras de dinero, los teléfonos y los correos, y crea 17 variables por
   palabras clave que describen solo la vivienda. No se elimina ninguna fila.
2. **Paso 2. TF-IDF (A2)** y **paso 3. vectores preentrenados (C1).** `10_texto_embeddings.py`
   calcula una vez los vectores de `intfloat/multilingual-e5-base` y los guarda en disco.
   `11_modelos_texto.py` estima, en log y en niveles, Random Forest con palabras clave, con
   PCA de TF-IDF y con PCA de los vectores; Ridge con TF-IDF; y un MLP híbrido en PyTorch
   (variables tabulares más vectores). Cada variante con texto tiene una pareja sin texto
   estimada igual, y hay una ablación sin estrato ni localidad.
3. **Grillas.** Una primera corrida con grillas amplias tardó 7.2 h, casi todo en el MLP y en
   Ridge + TF-IDF con alpha pequeño. Con esa evidencia se recortaron las grillas, se agregó una
   mejora mínima a la parada temprana del MLP y la corrida final de 11 tardó 46 min.
4. **Pipeline completo.** `00_main.py` corrió de 01 a 11 sin errores en 60.1 min. 10 no
   recalculó los vectores y el RF tabular de 11 reproduce el de 04 (diferencia relativa
   máxima 6.7e-16). Las tablas `04_*` y `05_*` se regeneraron: solo cambian los tiempos de
   estimación y diferencias numéricas menores a 1e-10.
5. **Paso 5. Comparación final.** `13_comparacion_final.py` reúne en una tabla los 15
   modelos (clásicos y de texto) contra la línea base, resume los sesgos por estrato y
   localidad y dibuja tres figuras para la presentación.

No hubo pérdida de observaciones: los scripts nuevos usan las 26,900 viviendas de la base
limpia y la misma partición (21,520 en entrenamiento, 5,380 en prueba).

## Archivos

- Creados:
  - `02_Scripts/09_texto_limpieza.py`, `02_Scripts/10_texto_embeddings.py`,
    `02_Scripts/11_modelos_texto.py`, `02_Scripts/13_comparacion_final.py`.
  - `01_Datos/02_Limpios/descripcion_limpia.csv` (15 MB) y
    `01_Datos/02_Limpios/embeddings_e5_base.npz` (38 MB).
  - Tablas `09_enmascaramiento.csv`, `09_variables_palabras_clave.csv`,
    `10_embeddings_resumen.csv`, `11_*.csv` (7 tablas) y `13_*.csv` (3 tablas).
  - Figuras `13_rmse_todas_variantes.png`, `13_mape_estrato_texto.png`,
    `13_sesgo_estrato_texto.png`.
  - Esta bitácora.
- Modificados: `CLAUDE.md` (seis decisiones nuevas), `requirements.txt` (librerías de texto),
  `HANDOFF.md`, `README.md`, y las tablas `04_*` y `05_*` regeneradas por `00_main.py`
  (sin cambios en los valores).
- Versionados en esta sesión, aunque no se produjeron en ella: los PDF de
  `04_Presentaciones/`, `04_Presentaciones/guion_presentacion_avance.docx` y
  `05_Notas/alternativas_aprendizaje_profundo_descripcion.md` y `.pdf`.
- Eliminados: ninguno.

## Detalle por archivo

### `02_Scripts/09_texto_limpieza.py`

Lee `codigo`, `descripcion` y `precio_venta` de la base limpia y escribe
`descripcion_limpia.csv` (26,900 × 21).

- **Enmascaramiento.** Las reglas se aplican en orden:
  1. correos;
  2. celulares y fijos, también escritos en palabras después de "celular", "whatsapp", etc.;
  3. montos con `$`;
  4. números con unidad ("millones", "mil", "mill" y errores de escritura como "millo");
  5. números en palabras seguidos de "millones";
  6. números de siete o más cifras con separadores;
  7. cifras con formato de miles después de una palabra de contexto (valor, precio,
     administración, canon, etc.).

  La intuición es quitar el precio literal (fuga del objetivo) y lo que está atado a él sin
  ser característica (administración, canon), sin borrar áreas ni pisos. Por eso la regla de
  contexto exige formato de miles y excluye los números seguidos de unidades de área.
- **Control de fuga.** Antes y después de enmascarar se cuenta en cuántas descripciones
  aparece el precio publicado (±2%). Para que un número pequeño no coincida por azar, el
  multiplicador solo se aplica si la cifra trae unidad o va después de `$`.
- **Variables por palabras clave (A1).** Son 15 binarias, más el número de piso mencionado y
  si se menciona algún piso. Las binarias son: vista, exterior, interior, balcón, remodelado,
  para remodelar, iluminado, dúplex, penthouse, estudio, depósito, cuarto de servicio,
  chimenea, esquinero y piso alto.
  - Una negación simple ("sin", "no tiene", "no hay") anula la mención.
  - El piso es la primera mención en el texto y debe estar entre 1 y 60.
  - No se crean variables de negociación, barrio ni estrato (decisión registrada en
    `CLAUDE.md`).
- **Supuesto sin confirmar:** los nombres de barrio no se enmascaran (pendiente con el equipo).

### `02_Scripts/10_texto_embeddings.py`

Calcula un vector de 768 dimensiones por descripción con `intfloat/multilingual-e5-base`, en
revisión fija, congelado y con el prefijo "query: ". Antes quita los marcadores del
enmascaramiento y normaliza cada vector a norma 1. Se eligió e5-base frente a MiniLM porque
lee hasta 512 tokens, y ninguna descripción se trunca (máximo 382). Los vectores se guardan
como float16 en un `.npz`. Si el archivo ya coincide en códigos, modelo y revisión, el script
no recalcula (el cálculo tarda 13.6 min en un M1 con MPS); `--recalcular` lo fuerza. El
modelo nunca ve el precio, así que calcularlo para toda la base no filtra información.

### `02_Scripts/11_modelos_texto.py`

Usa la partición de 03 y los hiperparámetros del Random Forest que eligió 04. Estima cada
variante en log y en niveles, con CV de 5 folds solo sobre entrenamiento.

- **Bloques de variables.** Hay matrices tabulares para árboles y para modelos lineales,
  palabras clave, TF-IDF de unigramas y bigramas (`min_df=5`), y vectores e5.
  - TF-IDF, PCA y escalamiento se ajustan solo con entrenamiento.
  - Los PCA tienen 50 componentes, y la CV elige cuántos se usan.
- **Variantes y su pareja sin texto:**

  | Variante con texto | Pareja sin texto |
  | --- | --- |
  | RF + palabras clave | RF tabular |
  | RF + TF-IDF PCA | RF tabular |
  | RF + e5 PCA | RF tabular |
  | RF + e5 PCA sin estrato ni localidad | RF sin estrato ni localidad |
  | Ridge + TF-IDF | Ridge tabular |
  | MLP + e5 | MLP tabular |
  | MLP + e5 PCA | MLP tabular |

  La intuición es atribuir la diferencia al texto y no a otra búsqueda de hiperparámetros,
  por eso los RF con texto conservan los hiperparámetros de 04.
- **MLP híbrido** (`MLPHibrido`, compatible con `cross_validate`):
  - Arquitectura: capas (256, 64), ReLU, Adam.
  - Objetivo: estandarizado dentro de cada fold.
  - La CV elige dropout y weight decay.
  - Parada temprana: usa un 10% del entrenamiento de cada fold (nunca la prueba) y exige una
    mejora mínima de 1e-4.
- **Grillas finales:**

  | Variante | Grilla |
  | --- | --- |
  | RF con PCA | k en [2, 5, 10, 25, 50] |
  | Ridge tabular | alpha desde 1e-4 |
  | Ridge + TF-IDF | alpha desde 0.1 |
  | MLP | dropout en [0.1, 0.3, 0.5] y weight decay en [1e-5, 1e-4, 1e-3] |

  La justificación con la corrida de 7.2 h está en `CLAUDE.md`. El RMSE de CV del RF sube de
  forma monótona con k, así que k=2 en el borde corresponde a "lo más cercano a no usar
  texto".
- **Controles y salidas:**
  - Control: el RF tabular debe reproducir las métricas de 04.
  - Importancia de variables con la participación del texto.
  - Errores por estrato y localidad.
  - Sensibilidad de prueba sin las viviendas cuya descripción limpia aparece idéntica en
    entrenamiento (219) o que tienen gemelo (241).

### `02_Scripts/13_comparacion_final.py`

No estima nada. Lee las tablas de 04 y 11 y produce:

- `13_comparacion_modelos.csv`: métricas de las 15 variantes y sus cambios frente a la base,
  al RF tabular y a la pareja sin texto.
- `13_errores_por_estrato.csv`.
- `13_resumen_sesgos.csv`.
- Tres figuras con la paleta de la presentación.

El número 12 queda libre para `12_texto_llm.py` (paso 4); si sus tablas existen con las
mismas columnas que las de 11, entran sin cambios. Las brechas entre grupos solo usan grupos
con al menos 30 viviendas en prueba; estrato 1 (16) se reporta en columnas aparte. Los dos
colores nuevos de las figuras pasaron un validador de separación para daltonismo y de
contraste sobre el fondo de las diapositivas.

### `CLAUDE.md` y `requirements.txt`

En `CLAUDE.md` se agregaron seis filas a "Decisiones tomadas" (2026-11-09):

- reglas de enmascaramiento;
- alcance de las variables A1;
- parejas sin texto y ablación;
- librerías nuevas;
- diseño del MLP;
- grillas.

`requirements.txt` fija `torch==2.15.0`, `sentence-transformers==6.2.0`,
`transformers==5.22.2` y `tokenizers==0.23.3`.

## Resultados nuevos (tablas, figuras, métricas)

- **`09_enmascaramiento.csv`.** Cuánto texto se modificó y si la fuga del precio desapareció.
  - Descripciones modificadas: 2,471 de 26,900 (9.19%).
  - Con dinero enmascarado: 1,956. Con teléfono: 546. Con correo: 4.
  - Con el precio publicado en el texto: 1,057 antes de enmascarar y 0 después.
- **`09_variables_palabras_clave.csv`.** Frecuencia de cada variable A1. El piso se menciona
  en el 41.1% de los anuncios.
- **`10_embeddings_resumen.csv`.** Modelo, revisión, largo en tokens (mediana 121,
  percentil 99 de 244, máximo 382, ninguna truncada) y tiempo de cálculo. Documenta la
  reproducibilidad de los vectores.
- **`11_*.csv`.** Métricas de entrenamiento, CV y prueba de cada variante con texto, junto a
  la línea base y a su pareja sin texto, más grillas, importancia, errores por grupo y
  sensibilidad. Es la evidencia técnica de la propuesta de aprendizaje profundo.
- **`13_comparacion_modelos.csv` y `13_rmse_todas_variantes.png`.** La tabla única que pide
  el criterio de terminado del paso 5: todas las variantes contra la línea base. RMSE en
  millones de COP:

  | Modelo | Objetivo | RMSE de CV | RMSE de prueba |
  | --- | --- | --- | --- |
  | Línea base | log | 462.9 | 433.4 |
  | Línea base | niveles | 508.9 | 473.3 |
  | Random Forest | log | 365.0 | 322.1 |
  | Random Forest | niveles | 354.8 | 310.1 |
  | XGBoost | log | 358.0 | 321.2 |
  | RF + e5 PCA | log | 369.7 | 328.3 |
  | RF + e5 PCA | niveles | 361.4 | 316.3 |
  | MLP tabular | log | 395.6 | 373.6 |
  | MLP tabular | niveles | 390.0 | 363.0 |
  | MLP + e5 PCA | log | 375.5 | 344.0 |
  | MLP + e5 PCA | niveles | 378.9 | 354.8 |
  | Ridge tabular | log | 446.1 | 399.9 |
  | Ridge tabular | niveles | 497.2 | 460.2 |
  | Ridge + TF-IDF | log | 392.1 | 346.0 |
  | Ridge + TF-IDF | niveles | 449.2 | 409.3 |

  - El menor RMSE de CV es el Random Forest con el objetivo en niveles (desviación entre
    folds de 65.2 M).
  - Frente a su pareja sin texto, el RMSE de CV:
    - sube entre 0.3% y 1.9% en los RF con texto;
    - baja 12.1% (log) y 9.7% (niveles) en Ridge + TF-IDF;
    - baja 5.1% y 2.9% en MLP + e5 PCA;
    - sube 6.3% y 5.6% en MLP + e5 sin PCA.
  - Las diferencias entre variantes de RF son menores que la desviación entre folds.
  - Ridge tabular con el alpha elegido (1e-4) reproduce al lineal completo de 04.
  - La importancia del texto en los RF es de 1.1% a 3.7% del total (`11_importancia_variables.csv`).
- **`13_resumen_sesgos.csv`, `13_mape_estrato_texto.png` y `13_sesgo_estrato_texto.png`.**
  Insumo de la sección de IA responsable.
  - Brecha de MAPE de prueba entre estratos, solo estratos 2 a 6:
    - RF tabular: 6.5 puntos (log) y 6.6 (niveles).
    - RF sin estrato ni localidad: 5.0 y 3.5 puntos, con un MAPE de prueba más alto en 0.3 y
      0.5 puntos.
    - Línea base, Lasso, Ridge y los MLP con el objetivo en niveles: de 17 a 60 puntos, con la
      mayor subvaloración en el estrato 2.
  - Ninguna conclusión se apoya en estrato 1 (16 viviendas en prueba).
- **Sensibilidad (`11_sensibilidad_duplicados.csv`).** Sin las 417 viviendas de prueba con
  descripción duplicada o gemelo en entrenamiento, el RMSE de prueba sube entre 1.8 y 8.1
  millones en todas las variantes. El orden de los modelos no cambia.

## Uso de IA

- **Herramienta:** Claude Code (Claude Opus 5.5).
- **Para qué se usó:**
  - Escribir los scripts 09, 10, 11 y 13.
  - Diseñar las reglas de enmascaramiento y las grillas.
  - Diagnosticar la corrida de 7.2 h, inspeccionando el proceso para ubicar el tiempo en el
    MLP y en Ridge + TF-IDF.
  - Redactar esta bitácora.
- **Cómo se verificó:**
  - El enmascaramiento se verificó con el contador de precio literal antes y después (1,057 →
    0) y revisando a mano ejemplos de cada regla. Así se detectaron y corrigieron áreas
    enmascaradas por error, teléfonos sin enmascarar y pisos mal extraídos.
  - El RF tabular de 11 reproduce las métricas de 04 (control con `assert`).
  - `00_main.py` corrió completo y las métricas coinciden con la corrida anterior de 11.
  - Las tablas `04_*` y `05_*` no cambiaron (diferencia relativa máxima de 1.2e-11).
  - Las figuras se revisaron visualmente.
- **Modelo de lenguaje dentro del pipeline:** `multilingual-e5-base` es un modelo
  preentrenado y congelado que solo convierte texto en vectores. No genera texto, no se
  entrenó con nuestros datos y no ve el precio.

## Pendientes

- **Siguiente objetivo (pedido por el usuario):** un borrador de presentación con los
  resultados de aprendizaje profundo, construido a partir de las tablas y figuras `11_*` y
  `13_*`.
- Confirmar con el equipo:
  - las librerías nuevas (`torch`, `sentence-transformers`);
  - si se enmascaran los nombres de barrio;
  - que los integrantes de esta sesión fueron los inferidos.
- **Paso 4 del plan (extracción con LLM, `12_texto_llm.py`):** decidir proveedor, presupuesto
  y SDK, y quién etiqueta a mano las 200 descripciones de validación y con qué criterio.
- Actualizar en `05_Notas/alternativas_aprendizaje_profundo_descripcion.md` las cifras
  marcadas con †: la nota dice 1,190 descripciones con el precio literal y la corrida da
  1,057.
- `02_analisis_descriptivo.py` usa el argumento `vert` de Matplotlib, que desaparece en la
  versión 3.13.
- Pendientes que se mantienen de sesiones anteriores:
  - revisión contra la rúbrica del avance;
  - roles y correos de los integrantes en `CLAUDE.md`;
  - bitácora del commit `bd96c50`.
