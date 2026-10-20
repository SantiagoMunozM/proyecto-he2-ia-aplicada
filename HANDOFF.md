# HANDOFF

Resumen accionable del proyecto para retomar el trabajo. El detalle de cada
sesión está en `06_Bitacoras/`; aquí solo va lo necesario para saber dónde
estamos y qué sigue.

## Siguiente objetivo

<!-- Una sola tarea concreta, con el script o archivo que debe producirse y
     cómo se sabe que quedó terminada. Se reescribe al cerrar cada sesión. -->

**Objetivo:** escribir `02_Scripts/01_lectura_datos.py`, que cargue el JSON y normalice el formato
MongoDB Extended JSON (texto a numérico, `$numberDouble: NaN` a faltante,
`$date`/`$oid`).

**Criterio de terminado:** el script corre desde la raíz, guarda la base en
`01_Datos/02_Limpios/` y reporta el número de registros y de faltantes por
columna.

**Bloqueos / preguntas abiertas:**

- Definir el entorno de Python (versión, `requirements.txt`).

## Estado actual

<!-- Qué existe y funciona hoy: datos, scripts, resultados. Se actualiza al
     cerrar cada sesión; no es un historial. -->

- Repositorio con `CLAUDE.md`, `HANDOFF.md` y la skill `registrar-sesion`.
- Datos crudos en `01_Datos/01_Crudos/`: JSON principal,
  `README_columnas.md` y `external/`. Se versionan tal cual.
- Estructura completa de carpetas creada; las vacías llevan `.gitkeep`.
- Aún no hay commits en el repositorio.
- Aún no hay scripts, resultados ni bitácoras.

## Registro de sesiones

<!-- Una entrada por sesión, la más reciente arriba. Tres a cinco líneas:
     qué se hizo y enlace a la bitácora. -->

### 2026-10-20: configuración inicial

- Se creó `CLAUDE.md` con el contexto del proyecto, la estructura de carpetas
  y las reglas de trabajo, a partir de la propuesta y de los laboratorios de
  Ciencia de Datos.
- Se creó este `HANDOFF.md` y la skill de proyecto `registrar-sesion`
  (bitácora + actualización del handoff).
- Se movieron los crudos de `datos/` a `01_Datos/01_Crudos/` sin modificarlos
  (16 archivos, sumas de verificación idénticas antes y después).
- Se creó el resto de carpetas con `.gitkeep`. Decisiones: crudos versionados
  sin LFS y solo dos niveles de datos (`01_Crudos/`, `02_Limpios/`).
- Bitácora: pendiente (sesión anterior a la estructura de `06_Bitacoras/`).
