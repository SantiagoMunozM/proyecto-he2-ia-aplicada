"""
03_particion_muestra.py

Partición de la base limpia en entrenamiento y prueba. El conjunto de prueba se
fija aquí una sola vez y lo usan todos los modelos, incluidos los posteriores
(p. ej. un modelo de texto sobre la descripción).

Insumos:
    01_Datos/02_Limpios/apartamentos_venta_limpio.csv

Salidas:
    01_Datos/02_Limpios/particion_train_test.csv
    03_Resultados/Tablas/03_composicion_particion.csv

Pasos:
    1. Lee la base limpia.
    2. Partición aleatoria 80/20 estratificada por estrato (random_state=2026).
       Es aleatoria y no temporal porque datetime solo cubre 3 jul - 3 sep de
       2024; se estratifica porque el estrato 1 tiene muy pocas viviendas.
    3. Verifica que la partición sea disjunta, completa y con todos los estratos
       en ambos conjuntos.
    4. Guarda los ids de cada conjunto y la composición por estrato y localidad.

Se corre desde la raíz del repo: python 02_Scripts/03_particion_muestra.py
"""

from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

# ---------------------------------------------------------------------------
# Rutas (ancladas a la raíz del proyecto, que es la carpeta padre de 02_Scripts)
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
RUTA_LIMPIA = RAIZ / "01_Datos" / "02_Limpios" / "apartamentos_venta_limpio.csv"
RUTA_PARTICION = RAIZ / "01_Datos" / "02_Limpios" / "particion_train_test.csv"
DIR_TABLAS = RAIZ / "03_Resultados" / "Tablas"

# ---------------------------------------------------------------------------
# Parámetros de la partición
# ---------------------------------------------------------------------------
SEMILLA = 2026
PROPORCION_PRUEBA = 0.2
VARIABLE_ESTRATIFICACION = "estrato"
ENTRENAMIENTO, PRUEBA = "entrenamiento", "prueba"
# Grupos con menos viviendas que esto en prueba se marcan: sus métricas son poco estables
N_MINIMO_GRUPO_PRUEBA = 30


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


# ---------------------------------------------------------------------------
# 1. Lectura
# ---------------------------------------------------------------------------
titulo("1. LECTURA DE LA BASE LIMPIA")
df = pd.read_csv(RUTA_LIMPIA, parse_dates=["datetime", "last_view"])
print(f"Base limpia: {len(df):,} viviendas x {df.shape[1]} columnas")
assert df["codigo"].is_unique, "Hay códigos de vivienda repetidos"

# ---------------------------------------------------------------------------
# 2. Partición
# ---------------------------------------------------------------------------
titulo("2. PARTICIÓN ENTRENAMIENTO / PRUEBA")
idx_train, idx_prueba = train_test_split(
    df.index,
    test_size=PROPORCION_PRUEBA,
    random_state=SEMILLA,
    stratify=df[VARIABLE_ESTRATIFICACION],
)
df["conjunto"] = ENTRENAMIENTO
df.loc[idx_prueba, "conjunto"] = PRUEBA
print(df["conjunto"].value_counts().to_string())

# ---------------------------------------------------------------------------
# 3. Verificaciones
# ---------------------------------------------------------------------------
titulo("3. VERIFICACIONES")
cod_train = set(df.loc[df["conjunto"] == ENTRENAMIENTO, "codigo"])
cod_prueba = set(df.loc[df["conjunto"] == PRUEBA, "codigo"])
assert cod_train.isdisjoint(cod_prueba), "Entrenamiento y prueba comparten viviendas"
assert len(cod_train) + len(cod_prueba) == len(df), "La partición no cubre toda la base"
estratos_por_conjunto = df.groupby("conjunto")[VARIABLE_ESTRATIFICACION].nunique()
assert (estratos_por_conjunto == df[VARIABLE_ESTRATIFICACION].nunique()).all(), \
    "Algún estrato no aparece en uno de los dos conjuntos"
print(f"Disjunta y completa: {len(cod_train):,} + {len(cod_prueba):,} = {len(df):,}")
print(f"Todos los estratos ({df[VARIABLE_ESTRATIFICACION].nunique()}) están en ambos conjuntos.")

# ---------------------------------------------------------------------------
# 4. Composición de cada conjunto (para mostrar que la prueba es comparable)
# ---------------------------------------------------------------------------
titulo("4. COMPOSICIÓN DE LA PARTICIÓN")


def composicion(grupo):
    """n, % y precio (media y mediana) de cada valor del grupo en cada conjunto."""
    if grupo is None:
        claves = pd.Series("total", index=df.index, name="valor")
    else:
        claves = df[grupo].astype(str).rename("valor")
    t = (df.groupby([claves, "conjunto"])["precio_venta"]
           .agg(n="size", precio_media="mean", precio_mediana="median")
           .unstack("conjunto"))
    t.columns = [f"{m}_{c}" for m, c in t.columns]
    t = t.fillna(0)
    for c in (ENTRENAMIENTO, PRUEBA):
        t[f"n_{c}"] = t[f"n_{c}"].astype(int)
        t[f"pct_{c}"] = (100 * t[f"n_{c}"] / t[f"n_{c}"].sum()).round(2)
    t["n_prueba_menor_minimo"] = t[f"n_{PRUEBA}"] < N_MINIMO_GRUPO_PRUEBA
    t = t.reset_index()
    t.insert(0, "grupo", grupo if grupo is not None else "total")
    columnas = ["grupo", "valor"]
    for m in ("n", "pct", "precio_media", "precio_mediana"):
        columnas += [f"{m}_{ENTRENAMIENTO}", f"{m}_{PRUEBA}"]
    return t[columnas + ["n_prueba_menor_minimo"]]


comp = pd.concat([composicion(None), composicion("estrato"), composicion("localidad")],
                 ignore_index=True)
for c in [c for c in comp.columns if c.startswith("precio_")]:
    comp[c] = comp[c].round(0)
with pd.option_context("display.width", 200, "display.max_columns", None):
    print(comp.to_string(index=False))
pequenos = comp[comp["n_prueba_menor_minimo"]]
print(f"\nGrupos con menos de {N_MINIMO_GRUPO_PRUEBA} viviendas en prueba: "
      f"{', '.join(pequenos['grupo'] + '=' + pequenos['valor']) if len(pequenos) else 'ninguno'}")

# ---------------------------------------------------------------------------
# 5. Guardado
# ---------------------------------------------------------------------------
titulo("5. GUARDADO")
df[["codigo", "conjunto"]].to_csv(RUTA_PARTICION, index=False, encoding="utf-8")
print(f"Partición: {ruta_relativa(RUTA_PARTICION)} ({len(df):,} filas)")
guardar_tabla(comp, "03_composicion_particion.csv")
