"""
11_modelos_texto.py

Modelos de precio que agregan información del texto de 'descripcion' a las variables
tabulares (plan de 05_Notas/alternativas_aprendizaje_profundo_descripcion.md, sección 7):

    Paso 1 (A1)  Random Forest + variables por palabras clave de 09.
    Paso 2 (A2)  TF-IDF: (i) Ridge con variables tabulares + TF-IDF y (ii) componentes
                 principales (PCA) del TF-IDF en el Random Forest.
    Paso 3 (C1)  Vectores del Transformer preentrenado de 10 (multilingual-e5-base):
                 (i) componentes principales en el Random Forest y (ii) red neuronal (MLP)
                 híbrida en PyTorch con variables tabulares + vectores.

Cada variante con texto tiene una pareja sin texto, estimada igual, para atribuir la
diferencia al texto: Random Forest tabular, Ridge tabular y MLP tabular. Además, una ablación
sin estrato ni localidad para ver si el texto reintroduce la ubicación (IA responsable).
Todo en las dos escalas del objetivo (log y niveles); las métricas siempre en pesos.

Insumos:
    01_Datos/02_Limpios/apartamentos_venta_limpio.csv
    01_Datos/02_Limpios/particion_train_test.csv    (lo produce 03_particion_muestra.py)
    01_Datos/02_Limpios/descripcion_limpia.csv      (lo produce 09_texto_limpieza.py)
    01_Datos/02_Limpios/embeddings_e5_base.npz      (lo produce 10_texto_embeddings.py)
    03_Resultados/Tablas/04_hiperparametros.csv     (lo produce 04_estimacion_modelos.py)
    03_Resultados/Tablas/04_metricas_modelos.csv    (línea base y control del Random Forest tabular)

Salidas:
    03_Resultados/Tablas/11_metricas_modelos_texto.csv
    03_Resultados/Tablas/11_cv_grillas.csv
    03_Resultados/Tablas/11_importancia_variables.csv
    03_Resultados/Tablas/11_errores_por_estrato.csv
    03_Resultados/Tablas/11_errores_por_localidad.csv
    03_Resultados/Tablas/11_sensibilidad_duplicados.csv
    03_Resultados/Tablas/11_predicciones_prueba.csv

Pasos:
    1. Lee la base limpia, la partición, el texto limpio y los vectores (no vuelve a partir los datos).
    2. Arma los bloques de variables. Todo lo que se aprende de los datos se ajusta solo con
       entrenamiento y la prueba solo se transforma: dummies, escalador, vocabulario e IDF del
       TF-IDF y los dos PCA. Ninguno usa el precio, así que (como permite CLAUDE.md) se ajustan
       con todo el entrenamiento también para la CV. Lo que sí usa el precio (el modelo y la
       estandarización del objetivo de la red) se ajusta dentro de cada fold.
    3. Elige los hiperparámetros de cada variante por RMSE de CV en pesos (KFold de 5,
       random_state=2026), solo con entrenamiento:
         - Random Forest: los hiperparámetros que eligió 04 para el tabular, en cada escala (no
           se vuelven a buscar); con texto se elige solo el número de componentes del PCA.
         - Ridge: alpha. MLP: dropout y weight decay; las épocas se eligen con parada temprana sobre un
           10% del entrenamiento de cada fold (nunca con la prueba).
       Las grillas y por qué tienen esos valores están en la sección de parámetros.
       Control: el Random Forest tabular debe reproducir las métricas de 04.
    4. Evalúa una sola vez en prueba: RMSE y MAPE en entrenamiento, CV y prueba, junto a la línea
       base (leída de 04), el cambio frente a la pareja sin texto y frente al Random Forest tabular.
    5. Importancia de variables de los Random Forest, errores de prueba por estrato y localidad, y
       sensibilidad: métricas de prueba sin las viviendas cuya descripción limpia es idéntica a una
       de entrenamiento y sin los gemelos (misma definición que 05).

Herramientas nuevas (aprobadas por Santiago Muñoz el 2026-11-09, pendientes de confirmar con el
equipo): PyTorch para la red (se vio en la clase 9) y TfidfVectorizer de scikit-learn (TF-IDF de
la clase de NLP). El PCA sobre la matriz dispersa del TF-IDF usa svd_solver="arpack", que centra
los datos sin volverlos densos.

Se corre desde la raíz del repo: python 02_Scripts/11_modelos_texto.py
"""

import copy
import itertools
import time
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp
import torch
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_percentage_error, root_mean_squared_error
from sklearn.model_selection import KFold, cross_validate
from sklearn.preprocessing import StandardScaler
from torch import nn

# ---------------------------------------------------------------------------
# Rutas (ancladas a la raíz del proyecto, que es la carpeta padre de 02_Scripts)
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
RUTA_LIMPIA = RAIZ / "01_Datos" / "02_Limpios" / "apartamentos_venta_limpio.csv"
RUTA_PARTICION = RAIZ / "01_Datos" / "02_Limpios" / "particion_train_test.csv"
RUTA_TEXTO = RAIZ / "01_Datos" / "02_Limpios" / "descripcion_limpia.csv"
RUTA_EMBEDDINGS = RAIZ / "01_Datos" / "02_Limpios" / "embeddings_e5_base.npz"
DIR_TABLAS = RAIZ / "03_Resultados" / "Tablas"
RUTA_HIPERPARAMETROS = DIR_TABLAS / "04_hiperparametros.csv"
RUTA_METRICAS_04 = DIR_TABLAS / "04_metricas_modelos.csv"

# ---------------------------------------------------------------------------
# Parámetros
# ---------------------------------------------------------------------------
SEMILLA = 2026
N_FOLDS = 5
OBJETIVO = "precio_venta"
ESCALAS = ["log", "niveles"]
N_MINIMO_GRUPO_PRUEBA = 30
# Tolerancia relativa para el control contra 04 (mismos datos, semilla e hiperparámetros)
TOLERANCIA_CONTROL = 1e-6

# Variables tabulares: las mismas de 04_estimacion_modelos.py y en el mismo orden
# (en el Random Forest el orden de las columnas cambia qué variables sortea cada árbol)
NUM_BASE = ["area", "habitaciones"]
NUM_EXTRA = ["banos", "parqueaderos", "latitud", "longitud",
             "distancia_estacion_tm_m", "distancia_parque_m",
             "is_cerca_estacion_tm", "is_cerca_parque", "jacuzzi", "gimnasio", "ascensor",
             "conjunto_cerrado", "piscina", "terraza", "vigilancia"]
NUM_ARBOL = NUM_BASE + NUM_EXTRA + ["estrato"]
CAT_ARBOL = ["antiguedad", "localidad", "tipo_propiedad"]
# Lineal completo de 04 (Ridge y MLP): estrato como categórica; área en log con el objetivo en log
CAT_LINEAL = ["estrato", "antiguedad", "localidad", "tipo_propiedad"]
# Ablación de IA responsable: variables de ubicación sensibles que se quitan
VARS_SENSIBLES = ["estrato", "localidad"]

# Variables por palabras clave de 09_texto_limpieza.py (A1)
VARS_PALABRAS_CLAVE = ["txt_vista", "txt_exterior", "txt_interior", "txt_balcon", "txt_remodelado",
                       "txt_para_remodelar", "txt_iluminado", "txt_duplex", "txt_penthouse", "txt_estudio",
                       "txt_deposito", "txt_cuarto_servicio", "txt_chimenea", "txt_esquinero",
                       "txt_piso_alto", "txt_piso_numero", "txt_menciona_piso"]

# Marcadores de 09: se quitan antes de TF-IDF (igual que en 10 antes de los vectores)
MARCADORES = r"<(?:cifra_dinero|telefono|correo)>"
# TF-IDF: palabras y pares de palabras que aparecen en al menos 5 anuncios de entrenamiento
TFIDF = dict(ngram_range=(1, 2), min_df=5, sublinear_tf=True)
# Componentes principales que se guardan de cada PCA; la grilla elige cuántas entran al modelo
N_COMPONENTES_MAX = 50

# Red neuronal: arquitectura fija; la grilla elige la regularización
MLP_CAPAS = (256, 64)
MLP_FIJOS = dict(tasa_aprendizaje=1e-3, tamano_lote=256, max_epocas=300, paciencia=20, fraccion_validacion=0.1,
                 mejora_minima=1e-4)
torch.set_num_threads(4)

# Grillas (se eligen por RMSE de CV en pesos). Historia (corridas del 2026-11-09):
#   - Primera corrida: [10, 25, 50] componentes, alpha desde 0.01, dropout [0.1, 0.3] y weight decay
#     [1e-5, 1e-3]; varios elegidos en el borde, así que se ampliaron.
#   - Segunda corrida (grillas ampliadas, 7.2 horas): el RMSE de CV del Random Forest sube de forma monótona
#     con k (el borde k=2 es real: k=0 es el Random Forest tabular); el Ridge tabular es plano y con alpha
#     pequeño converge a MCO (lineal completo de 04); en Ridge + TF-IDF los alpha menores a 0.1 dieron más
#     error y tardaron hasta 95 min cada uno, así que se quitan; en el MLP, weight decay 1e-2 fue el peor en
#     las seis superficies, así que se quita, y las demás diferencias son menores que la desviación entre folds.
GRILLA_K = {"k": [2, 5, 10, 25, 50]}
GRILLA_ALPHA = {"alpha": [1e-4, 1e-3, 0.01, 0.1, 1, 3, 10, 30, 100, 300]}
GRILLA_ALPHA_TFIDF = {"alpha": [0.1, 0.3, 1, 3, 10, 30, 100, 300]}
GRILLA_MLP = {"dropout": [0.1, 0.3, 0.5], "weight_decay": [1e-5, 1e-4, 1e-3]}

# Variantes: familia, bloques de variables, grilla, pareja sin texto y paso del plan.
# "k" es el número de componentes del PCA (bloques *_pca); los demás son del estimador.
# k_de: usa el k elegido por otra variante (no se vuelve a buscar).
VARIANTES = {
    "random_forest":                {"familia": "rf", "bloques": ["arbol"], "grilla": {},
                                     "sin_texto": None, "paso": "tabular"},
    "rf_palabras_clave":            {"familia": "rf", "bloques": ["arbol", "palabras_clave"], "grilla": {},
                                     "sin_texto": "random_forest", "paso": "1 (A1)"},
    "rf_tfidf_pca":                 {"familia": "rf", "bloques": ["arbol", "tfidf_pca"], "grilla": GRILLA_K,
                                     "sin_texto": "random_forest", "paso": "2 (A2)"},
    "rf_e5_pca":                    {"familia": "rf", "bloques": ["arbol", "e5_pca"], "grilla": GRILLA_K,
                                     "sin_texto": "random_forest", "paso": "3 (C1)"},
    "rf_sin_ubicacion":             {"familia": "rf", "bloques": ["arbol_sin_ubicacion"], "grilla": {},
                                     "sin_texto": None, "paso": "ablación"},
    "rf_e5_pca_sin_ubicacion":      {"familia": "rf", "bloques": ["arbol_sin_ubicacion", "e5_pca"], "grilla": {},
                                     "k_de": "rf_e5_pca", "sin_texto": "rf_sin_ubicacion", "paso": "ablación"},
    "ridge_tabular":                {"familia": "ridge", "bloques": ["lineal"],
                                     "grilla": GRILLA_ALPHA,
                                     "sin_texto": None, "paso": "tabular"},
    "ridge_tfidf":                  {"familia": "ridge", "bloques": ["lineal", "tfidf"],
                                     "grilla": GRILLA_ALPHA_TFIDF,
                                     "sin_texto": "ridge_tabular", "paso": "2 (A2)"},
    "mlp_tabular":                  {"familia": "mlp", "bloques": ["lineal"],
                                     "grilla": GRILLA_MLP,
                                     "sin_texto": None, "paso": "tabular"},
    "mlp_e5":                       {"familia": "mlp", "bloques": ["lineal", "e5"],
                                     "grilla": GRILLA_MLP,
                                     "sin_texto": "mlp_tabular", "paso": "3 (C1)"},
    # Misma red con las 50 componentes principales de los vectores (estandarizadas) en vez de los 768 valores
    "mlp_e5_pca":                   {"familia": "mlp", "bloques": ["lineal", "e5_pca_estandarizado"],
                                     "grilla": GRILLA_MLP,
                                     "sin_texto": "mlp_tabular", "paso": "3 (C1)"},
}
# Nombre de grupo para la importancia de variables de los bloques de texto
GRUPO_TEXTO = {"tfidf_pc": "tfidf_pca", "e5_pc": "e5_pca"}

# Gemelo: vivienda de entrenamiento con estas mismas columnas que una de prueba (igual que 05)
CLAVE_GEMELO = ["area", "precio_venta", "latitud", "longitud", "habitaciones"]


# ---------------------------------------------------------------------------
# Funciones auxiliares (las de métricas y CV son las mismas de 04)
# ---------------------------------------------------------------------------
def titulo(texto):
    print("\n" + "=" * 78)
    print(texto)
    print("=" * 78)


def guardar_tabla(tabla, nombre):
    DIR_TABLAS.mkdir(parents=True, exist_ok=True)
    ruta = DIR_TABLAS / nombre
    tabla.to_csv(ruta, index=False, encoding="utf-8")
    print(f"  -> {ruta.relative_to(RAIZ)}")


def requerir(ruta, script):
    if not ruta.exists():
        raise SystemExit(f"No existe {ruta.relative_to(RAIZ)}: corra antes 02_Scripts/{script}")


def rmse(y, pred):
    return root_mean_squared_error(y, pred)


def mape(y, pred):
    """MAPE en porcentaje."""
    return 100 * mean_absolute_percentage_error(y, pred)


def a_escala(y, escala):
    return np.log(y) if escala == "log" else y


def a_pesos(pred, escala):
    return np.exp(pred) if escala == "log" else pred


def puntaje_rmse_log(modelo, X, y_log):
    """-RMSE en pesos para cross_validate con el objetivo en log."""
    return -rmse(a_pesos(y_log, "log"), a_pesos(modelo.predict(X), "log"))


def puntaje_mape_log(modelo, X, y_log):
    """-MAPE (fracción) en pesos para cross_validate con el objetivo en log."""
    return -mean_absolute_percentage_error(a_pesos(y_log, "log"), a_pesos(modelo.predict(X), "log"))


def puntajes(escala):
    if escala == "log":
        return {"rmse": puntaje_rmse_log, "mape": puntaje_mape_log}
    return {"rmse": "neg_root_mean_squared_error", "mape": "neg_mean_absolute_percentage_error"}


def cv_en_pesos(modelo, X, y, escala):
    """cross_validate con el KFold fijo: RMSE y MAPE en pesos (media y desviación entre folds)."""
    cv = cross_validate(modelo, X, a_escala(y, escala), cv=KFOLD, scoring=puntajes(escala))
    return {"rmse_cv": -cv["test_rmse"].mean(), "rmse_cv_sd": cv["test_rmse"].std(),
            "mape_cv": -100 * cv["test_mape"].mean(), "mape_cv_sd": 100 * cv["test_mape"].std()}


def leer_hiperparametros(texto):
    """'max_features=0.5, min_samples_leaf=1' -> {'max_features': 0.5, 'min_samples_leaf': 1}."""
    params = {}
    for par in texto.split(","):
        clave, valor = par.strip().split("=")
        params[clave] = int(valor) if valor.isdigit() else float(valor)
    return params


def dummies(columnas_num, columnas_cat):
    """Matrices de entrenamiento y prueba con dummies definidas en entrenamiento (igual que matrices() de 04)."""
    X_tr = pd.get_dummies(train[columnas_num + columnas_cat], columns=columnas_cat, drop_first=True, dtype=float)
    X_pr = pd.get_dummies(prueba[columnas_num + columnas_cat], columns=columnas_cat, dtype=float).reindex(
        columns=X_tr.columns, fill_value=0)
    return X_tr, X_pr


def estandarizar(X_tr, X_pr):
    """Escalador ajustado con entrenamiento; la prueba solo se transforma."""
    escalador = StandardScaler().fit(X_tr)
    return (pd.DataFrame(escalador.transform(X_tr), columns=X_tr.columns),
            pd.DataFrame(escalador.transform(X_pr), columns=X_tr.columns))


def componentes(M_tr, M_pr, prefijo):
    """PCA ajustado con entrenamiento (N_COMPONENTES_MAX componentes); la prueba solo se transforma."""
    pca = PCA(n_components=N_COMPONENTES_MAX, svd_solver="arpack", random_state=SEMILLA).fit(M_tr)
    nombres = [f"{prefijo}{i + 1:02d}" for i in range(N_COMPONENTES_MAX)]
    return (pd.DataFrame(pca.transform(M_tr), columns=nombres), pd.DataFrame(pca.transform(M_pr), columns=nombres),
            pca.explained_variance_ratio_)


def armar(nombres_bloques, escala, k=None):
    """Une los bloques de variables (entrenamiento, prueba). Los bloques *_pca se cortan a k componentes.
    Si algún bloque es disperso (TF-IDF), el resultado es una matriz dispersa."""
    partes_tr, partes_pr = [], []
    for nombre in nombres_bloques:
        X_tr, X_pr = BLOQUES[(nombre, escala)] if (nombre, escala) in BLOQUES else BLOQUES[nombre]
        if nombre.endswith("_pca"):
            X_tr, X_pr = X_tr.iloc[:, :k], X_pr.iloc[:, :k]
        partes_tr.append(X_tr)
        partes_pr.append(X_pr)
    if any(sp.issparse(p) for p in partes_tr):
        return (sp.hstack([sp.csr_matrix(p.to_numpy() if hasattr(p, "to_numpy") else p) for p in partes_tr]).tocsr(),
                sp.hstack([sp.csr_matrix(p.to_numpy() if hasattr(p, "to_numpy") else p) for p in partes_pr]).tocsr())
    return pd.concat(partes_tr, axis=1), pd.concat(partes_pr, axis=1)


class MLPHibrido(BaseEstimator, RegressorMixin):
    """Red neuronal densa (MLP) en PyTorch para regresión, con la interfaz fit/predict de scikit-learn
    para poder usarla en cross_validate.

    - Capas ocultas con ReLU y dropout, salida lineal, pérdida MSE y optimizador Adam (weight decay = L2).
    - El objetivo se estandariza con la media y la desviación del entrenamiento que recibe fit (dentro de
      cada fold en la CV), y predict lo devuelve a su escala.
    - Parada temprana: separa al azar una fracción de lo que recibe fit como validación, guarda los pesos
      de la época con menor error de validación y para tras 'paciencia' épocas sin mejorar. Solo cuenta como
      mejora una caída del MSE de validación (objetivo estandarizado) mayor que 'mejora_minima': sin ese umbral,
      mejoras diminutas mantenían algunas redes entrenando hasta max_epocas.
    - Semilla fija (torch.manual_seed) en la inicialización, el orden de los minilotes y la validación.
    """

    def __init__(self, capas=MLP_CAPAS, dropout=0.1, weight_decay=1e-5, tasa_aprendizaje=1e-3, tamano_lote=256,
                 max_epocas=300, paciencia=20, fraccion_validacion=0.1, mejora_minima=1e-4, semilla=SEMILLA):
        self.capas = capas
        self.dropout = dropout
        self.weight_decay = weight_decay
        self.tasa_aprendizaje = tasa_aprendizaje
        self.tamano_lote = tamano_lote
        self.max_epocas = max_epocas
        self.paciencia = paciencia
        self.fraccion_validacion = fraccion_validacion
        self.mejora_minima = mejora_minima
        self.semilla = semilla

    def fit(self, X, y):
        X = np.asarray(X, dtype=np.float32)
        y = np.asarray(y, dtype=np.float64)
        torch.manual_seed(self.semilla)
        orden = np.random.default_rng(self.semilla).permutation(len(X))
        n_val = int(round(self.fraccion_validacion * len(X)))
        idx_val, idx_ent = orden[:n_val], orden[n_val:]
        # Estandarización del objetivo con la parte de entrenamiento (usa el precio: va dentro del fold)
        self.media_y_, self.sd_y_ = y[idx_ent].mean(), y[idx_ent].std()
        z = ((y - self.media_y_) / self.sd_y_).astype(np.float32)

        capas, entrada = [], X.shape[1]
        for n in self.capas:
            capas += [nn.Linear(entrada, n), nn.ReLU(), nn.Dropout(self.dropout)]
            entrada = n
        capas.append(nn.Linear(entrada, 1))
        self.red_ = nn.Sequential(*capas)
        optimizador = torch.optim.Adam(self.red_.parameters(), lr=self.tasa_aprendizaje,
                                       weight_decay=self.weight_decay)
        perdida = nn.MSELoss()
        X_ent, z_ent = torch.from_numpy(X[idx_ent]), torch.from_numpy(z[idx_ent])
        X_val, z_val = torch.from_numpy(X[idx_val]), torch.from_numpy(z[idx_val])
        generador = torch.Generator().manual_seed(self.semilla)

        mejor, mejor_estado, sin_mejora = np.inf, None, 0
        for epoca in range(self.max_epocas):
            self.red_.train()
            permutacion = torch.randperm(len(X_ent), generator=generador)
            for inicio in range(0, len(permutacion), self.tamano_lote):
                lote = permutacion[inicio:inicio + self.tamano_lote]
                optimizador.zero_grad()
                error = perdida(self.red_(X_ent[lote]).squeeze(1), z_ent[lote])
                error.backward()
                optimizador.step()
            self.red_.eval()
            with torch.no_grad():
                error_val = perdida(self.red_(X_val).squeeze(1), z_val).item()
            if error_val < mejor - self.mejora_minima:
                mejor, mejor_estado, sin_mejora = error_val, copy.deepcopy(self.red_.state_dict()), 0
                self.mejor_epoca_ = epoca + 1
            else:
                sin_mejora += 1
                if sin_mejora >= self.paciencia:
                    break
        self.red_.load_state_dict(mejor_estado)
        self.epocas_ = epoca + 1
        return self

    def predict(self, X):
        self.red_.eval()
        with torch.no_grad():
            z = self.red_(torch.from_numpy(np.asarray(X, dtype=np.float32))).squeeze(1).numpy()
        return z.astype(np.float64) * self.sd_y_ + self.media_y_


def crear_modelo(familia, escala, params):
    if familia == "rf":
        return RandomForestRegressor(n_estimators=300, random_state=SEMILLA, n_jobs=-1, **HIPER_RF[escala])
    if familia == "ridge":
        return Ridge(**params)
    return MLPHibrido(**MLP_FIJOS, **params)


def grupo_variable(columna, variables):
    """Variable de la base (o bloque de texto) de la que sale una columna de la matriz."""
    for prefijo, grupo in GRUPO_TEXTO.items():
        if columna.startswith(prefijo):
            return grupo
    if columna in variables:
        return columna
    return next(v for v in variables if columna.startswith(v + "_"))


# ---------------------------------------------------------------------------
# 1. Lectura
# ---------------------------------------------------------------------------
titulo("1. LECTURA")
requerir(RUTA_PARTICION, "03_particion_muestra.py")
requerir(RUTA_HIPERPARAMETROS, "04_estimacion_modelos.py")
requerir(RUTA_TEXTO, "09_texto_limpieza.py")
requerir(RUTA_EMBEDDINGS, "10_texto_embeddings.py")
df = pd.read_csv(RUTA_LIMPIA)
df = df.merge(pd.read_csv(RUTA_PARTICION), on="codigo", how="left", validate="one_to_one")
texto = pd.read_csv(RUTA_TEXTO, usecols=["codigo", "descripcion_limpia"] + VARS_PALABRAS_CLAVE)
df = df.merge(texto, on="codigo", how="left", validate="one_to_one")
if df["conjunto"].isna().any() or df["descripcion_limpia"].isna().any():
    raise SystemExit("Hay viviendas sin partición o sin texto limpio: corra de nuevo 03 y 09")
guardado = np.load(RUTA_EMBEDDINGS, allow_pickle=False)
vectores = pd.DataFrame(guardado["vectores"].astype(np.float32), index=guardado["codigo"])
vectores = vectores.reindex(df["codigo"].astype(str))
if vectores.isna().any().any():
    raise SystemExit("Hay viviendas sin vector: corra de nuevo 02_Scripts/10_texto_embeddings.py")
print(f"Base limpia: {len(df):,} viviendas; vectores de {guardado['modelo']} ({vectores.shape[1]} dimensiones)")
print(df["conjunto"].value_counts().to_string())

# ---------------------------------------------------------------------------
# 2. Bloques de variables (todo lo aprendido se ajusta con entrenamiento)
# ---------------------------------------------------------------------------
titulo("2. BLOQUES DE VARIABLES")
df[NUM_EXTRA] = df[NUM_EXTRA].astype(float)  # las binarias entran como 0/1
es_train = (df["conjunto"] == "entrenamiento").to_numpy()
train = df[es_train].reset_index(drop=True)
prueba = df[~es_train].reset_index(drop=True)
y_train, y_prueba = train[OBJETIVO], prueba[OBJETIVO]
print(f"Entrenamiento: {len(train):,} | Prueba: {len(prueba):,}")

BLOQUES = {}
# Árboles: matriz de 04 (estrato ordinal, área en niveles), y sin estrato ni localidad
BLOQUES["arbol"] = dummies(NUM_ARBOL, CAT_ARBOL)
columnas_sensibles = [c for c in BLOQUES["arbol"][0].columns
                      if c == "estrato" or c.startswith("localidad_")]
BLOQUES["arbol_sin_ubicacion"] = tuple(X.drop(columns=columnas_sensibles) for X in BLOQUES["arbol"])
# Lineal completo de 04, estandarizado (Ridge y MLP); con el objetivo en log, el área entra en log
for escala in ESCALAS:
    X_tr, X_pr = dummies(NUM_BASE + NUM_EXTRA, CAT_LINEAL)
    if escala == "log":
        for X_ in (X_tr, X_pr):
            X_["area"] = np.log(X_["area"])
    BLOQUES[("lineal", escala)] = estandarizar(X_tr, X_pr)
# Paso 1: palabras clave (reglas fijas de 09)
BLOQUES["palabras_clave"] = (train[VARS_PALABRAS_CLAVE].astype(float), prueba[VARS_PALABRAS_CLAVE].astype(float))
# Paso 2: TF-IDF con vocabulario e IDF de entrenamiento, y su PCA
texto_tr = train["descripcion_limpia"].str.replace(MARCADORES, " ", regex=True)
texto_pr = prueba["descripcion_limpia"].str.replace(MARCADORES, " ", regex=True)
tfidf = TfidfVectorizer(**TFIDF).fit(texto_tr)
BLOQUES["tfidf"] = (tfidf.transform(texto_tr), tfidf.transform(texto_pr))
*BLOQUES["tfidf_pca"], varianza_tfidf = componentes(*BLOQUES["tfidf"], "tfidf_pc")
print(f"TF-IDF: {len(tfidf.vocabulary_):,} términos (palabras y pares con min_df={TFIDF['min_df']}); "
      f"PCA de {N_COMPONENTES_MAX} componentes explica {100 * varianza_tfidf.sum():.1f}% de la varianza")
# Paso 3: vectores del Transformer (estandarizados para la red) y su PCA
e5_tr, e5_pr = vectores[es_train].reset_index(drop=True), vectores[~es_train].reset_index(drop=True)
e5_tr.columns = e5_pr.columns = [f"e5_{i:03d}" for i in range(e5_tr.shape[1])]
BLOQUES["e5"] = estandarizar(e5_tr, e5_pr)
*BLOQUES["e5_pca"], varianza_e5 = componentes(e5_tr, e5_pr, "e5_pc")
BLOQUES["e5_pca_estandarizado"] = estandarizar(*BLOQUES["e5_pca"])
print(f"Vectores e5: PCA de {N_COMPONENTES_MAX} componentes explica {100 * varianza_e5.sum():.1f}% de la varianza")
for nombre, (X_tr, X_pr) in [(k, v) for k, v in BLOQUES.items()]:
    assert X_tr.shape[1] == X_pr.shape[1] and X_pr.shape[0] == len(prueba), nombre

KFOLD = KFold(n_splits=N_FOLDS, shuffle=True, random_state=SEMILLA)
hiper_04 = pd.read_csv(RUTA_HIPERPARAMETROS).query("modelo == 'random_forest'").set_index("escala")
HIPER_RF = {e: leer_hiperparametros(hiper_04.loc[e, "hiperparametros"]) for e in ESCALAS}

# ---------------------------------------------------------------------------
# 3. Estimación con validación cruzada (solo entrenamiento)
# ---------------------------------------------------------------------------
titulo("3. ESTIMACIÓN CON VALIDACIÓN CRUZADA (SOLO ENTRENAMIENTO)")
ajustados, cv_metricas, elegidos, matrices, segundos = {}, {}, {}, {}, {}
filas_grilla = []
for escala in ESCALAS:
    print(f"\n--- Escala del objetivo: {escala} | Random Forest con los hiperparámetros de 04: {HIPER_RF[escala]} ---")
    for nombre, spec in VARIANTES.items():
        t0 = time.time()
        grilla = spec["grilla"]
        combinaciones = [dict(zip(grilla, v)) for v in itertools.product(*grilla.values())] or [{}]
        if "k_de" in spec:
            combinaciones = [{"k": elegidos[(spec["k_de"], escala)]["k"]}]
        resultados = []
        for params in combinaciones:
            t1 = time.time()
            params_modelo = {p: v for p, v in params.items() if p != "k"}
            X_tr, _ = armar(spec["bloques"], escala, params.get("k"))
            cv = cv_en_pesos(crear_modelo(spec["familia"], escala, params_modelo), X_tr, y_train, escala)
            resultados.append((params, cv))
            filas_grilla.append({"modelo": nombre, "escala": escala,
                                 "parametros": ", ".join(f"{p}={v}" for p, v in params.items()) or "ninguno",
                                 **cv, "segundos": time.time() - t1})
        params, cv = min(resultados, key=lambda r: r[1]["rmse_cv"])
        # Aviso si el elegido está en el borde de una grilla numérica
        for p, valores in grilla.items():
            if len(valores) > 1 and params[p] in (min(valores), max(valores)):
                print(f"  AVISO: {nombre} eligió {p}={params[p]}, en el borde de la grilla {valores}", flush=True)
        X_tr, X_pr = armar(spec["bloques"], escala, params.get("k"))
        modelo = crear_modelo(spec["familia"], escala, {p: v for p, v in params.items() if p != "k"})
        ajustados[(nombre, escala)] = modelo.fit(X_tr, a_escala(y_train, escala))
        cv_metricas[(nombre, escala)], elegidos[(nombre, escala)] = cv, params
        matrices[(nombre, escala)] = (X_tr, X_pr)
        segundos[(nombre, escala)] = time.time() - t0
        extra = f", épocas {modelo.mejor_epoca_}" if spec["familia"] == "mlp" else ""
        print(f"  {nombre}: {params or 'sin grilla'}{extra} | RMSE CV {cv['rmse_cv'] / 1e6:,.1f} M "
              f"({segundos[(nombre, escala)] / 60:.1f} min)", flush=True)

# ---------------------------------------------------------------------------
# 4. Evaluación: entrenamiento, CV y prueba. La prueba se usa solo aquí.
# ---------------------------------------------------------------------------
titulo("4. EVALUACIÓN EN ENTRENAMIENTO, VALIDACIÓN CRUZADA Y PRUEBA")
predicciones = prueba[["codigo", "estrato", "localidad", "barrio", OBJETIVO]].copy()
filas = []
for escala in ESCALAS:
    for nombre, spec in VARIANTES.items():
        modelo = ajustados[(nombre, escala)]
        X_tr, X_pr = matrices[(nombre, escala)]
        pred_train = a_pesos(modelo.predict(X_tr), escala)
        pred_prueba = a_pesos(modelo.predict(X_pr), escala)
        assert np.isfinite(pred_prueba).all(), f"{nombre} ({escala}) tiene predicciones no finitas"
        predicciones[f"pred_{nombre}_{escala}"] = pred_prueba
        params = dict(elegidos[(nombre, escala)])
        if spec["familia"] == "rf":
            params = {**HIPER_RF[escala], **params}
        if spec["familia"] == "mlp":
            params["epocas"] = modelo.mejor_epoca_
        cv = cv_metricas[(nombre, escala)]
        filas.append({"modelo": nombre, "escala": escala, "familia": spec["familia"], "paso": spec["paso"],
                      "sin_texto": spec["sin_texto"], "n_columnas": X_tr.shape[1],
                      "hiperparametros": ", ".join(f"{p}={v}" for p, v in params.items()) or "ninguno",
                      "rmse_train": rmse(y_train, pred_train), "rmse_cv": cv["rmse_cv"], "rmse_cv_sd": cv["rmse_cv_sd"],
                      "rmse_prueba": rmse(y_prueba, pred_prueba),
                      "mape_train": mape(y_train, pred_train), "mape_cv": cv["mape_cv"], "mape_cv_sd": cv["mape_cv_sd"],
                      "mape_prueba": mape(y_prueba, pred_prueba),
                      "n_pred_negativas_prueba": int((pred_prueba < 0).sum()),
                      "segundos_estimacion": segundos[(nombre, escala)]})
metricas = pd.DataFrame(filas)

# Control: el Random Forest tabular reproduce las métricas de 04
metricas_04 = pd.read_csv(RUTA_METRICAS_04)
COLUMNAS_METRICAS = ["rmse_train", "rmse_cv", "rmse_prueba", "mape_train", "mape_cv", "mape_prueba"]
control = metricas.query("modelo == 'random_forest'").merge(
    metricas_04.query("modelo == 'random_forest'"), on="escala", suffixes=("", "_04"))
dif_control = max((control[c] / control[c + "_04"] - 1).abs().max() for c in COLUMNAS_METRICAS)
print(f"Control contra 04 (Random Forest tabular): diferencia relativa máxima {dif_control:.1e}")
assert dif_control < TOLERANCIA_CONTROL, "El Random Forest tabular no reproduce 04: revise la matriz o los datos"

# Línea base leída de 04 (misma partición), para reportar todo junto a ella
base = metricas_04.query("modelo == 'lineal_base'")[["modelo", "escala"] + COLUMNAS_METRICAS
                                                     + ["rmse_cv_sd", "mape_cv_sd", "n_pred_negativas_prueba"]]
base = base.assign(familia="lineal", paso="línea base", hiperparametros="ninguno")
metricas = pd.concat([base, metricas], ignore_index=True)
metricas["dif_rmse_prueba_vs_cv_pct"] = 100 * (metricas["rmse_prueba"] / metricas["rmse_cv"] - 1)


def cambio_frente_a(referencia, sufijo):
    """Cambio de RMSE (%) y MAPE (puntos) de cada fila frente a la fila 'referencia' de la misma escala."""
    clave = metricas[["escala"]].assign(modelo=referencia)
    ref = clave.merge(metricas, on=["escala", "modelo"], how="left").set_index(metricas.index)
    for c in ["rmse_cv", "rmse_prueba"]:
        metricas[f"cambio_{c}_vs_{sufijo}_pct"] = 100 * (metricas[c] / ref[c] - 1)
    for c in ["mape_cv", "mape_prueba"]:
        metricas[f"cambio_{c}_vs_{sufijo}_pp"] = metricas[c] - ref[c]


cambio_frente_a("lineal_base", "base")
cambio_frente_a(pd.Series("random_forest", index=metricas.index), "rf_tabular")
cambio_frente_a(metricas["sin_texto"], "sin_texto")
orden_modelos = {m: i for i, m in enumerate(["lineal_base"] + list(VARIANTES))}
metricas = metricas.sort_values(["escala", "modelo"], key=lambda s: s.map(orden_modelos) if s.name == "modelo"
                                else s, ignore_index=True)

vista = metricas[["modelo", "escala", "rmse_train", "rmse_cv", "rmse_prueba", "mape_cv", "mape_prueba",
                  "cambio_rmse_cv_vs_sin_texto_pct", "cambio_rmse_prueba_vs_sin_texto_pct",
                  "cambio_rmse_cv_vs_rf_tabular_pct"]].copy()
for c in ["rmse_train", "rmse_cv", "rmse_prueba"]:
    vista[c] = (vista[c] / 1e6).round(1)
with pd.option_context("display.width", 250, "display.max_columns", None):
    print("RMSE en millones de COP; MAPE en %; cambios de RMSE en % frente a la pareja sin texto y al RF tabular")
    print(vista.round(2).to_string(index=False))

# ---------------------------------------------------------------------------
# 5. Importancia de variables, errores por grupo y sensibilidad a duplicados
# ---------------------------------------------------------------------------
titulo("5. IMPORTANCIA, ERRORES POR GRUPO Y SENSIBILIDAD")
VARS_GRUPO = NUM_ARBOL + CAT_ARBOL + VARS_PALABRAS_CLAVE
importancias = []
for escala in ESCALAS:
    for nombre, spec in VARIANTES.items():
        if spec["familia"] != "rf":
            continue
        t = pd.DataFrame({"columna": matrices[(nombre, escala)][0].columns,
                          "importancia": ajustados[(nombre, escala)].feature_importances_})
        t["variable"] = [grupo_variable(c, VARS_GRUPO) for c in t["columna"]]
        t = t.groupby("variable", as_index=False)["importancia"].sum()
        t["importancia_pct"] = 100 * t["importancia"] / t["importancia"].sum()
        t["de_texto"] = t["variable"].isin(VARS_PALABRAS_CLAVE + list(GRUPO_TEXTO.values()))
        t.insert(0, "escala", escala)
        t.insert(0, "modelo", nombre)
        importancias.append(t.sort_values("importancia_pct", ascending=False))
importancias = pd.concat(importancias, ignore_index=True)
print("Importancia de las variables de texto (% del total, dummies y componentes sumados):")
print(importancias[importancias["de_texto"]].groupby(["modelo", "escala"])["importancia_pct"].sum()
      .unstack().round(1).to_string())


def errores_por_grupo(grupo):
    filas = []
    y = predicciones[OBJETIVO]
    for escala in ESCALAS:
        for nombre in VARIANTES:
            pred = predicciones[f"pred_{nombre}_{escala}"]
            error_rel = 100 * (pred - y) / y
            for valor, idx in predicciones.groupby(grupo).groups.items():
                filas.append({
                    "modelo": nombre, "escala": escala, grupo: valor, "n_prueba": len(idx),
                    "rmse": rmse(y[idx], pred[idx]), "mape": mape(y[idx], pred[idx]),
                    # Con signo: positivo = sobrevalora, negativo = subvalora
                    "error_relativo_medio_pct": error_rel[idx].mean(),
                    "n_prueba_menor_minimo": len(idx) < N_MINIMO_GRUPO_PRUEBA,
                })
    return pd.DataFrame(filas)


err_estrato = errores_por_grupo("estrato")
err_localidad = errores_por_grupo("localidad")
with pd.option_context("display.width", 250, "display.max_columns", None):
    for escala in ESCALAS:
        print(f"\nMAPE (%) en prueba por estrato, objetivo en {escala}:")
        print(err_estrato.query("escala == @escala").pivot_table(index="estrato", columns="modelo", values="mape")
              [list(VARIANTES)].round(1).to_string())

# Sensibilidad: viviendas de prueba con descripción limpia idéntica a una de entrenamiento, y gemelos
duplicada = prueba["descripcion_limpia"].isin(set(train["descripcion_limpia"])).to_numpy()
claves_entrenamiento = train[CLAVE_GEMELO].drop_duplicates().assign(tiene_gemelo=True)
gemelo = prueba[CLAVE_GEMELO].merge(claves_entrenamiento, on=CLAVE_GEMELO, how="left")["tiene_gemelo"]
gemelo = gemelo.fillna(False).astype(bool).to_numpy()
print(f"\nViviendas de prueba con descripción idéntica en entrenamiento: {int(duplicada.sum()):,}; "
      f"con gemelo: {int(gemelo.sum()):,}; con alguno de los dos: {int((duplicada | gemelo).sum()):,}")
subconjuntos = {"todas": np.ones(len(prueba), dtype=bool), "sin_descripcion_duplicada": ~duplicada,
                "sin_gemelo": ~gemelo, "sin_duplicada_ni_gemelo": ~(duplicada | gemelo)}
filas = []
for escala in ESCALAS:
    for nombre in VARIANTES:
        pred = predicciones[f"pred_{nombre}_{escala}"]
        for sub, mascara in subconjuntos.items():
            filas.append({"modelo": nombre, "escala": escala, "subconjunto": sub, "n_prueba": int(mascara.sum()),
                          "rmse": rmse(y_prueba[mascara], pred[mascara]), "mape": mape(y_prueba[mascara], pred[mascara])})
sensibilidad = pd.DataFrame(filas)
with pd.option_context("display.width", 250):
    print("RMSE de prueba (millones de COP) por subconjunto:")
    print(sensibilidad.pivot_table(index=["escala", "modelo"], columns="subconjunto", values="rmse", sort=False)
          .div(1e6).round(1)[list(subconjuntos)].to_string())

# ---------------------------------------------------------------------------
# 6. Guardado
# ---------------------------------------------------------------------------
titulo("6. GUARDADO")
guardar_tabla(metricas, "11_metricas_modelos_texto.csv")
guardar_tabla(pd.DataFrame(filas_grilla), "11_cv_grillas.csv")
guardar_tabla(importancias, "11_importancia_variables.csv")
guardar_tabla(err_estrato, "11_errores_por_estrato.csv")
guardar_tabla(err_localidad, "11_errores_por_localidad.csv")
guardar_tabla(sensibilidad, "11_sensibilidad_duplicados.csv")
guardar_tabla(predicciones, "11_predicciones_prueba.csv")
print(f"\nTiempo total de estimación: {sum(segundos.values()) / 60:.1f} min")
