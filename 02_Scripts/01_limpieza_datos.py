"""
01_limpieza_datos.py

Lectura, reconocimiento y limpieza de la base de apartamentos de Bogotá.

Insumos:
    01_Datos/01_Crudos/processed_v2.0.0_august_2_2024.json
    01_Datos/01_Crudos/README_columnas.md

Salidas:
    01_Datos/02_Limpios/apartamentos_venta_limpio.csv
    03_Resultados/Tablas/01_resumen_columnas.csv
    03_Resultados/Tablas/01_perdida_observaciones.csv
    03_Resultados/Tablas/01_perdida_por_localidad_estrato.csv
    03_Resultados/Tablas/01_estadisticas_numericas.csv
    03_Resultados/Tablas/01_anomalias.csv
    03_Resultados/Tablas/01_duplicados_eliminados.csv

Pasos:
    1. Lee el JSON y normaliza el formato MongoDB Extended JSON.
    2. Reconocimiento: tipos crudos frente al README, faltantes, estadísticas.
    3. Alcance (ventas), eliminación de columnas excluidas o casi vacías,
       sector/barrio en N/A -> SIN_DATO, eliminación de filas con N/A en el
       resto, parqueaderos negativos -> 0, filtros de validez (area > 0,
       estrato entre 1 y 6, banos >= 1, precio por m2 en rango plausible) y
       eliminación de anuncios repetidos (filas idénticas salvo codigo y fechas).
    4. Convierte cada columna al tipo que describe el README y lo verifica.
    5. Guarda la base limpia. Los crudos nunca se modifican.

Se corre desde la raíz del repo: python3 02_Scripts/01_limpieza_datos.py
"""

import json
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Rutas (ancladas a la raíz del proyecto, que es la carpeta padre de 02_Scripts)
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
RUTA_JSON = RAIZ / "01_Datos" / "01_Crudos" / "processed_v2.0.0_august_2_2024.json"
RUTA_README = RAIZ / "01_Datos" / "01_Crudos" / "README_columnas.md"
RUTA_SALIDA = RAIZ / "01_Datos" / "02_Limpios" / "apartamentos_venta_limpio.csv"
DIR_TABLAS = RAIZ / "03_Resultados" / "Tablas"

# ---------------------------------------------------------------------------
# Parámetros de la limpieza
# ---------------------------------------------------------------------------
# La variable objetivo es precio_venta; precio_arriendo es un problema aparte.
OPERACIONES_EN_ALCANCE = ["VENTA", "VENTA Y ARRIENDO"]

# Dentro del alcance, una columna con más faltantes que este umbral se descarta
# en lugar de eliminar las filas (si no, no quedaría ninguna observación).
UMBRAL_FALTANTES_COLUMNA = 0.5

# Columnas que se excluyen siempre, con su razón.
COLUMNAS_EXCLUIDAS = {
    "_id": "identificador interno de MongoDB; no está en el README (codigo identifica la vivienda)",
    "timeline": "lista anidada con el historial de precios; no cabe en un CSV plano",
    "compañia": "decisión del equipo: es metadato del anuncio, no una característica de la vivienda; "
                "habi.co no la reporta (rompería la cobertura de esa fuente)",
    "administracion": "decisión del equipo: está en N/A en todos los proyectos nuevos (sobre planos, "
                      "en construcción, para estrenar), que de otro modo se perderían",
    "estado": "decisión del equipo: redundante con antiguedad (NUEVO = SOBRE PLANOS, EN CONSTRUCCION, "
              "PARA ESTRENAR; el resto es USADO) y habi.co no la reporta (796 filas en N/A)",
}

# Variables categóricas de ubicación: el N/A se conserva como categoría propia en vez
# de eliminar la fila (constante, no se aprende de los datos, así que no hay fuga)
COLUMNAS_SIN_DATO = ["sector", "barrio"]
CATEGORIA_SIN_DATO = "SIN_DATO"

# Filtros de validez sobre la base sin N/A
AREA_MINIMA_EXCLUSIVA = 0   # se conserva area > 0
ESTRATO_MINIMO = 1          # se conserva ESTRATO_MINIMO <= estrato <= ESTRATO_MAXIMO
ESTRATO_MAXIMO = 6
# banos == 0 se trata como faltante (apartamentos de 40 a 481 m2 cuya descripción menciona
# baños) y la fila se elimina; se conserva banos >= BANOS_MINIMO
BANOS_MINIMO = 1
# Rango plausible de precio por m2 (COP). Las filas fuera del rango muestran errores de
# escala en precio (~x1000) o en área (decimal desplazado, 1 o 2 m2). El umbral se fija por
# plausibilidad, no según el desempeño de ningún modelo.
PRECIO_M2_MINIMO = 1_000_000
PRECIO_M2_MAXIMO = 40_000_000

# Anuncios repetidos: el mismo anuncio publicado de nuevo (casi siempre por la misma
# inmobiliaria, con otro codigo) es idéntico en todas las columnas salvo estas. Se conserva
# la publicación más reciente. No se eliminan filas que difieran en cualquier otra columna
# (descripción, baños, amenidades...), porque pueden ser unidades distintas de un mismo edificio.
COLUMNAS_IGNORADAS_DUPLICADOS = ["codigo", "datetime", "last_view"]

# Límites aproximados de Bogotá, solo para marcar coordenadas atípicas.
LAT_BOGOTA = (4.45, 4.85)
LON_BOGOTA = (-74.25, -73.99)

# ---------------------------------------------------------------------------
# Tipo esperado de cada columna según README_columnas.md
# ---------------------------------------------------------------------------
TEXTO = [
    "codigo", "tipo_propiedad", "tipo_operacion", "sector", "antiguedad",
    "estado", "descripcion", "localidad", "barrio", "estacion_tm_cercana",
    "parque_cercano", "centro_comercial_cercano", "website", "compañia", "url",
    "direccion",  # no está en el README, pero viene en el JSON
]
ENTERO = [
    "precio_venta", "precio_arriendo", "habitaciones", "banos", "administracion",
    "parqueaderos", "estrato", "piso", "closets",
]
DECIMAL = [
    "area", "latitud", "longitud", "distancia_estacion_tm_m",
    "distancia_parque_m", "distancia_centro_comercial_m",
]
BINARIO = [
    "jacuzzi", "piscina", "salon_comunal", "terraza", "vigilancia", "chimenea",
    "permite_mascotas", "gimnasio", "ascensor", "conjunto_cerrado",
    "coords_modified", "is_cerca_estacion_tm", "is_cerca_parque",
    "is_cerca_centro_comercial",
]
FECHA = ["datetime", "last_view"]

TIPO_ESPERADO = {}
for _columnas, _tipo in [(TEXTO, "texto"), (ENTERO, "entero"), (DECIMAL, "decimal"),
                         (BINARIO, "binario"), (FECHA, "fecha")]:
    for _c in _columnas:
        TIPO_ESPERADO[_c] = _tipo

# Diferencias conocidas entre el README y los datos.
NOTAS_README = {
    "antiguedad": "el README dice 'en años'; los datos son rangos categóricos (p. ej. ENTRE 10 Y 20 ANOS)",
    "coords_modified": "coordenadas ajustadas: tratar con cautela en variables geográficas",
    "last_view": "se actualiza en cada corrida del scraper; no es fecha confiable de vigencia",
    "chimenea": "constante (siempre False) en toda la base: no aporta información",
    "permite_mascotas": "constante (siempre False) en toda la base: no aporta información",
    "salon_comunal": "constante (siempre False) en toda la base: no aporta información",
}


# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------
def titulo(texto):
    print("\n" + "=" * 78)
    print(texto)
    print("=" * 78)


def ruta_relativa(ruta):
    return str(Path(ruta).relative_to(RAIZ))


def guardar_tabla(tabla, nombre):
    DIR_TABLAS.mkdir(parents=True, exist_ok=True)
    ruta = DIR_TABLAS / nombre
    tabla.to_csv(ruta, index=False, encoding="utf-8")
    print(f"  -> {ruta_relativa(ruta)}")


def leer_columnas_readme(ruta):
    """Extrae los nombres de columna de la tabla del README (filas '| nombre | descripción |')."""
    columnas = []
    # Se ignoran los bloques comentados (<!-- ... -->), que incluyen una tabla de imágenes
    texto = re.sub(r"<!--.*?-->", "", ruta.read_text(encoding="utf-8"), flags=re.DOTALL)
    for linea in texto.splitlines():
        m = re.match(r"^\|\s*([A-Za-zñÑ_0-9]+)\s*\|", linea)
        if m and m.group(1).lower() not in ("columna",):
            columnas.append(m.group(1))
    return columnas


def normalizar_valor(v):
    """Convierte un valor MongoDB Extended JSON a un valor de Python."""
    if isinstance(v, dict):
        if len(v) == 1:
            clave, valor = next(iter(v.items()))
            if clave == "$numberDouble":
                return float(valor)  # 'NaN' -> nan
            if clave in ("$numberInt", "$numberLong"):
                return int(valor)
            if clave == "$oid":
                return valor
            if clave == "$date" and isinstance(valor, str):
                return valor  # cadena ISO; se convierte a fecha más adelante
        raise ValueError(f"Estructura Extended JSON no reconocida: {v}")
    return v


def tipo_crudo(v):
    """Nombre del tipo de un valor tal como viene en el JSON (antes de normalizar)."""
    if isinstance(v, dict):
        return next(iter(v.keys())) if len(v) == 1 else "dict"
    return type(v).__name__


def a_numerico(serie, columna):
    """Convierte a numérico (acepta números en texto) y cuenta lo que no se pudo convertir."""
    convertida = pd.to_numeric(serie, errors="coerce")
    fallidas = int((serie.notna() & convertida.isna()).sum())
    if fallidas:
        print(f"  ! {columna}: {fallidas} valores no numéricos pasan a faltante")
    return convertida.astype("float64")


# ---------------------------------------------------------------------------
# 1. Lectura y normalización
# ---------------------------------------------------------------------------
titulo("1. LECTURA Y NORMALIZACIÓN DEL JSON")
with open(RUTA_JSON, encoding="utf-8") as f:
    registros = json.load(f)
print(f"Registros en el JSON: {len(registros):,}")

tipos_crudos = {}
filas = []
for r in registros:
    for k, v in r.items():
        tipos_crudos.setdefault(k, Counter())[tipo_crudo(v)] += 1
    # timeline se excluye: es una lista anidada y no se usa en esta base
    filas.append({k: normalizar_valor(v) for k, v in r.items() if k != "timeline"})
del registros

df = pd.DataFrame(filas)
del filas
print(f"Columnas en el JSON: {len(tipos_crudos)}")

# Cadenas vacías en columnas de texto equivalen a faltante
for c in df.columns:
    if TIPO_ESPERADO.get(c) == "texto":
        vacias = df[c].map(lambda x: isinstance(x, str) and x.strip() == "")
        if vacias.any():
            print(f"  {c}: {int(vacias.sum())} cadenas vacías pasan a faltante")
            df.loc[vacias, c] = np.nan

# Conversión a tipos "con faltantes" (float64 / datetime64 / texto) para poder contar N/A
for c in df.columns:
    tipo = TIPO_ESPERADO.get(c)
    if tipo in ("entero", "decimal", "binario"):
        df[c] = a_numerico(df[c], c)
    elif tipo == "fecha":
        antes = df[c].notna().sum()
        df[c] = pd.to_datetime(df[c], errors="coerce")
        if df[c].notna().sum() != antes:
            print(f"  ! {c}: {int(antes - df[c].notna().sum())} fechas no interpretables pasan a faltante")

# ---------------------------------------------------------------------------
# 2. Reconocimiento: columnas frente al README
# ---------------------------------------------------------------------------
titulo("2. RECONOCIMIENTO: COLUMNAS Y TIPOS FRENTE AL README")
cols_readme = leer_columnas_readme(RUTA_README)
cols_datos = list(tipos_crudos.keys())
solo_readme = [c for c in cols_readme if c not in cols_datos]
solo_datos = [c for c in cols_datos if c not in cols_readme]
print(f"Columnas en el README: {len(cols_readme)} | en el JSON: {len(cols_datos)}")
print(f"En el README y no en el JSON: {solo_readme if solo_readme else 'ninguna'}")
print(f"En el JSON y no en el README: {solo_datos if solo_datos else 'ninguna'}")
sin_tipo = [c for c in cols_datos if c not in TIPO_ESPERADO and c not in COLUMNAS_EXCLUIDAS]
if sin_tipo:
    raise SystemExit(f"Columnas sin tipo esperado definido en el script: {sin_tipo}")

n_total = len(df)
resumen = []
for c in cols_readme + [c for c in solo_datos]:
    fila = {
        "columna": c,
        "en_readme": c in cols_readme,
        "en_json": c in cols_datos,
        "tipo_esperado": TIPO_ESPERADO.get(c, "excluida" if c in COLUMNAS_EXCLUIDAS else ""),
        "tipos_crudos_json": "; ".join(f"{t}={n}" for t, n in tipos_crudos.get(c, {}).items()),
    }
    if c in df.columns:
        s = df[c]
        fila.update({
            "tipo_pandas_leido": str(s.dtype),
            "n_faltantes": int(s.isna().sum()),
            "pct_faltantes": round(100 * s.isna().mean(), 2),
            "n_unicos": int(s.nunique(dropna=True)),
        })
        if pd.api.types.is_numeric_dtype(s) or pd.api.types.is_datetime64_any_dtype(s):
            fila["minimo"], fila["maximo"] = s.min(), s.max()
    elif c in cols_datos:
        fila["observacion"] = COLUMNAS_EXCLUIDAS.get(c, "")
    else:
        fila["observacion"] = "listada en el README pero no existe en el JSON"
    if c in NOTAS_README:
        fila["observacion"] = NOTAS_README[c]
    resumen.append(fila)
resumen = pd.DataFrame(resumen)

print("\nFaltantes por columna (sobre todos los registros):")
vista = resumen.dropna(subset=["n_faltantes"]).sort_values("n_faltantes", ascending=False)
print(vista[["columna", "n_faltantes", "pct_faltantes"]].query("n_faltantes > 0").to_string(index=False))
print("\nDistribución de tipo_operacion:")
print(df["tipo_operacion"].value_counts(dropna=False).to_string())
print("\nDistribución de tipo_propiedad:")
print(df["tipo_propiedad"].value_counts(dropna=False).to_string())

# ---------------------------------------------------------------------------
# 3. Alcance, columnas casi vacías y eliminación de filas con N/A
# ---------------------------------------------------------------------------
titulo("3. ALCANCE Y ELIMINACIÓN DE N/A")
embudo = [{"paso": "Registros leídos del JSON", "n_antes": n_total, "n_despues": n_total,
           "n_perdidas": 0, "n_faltantes_columna": ""}]


def registrar(paso, antes, despues, faltantes_columna=""):
    embudo.append({"paso": paso, "n_antes": antes, "n_despues": despues,
                   "n_perdidas": antes - despues, "n_faltantes_columna": faltantes_columna})
    print(f"  {paso}: {antes:,} -> {despues:,} (pierde {antes - despues:,})")


# 3a. Alcance: operaciones con precio de venta
n0 = len(df)
alcance = df[df["tipo_operacion"].isin(OPERACIONES_EN_ALCANCE)].copy()
registrar(f"Alcance: tipo_operacion en {OPERACIONES_EN_ALCANCE}", n0, len(alcance))
registro_alcance = alcance[["localidad", "estrato"]].copy()  # para la tabla de pérdida por grupo

# 3b. Columnas excluidas y columnas casi vacías (dentro del alcance)
descartadas = {}
for c, razon in COLUMNAS_EXCLUIDAS.items():
    if c in alcance.columns:
        descartadas[c] = razon
pct_faltante_alcance = alcance.isna().mean()
for c in alcance.columns:
    if c not in descartadas and pct_faltante_alcance[c] > UMBRAL_FALTANTES_COLUMNA:
        descartadas[c] = f"{100 * pct_faltante_alcance[c]:.1f}% de faltantes en el alcance (> {100 * UMBRAL_FALTANTES_COLUMNA:.0f}%)"
alcance = alcance.drop(columns=list(descartadas))
print(f"\nColumnas descartadas ({len(descartadas)}):")
for c, razon in descartadas.items():
    print(f"  - {c}: {razon}")
print(f"Columnas que se conservan: {alcance.shape[1]}")
resumen["descartada_en_limpieza"] = resumen["columna"].map(descartadas).fillna("")

# 3c. N/A de ubicación categórica -> categoría SIN_DATO (no se pierden filas)
print("\nN/A conservados como categoría:")
for c in COLUMNAS_SIN_DATO:
    n_falt = int(alcance[c].isna().sum())
    alcance[c] = alcance[c].fillna(CATEGORIA_SIN_DATO)
    registrar(f"N/A en {c} -> '{CATEGORIA_SIN_DATO}'", len(alcance), len(alcance), n_falt)

# 3d. Eliminación de filas con N/A, columna por columna
print("\nEliminación de filas con N/A (en el orden de las columnas):")
faltantes_en_alcance = alcance.isna().sum()
limpio = alcance
for c in alcance.columns:
    n_falt = int(faltantes_en_alcance[c])
    if n_falt == 0:
        continue
    antes = len(limpio)
    limpio = limpio[limpio[c].notna()]
    registrar(f"N/A en {c}", antes, len(limpio), n_falt)
assert limpio.isna().sum().sum() == 0, "Quedaron N/A en la base limpia"

# 3e. Corrección de valores: parqueaderos negativos se toman como 0 (no se pierden filas)
print("\nCorrecciones de valores:")
n_neg = int((limpio["parqueaderos"] < 0).sum())
limpio.loc[limpio["parqueaderos"] < 0, "parqueaderos"] = 0
registrar("Corrección: parqueaderos < 0 -> 0", len(limpio), len(limpio), n_neg)

# 3f. Filtros de validez: area > 0 y estrato dentro de la estratificación (1 a 6)
print("\nFiltros de validez:")
antes = len(limpio)
limpio = limpio[limpio["area"] > AREA_MINIMA_EXCLUSIVA]
registrar(f"Filtro: area > {AREA_MINIMA_EXCLUSIVA}", antes, len(limpio))
antes = len(limpio)
limpio = limpio[limpio["estrato"].between(ESTRATO_MINIMO, ESTRATO_MAXIMO)]
registrar(f"Filtro: {ESTRATO_MINIMO} <= estrato <= {ESTRATO_MAXIMO}", antes, len(limpio))
antes = len(limpio)
limpio = limpio[limpio["banos"] >= BANOS_MINIMO]
registrar(f"Filtro: banos >= {BANOS_MINIMO} (banos == 0 como faltante)", antes, len(limpio))
antes = len(limpio)
precio_m2 = limpio["precio_venta"] / limpio["area"]
limpio = limpio[precio_m2.between(PRECIO_M2_MINIMO, PRECIO_M2_MAXIMO)]
registrar(f"Filtro: {PRECIO_M2_MINIMO:,} <= precio/m2 <= {PRECIO_M2_MAXIMO:,}", antes, len(limpio))

# 3g. Anuncios repetidos: filas idénticas en todo salvo codigo y fechas -> se conserva la más reciente
print("\nAnuncios repetidos:")
clave_duplicados = [c for c in limpio.columns if c not in COLUMNAS_IGNORADAS_DUPLICADOS]
antes = len(limpio)
limpio = limpio.sort_values(["datetime", "codigo"], ascending=[False, True])
repetida = limpio.duplicated(clave_duplicados, keep="first")
# Para cada fila eliminada se anota el codigo que se conservó en su lugar
conservado = limpio.groupby(clave_duplicados, dropna=False)["codigo"].transform("first")
duplicados = pd.DataFrame({
    "codigo_eliminado": limpio.loc[repetida, "codigo"],
    "codigo_conservado": conservado[repetida],
    "datetime_eliminado": limpio.loc[repetida, "datetime"],
}).sort_values(["codigo_conservado", "codigo_eliminado"])
limpio = limpio[~repetida].sort_index()
print(f"  Clave: todas las columnas salvo {COLUMNAS_IGNORADAS_DUPLICADOS}")
print(f"  Grupos con repetidos: {duplicados['codigo_conservado'].nunique():,}")
registrar("Anuncios repetidos (idénticos salvo codigo y fechas; se conserva el más reciente)",
          antes, len(limpio))
registrar("Total tras alcance, N/A, filtros y repetidos", n_total, len(limpio))

# ---------------------------------------------------------------------------
# 4. Tipos finales y verificación
# ---------------------------------------------------------------------------
titulo("4. TIPOS FINALES Y VERIFICACIÓN")
limpio = limpio.copy()
for c in limpio.columns:
    tipo = TIPO_ESPERADO[c]
    s = limpio[c]
    if tipo == "entero":
        if not (s % 1 == 0).all():
            raise SystemExit(f"{c}: tiene valores no enteros; no se puede castear a entero")
        limpio[c] = s.astype("int64")
    elif tipo == "binario":
        if not s.isin([0, 1]).all():
            raise SystemExit(f"{c}: tiene valores distintos de 0/1; no se puede castear a booleano")
        limpio[c] = s.astype(bool)
    elif tipo == "texto":
        if not s.map(lambda x: isinstance(x, str)).all():
            raise SystemExit(f"{c}: tiene valores que no son texto")
    # decimal y fecha ya están en float64 y datetime64

verificacion = {
    "entero": lambda s: pd.api.types.is_integer_dtype(s),
    "decimal": lambda s: pd.api.types.is_float_dtype(s),
    "binario": lambda s: pd.api.types.is_bool_dtype(s),
    "fecha": lambda s: pd.api.types.is_datetime64_any_dtype(s),
    "texto": lambda s: pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s),
}
filas_tipos = []
for c in limpio.columns:
    ok = verificacion[TIPO_ESPERADO[c]](limpio[c])
    filas_tipos.append((c, TIPO_ESPERADO[c], str(limpio[c].dtype), ok))
tipos_df = pd.DataFrame(filas_tipos, columns=["columna", "tipo_esperado", "tipo_final", "coincide"])
print(tipos_df.to_string(index=False))
assert tipos_df["coincide"].all(), "Hay columnas cuyo tipo final no coincide con el README"
resumen = resumen.merge(tipos_df[["columna", "tipo_final"]], on="columna", how="left")
print(f"\nTodos los tipos coinciden con el README ({len(tipos_df)} columnas).")

assert limpio["codigo"].is_unique, "Hay códigos de vivienda repetidos"
print(f"codigo es único: {len(limpio):,} viviendas.")

# ---------------------------------------------------------------------------
# 5. Reconocimiento de la base limpia: estadísticas y anomalías (solo se reportan)
# ---------------------------------------------------------------------------
titulo("5. RECONOCIMIENTO DE LA BASE LIMPIA")
numericas = limpio.select_dtypes(include=["int64", "float64"])
estadisticas = numericas.describe(percentiles=[0.01, 0.25, 0.5, 0.75, 0.99]).T
estadisticas.insert(0, "columna", estadisticas.index)
print(estadisticas.drop(columns="columna").round(2).to_string())

reglas = {
    "area <= 0": limpio["area"] <= 0,
    "precio_venta <= 0": limpio["precio_venta"] <= 0,
    "banos == 0": limpio["banos"] == 0,
    "precio/m2 fuera de rango": ~(limpio["precio_venta"] / limpio["area"]).between(PRECIO_M2_MINIMO, PRECIO_M2_MAXIMO),
    "parqueaderos < 0": limpio["parqueaderos"] < 0,
    "estrato fuera de 1-6": ~limpio["estrato"].between(1, 6),
    "latitud fuera de Bogotá (aprox.)": ~limpio["latitud"].between(*LAT_BOGOTA),
    "longitud fuera de Bogotá (aprox.)": ~limpio["longitud"].between(*LON_BOGOTA),
    "coords_modified == True": limpio["coords_modified"],
}
anomalias = pd.DataFrame([
    {"regla": r, "n_filas": int(m.sum()), "pct_filas": round(100 * m.mean(), 3)}
    for r, m in reglas.items()
])
constantes = [c for c in limpio.columns if limpio[c].nunique() == 1]
print("\nAnomalías (solo se reportan, no se eliminan):")
print(anomalias.to_string(index=False))
print(f"\nColumnas constantes en la base limpia: {constantes if constantes else 'ninguna'}")

# Pérdida de observaciones por localidad y estrato (insumo para la sección de IA responsable)
perdida = []
for grupo in ["localidad", "estrato"]:
    n_alc = registro_alcance.groupby(grupo, dropna=False).size().rename("n_alcance")
    n_fin = limpio.groupby(grupo).size().rename("n_final")
    t = pd.concat([n_alc, n_fin], axis=1).fillna(0).astype(int)
    t["n_perdidas"] = t["n_alcance"] - t["n_final"]
    t["pct_perdidas"] = (100 * t["n_perdidas"] / t["n_alcance"]).round(2)
    t.insert(0, "valor", t.index.astype(str))
    t.insert(0, "grupo", grupo)
    perdida.append(t.reset_index(drop=True))
perdida = pd.concat(perdida, ignore_index=True)
print("\nPérdida de observaciones por grupo (alcance -> final):")
print(perdida.to_string(index=False))

# ---------------------------------------------------------------------------
# 6. Guardado
# ---------------------------------------------------------------------------
titulo("6. GUARDADO")
RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
limpio.to_csv(RUTA_SALIDA, index=False, encoding="utf-8")
tam_mb = RUTA_SALIDA.stat().st_size / 1e6
print(f"Base limpia: {ruta_relativa(RUTA_SALIDA)} ({len(limpio):,} filas x {limpio.shape[1]} columnas, {tam_mb:.1f} MB)")
if tam_mb > 50:
    print("  ! Supera 50 MB: GitHub advierte; consultar antes de versionarla.")

# Relectura para comprobar que el CSV conserva forma y tipos
fechas_presentes = [c for c in FECHA if c in limpio.columns]
releida = pd.read_csv(RUTA_SALIDA, parse_dates=fechas_presentes)
assert releida.shape == limpio.shape, "La relectura del CSV cambió la forma de la base"
assert all(verificacion[TIPO_ESPERADO[c]](releida[c]) for c in releida.columns), \
    "La relectura del CSV cambió los tipos"
assert releida.isna().sum().sum() == 0, "La relectura del CSV introdujo N/A"
print("Relectura del CSV: forma, tipos y ausencia de N/A conservados.")

print("\nTablas de reconocimiento:")
guardar_tabla(resumen, "01_resumen_columnas.csv")
guardar_tabla(pd.DataFrame(embudo), "01_perdida_observaciones.csv")
guardar_tabla(perdida, "01_perdida_por_localidad_estrato.csv")
guardar_tabla(estadisticas.reset_index(drop=True), "01_estadisticas_numericas.csv")
guardar_tabla(anomalias, "01_anomalias.csv")
guardar_tabla(duplicados, "01_duplicados_eliminados.csv")
