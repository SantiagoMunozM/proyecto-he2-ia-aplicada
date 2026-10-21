"""
08_objetivos_practicos.py

Traduce el error de prueba del modelo principal a cifras que un comprador o vendedor
puede usar para decidir: cuánto se equivoca el modelo en una vivienda típica de cada
estrato, en pesos y en porcentaje, y un ejemplo concreto de una vivienda de prueba.
No reestima ningún modelo: usa las predicciones de prueba que guardó
04_estimacion_modelos.py. Todas las cifras describen el error en el conjunto de
prueba; no se ajusta ningún umbral con él.

Insumos:
    03_Resultados/Tablas/04_predicciones_prueba.csv   (lo produce 04_estimacion_modelos.py)
    01_Datos/02_Limpios/apartamentos_venta_limpio.csv  (características del ejemplo)

Salidas:
    03_Resultados/Tablas/08_error_tipico_por_estrato.csv
    03_Resultados/Tablas/08_ejemplo_vivienda.csv

Pasos:
    1. Lee las predicciones de prueba del modelo principal (Random Forest, objetivo en
       niveles: el de menor RMSE de CV) y calcula el error de cada vivienda.
    2. Por estrato y en total: precio mediano, error absoluto mediano en pesos, error
       relativo mediano y percentil 80 del error relativo (el error que no supera el 80%
       de las viviendas de prueba). Los grupos con menos de N_MINIMO_GRUPO_PRUEBA
       viviendas se marcan.
    3. Ejemplo: en el estrato ESTRATO_EJEMPLO, la vivienda cuyo error relativo absoluto
       está más cerca del error relativo mediano de su estrato (un caso típico, no uno
       escogido a mano); empates por código. Se reportan sus características, el precio
       publicado y el estimado.

Se corre desde la raíz del repo: python 02_Scripts/08_objetivos_practicos.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Rutas (ancladas a la raíz del proyecto, que es la carpeta padre de 02_Scripts)
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
RUTA_PREDICCIONES = RAIZ / "03_Resultados" / "Tablas" / "04_predicciones_prueba.csv"
RUTA_LIMPIA = RAIZ / "01_Datos" / "02_Limpios" / "apartamentos_venta_limpio.csv"
DIR_TABLAS = RAIZ / "03_Resultados" / "Tablas"

# ---------------------------------------------------------------------------
# Parámetros
# ---------------------------------------------------------------------------
OBJETIVO = "precio_venta"
# Modelo principal de la presentación: Random Forest con el objetivo en niveles
COLUMNA_PREDICCION = "pred_random_forest_niveles"
# Mismo umbral que 04 y 05: los grupos más pequeños se marcan, no se omiten
N_MINIMO_GRUPO_PRUEBA = 30
# Percentil del error relativo que se reporta como banda de error
PERCENTIL_BANDA = 80
# Estrato del ejemplo: el estrato medio del mercado, con suficientes viviendas en prueba
ESTRATO_EJEMPLO = 3
COLUMNAS_EJEMPLO = ["codigo", "estrato", "localidad", "barrio", "area", "habitaciones",
                    "banos", "parqueaderos", "antiguedad"]


def resumen_error(grupo):
    """Precio mediano y error típico (mediano y percentil) de un grupo de viviendas."""
    return pd.Series({
        "n_prueba": len(grupo),
        "precio_mediano": grupo[OBJETIVO].median(),
        "error_abs_mediano_cop": grupo["error_abs"].median(),
        "error_rel_mediano_pct": grupo["error_rel_abs_pct"].median(),
        f"error_rel_p{PERCENTIL_BANDA}_pct": np.percentile(grupo["error_rel_abs_pct"],
                                                           PERCENTIL_BANDA),
        "pct_sobrevaloradas": 100 * (grupo["error"] > 0).mean(),
    })


# ---------------------------------------------------------------------------
# 1. Error de cada vivienda de prueba
# ---------------------------------------------------------------------------
pred = pd.read_csv(RUTA_PREDICCIONES)
print(f"Predicciones de prueba: {len(pred):,} viviendas")
pred["estimado"] = pred[COLUMNA_PREDICCION]
# Error con signo: positivo = el modelo sobrevalora frente al precio publicado
pred["error"] = pred["estimado"] - pred[OBJETIVO]
pred["error_abs"] = pred["error"].abs()
pred["error_rel_abs_pct"] = 100 * pred["error_abs"] / pred[OBJETIVO]

# ---------------------------------------------------------------------------
# 2. Error típico por estrato y en total
# ---------------------------------------------------------------------------
por_estrato = pred.groupby("estrato").apply(resumen_error, include_groups=False)
por_estrato.index = por_estrato.index.astype(str)
total = resumen_error(pred).to_frame("TODAS").T
tabla = pd.concat([por_estrato, total])
tabla.index.name = "estrato"
tabla["n_prueba"] = tabla["n_prueba"].astype(int)
tabla["n_prueba_menor_minimo"] = tabla["n_prueba"] < N_MINIMO_GRUPO_PRUEBA
tabla.insert(0, "modelo", COLUMNA_PREDICCION)
tabla.to_csv(DIR_TABLAS / "08_error_tipico_por_estrato.csv")
print("\nError típico del Random Forest (niveles) en prueba:")
print(tabla.drop(columns="modelo").round(1).to_string())

# ---------------------------------------------------------------------------
# 3. Ejemplo: vivienda típica del estrato elegido
# ---------------------------------------------------------------------------
candidatas = pred[pred["estrato"] == ESTRATO_EJEMPLO].copy()
mediana_estrato = candidatas["error_rel_abs_pct"].median()
candidatas["distancia_mediana"] = (candidatas["error_rel_abs_pct"] - mediana_estrato).abs()
elegida = candidatas.sort_values(["distancia_mediana", "codigo"]).iloc[0]

limpia = pd.read_csv(RUTA_LIMPIA, usecols=COLUMNAS_EJEMPLO)
ejemplo = limpia[limpia["codigo"] == elegida["codigo"]].copy()
ejemplo["precio_publicado"] = elegida[OBJETIVO]
ejemplo["precio_estimado_rf"] = elegida["estimado"]
ejemplo["diferencia_cop"] = elegida["error"]
ejemplo["error_rel_pct"] = 100 * elegida["error"] / elegida[OBJETIVO]
ejemplo["error_rel_mediano_estrato_pct"] = mediana_estrato
ejemplo.to_csv(DIR_TABLAS / "08_ejemplo_vivienda.csv", index=False)
print(f"\nEjemplo (estrato {ESTRATO_EJEMPLO}, error más cercano a la mediana del estrato):")
print(ejemplo.T.to_string(header=False))
