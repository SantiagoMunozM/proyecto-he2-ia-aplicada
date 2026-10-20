---
name: registrar-sesion
description: Cierra una sesión de trabajo del proyecto de precios de vivienda en Bogotá — escribe la bitácora en 06_Bitacoras/ con el formato exigido por CLAUDE.md, actualiza HANDOFF.md con el estado actual y el siguiente objetivo, y actualiza README.md si la sesión cambió algo que este documenta. Usar cuando el usuario pida "cerrar sesión", "registrar la sesión", "escribir la bitácora" o "actualizar el handoff".
---

# Registrar sesión de trabajo

Al terminar una sesión de trabajo en este proyecto, hace tres cosas en este
orden:

1. Escribir la bitácora de la sesión en `06_Bitacoras/`.
2. Actualizar `HANDOFF.md` (raíz del repo) a partir de esa bitácora.
3. Revisar `README.md` (raíz del repo) y actualizarlo solo si es necesario.

Básate solo en lo que ocurrió en la conversación. Confirma los archivos
afectados con `git status` / `git diff --stat` (y `git log` si hubo commits).
Si algo no es inferible con certeza (quién de los integrantes trabajó en la
sesión, un supuesto, un resultado ambiguo, cuál debe ser el siguiente
objetivo), pregunta al usuario en vez de adivinar. Si el usuario pide solo
algunas de las partes, haz solo esas.

## Paso 1: bitácora

Antes de escribir, lee `HANDOFF.md` y las bitácoras previas en `06_Bitacoras/`
(si existen) para entender qué se hizo, qué quedó pendiente y mantener el
formato.

Nombre del archivo: `YYYY-MM-DD_slug-descriptivo.md` (minúsculas, guiones), con
la fecha real de la sesión. Si ya hay una bitácora del mismo día con el mismo
tema, agrega un sufijo numérico (`_2`) o pregunta.

Estructura:

```markdown
# Bitácora — YYYY-MM-DD: <descripción corta>

**Integrantes en la sesión:** ...

## Resumen
Objetivo de la sesión y desarrollo, en pocos párrafos. Indica si se cumplió el
"Siguiente objetivo" que traía HANDOFF.md.

## Archivos
- Creados: ...
- Modificados: ...
- Eliminados: ...

## Detalle por archivo
### `ruta/relativa/archivo`
Qué cambió, decisiones de implementación, supuestos usados y la intuición
en lenguaje natural de cada decisión.

## Resultados nuevos (tablas, figuras, métricas)
Por cada uno: qué busca comunicar, cómo se generan los datos que lo alimentan
y qué rol cumple dentro del proyecto. Omitir la sección si no hubo.

## Uso de IA
Herramienta usada, para qué se usó en la sesión y cómo se verificó el
resultado (política del curso).

## Pendientes
Lo que quedó sin hacer, supuestos sin confirmar y el siguiente paso. Esta
sección alimenta el "Siguiente objetivo" de HANDOFF.md.
```

Reglas de contenido (de `CLAUDE.md`):

- Reporta cuántas observaciones se pierden en cualquier limpieza o filtro
  mencionado.
- Las métricas (RMSE, MAPE) se reportan siempre junto a la línea base lineal y
  aclarando si son de entrenamiento, validación cruzada o prueba.
- No juicios de "bueno" o "malo" sobre resultados, ni entusiasmo por métricas o
  modelos.
- Sin código en la bitácora salvo que aporte a entender una decisión.
- Si en la sesión se tomó una decisión metodológica, se descartó un análisis o
  se aplicó una restricción de muestra, propón agregarla a la tabla
  correspondiente de `CLAUDE.md`.

## Paso 2: actualizar `HANDOFF.md`

Sigue las reglas de la sección "`HANDOFF.md`" de `CLAUDE.md`:

- **Siguiente objetivo:** reescríbelo. Una sola tarea concreta, con el archivo
  que debe producirse, un criterio de terminado verificable y los bloqueos o
  preguntas abiertas para el equipo. Derívalo de "Pendientes" de la bitácora; si
  hay varias opciones razonables, pregunta al usuario cuál sigue. Si el objetivo
  anterior no se terminó, se mantiene.
- **Estado actual:** reescríbelo para reflejar qué existe y funciona hoy
  (datos, scripts, resultados). No es un historial.
- **Registro de sesiones:** agrega una entrada arriba (la más reciente
  primero) con encabezado `### YYYY-MM-DD: <tema>`, de tres a cinco líneas, con
  lo que se hizo, quién trabajó y el enlace a la bitácora. Si el objetivo no se
  terminó, anota qué avanzó y qué lo impidió. No edites las entradas
  anteriores.

## Paso 3: revisar `README.md`

El README es la carta de presentación del repo para quien llega por primera
vez (profesor, evaluadores, equipo). A diferencia de `HANDOFF.md`, no es un
registro de avance: describe el proyecto tal como está. Solo se toca si la
sesión cambió algo que él documenta. Si nada cambió, no lo edites y dilo en el
cierre ("README sin cambios").

Revisa estos puntos contra lo ocurrido en la sesión y contra el contenido del
repo (`git status`, `ls`):

| Sección del README | Actualizar si la sesión... |
| --- | --- |
| Enfoque (línea base, modelo, métricas, validación) | cambió o fijó una decisión metodológica (modelos, métricas, tipo de partición, semilla) |
| Datos | agregó, quitó o transformó fuentes de datos, o descubrió una advertencia nueva sobre la base |
| Estructura del repositorio | creó, renombró o eliminó carpetas o archivos de la raíz, o `00_main.py` pasó a existir |
| Cómo reproducir | creó scripts, `00_main.py`, `requirements.txt` o cambió el entorno o el orden de ejecución |
| IA responsable | produjo hallazgos o decisiones sobre sesgos y su mitigación |
| Integrantes | cambió el equipo |

Reglas:

- Ediciones mínimas y puntuales: cambia solo las líneas afectadas, no
  reescribas el documento. Conserva el tono, el orden de secciones y el idioma
  (español).
- Quita los marcadores "pendiente" de lo que ya existe y funciona. No describas
  como existente algo que no está en el repo: verifícalo antes de escribirlo.
- Cuando el pipeline exista, la sección "Cómo reproducir" lista los comandos
  reales y los scripts en orden. No incluyas cifras de resultados escritas a
  mano. Si se muestra una métrica, debe salir de una corrida y apuntar a la
  tabla o figura de `03_Resultados/` que la contiene.
- Sin juicios de "bueno" o "malo" ni entusiasmo por métricas o modelos
  (`CLAUDE.md`, "Primero el diseño, después los resultados").
- No dupliques lo que ya está en `HANDOFF.md` (siguiente objetivo, historial de
  sesiones) ni en las bitácoras; enlázalos.
- Si el cambio al README no es obvio (por ejemplo, cambia el enfoque
  metodológico), muéstraselo al usuario antes de escribirlo.
- Anota en la bitácora (sección "Archivos") que se modificó `README.md`.

## Versionado

Haz commit de la bitácora, de `HANDOFF.md` y de `README.md` si cambió (junto con
los scripts y resultados de la sesión, si el usuario no los ha versionado aún) y
súbelos al
repositorio de GitHub asociado, salvo que el usuario indique lo contrario.

- Los datos de `01_Datos/` se versionan. Si un archivo nuevo supera los
  100 MB (límite de GitHub), no lo agregues y consulta al usuario.
- Nunca push a `main` sin que el usuario lo pida; si la sesión trabajó en otra
  rama, súbela en esa rama.

## Cierre

Termina con un reporte corto: ruta de la bitácora, el siguiente objetivo que
quedó en `HANDOFF.md`, si `README.md` se actualizó (y qué secciones) o quedó sin
cambios, y si hubo commit/push.
