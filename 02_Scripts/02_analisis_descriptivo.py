"""
02_analisis_descriptivo.py

Análisis descriptivo de la base limpia de apartamentos en venta
(01_Datos/02_Limpios/apartamentos_venta_limpio.csv). No filtra ni modifica
la base: solo describe. El modelado (línea base y Random Forest) es tarea
de un script posterior.

Variable derivada: 'precio_m2' = precio_venta / area. No se guarda en el CSV
limpio (ver CLAUDE.md, Decisiones tomadas), pero es la métrica comparable
entre viviendas que se usó para filtrar la base y la que se usa aquí.

Salidas (todas con prefijo 02_, sin números escritos a mano):
  - 03_Resultados/Tablas/02_distribucion_precio_area.csv
  - 03_Resultados/Tablas/02_precio_m2_por_estrato.csv
  - 03_Resultados/Tablas/02_precio_m2_por_localidad.csv
  - 03_Resultados/Tablas/02_composicion_localidad_estrato.csv
  - 03_Resultados/Tablas/02_composicion_website.csv
  - 03_Resultados/Tablas/02_antiguedad_estrato_precio_m2.csv
  - 03_Resultados/Tablas/02_asociacion_variables_sensibles.csv
  - 03_Resultados/Figuras/02_histograma_precio_venta.png
  - 03_Resultados/Figuras/02_histograma_area.png
  - 03_Resultados/Figuras/02_histograma_precio_m2.png
  - 03_Resultados/Figuras/02_boxplot_precio_m2_por_estrato.png
  - 03_Resultados/Figuras/02_boxplot_precio_m2_por_localidad.png
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # backend sin interfaz grafica, para correr desde script
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

# Rutas ancladas a la raíz del repositorio (este script vive en 02_Scripts/)
RAIZ = Path(__file__).resolve().parent.parent
RUTA_DATOS = RAIZ / "01_Datos" / "02_Limpios" / "apartamentos_venta_limpio.csv"
DIR_TABLAS = RAIZ / "03_Resultados" / "Tablas"
DIR_FIGURAS = RAIZ / "03_Resultados" / "Figuras"

VARIABLES_SENSIBLES = ["estrato", "localidad", "barrio"]


def cargar_datos() -> pd.DataFrame:
    """Carga la base limpia y agrega la variable derivada precio_m2."""
    df = pd.read_csv(RUTA_DATOS, parse_dates=["datetime", "last_view"])
    df["precio_m2"] = df["precio_venta"] / df["area"]
    return df


def guardar_tabla(tabla: pd.DataFrame, nombre_archivo: str) -> None:
    DIR_TABLAS.mkdir(parents=True, exist_ok=True)
    ruta = DIR_TABLAS / nombre_archivo
    tabla.to_csv(ruta, index=False, encoding="utf-8")
    print(f"Tabla guardada: {ruta}")


def guardar_figura(fig: plt.Figure, nombre_archivo: str) -> None:
    DIR_FIGURAS.mkdir(parents=True, exist_ok=True)
    ruta = DIR_FIGURAS / nombre_archivo
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Figura guardada: {ruta}")


def distribucion_precio_area(df: pd.DataFrame) -> None:
    """Estadísticas descriptivas de precio_venta, area y precio_m2, con
    histogramas de cada una."""
    columnas = ["precio_venta", "area", "precio_m2"]
    resumen = df[columnas].describe().T.rename(
        columns={
            "count": "n",
            "mean": "media",
            "std": "desv_std",
            "25%": "p25",
            "50%": "mediana",
            "75%": "p75",
        }
    )
    resumen = resumen[["n", "media", "desv_std", "min", "p25", "mediana", "p75", "max"]]
    guardar_tabla(resumen.reset_index(names="variable"), "02_distribucion_precio_area.csv")

    titulos = {
        "precio_venta": ("Precio de venta (COP)", "02_histograma_precio_venta.png"),
        "area": ("Área (m²)", "02_histograma_area.png"),
        "precio_m2": ("Precio por m² (COP/m²)", "02_histograma_precio_m2.png"),
    }
    for columna, (titulo, nombre_fig) in titulos.items():
        fig, ax = plt.subplots(figsize=(7, 4.5))
        ax.hist(df[columna], bins=60, color="#4C72B0", edgecolor="white", linewidth=0.3)
        ax.set_title(f"Distribución de {titulo}")
        ax.set_xlabel(titulo)
        ax.set_ylabel("Número de viviendas")
        guardar_figura(fig, nombre_fig)


def precio_m2_por_grupo(df: pd.DataFrame, columna_grupo: str, nombre_tabla: str) -> pd.DataFrame:
    """Conteo, media y mediana de precio_m2 desagregado por una columna
    (estrato o localidad), ordenado por mediana descendente."""
    tabla = (
        df.groupby(columna_grupo)["precio_m2"]
        .agg(n="count", media="mean", mediana="median", desv_std="std")
        .sort_values("mediana", ascending=False)
        .reset_index()
    )
    guardar_tabla(tabla, nombre_tabla)
    return tabla


def composicion_localidad_estrato(df: pd.DataFrame) -> None:
    """Tabla de conteos localidad x estrato (composición de la muestra)."""
    tabla = pd.crosstab(df["localidad"], df["estrato"])
    tabla.columns = [f"estrato_{c}" for c in tabla.columns]
    guardar_tabla(tabla.reset_index(names="localidad"), "02_composicion_localidad_estrato.csv")


def composicion_website(df: pd.DataFrame) -> None:
    """Conteo y porcentaje de viviendas por sitio web de origen."""
    conteos = df["website"].value_counts()
    tabla = pd.DataFrame(
        {
            "website": conteos.index,
            "n": conteos.values,
            "pct": (conteos.values / len(df) * 100).round(2),
        }
    )
    guardar_tabla(tabla, "02_composicion_website.csv")


def antiguedad_estrato_precio_m2(df: pd.DataFrame) -> None:
    """Precio por m² (n, media, mediana) cruzando antigüedad y estrato."""
    tabla = (
        df.groupby(["antiguedad", "estrato"])["precio_m2"]
        .agg(n="count", media="mean", mediana="median")
        .reset_index()
        .sort_values(["antiguedad", "estrato"])
    )
    guardar_tabla(tabla, "02_antiguedad_estrato_precio_m2.csv")


def _cramers_v(x: pd.Series, y: pd.Series) -> float:
    """Coeficiente de asociación de Cramér's V entre dos variables
    categóricas (0 = sin asociación, 1 = asociación perfecta). Se usa en
    vez de una correlación porque estrato, localidad y barrio son
    categóricas (estrato es ordinal, pero se trata como tal para comparar
    con localidad y barrio en la misma escala)."""
    tabla_contingencia = pd.crosstab(x, y)
    chi2 = chi2_contingency(tabla_contingencia)[0]
    n = tabla_contingencia.to_numpy().sum()
    filas, columnas = tabla_contingencia.shape
    phi2 = chi2 / n
    return float(np.sqrt(phi2 / min(filas - 1, columnas - 1)))


def asociacion_variables_sensibles(df: pd.DataFrame) -> pd.DataFrame:
    """Matriz de Cramér's V entre estrato, localidad y barrio: cuantifica
    qué tan redundantes son entre sí estas variables sensibles, como
    insumo directo para la sección de IA responsable (CLAUDE.md)."""
    matriz = pd.DataFrame(
        index=VARIABLES_SENSIBLES, columns=VARIABLES_SENSIBLES, dtype=float
    )
    for var_a in VARIABLES_SENSIBLES:
        for var_b in VARIABLES_SENSIBLES:
            matriz.loc[var_a, var_b] = (
                1.0 if var_a == var_b else _cramers_v(df[var_a], df[var_b])
            )
    guardar_tabla(matriz.round(4).reset_index(names="variable"), "02_asociacion_variables_sensibles.csv")
    return matriz


def boxplot_precio_m2_por_grupo(
    df: pd.DataFrame, columna_grupo: str, titulo: str, nombre_fig: str
) -> None:
    """Boxplot horizontal de precio_m2 por categoría, ordenado por mediana."""
    orden = (
        df.groupby(columna_grupo)["precio_m2"].median().sort_values(ascending=False).index
    )
    datos = [df.loc[df[columna_grupo] == categoria, "precio_m2"] for categoria in orden]

    fig, ax = plt.subplots(figsize=(8, max(3, 0.35 * len(orden))))
    ax.boxplot(datos, tick_labels=list(orden), vert=False, showfliers=False)
    ax.set_title(f"Precio por m² según {titulo}")
    ax.set_xlabel("Precio por m² (COP/m²)")
    guardar_figura(fig, nombre_fig)


def main():
    print(f"Leyendo base limpia desde: {RUTA_DATOS}")
    df = cargar_datos()
    print(f"Registros: {len(df)}, columnas: {df.shape[1]}")

    distribucion_precio_area(df)
    precio_m2_por_grupo(df, "estrato", "02_precio_m2_por_estrato.csv")
    precio_m2_por_grupo(df, "localidad", "02_precio_m2_por_localidad.csv")
    composicion_localidad_estrato(df)
    composicion_website(df)
    antiguedad_estrato_precio_m2(df)
    matriz_asociacion = asociacion_variables_sensibles(df)
    print("\nAsociación (Cramér's V) entre variables sensibles:")
    print(matriz_asociacion.round(3).to_string())

    boxplot_precio_m2_por_grupo(df, "estrato", "estrato", "02_boxplot_precio_m2_por_estrato.png")
    boxplot_precio_m2_por_grupo(df, "localidad", "localidad", "02_boxplot_precio_m2_por_localidad.png")


if __name__ == "__main__":
    main()
