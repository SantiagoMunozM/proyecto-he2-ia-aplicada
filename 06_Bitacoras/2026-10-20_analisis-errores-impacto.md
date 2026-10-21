# Bitácora — 2026-10-20: análisis de errores por estrato y localidad y evaluación de impacto

**Integrantes en la sesión:** Santiago Muñoz (inferido del usuario de git; confirmar)

## Resumen

El "Siguiente objetivo" que traía `HANDOFF.md` era `02_Scripts/05_analisis_errores_impacto.py`:
desagregar los errores de prueba por estrato y localidad y traducirlos a costo para el
usuario, con el diseño de la prueba A/B reducido a lo calculable. Se cumplió: el script
existe, corre desde la raíz en pocos segundos y escribe tablas y figuras `05_*`. No se
corrió `00_main.py` completo (el script 04 tarda varios minutos), así que la corrida
encadenada no está verificada.

El script no reestima nada: lee `04_predicciones_prueba.csv` y compara la línea base
lineal con el Random Forest en las dos escalas del objetivo (log y niveles). Se
resolvieron dos bloqueos del HANDOFF por decisión de esta sesión (ver Pendientes para lo
que sigue abierto): el tamaño mínimo de grupo es 30 (el mismo
`N_MINIMO_GRUPO_PRUEBA` del script 04) y la evaluación de impacto calcula solo el error
de precio; tiempo de compra/venta y ahorro real quedan como propuesta.

Pérdida de observaciones: ninguna. Se usan las 5,465 viviendas del conjunto de prueba.

## Archivos

- Creados: `02_Scripts/05_analisis_errores_impacto.py`;
  `03_Resultados/Tablas/05_errores_por_estrato.csv`, `05_errores_por_localidad.csv`,
  `05_costo_esperado_por_estrato.csv`, `05_comparacion_por_localidad.csv`,
  `05_diseno_ab.csv`; `03_Resultados/Figuras/05_costo_esperado_por_estrato.png`,
  `05_sesgo_por_localidad.png`; esta bitácora.
- Modificados: `HANDOFF.md`, `README.md` (paso 5 de "Cómo reproducir" y una frase en
  "IA responsable").
- Eliminados: ninguno.

## Detalle por archivo

### `02_Scripts/05_analisis_errores_impacto.py`

1. **Error por vivienda.** Formato largo (vivienda × modelo × escala). Error =
   predicción − precio publicado: positivo es sobrevaloración, negativo subvaloración.
2. **Errores por grupo** (estrato, localidad y total): RMSE, MAE, mediana y percentil 90
   del error absoluto, sesgo en COP, MAPE, sesgo relativo medio y mediano con su error
   estándar, proporción de viviendas sobre y subvaloradas, y el conteo de predicciones
   no positivas. Los grupos con menos de 30 viviendas en prueba llevan la marca
   `n_prueba_menor_minimo`; no se omiten.
3. **Costo esperado por vivienda.** Supone que el usuario sigue el precio del modelo: el
   comprador paga de más cuando el modelo sobrevalora (`max(pred − precio, 0)`) y el
   vendedor deja de recibir cuando subvalora (`max(precio − pred, 0)`). Se reportan en
   COP y como % del precio mediano del grupo, y la reducción del Random Forest frente a la
   línea base. La intuición: un error simétrico en pesos no afecta igual a quien compra
   que a quien vende, y en estratos bajos el mismo monto pesa más sobre el precio.
4. **Diseño A/B.** Entre usuarios independientes, tamaño por brazo para detectar la
   reducción observada del error absoluto (en pesos y relativo) con la aproximación normal
   (alfa 0.05 a dos colas, potencia 0.80; z escritos como constantes para no depender de
   `scipy`) y efecto mínimo detectable con 100, 500 y 1,000 usuarios por brazo. Se calcula
   por estrato y en total, en las dos escalas.
5. **Figuras.** Dos, con la paleta del script 04. La leyenda de la figura por localidad se
   movió fuera de los ejes tras ver que tapaba un punto.

Supuestos: el precio es el publicado, no el de transacción, de modo que el costo es una
aproximación al error de precio, no un ahorro medido. La aproximación normal se aplica a un
error con colas pesadas, así que los tamaños por brazo son indicativos.

## Resultados nuevos (tablas, figuras, métricas)

Todo sale de la corrida del script; los valores se citan de las tablas. Prueba, 5,465
viviendas. MAE en millones de COP por vivienda, línea base lineal frente a Random Forest
de la misma escala (`05_costo_esperado_por_estrato.csv`):

| Estrato (n prueba) | MAE base, log | MAE RF, log | MAE base, niveles | MAE RF, niveles |
|---|---|---|---|---|
| 1 (16, marcado) | 233.4 | 124.0 | 262.3 | 105.5 |
| 2 (191) | 31.3 | 22.1 | 126.9 | 23.3 |
| 3 (676) | 57.3 | 36.7 | 183.1 | 36.8 |
| 4 (1,148) | 79.2 | 52.5 | 181.6 | 56.0 |
| 5 (1,056) | 136.3 | 102.6 | 209.3 | 105.6 |
| 6 (2,378) | 339.3 | 241.0 | 379.1 | 239.6 |
| Total (5,465) | 199.5 | 141.4 | 271.4 | 142.1 |

Observaciones descriptivas:

- En los seis estratos el MAE del Random Forest es menor que el de la línea base en
  ambas escalas; la reducción total es 29.1% en log y 47.6% en niveles.
- Estrato 1: con 16 viviendas la cifra es poco estable. En log, la pérdida esperada del
  vendedor con el Random Forest (101.1) es mayor que el sobrecosto del comprador (23.0).
- Estrato 6, en log: pérdida del vendedor 142.3 frente a sobrecosto del comprador 98.7.
- Localidades: con 30 o más viviendas, el sesgo relativo medio del Random Forest en log
  es mayor en magnitud que el de la línea base en varias (p. ej. Los Mártires, +6.9% frente
  a +0.4%; Santa Fe, −3.4% frente a +0.4%). Los grupos pequeños (siete localidades) llegan
  a ±15–23% en el Random Forest en log y no se interpretan.
- A/B, error absoluto relativo en log: 148 usuarios por brazo para detectar la reducción
  observada en total; por estrato, entre 7 (estrato 1) y 690 (estrato 5, la mayor
  varianza). Los lineales en niveles producen predicciones negativas (ver
  `n_pred_no_positivas` en `05_errores_por_*.csv`).

Rol en el proyecto: insumo de la traducción a costo/beneficio y del análisis de sesgos
para las presentaciones de avance y la sección de IA responsable.

## Uso de IA

- **Herramienta:** Claude Code (Claude Sonnet 5.5).
- **Para qué:** diseñar y escribir el script 05, correrlo, revisar las figuras y redactar
  esta bitácora.
- **Cómo se verificó:** el script corrió dos veces sin errores desde la raíz con
  `.venv/bin/python`; se revisaron visualmente las dos figuras (una leyenda que tapaba un
  punto se corrigió y se volvió a revisar); las cifras de esta bitácora se copiaron de la
  salida de la corrida. No se contrastaron las tablas con un cálculo independiente ni se
  corrió `00_main.py` completo.

## Pendientes

- **Siguiente objetivo (elegido por el usuario):** ampliar la grilla del Random Forest
  (`min_samples_leaf=1` quedó en el borde) en `04_estimacion_modelos.py` y volver a correr
  04 y 05, antes de interpretar los errores por grupo.
- Confirmar con el equipo el umbral de 30 viviendas y el reparto de la evaluación de
  impacto (qué se calcula y qué queda como propuesta).
- Verificar `python 00_main.py` completo con el script 05 incluido.
- Completar roles y correos de Maria Paula Rivera y Angelo Di Marco en `CLAUDE.md`.
- El commit `bd96c50` (partición, estimación y `00_main.py`) sigue sin bitácora propia.
- Decisiones propuestas para la tabla de `CLAUDE.md`: (a) los grupos con menos de 30
  viviendas en prueba se marcan y no se interpretan; (b) el costo del error se traduce
  como sobrecosto del comprador y pérdida del vendedor, sobre el precio publicado;
  (c) la prueba A/B se dimensiona con el error de precio, y tiempo y ahorro quedan como
  propuesta.
