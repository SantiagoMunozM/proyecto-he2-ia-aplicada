---
name: registrar-sesion
description: Cierra una sesión de trabajo del proyecto de precios de vivienda en Bogotá — escribe la bitácora en 06_Bitacoras/ con el formato exigido por CLAUDE.md y actualiza HANDOFF.md con el estado actual y el siguiente objetivo. Usar cuando el usuario pida "cerrar sesión", "registrar la sesión", "escribir la bitácora" o "actualizar el handoff".
---

# Registrar sesión de trabajo

Al terminar una sesión de trabajo en este proyecto, hace dos cosas en este
orden:

1. Escribir la bitácora de la sesión en `06_Bitacoras/`.
2. Actualizar `HANDOFF.md` (raíz del repo) a partir de esa bitácora.

Básate solo en lo que ocurrió en la conversación. Confirma los archivos
afectados con `git status` / `git diff --stat` (y `git log` si hubo commits).
Si algo no es inferible con certeza (quién de los integrantes trabajó en la
sesión, un supuesto, un resultado ambiguo, cuál debe ser el siguiente
objetivo), pregunta al usuario en vez de adivinar. Si el usuario pide solo una
de las dos partes, haz solo esa.

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

## Versionado

Haz commit de la bitácora y de `HANDOFF.md` (junto con los scripts y
resultados de la sesión, si el usuario no los ha versionado aún) y súbelos al
repositorio de GitHub asociado, salvo que el usuario indique lo contrario.

- Los datos de `01_Datos/` se versionan. Si un archivo nuevo supera los
  100 MB (límite de GitHub), no lo agregues y consulta al usuario.
- Nunca push a `main` sin que el usuario lo pida; si la sesión trabajó en otra
  rama, súbela en esa rama.

## Cierre

Termina con un reporte corto: ruta de la bitácora, el siguiente objetivo que
quedó en `HANDOFF.md` y si hubo commit/push.
