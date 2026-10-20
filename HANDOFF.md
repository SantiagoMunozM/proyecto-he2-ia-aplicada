# HANDOFF

Resumen accionable del proyecto para retomar el trabajo. El detalle de cada
sesión está en `06_Bitacoras/`; aquí solo va lo necesario para saber dónde
estamos y qué sigue.

## Siguiente objetivo

<!-- Una sola tarea concreta, con el script o archivo que debe producirse y
     cómo se sabe que quedó terminada. Se reescribe al cerrar cada sesión. -->

**Objetivo:** escribir `02_Scripts/01_lectura_datos.py`, que cargue el JSON y
normalice el formato MongoDB Extended JSON (texto a numérico,
`$numberDouble: NaN` a faltante, `$date`/`$oid`).

**Criterio de terminado:** el script corre desde la raíz, guarda la base en
`01_Datos/02_Limpios/` y reporta el número de registros y de faltantes por
columna.

**Bloqueos / preguntas abiertas:**

- Definir el entorno de Python (versión, `requirements.txt`).
- Completar roles y correos de Maria Paula Rivera y Angelo Di Marco en
  `CLAUDE.md`.

## Estado actual

<!-- Qué existe y funciona hoy: datos, scripts, resultados. Se actualiza al
     cerrar cada sesión; no es un historial. -->

- `CLAUDE.md` con contexto, reglas y estructura; `HANDOFF.md`; skill de
  proyecto `registrar-sesion` para cerrar sesiones.
- Datos crudos versionados en `01_Datos/01_Crudos/`: JSON principal (43,013
  registros), `README_columnas.md` y `external/`.
- Estructura completa de carpetas; las vacías llevan `.gitkeep`.
- Aún no hay scripts ni resultados.
- Todo está en `main` en GitHub.

## Registro de sesiones

<!-- Una entrada por sesión, la más reciente arriba. Tres a cinco líneas:
     qué se hizo y enlace a la bitácora. -->

### 2026-10-20: configuración inicial

- Santiago Muñoz. Se crearon `CLAUDE.md`, `HANDOFF.md` y la skill
  `registrar-sesion`.
- Se movieron los crudos a `01_Datos/01_Crudos/` sin modificarlos y se creó la
  estructura de carpetas (dos niveles de datos: crudos y limpios).
- Primer commit y push a `main`.
- Bitácora: [2026-10-20_configuracion-inicial.md](06_Bitacoras/2026-10-20_configuracion-inicial.md)
