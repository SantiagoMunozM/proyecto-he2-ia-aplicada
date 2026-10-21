"""
07_perfil_descripcion.py

Perfil de la columna 'descripcion' de la base limpia, para sustentar la propuesta
de aprendizaje profundo (procesamiento de texto del anuncio). No estima ningún
modelo ni modifica la base: solo describe qué contiene el texto.

Insumo:
    01_Datos/02_Limpios/apartamentos_venta_limpio.csv

Salidas:
    03_Resultados/Tablas/07_perfil_descripcion.csv   largo del texto y % de anuncios que mencionan cada tema
    03_Resultados/Tablas/07_ejemplos_descripcion.csv  tres descripciones de ejemplo (muestra con semilla fija)

Notas:
    - El texto de la base viene en minúsculas y sin tildes, por eso los patrones no llevan tildes.
    - Las menciones se buscan con palabras clave: son una aproximación, no una clasificación.
    - 'estructurada' indica si la base ya trae una columna con esa característica.

Se corre desde la raíz del repo: python 02_Scripts/07_perfil_descripcion.py
"""

from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Rutas (ancladas a la raíz del proyecto, que es la carpeta padre de 02_Scripts)
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
BASE_LIMPIA = RAIZ / "01_Datos" / "02_Limpios" / "apartamentos_venta_limpio.csv"
TABLAS = RAIZ / "03_Resultados" / "Tablas"
TABLAS.mkdir(parents=True, exist_ok=True)

SEMILLA = 2026

# Temas buscados en el texto: (nombre, patrón, ¿la base ya trae una columna con esto?)
TEMAS = [
    ("vista", "vista", False),
    ("remodelado", "remodelad", False),
    ("iluminación", "iluminacion", False),
    ("balcón", "balcon", False),
    ("cercanía (colegio, TransMilenio o centro comercial)", "colegio|transmilenio|centro comercial", False),
    ("terraza", "terraza", True),
    ("ascensor", "ascensor", True),
]

base = pd.read_csv(BASE_LIMPIA)
texto = base["descripcion"].fillna("").astype(str)
print(f"Viviendas en la base limpia: {len(base):,}")

# ---------------------------------------------------------------------------
# 1. Largo del texto y cobertura
# ---------------------------------------------------------------------------
n_palabras = texto.str.split().str.len()
filas = [
    ("viviendas", len(base), "n"),
    ("con descripción no vacía", int((texto.str.strip() != "").sum()), "n"),
    ("palabras, mediana", float(n_palabras.median()), "palabras"),
    ("palabras, percentil 10", float(n_palabras.quantile(0.10)), "palabras"),
    ("palabras, percentil 90", float(n_palabras.quantile(0.90)), "palabras"),
]

# ---------------------------------------------------------------------------
# 2. Porcentaje de anuncios que mencionan cada tema
# ---------------------------------------------------------------------------
for nombre, patron, estructurada in TEMAS:
    pct = texto.str.contains(patron, case=False, regex=True).mean() * 100
    filas.append((f"menciona {nombre}" + (" (ya hay columna)" if estructurada else " (sin columna)"), round(pct, 1), "%"))

perfil = pd.DataFrame(filas, columns=["medida", "valor", "unidad"])
perfil.to_csv(TABLAS / "07_perfil_descripcion.csv", index=False)
print(perfil.to_string(index=False))

# ---------------------------------------------------------------------------
# 3. Tres ejemplos con semilla fija
# ---------------------------------------------------------------------------
ejemplos = base.loc[texto.sample(3, random_state=SEMILLA).index, ["codigo", "estrato", "localidad", "descripcion"]]
ejemplos.to_csv(TABLAS / "07_ejemplos_descripcion.csv", index=False)
print(f"Ejemplos guardados: {', '.join(ejemplos['codigo'].astype(str))}")
