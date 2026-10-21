"""
04_estimacion_modelos.py

Estimación y evaluación de los modelos de precio de venta: regresión lineal
(línea base), Lasso, Random Forest (modelo principal) y XGBoost (comparación).
Cada modelo se estima en dos escalas del objetivo: log(precio) y precio en
niveles. Las métricas se reportan siempre en pesos.

Insumos:
    01_Datos/02_Limpios/apartamentos_venta_limpio.csv
    01_Datos/02_Limpios/particion_train_test.csv   (lo produce 03_particion_muestra.py)

Salidas:
    03_Resultados/Tablas/04_metricas_modelos.csv
    03_Resultados/Tablas/04_hiperparametros.csv
    03_Resultados/Tablas/04_cv_grilla_random_forest.csv
    03_Resultados/Tablas/04_cv_grilla_xgboost.csv
    03_Resultados/Tablas/04_coeficientes_lineales.csv
    03_Resultados/Tablas/04_importancia_variables.csv
    03_Resultados/Tablas/04_errores_por_estrato.csv
    03_Resultados/Tablas/04_errores_por_localidad.csv
    03_Resultados/Tablas/04_predicciones_prueba.csv
    03_Resultados/Figuras/04_rmse_prueba_por_modelo.png
    03_Resultados/Figuras/04_error_relativo_por_estrato.png
    03_Resultados/Figuras/04_importancia_variables.png

Pasos:
    1. Lee la base limpia y la partición (no vuelve a partir los datos).
    2. Arma las matrices de variables con dummies. Las columnas se definen con
       entrenamiento y la prueba se alinea a ellas.
    3. Estima cada modelo solo con entrenamiento. Los hiperparámetros se eligen
       con validación cruzada (KFold de 5, random_state=2026) por RMSE en pesos.
    4. Evalúa una sola vez en prueba: RMSE y MAPE en entrenamiento, CV y prueba,
       diferencia entre CV y prueba y cambio frente a la línea base.
    5. Desagrega los errores de prueba por estrato y localidad, e interpreta
       (coeficientes lineales e importancia de variables de los árboles).

Se corre desde la raíz del repo: python 02_Scripts/04_estimacion_modelos.py
"""

import itertools
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Lasso, LassoCV, LinearRegression
from sklearn.metrics import mean_absolute_percentage_error, root_mean_squared_error
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

# ---------------------------------------------------------------------------
# Rutas (ancladas a la raíz del proyecto, que es la carpeta padre de 02_Scripts)
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
RUTA_LIMPIA = RAIZ / "01_Datos" / "02_Limpios" / "apartamentos_venta_limpio.csv"
RUTA_PARTICION = RAIZ / "01_Datos" / "02_Limpios" / "particion_train_test.csv"
DIR_TABLAS = RAIZ / "03_Resultados" / "Tablas"
DIR_FIGURAS = RAIZ / "03_Resultados" / "Figuras"

# ---------------------------------------------------------------------------
# Parámetros
# ---------------------------------------------------------------------------
SEMILLA = 2026
N_FOLDS = 5
OBJETIVO = "precio_venta"
ESCALAS = ["log", "niveles"]
# Grupos con menos viviendas que esto en prueba se marcan: sus métricas son poco estables
N_MINIMO_GRUPO_PRUEBA = 30

# Conjunto base (línea base): área, habitaciones, estrato, antigüedad y ubicación (localidad)
NUM_BASE = ["area", "habitaciones"]
CAT_BASE = ["estrato", "antiguedad", "localidad"]

# Conjunto completo (Lasso, Random Forest, XGBoost): base + estas variables
NUM_EXTRA = ["banos", "parqueaderos", "latitud", "longitud",
             "distancia_estacion_tm_m", "distancia_parque_m",
             "is_cerca_estacion_tm", "is_cerca_parque", "jacuzzi", "gimnasio", "ascensor",
             "conjunto_cerrado", "piscina", "terraza", "vigilancia"]
CAT_EXTRA = ["tipo_propiedad"]

# Columnas de la base limpia que no entran a ningún modelo, con su razón
COLUMNAS_EXCLUIDAS = {
    "codigo": "identificador de la vivienda",
    "descripcion": "texto libre; se reserva para un modelo de texto posterior",
    "datetime": "fecha de captura; la ventana (jul-sep 2024) es muy corta y la partición es aleatoria",
    "last_view": "se actualiza en cada corrida del scraper; no es característica de la vivienda",
    "tipo_operacion": "VENTA vs VENTA Y ARRIENDO es metadato del anuncio",
    "website": "metadato de la fuente, no característica de la vivienda",
    "sector": "ubicación redundante con localidad y lat/lon",
    "barrio": "decisión del equipo: 1,387 categorías; la ubicación fina se toma de lat/lon",
    "estacion_tm_cercana": "nombre de la estación; ya está la distancia",
    "parque_cercano": "nombre del parque; ya está la distancia",
    "coords_modified": "marca de calidad de las coordenadas; se conserva para desagregar errores",
    "chimenea": "constante (siempre False)",
    "permite_mascotas": "constante (siempre False)",
    "salon_comunal": "constante (siempre False)",
}

# Grillas de hiperparámetros (se eligen por RMSE de validación cruzada, solo en entrenamiento)
GRILLA_RF = {"max_features": [0.33, 0.5, 1.0], "min_samples_leaf": [1, 3, 10]}
GRILLA_XGB = {"n_estimators": [300, 800], "learning_rate": [0.05, 0.1], "max_depth": [4, 6, 8]}

# Nombres legibles y orden de presentación de los modelos
MODELOS = ["lineal_base", "lineal_completo", "lasso", "random_forest", "xgboost"]
NOMBRES = {"lineal_base": "Lineal (base)", "lineal_completo": "Lineal (completo)",
           "lasso": "Lasso", "random_forest": "Random Forest", "xgboost": "XGBoost"}

# Colores de las figuras (paleta de referencia validada para daltonismo, modo claro)
SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
GRILLA = "#e1e0d9"
EJE = "#c3c2b7"
COLOR_MODELO = dict(zip(MODELOS, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]))
COLOR_ESCALA = {"log": "#2a78d6", "niveles": "#eb6834"}


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


def guardar_figura(fig, nombre):
    DIR_FIGURAS.mkdir(parents=True, exist_ok=True)
    ruta = DIR_FIGURAS / nombre
    fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor=SUPERFICIE)
    plt.close(fig)
    print(f"  -> {ruta_relativa(ruta)}")


def rmse(y, pred):
    return root_mean_squared_error(y, pred)


def mape(y, pred):
    """MAPE en porcentaje."""
    return 100 * mean_absolute_percentage_error(y, pred)


def a_escala(y, escala):
    """Objetivo con el que se entrena el modelo: log(precio) o precio en niveles."""
    return np.log(y) if escala == "log" else y


def a_pesos(pred, escala):
    """Devuelve las predicciones a pesos (exp si el modelo se entrenó en log)."""
    return np.exp(pred) if escala == "log" else pred


def matrices(num, cat, log_area=False):
    """Matrices de entrenamiento y prueba con dummies de las categóricas.

    Las columnas se definen con entrenamiento (una dummy de referencia por variable) y la prueba se
    alinea a ellas: una categoría que no aparece en entrenamiento queda como la de referencia.
    Con log_area=True el área entra como log(area): con el objetivo en log y el área en niveles,
    exp(b * area) explota para las viviendas de más de 1,000 m2.
    """
    X_tr = pd.get_dummies(train[num + cat], columns=cat, drop_first=True, dtype=float)
    X_pr = pd.get_dummies(prueba[num + cat], columns=cat, dtype=float).reindex(columns=X_tr.columns, fill_value=0)
    if log_area:
        for X in (X_tr, X_pr):
            X["area"] = np.log(X["area"])
        X_tr, X_pr = X_tr.rename(columns={"area": "log_area"}), X_pr.rename(columns={"area": "log_area"})
    return X_tr, X_pr


def cv_en_pesos(modelo, X, y, escala):
    """Validación cruzada con KFold: RMSE y MAPE en pesos (media y desviación entre folds).

    En cada fold el modelo se ajusta con 4/5 del entrenamiento y se evalúa en el 1/5 restante.
    """
    rmses, mapes = [], []
    for idx_ajuste, idx_validacion in KFOLD.split(X):
        modelo.fit(X.iloc[idx_ajuste], a_escala(y.iloc[idx_ajuste], escala))
        pred = a_pesos(modelo.predict(X.iloc[idx_validacion]), escala)
        rmses.append(rmse(y.iloc[idx_validacion], pred))
        mapes.append(mape(y.iloc[idx_validacion], pred))
    return {"rmse_cv": np.mean(rmses), "rmse_cv_sd": np.std(rmses),
            "mape_cv": np.mean(mapes), "mape_cv_sd": np.std(mapes)}


def elegir_por_cv(crear_modelo, grilla, X, y, escala, nombre):
    """Prueba cada combinación de la grilla con cv_en_pesos y elige la de menor RMSE de CV."""
    filas, resultados = [], []
    for valores in itertools.product(*grilla.values()):
        params = dict(zip(grilla, valores))
        t0 = time.time()
        cv = cv_en_pesos(crear_modelo(params), X, y, escala)
        resultados.append((params, cv))
        filas.append({"modelo": nombre, "escala": escala, **params, **cv, "segundos": time.time() - t0})
    mejores_params, mejor_cv = min(resultados, key=lambda r: r[1]["rmse_cv"])
    tabla = pd.DataFrame(filas)
    tabla["rango_rmse"] = tabla["rmse_cv"].rank(method="min").astype(int)
    return mejores_params, mejor_cv, tabla


def variable_original(columna, variables):
    """Variable de la base de la que sale una columna de la matriz (las dummies llevan sufijo)."""
    if columna in variables:
        return columna
    return next(v for v in variables if columna.startswith(v + "_"))


def estilo_ejes(ax):
    """Ejes y grilla recesivos: líneas finas y sólidas, texto en tinta secundaria."""
    ax.set_facecolor(SUPERFICIE)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color(EJE)
    ax.tick_params(colors=TINTA_SECUNDARIA, labelsize=9, length=0)
    ax.grid(color=GRILLA, linewidth=0.6)
    ax.set_axisbelow(True)


# ---------------------------------------------------------------------------
# 1. Lectura de la base limpia y de la partición
# ---------------------------------------------------------------------------
titulo("1. LECTURA")
df = pd.read_csv(RUTA_LIMPIA, parse_dates=["datetime", "last_view"])
if not RUTA_PARTICION.exists():
    raise SystemExit(f"No existe {ruta_relativa(RUTA_PARTICION)}: corra antes 02_Scripts/03_particion_muestra.py")
particion = pd.read_csv(RUTA_PARTICION)
df = df.merge(particion, on="codigo", how="left", validate="one_to_one")
if df["conjunto"].isna().any():
    raise SystemExit(f"{int(df['conjunto'].isna().sum())} viviendas no están en la partición: "
                     "corra de nuevo 02_Scripts/03_particion_muestra.py")
print(f"Base limpia: {len(df):,} viviendas")
print(df["conjunto"].value_counts().to_string())

# ---------------------------------------------------------------------------
# 2. Variables y matrices de diseño
# ---------------------------------------------------------------------------
titulo("2. VARIABLES Y MATRICES")
VARS_BASE = NUM_BASE + CAT_BASE
VARS_COMPLETO = NUM_BASE + NUM_EXTRA + CAT_BASE + CAT_EXTRA
# Toda columna de la base debe estar usada o excluida con razón
sin_clasificar = set(df.columns) - set(VARS_COMPLETO) - set(COLUMNAS_EXCLUIDAS) - {OBJETIVO, "conjunto"}
assert not sin_clasificar, f"Columnas sin clasificar: {sin_clasificar}"
print(f"Base ({len(VARS_BASE)}): {VARS_BASE}")
print(f"Completo ({len(VARS_COMPLETO)}): {VARS_COMPLETO}")
print(f"Excluidas ({len(COLUMNAS_EXCLUIDAS)}):")
for c, razon in COLUMNAS_EXCLUIDAS.items():
    print(f"  - {c}: {razon}")

df[NUM_EXTRA] = df[NUM_EXTRA].astype(float)  # las binarias entran como 0/1
train = df[df["conjunto"] == "entrenamiento"].reset_index(drop=True)
prueba = df[df["conjunto"] == "prueba"].reset_index(drop=True)
y_train, y_prueba = train[OBJETIVO], prueba[OBJETIVO]
print(f"\nEntrenamiento: {len(train):,} | Prueba: {len(prueba):,}")

# Matrices (entrenamiento, prueba) de cada modelo y escala. En los lineales estrato es
# categórica (dummies); en los árboles es numérica (ordinal) y el área va en niveles en ambas escalas.
X = {}
for escala in ESCALAS:
    X[("lineal_base", escala)] = matrices(NUM_BASE, CAT_BASE, log_area=escala == "log")
    X[("lineal_completo", escala)] = matrices(NUM_BASE + NUM_EXTRA, CAT_BASE + CAT_EXTRA, log_area=escala == "log")
    # Lasso usa las variables del lineal completo, estandarizadas para que la penalización las trate
    # por igual. El escalador se ajusta con todo el entrenamiento (solo usa las X, nunca el precio).
    X_tr, X_pr = X[("lineal_completo", escala)]
    escalador = StandardScaler().fit(X_tr)
    X[("lasso", escala)] = (pd.DataFrame(escalador.transform(X_tr), columns=X_tr.columns),
                            pd.DataFrame(escalador.transform(X_pr), columns=X_tr.columns))
    arbol = matrices(NUM_BASE + NUM_EXTRA + ["estrato"], ["antiguedad", "localidad", "tipo_propiedad"])
    X[("random_forest", escala)] = X[("xgboost", escala)] = arbol
for (nombre, escala), (X_tr, X_pr) in X.items():
    assert list(X_tr.columns) == list(X_pr.columns) and len(X_pr) == len(prueba)
print("Columnas por matriz (escala log):",
      {m: X[(m, "log")][0].shape[1] for m in MODELOS})

KFOLD = KFold(n_splits=N_FOLDS, shuffle=True, random_state=SEMILLA)

# ---------------------------------------------------------------------------
# 3. Estimación (solo entrenamiento)
# ---------------------------------------------------------------------------
titulo("3. ESTIMACIÓN CON VALIDACIÓN CRUZADA (SOLO ENTRENAMIENTO)")
ajustados = {}       # (modelo, escala) -> modelo ajustado en todo el entrenamiento
cv_metricas = {}     # (modelo, escala) -> métricas de validación cruzada
hiperparametros = []
grillas = {"random_forest": [], "xgboost": []}
segundos = {}

for escala in ESCALAS:
    print(f"\n--- Escala del objetivo: {escala} ---")

    # 3a. Línea base y lineal completo (MCO): sin hiperparámetros
    for nombre in ["lineal_base", "lineal_completo"]:
        t0 = time.time()
        X_tr, _ = X[(nombre, escala)]
        modelo = LinearRegression()
        cv_metricas[(nombre, escala)] = cv_en_pesos(modelo, X_tr, y_train, escala)
        ajustados[(nombre, escala)] = modelo.fit(X_tr, a_escala(y_train, escala))
        segundos[(nombre, escala)] = time.time() - t0
        hiperparametros.append({"modelo": nombre, "escala": escala, "hiperparametros": "ninguno"})
        print(f"  {nombre}: RMSE CV {cv_metricas[(nombre, escala)]['rmse_cv']:,.0f}")

    # 3b. Lasso: LassoCV elige alpha con el mismo KFold sobre el camino de alphas que calcula de
    # los datos; luego se mide la CV en pesos con ese alpha fijo.
    t0 = time.time()
    X_tr, _ = X[("lasso", escala)]
    alpha = LassoCV(alphas=100, cv=KFOLD, max_iter=20000).fit(X_tr, a_escala(y_train, escala)).alpha_
    modelo = Lasso(alpha=alpha, max_iter=20000)
    cv_metricas[("lasso", escala)] = cv_en_pesos(modelo, X_tr, y_train, escala)
    ajustados[("lasso", escala)] = modelo.fit(X_tr, a_escala(y_train, escala))
    segundos[("lasso", escala)] = time.time() - t0
    hiperparametros.append({"modelo": "lasso", "escala": escala, "hiperparametros": f"alpha={alpha:.6g}"})
    print(f"  lasso: alpha={alpha:.6g}, RMSE CV {cv_metricas[('lasso', escala)]['rmse_cv']:,.0f}")

    # 3c. Random Forest y XGBoost: se recorre la grilla y se elige por RMSE de CV en pesos
    creadores = {
        "random_forest": (lambda p: RandomForestRegressor(n_estimators=300, random_state=SEMILLA,
                                                          n_jobs=-1, **p), GRILLA_RF),
        "xgboost": (lambda p: XGBRegressor(objective="reg:squarederror", tree_method="hist", subsample=0.8,
                                           colsample_bytree=0.8, random_state=SEMILLA, n_jobs=-1, **p),
                    GRILLA_XGB),
    }
    for nombre, (crear_modelo, grilla) in creadores.items():
        t0 = time.time()
        X_tr, _ = X[(nombre, escala)]
        params, mejor, tabla = elegir_por_cv(crear_modelo, grilla, X_tr, y_train, escala, nombre)
        cv_metricas[(nombre, escala)] = mejor
        ajustados[(nombre, escala)] = crear_modelo(params).fit(X_tr, a_escala(y_train, escala))
        segundos[(nombre, escala)] = time.time() - t0
        hiperparametros.append({"modelo": nombre, "escala": escala,
                                "hiperparametros": ", ".join(f"{k}={v}" for k, v in params.items())})
        grillas[nombre].append(tabla)
        print(f"  {nombre}: {params}, RMSE CV {mejor['rmse_cv']:,.0f} ({segundos[(nombre, escala)] / 60:.1f} min)")

# ---------------------------------------------------------------------------
# 4. Evaluación: entrenamiento (in-sample), CV y prueba. La prueba se usa solo aquí.
# ---------------------------------------------------------------------------
titulo("4. EVALUACIÓN EN ENTRENAMIENTO, VALIDACIÓN CRUZADA Y PRUEBA")
predicciones = prueba[["codigo", "estrato", "localidad", "barrio", "coords_modified", OBJETIVO]].copy()
filas = []
for escala in ESCALAS:
    for nombre in MODELOS:
        modelo = ajustados[(nombre, escala)]
        X_tr, X_pr = X[(nombre, escala)]
        pred_train = a_pesos(modelo.predict(X_tr), escala)
        pred_prueba = a_pesos(modelo.predict(X_pr), escala)
        assert np.isfinite(pred_prueba).all(), f"{nombre} ({escala}) tiene predicciones no finitas"
        predicciones[f"pred_{nombre}_{escala}"] = pred_prueba
        cv = cv_metricas[(nombre, escala)]
        filas.append({
            "modelo": nombre, "escala": escala,
            "rmse_train": rmse(y_train, pred_train), "rmse_cv": cv["rmse_cv"], "rmse_cv_sd": cv["rmse_cv_sd"],
            "rmse_prueba": rmse(y_prueba, pred_prueba),
            "mape_train": mape(y_train, pred_train), "mape_cv": cv["mape_cv"], "mape_cv_sd": cv["mape_cv_sd"],
            "mape_prueba": mape(y_prueba, pred_prueba),
            "n_pred_negativas_prueba": int((pred_prueba < 0).sum()),
            "segundos_estimacion": segundos[(nombre, escala)],
        })
metricas = pd.DataFrame(filas)
# Consistencia fuera de muestra: prueba frente a CV (ambos sobre datos no usados para ajustar).
# No hay umbral: la regla de las diapositivas es para clasificación, no para RMSE/MAPE.
metricas["dif_rmse_prueba_vs_cv_pct"] = 100 * (metricas["rmse_prueba"] - metricas["rmse_cv"]) / metricas["rmse_cv"]
metricas["dif_mape_prueba_vs_cv_pp"] = metricas["mape_prueba"] - metricas["mape_cv"]
base = metricas[metricas["modelo"] == "lineal_base"].set_index("escala")
metricas["cambio_rmse_prueba_vs_base_pct"] = 100 * (
    metricas["rmse_prueba"] / metricas["escala"].map(base["rmse_prueba"]) - 1)
metricas["cambio_mape_prueba_vs_base_pp"] = metricas["mape_prueba"] - metricas["escala"].map(base["mape_prueba"])
assert predicciones.notna().all().all(), "Hay N/A en las predicciones de prueba"

vista = metricas[["modelo", "escala", "rmse_train", "rmse_cv", "rmse_prueba", "mape_train", "mape_cv",
                  "mape_prueba", "dif_rmse_prueba_vs_cv_pct", "dif_mape_prueba_vs_cv_pp",
                  "cambio_rmse_prueba_vs_base_pct"]].copy()
for c in ["rmse_train", "rmse_cv", "rmse_prueba"]:
    vista[c] = (vista[c] / 1e6).round(1)
vista = vista.rename(columns={c: c + "_M" for c in ["rmse_train", "rmse_cv", "rmse_prueba"]})
with pd.option_context("display.width", 200, "display.max_columns", None):
    print("RMSE en millones de COP; MAPE en %; dif. prueba vs CV y cambio vs base en % (MAPE: puntos)")
    print(vista.round(2).to_string(index=False))

# ---------------------------------------------------------------------------
# 5. Errores de prueba por estrato y localidad (IA responsable)
# ---------------------------------------------------------------------------
titulo("5. ERRORES DE PRUEBA POR ESTRATO Y LOCALIDAD")


def errores_por_grupo(grupo):
    filas = []
    y = predicciones[OBJETIVO]
    for escala in ESCALAS:
        for nombre in MODELOS:
            pred = predicciones[f"pred_{nombre}_{escala}"]
            error_rel = 100 * (pred - y) / y
            for valor, idx in predicciones.groupby(grupo).groups.items():
                filas.append({
                    "modelo": nombre, "escala": escala, grupo: valor, "n_prueba": len(idx),
                    "rmse": rmse(y[idx], pred[idx]), "mape": mape(y[idx], pred[idx]),
                    # Con signo: positivo = sobrevalora, negativo = subvalora
                    "error_relativo_medio_pct": error_rel[idx].mean(),
                    "error_relativo_mediano_pct": error_rel[idx].median(),
                    "n_prueba_menor_minimo": len(idx) < N_MINIMO_GRUPO_PRUEBA,
                })
    return pd.DataFrame(filas)


err_estrato = errores_por_grupo("estrato")
err_localidad = errores_por_grupo("localidad")
columnas_orden = [(e, m) for e in ESCALAS for m in MODELOS]
with pd.option_context("display.width", 200):
    print("MAPE (%) en prueba por estrato:")
    print(err_estrato.pivot_table(index="estrato", columns=["escala", "modelo"], values="mape")
          [columnas_orden].round(1).to_string())
    print("\nError relativo medio con signo (%) en prueba por estrato (+ sobrevalora, - subvalora):")
    print(err_estrato.pivot_table(index="estrato", columns=["escala", "modelo"], values="error_relativo_medio_pct")
          [columnas_orden].round(1).to_string())

# ---------------------------------------------------------------------------
# 6. Interpretación: coeficientes lineales e importancia de variables de los árboles
# ---------------------------------------------------------------------------
titulo("6. INTERPRETACIÓN")
coefs = []
for escala in ESCALAS:
    for nombre in ["lineal_base", "lasso"]:
        modelo = ajustados[(nombre, escala)]
        columnas = X[(nombre, escala)][0].columns
        coefs.append(pd.DataFrame({"modelo": nombre, "escala": escala,
                                   "variable": list(columnas) + ["(intercepto)"],
                                   "coeficiente": list(modelo.coef_) + [modelo.intercept_]}))
        if nombre == "lasso":
            print(f"Lasso ({escala}): {int((modelo.coef_ == 0).sum())} de {len(modelo.coef_)} coeficientes en cero")
coefs = pd.concat(coefs, ignore_index=True)
coefs["unidad_objetivo"] = np.where(coefs["escala"] == "log", "log(COP)", "COP")
coefs["unidad_variables"] = np.where(coefs["modelo"] == "lasso", "estandarizadas (1 desviación estándar)",
                                     "naturales (log_area en log de m2; dummies frente a la categoría de referencia)")

# Importancia de los árboles (feature_importances_): reducción del error que aporta cada columna.
# Las dummies de una misma variable (p. ej. las de localidad) se suman.
VARS_ARBOL = NUM_BASE + NUM_EXTRA + ["estrato", "antiguedad", "localidad", "tipo_propiedad"]
importancias = []
for escala in ESCALAS:
    for nombre in ["random_forest", "xgboost"]:
        columnas = X[(nombre, escala)][0].columns
        t = pd.DataFrame({"columna": columnas, "importancia": ajustados[(nombre, escala)].feature_importances_})
        t["variable"] = [variable_original(c, VARS_ARBOL) for c in t["columna"]]
        t = t.groupby("variable", as_index=False)["importancia"].sum()
        t["importancia_pct"] = 100 * t["importancia"] / t["importancia"].sum()
        t.insert(0, "escala", escala)
        t.insert(0, "modelo", nombre)
        importancias.append(t.sort_values("importancia_pct", ascending=False))
        print(f"Importancia {nombre} ({escala}): primeras "
              f"{', '.join(importancias[-1]['variable'].head(5))}")
importancias = pd.concat(importancias, ignore_index=True)

# ---------------------------------------------------------------------------
# 7. Figuras
# ---------------------------------------------------------------------------
titulo("7. FIGURAS")
plt.rcParams.update({"font.family": "sans-serif", "font.size": 9, "text.color": TINTA,
                     "axes.labelcolor": TINTA_SECUNDARIA, "figure.facecolor": SUPERFICIE})

# 7a. RMSE de prueba por modelo y escala (barras horizontales agrupadas)
fig, ax = plt.subplots(figsize=(7.5, 4.2))
estilo_ejes(ax)
ax.grid(axis="y", visible=False)
alto = 0.38
for j, escala in enumerate(ESCALAS):
    valores = [metricas.query("modelo == @m and escala == @escala")["rmse_prueba"].iloc[0] / 1e6 for m in MODELOS]
    posiciones = np.arange(len(MODELOS)) + (j - 0.5) * alto
    ax.barh(posiciones, valores, height=alto, color=COLOR_ESCALA[escala], edgecolor=SUPERFICIE,
            linewidth=1.5, label=f"Objetivo en {escala}")
    for p, v in zip(posiciones, valores):
        ax.text(v, p, f" {v:,.0f}", va="center", fontsize=8, color=TINTA_SECUNDARIA)
ax.set_yticks(np.arange(len(MODELOS)), [NOMBRES[m] for m in MODELOS], color=TINTA)
ax.invert_yaxis()
ax.set_xlabel("RMSE en prueba (millones de COP)")
ax.set_title("RMSE en el conjunto de prueba por modelo", loc="left", fontsize=11, color=TINTA)
ax.legend(frameon=False, loc="lower right", fontsize=8)
guardar_figura(fig, "04_rmse_prueba_por_modelo.png")

# 7b. Error relativo medio con signo por estrato, un panel por escala
estratos = sorted(err_estrato["estrato"].unique())
n_por_estrato = predicciones.groupby("estrato").size()
fig, ejes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
ancho = 0.16
for ax, escala in zip(ejes, ESCALAS):
    estilo_ejes(ax)
    ax.grid(axis="x", visible=False)
    for j, nombre in enumerate(MODELOS):
        sub = err_estrato.query("modelo == @nombre and escala == @escala").set_index("estrato")
        posiciones = np.arange(len(estratos)) + (j - (len(MODELOS) - 1) / 2) * ancho
        ax.bar(posiciones, sub.loc[estratos, "error_relativo_medio_pct"], width=ancho,
               color=COLOR_MODELO[nombre], edgecolor=SUPERFICIE, linewidth=1, label=NOMBRES[nombre])
    ax.axhline(0, color=EJE, linewidth=0.8)
    ax.set_xticks(np.arange(len(estratos)), [f"{e}\nn={n_por_estrato[e]}" for e in estratos])
    ax.set_xlabel("Estrato (n en prueba)")
    ax.set_title(f"Objetivo en {escala}", loc="left", fontsize=10, color=TINTA)
ejes[0].set_ylabel("Error relativo medio (%)\n+ sobrevalora · − subvalora")
ejes[1].legend(frameon=False, fontsize=8, loc="upper right")
fig.suptitle("Error relativo medio con signo en prueba, por estrato", x=0.07, ha="left", fontsize=11, color=TINTA)
guardar_figura(fig, "04_error_relativo_por_estrato.png")

# 7c. Importancia de variables: múltiplos pequeños (modelo x escala), un solo color
N_TOP = 12
fig, ejes = plt.subplots(2, 2, figsize=(11, 7.5))
for i, nombre in enumerate(["random_forest", "xgboost"]):
    for j, escala in enumerate(ESCALAS):
        ax = ejes[i, j]
        estilo_ejes(ax)
        ax.grid(axis="y", visible=False)
        sub = importancias.query("modelo == @nombre and escala == @escala").head(N_TOP)
        ax.barh(np.arange(len(sub)), sub["importancia_pct"], color=COLOR_MODELO["lineal_base"],
                edgecolor=SUPERFICIE, linewidth=1)
        ax.set_yticks(np.arange(len(sub)), sub["variable"], color=TINTA, fontsize=8)
        ax.invert_yaxis()
        ax.set_title(f"{NOMBRES[nombre]} · objetivo en {escala}", loc="left", fontsize=10, color=TINTA)
        if i == 1:
            ax.set_xlabel("Importancia relativa (% del total)")
fig.suptitle(f"Importancia de variables ({N_TOP} principales; dummies sumadas por variable)",
             x=0.07, ha="left", fontsize=11, color=TINTA)
fig.tight_layout()
guardar_figura(fig, "04_importancia_variables.png")

# ---------------------------------------------------------------------------
# 8. Guardado de tablas
# ---------------------------------------------------------------------------
titulo("8. GUARDADO")
guardar_tabla(metricas, "04_metricas_modelos.csv")
guardar_tabla(pd.DataFrame(hiperparametros), "04_hiperparametros.csv")
guardar_tabla(pd.concat(grillas["random_forest"], ignore_index=True), "04_cv_grilla_random_forest.csv")
guardar_tabla(pd.concat(grillas["xgboost"], ignore_index=True), "04_cv_grilla_xgboost.csv")
guardar_tabla(coefs, "04_coeficientes_lineales.csv")
guardar_tabla(importancias, "04_importancia_variables.csv")
guardar_tabla(err_estrato, "04_errores_por_estrato.csv")
guardar_tabla(err_localidad, "04_errores_por_localidad.csv")
guardar_tabla(predicciones, "04_predicciones_prueba.csv")
print(f"\nTiempo total de estimación: {sum(segundos.values()) / 60:.1f} min")
