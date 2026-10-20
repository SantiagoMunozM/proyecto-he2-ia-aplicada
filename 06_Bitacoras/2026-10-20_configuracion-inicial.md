# Bitácora — 2026-10-20: configuración inicial del repositorio

**Integrantes en la sesión:** Santiago Muñoz

## Resumen

Objetivo: dejar el repositorio listo para empezar el trabajo técnico del
proyecto (predicción del precio de vivienda en Bogotá), con las reglas de
trabajo documentadas, un mecanismo para registrar cada sesión y los datos
crudos en su lugar.

Desarrollo:

1. Se escribió `CLAUDE.md` a partir de los documentos de contexto de la carpeta
   padre (propuesta presentada, enunciado de la Presentación 1, rúbricas de la
   Presentación 1 y del avance), del programa del curso, de las diapositivas
   (uso de scikit-learn) y de los `CLAUDE.md` del Taller 1 y de los
   Laboratorios 5 y 9 de Ciencia de Datos, que sirvieron como plantilla.
2. Se creó `HANDOFF.md`, un resumen de las bitácoras orientado a la siguiente
   acción, y se documentaron sus reglas de uso en `CLAUDE.md`.
3. Se adaptó la skill `registrar-sesion` del Laboratorio 9 como skill del
   proyecto, versionada para todo el equipo.
4. Se movieron los datos crudos de `datos/` a `01_Datos/01_Crudos/` y se creó
   la estructura de carpetas, con `.gitkeep` en las vacías.
5. Se hizo el primer commit y push a `main` (`79b8bd7`).

No había un "Siguiente objetivo" previo: es la primera sesión.

## Archivos

- Creados:
  - `CLAUDE.md`
  - `HANDOFF.md`
  - `.claude/skills/registrar-sesion/SKILL.md`
  - `.gitkeep` en `01_Datos/02_Limpios/`, `02_Scripts/`,
    `03_Resultados/Tablas/`, `03_Resultados/Figuras/`, `04_Presentaciones/`,
    `05_Notas/`, `06_Bitacoras/` y `07_Recursos/`
  - `06_Bitacoras/2026-10-20_configuracion-inicial.md` (este archivo)
- Movidos (sin modificar): `datos/*` → `01_Datos/01_Crudos/`
  (`processed_v2.0.0_august_2_2024.json`, `README_columnas.md`, `external/`)
- Eliminados: la carpeta `datos/`, que quedó vacía tras el movimiento.

## Detalle por archivo

### `CLAUDE.md`

Reglas del proyecto para Claude Code. Sigue la estructura del `CLAUDE.md` del
Taller 1 (contexto, estructura, reglas de trabajo, regla metodológica, datos,
integrantes, tablas de decisiones/descartes/restricciones, reglas estrictas).

Decisiones:

- **Contexto** tomado de la propuesta presentada: pregunta, Random Forest como
  modelo propuesto, regresión lineal como línea base, RMSE y MAPE, prueba A/B
  como evaluación de impacto y estrato/localidad como variables sensibles. Se
  agregó lo que piden la rúbrica de avance y el proyecto final, porque son los
  criterios con los que se calificará el trabajo que sigue.
- **Datos:** al inspeccionar el JSON se encontró que está en formato MongoDB
  Extended JSON (numéricos como texto, faltantes como
  `{'$numberDouble': 'NaN'}`, fechas e id como `$date`/`$oid`) y que
  `antiguedad` viene en rangos. Se documentó porque condiciona el primer
  script. Conteos: 43,013 registros; 27,270 de venta, 15,515 de arriendo y 228
  de venta y arriendo.
- **Método:** scikit-learn como librería de machine learning, siguiendo las
  diapositivas de las clases 2 y 4. Se fijaron reglas de evaluación fuera de
  muestra, validación cruzada solo sobre entrenamiento y uso de `Pipeline` para
  evitar fuga de información.
- **Semilla:** `random_state=2026`, para coincidir con los laboratorios (las
  diapositivas usan 42).
- **Un script por tarea**, numerado, corrido desde la raíz, con `00_main.py`
  para reproducir todo.

### `HANDOFF.md`

Tiene tres secciones: "Siguiente objetivo" (una sola tarea con criterio de
terminado y bloqueos, que se reescribe en cada cierre), "Estado actual" (qué
existe hoy, también se reescribe) y "Registro de sesiones" (una entrada corta
por sesión; las anteriores no se editan). La intuición es separar el porqué,
que va en las bitácoras, del qué sigue, que va en el handoff, para que quien
retome el proyecto no tenga que leer todas las bitácoras.

### `.claude/skills/registrar-sesion/SKILL.md`

Adaptación de la skill del Laboratorio 9. Cambios:

- Se quitó la copia del `.jsonl` de la conversación.
- Se agregó el paso de actualizar `HANDOFF.md`.
- Las bitácoras van en `06_Bitacoras/`.
- Se agregaron los campos "Integrantes en la sesión" (el curso califica
  contribuciones individuales) y "Uso de IA" (el programa exige documentarlo).
- Se agregaron reglas propias del proyecto: métricas siempre junto a la línea
  base y diciendo de qué conjunto vienen, y proponer actualizar las tablas de
  decisiones de `CLAUDE.md`.

### `01_Datos/01_Crudos/`

Se movieron los 16 archivos de `datos/` sin modificarlos. Se verificó con
sumas de verificación SHA-1 antes y después: idénticas.

### Estructura de carpetas

Por decisión del equipo, solo hay dos niveles de datos (`01_Crudos/` y
`02_Limpios/`), en vez de los tres del Taller 1. Las carpetas vacías llevan
`.gitkeep` para que git las conserve.

## Uso de IA

- **Herramienta:** Claude Code (Claude Opus 5.5).
- **Para qué:** redactar `CLAUDE.md`, `HANDOFF.md` y la skill a partir de los
  documentos del curso y de los laboratorios; inspeccionar la estructura del
  JSON; mover los datos y crear las carpetas; hacer el commit y el push.
- **Cómo se verificó:** el movimiento de datos se verificó con sumas de
  verificación. Los conteos del JSON salen de cargarlo con Python. Santiago
  Muñoz revisó cada archivo y pidió los ajustes (estructura de dos niveles,
  versionar el JSON, quitar la copia del `.jsonl`).

## Pendientes

- Escribir `02_Scripts/01_lectura_datos.py`, que cargue el JSON y normalice el
  formato MongoDB Extended JSON.
- Definir el entorno de Python (versión y `requirements.txt`).
- Completar roles y correos de Maria Paula Rivera y Angelo Di Marco en la tabla
  de integrantes de `CLAUDE.md`.
