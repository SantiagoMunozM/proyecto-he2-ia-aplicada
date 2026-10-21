"""
06_figuras_presentacion.py

Figuras de la presentación de avance, con la paleta de las diapositivas
(fondo azul marino, celestes y un acento naranja). No estima nada: solo lee las
tablas que ya produjeron 04_estimacion_modelos.py y 05_analisis_errores_impacto.py
y las dibuja de nuevo para que se lean sobre el fondo de Canva. Las figuras de
04_ y 05_ (fondo claro) se conservan para el entregable de GitHub.

Insumos:
    03_Resultados/Tablas/04_metricas_modelos.csv
    03_Resultados/Tablas/04_importancia_variables.csv
    03_Resultados/Tablas/05_errores_por_estrato.csv
    03_Resultados/Tablas/05_comparacion_por_localidad.csv

Salidas (03_Resultados/Figuras/):
    06_tabla_metricas.png
    06_rmse_cv_prueba.png
    06_importancia_rf.png
    06_rmse_train_cv_prueba.png
    06_costo_estrato.png
    06_mape_estrato.png
    06_sesgo_estrato.png
    06_sesgo_localidad.png

Se corre desde la raíz del repo: python 02_Scripts/06_figuras_presentacion.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Rutas (ancladas a la raíz del proyecto, que es la carpeta padre de 02_Scripts)
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
TABLAS = RAIZ / "03_Resultados" / "Tablas"
FIGURAS = RAIZ / "03_Resultados" / "Figuras"
FIGURAS.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Paleta de la presentación (colores tomados de las diapositivas de Canva)
# ---------------------------------------------------------------------------
FONDO = "#051d40"
TINTA = "#ffffff"
TINTA_SECUNDARIA = "#b9cde6"
GRILLA = "#1d3b68"
EJE = "#56718f"
AZUL = "#56aeff"      # línea base / escala log
AZUL_MEDIO = "#145da0"
NARANJA = "#ffa94d"   # Random Forest / escala niveles
COLOR_BASE, COLOR_RF = AZUL, NARANJA

MODELOS = ["lineal_base", "lineal_completo", "lasso", "random_forest", "xgboost"]
NOMBRES = {"lineal_base": "Lineal (base)", "lineal_completo": "Lineal (completo)", "lasso": "Lasso",
           "random_forest": "Random Forest", "xgboost": "XGBoost"}
ESCALAS = ["log", "niveles"]
TITULO_ESCALA = {"log": "Objetivo en log(precio)", "niveles": "Objetivo en niveles"}
UMBRAL_GRUPO = 30  # viviendas mínimas en prueba para interpretar un grupo (decisión del script 05)

plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 15, "text.color": TINTA,
    "axes.labelcolor": TINTA_SECUNDARIA, "figure.facecolor": FONDO, "axes.facecolor": FONDO,
    "axes.edgecolor": EJE, "xtick.color": TINTA_SECUNDARIA, "ytick.color": TINTA,
    "legend.facecolor": FONDO, "legend.edgecolor": EJE, "legend.labelcolor": TINTA,
})


def guardar(fig, nombre):
    """Guarda la figura con el fondo de la diapositiva y la cierra."""
    fig.savefig(FIGURAS / nombre, dpi=200, bbox_inches="tight", facecolor=FONDO)
    plt.close(fig)


def estilo_ejes(ax, eje_grilla="x"):
    """Quita bordes innecesarios y deja una grilla tenue."""
    for lado in ["top", "right", "left"]:
        ax.spines[lado].set_visible(False)
    ax.tick_params(length=0)
    ax.grid(axis=eje_grilla, color=GRILLA, linewidth=0.8)
    ax.set_axisbelow(True)


# ---------------------------------------------------------------------------
# Lectura de tablas
# ---------------------------------------------------------------------------
metricas = pd.read_csv(TABLAS / "04_metricas_modelos.csv")
importancia = pd.read_csv(TABLAS / "04_importancia_variables.csv")
estratos = pd.read_csv(TABLAS / "05_errores_por_estrato.csv")
localidades = pd.read_csv(TABLAS / "05_comparacion_por_localidad.csv")

estratos = estratos[estratos["estrato"].astype(str).str.isdigit()].copy()
estratos["estrato"] = estratos["estrato"].astype(int)
ESTRATOS = sorted(estratos["estrato"].unique())
N_ESTRATO = estratos.drop_duplicates("estrato").set_index("estrato")["n_prueba"]
ETIQ_ESTRATO = [f"{e}\nn={N_ESTRATO[e]:,}" + ("*" if N_ESTRATO[e] < UMBRAL_GRUPO else "") for e in ESTRATOS]


def fila(modelo, escala):
    return metricas[(metricas["modelo"] == modelo) & (metricas["escala"] == escala)].iloc[0]


# ---------------------------------------------------------------------------
# 1. Tabla de métricas (RMSE en millones de COP, MAPE en %)
# ---------------------------------------------------------------------------
# Modelo seleccionado: el de menor RMSE de CV (solo entrenamiento), no de prueba.
elegido = metricas.loc[metricas["rmse_cv"].idxmin(), ["modelo", "escala"]].tolist()

columnas = ["Modelo", "Objetivo", "RMSE CV", "RMSE prueba", "MAPE CV", "MAPE prueba"]
filas = []
for escala in ESCALAS:
    for modelo in MODELOS:
        f = fila(modelo, escala)
        filas.append([NOMBRES[modelo], "log" if escala == "log" else "niveles",
                      f"{f['rmse_cv'] / 1e6:,.0f}", f"{f['rmse_prueba'] / 1e6:,.0f}",
                      f"{f['mape_cv']:.1f}%", f"{f['mape_prueba']:.1f}%"])

fig, ax = plt.subplots(figsize=(14, 7.4))
ax.axis("off")
x_col = [0.0, 0.27, 0.52, 0.69, 0.82, 1.0]
alto_fila = 1 / (len(filas) + 1.4)
for j, nombre in enumerate(columnas):
    ax.text(x_col[j], 1 - alto_fila * 0.5, nombre, ha="left" if j < 2 else "right", va="center",
            fontsize=15, fontweight="bold", color=AZUL, transform=ax.transAxes)
ax.plot([0, 1], [1 - alto_fila, 1 - alto_fila], color=EJE, linewidth=1.2, transform=ax.transAxes)
for i, valores in enumerate(filas):
    y = 1 - alto_fila * (i + 1.5) - (alto_fila * 0.3 if i >= len(MODELOS) else 0)
    es_elegido = [valores[0], valores[1]] == [NOMBRES[elegido[0]], elegido[1]]
    es_base = valores[0] == NOMBRES["lineal_base"]
    color = NARANJA if es_elegido else (TINTA_SECUNDARIA if es_base else TINTA)
    if es_elegido:
        ax.add_patch(plt.Rectangle((-0.01, y - alto_fila * 0.5), 1.02, alto_fila, color=AZUL_MEDIO, alpha=0.55,
                                   transform=ax.transAxes, zorder=0))
    for j, texto in enumerate(valores):
        ax.text(x_col[j], y, texto, ha="left" if j < 2 else "right", va="center", fontsize=14,
                color=color, fontweight="bold" if es_elegido else "normal", transform=ax.transAxes)
ax.text(0, -0.03, "RMSE en millones de COP. CV: 5 folds sobre entrenamiento. En naranja, el menor RMSE de CV; "
        "en gris, la línea base.", ha="left", va="top", fontsize=12, color=TINTA_SECUNDARIA, transform=ax.transAxes)
guardar(fig, "06_tabla_metricas.png")

# ---------------------------------------------------------------------------
# 2. RMSE de CV y de prueba por modelo
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(14, 6.2), sharex=True)
y = np.arange(len(MODELOS))[::-1]
for ax, escala in zip(axes, ESCALAS):
    cv = [fila(m, escala)["rmse_cv"] / 1e6 for m in MODELOS]
    prueba = [fila(m, escala)["rmse_prueba"] / 1e6 for m in MODELOS]
    ax.barh(y + 0.2, cv, height=0.38, color=AZUL, label="Validación cruzada")
    ax.barh(y - 0.2, prueba, height=0.38, color=NARANJA, label="Prueba")
    for yy, v in zip(y + 0.2, cv):
        ax.text(v + 6, yy, f"{v:,.0f}", va="center", fontsize=12, color=TINTA_SECUNDARIA)
    for yy, v in zip(y - 0.2, prueba):
        ax.text(v + 6, yy, f"{v:,.0f}", va="center", fontsize=12, color=TINTA_SECUNDARIA)
    ax.set_yticks(y, [NOMBRES[m] for m in MODELOS])
    ax.set_title(TITULO_ESCALA[escala], loc="left", fontsize=16, color=TINTA)
    ax.set_xlabel("RMSE (millones de COP)")
    estilo_ejes(ax)
handles, etiquetas = axes[0].get_legend_handles_labels()
fig.legend(handles, etiquetas, loc="upper right", ncol=2, fontsize=13, bbox_to_anchor=(1, 1.0))
fig.tight_layout(rect=[0, 0, 1, 0.93])
guardar(fig, "06_rmse_cv_prueba.png")

# ---------------------------------------------------------------------------
# 3. Importancia de variables del Random Forest (dummies sumadas por variable)
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(14, 6.2), sharex=True)
for ax, escala in zip(axes, ESCALAS):
    sub = (importancia[(importancia["modelo"] == "random_forest") & (importancia["escala"] == escala)]
           .sort_values("importancia_pct", ascending=False).head(8).iloc[::-1])
    ax.barh(np.arange(len(sub)), sub["importancia_pct"], color=COLOR_RF if escala == "niveles" else AZUL, height=0.65)
    for yy, v in enumerate(sub["importancia_pct"]):
        ax.text(v + 0.7, yy, f"{v:.1f}%", va="center", fontsize=12, color=TINTA_SECUNDARIA)
    ax.set_yticks(np.arange(len(sub)), sub["variable"])
    ax.set_title(TITULO_ESCALA[escala], loc="left", fontsize=16, color=TINTA)
    ax.set_xlabel("Importancia (% del total)")
    estilo_ejes(ax)
fig.tight_layout()
guardar(fig, "06_importancia_rf.png")

# ---------------------------------------------------------------------------
# 4. RMSE en entrenamiento, CV y prueba (descriptivo): línea base, RF y XGBoost
# ---------------------------------------------------------------------------
seleccion = ["lineal_base", "random_forest", "xgboost"]
fig, axes = plt.subplots(1, 2, figsize=(14, 6.2), sharey=True)
ancho = 0.26
x = np.arange(len(seleccion))
colores = [AZUL_MEDIO, AZUL, NARANJA]
for ax, escala in zip(axes, ESCALAS):
    for k, (col, etiqueta) in enumerate([("rmse_train", "Entrenamiento"), ("rmse_cv", "CV"), ("rmse_prueba", "Prueba")]):
        valores = [fila(m, escala)[col] / 1e6 for m in seleccion]
        ax.bar(x + (k - 1) * ancho, valores, width=ancho, color=colores[k], label=etiqueta)
        for xx, v in zip(x + (k - 1) * ancho, valores):
            ax.text(xx, v + 6, f"{v:,.0f}", ha="center", fontsize=11, color=TINTA_SECUNDARIA)
    ax.set_xticks(x, [NOMBRES[m] for m in seleccion])
    ax.set_title(TITULO_ESCALA[escala], loc="left", fontsize=16, color=TINTA)
    estilo_ejes(ax, "y")
axes[0].set_ylabel("RMSE (millones de COP)")
axes[0].legend(loc="upper right", fontsize=13)
fig.tight_layout()
guardar(fig, "06_rmse_train_cv_prueba.png")


# ---------------------------------------------------------------------------
# 5-7. Por estrato: costo esperado, MAPE y sesgo (línea base frente a Random Forest)
# ---------------------------------------------------------------------------
def por_estrato(modelo, escala, columna):
    sub = estratos[(estratos["modelo"] == modelo) & (estratos["escala"] == escala)].set_index("estrato")
    return sub.loc[ESTRATOS, columna].to_numpy()


def barras_estrato(nombre_figura, columna, ylabel, signo=1, bajo=None, simetrico=False):
    """Barras agrupadas por estrato (línea base y Random Forest), un panel por escala.
    `bajo` es una segunda columna que se dibuja hacia abajo (costo del vendedor)."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6.2), sharey=True)
    x = np.arange(len(ESTRATOS))
    for ax, escala in zip(axes, ESCALAS):
        for k, (modelo, color) in enumerate([("lineal_base", COLOR_BASE), ("random_forest", COLOR_RF)]):
            posicion = x + (k - 0.5) * 0.38
            ax.bar(posicion, signo * por_estrato(modelo, escala, columna), width=0.36, color=color,
                   label=NOMBRES[modelo])
            if bajo:
                ax.bar(posicion, -por_estrato(modelo, escala, bajo), width=0.36, color=color)
        ax.axhline(0, color=EJE, linewidth=1)
        ax.set_xticks(x, ETIQ_ESTRATO)
        ax.set_title(TITULO_ESCALA[escala], loc="left", fontsize=16, color=TINTA)
        ax.set_xlabel("Estrato (n en prueba; * = menos de 30 viviendas)")
        estilo_ejes(ax, "y")
    axes[0].set_ylabel(ylabel)
    axes[0].legend(loc="upper right", fontsize=13)
    fig.tight_layout()
    guardar(fig, nombre_figura)


barras_estrato("06_costo_estrato.png", "sobrecosto_pct_precio_mediano",
               "% del precio mediano del estrato\n↑ comprador paga de más · ↓ vendedor pierde",
               bajo="perdida_pct_precio_mediano")
barras_estrato("06_mape_estrato.png", "mape", "MAPE en prueba (%)")
barras_estrato("06_sesgo_estrato.png", "sesgo_rel_medio_pct",
               "Error relativo medio con signo (%)\n+ sobrevalorada · − subvalorada")

# ---------------------------------------------------------------------------
# 8. Sesgo por localidad (solo localidades con al menos 30 viviendas en prueba)
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(14, 7.4), sharey=True)
for ax, escala in zip(axes, ESCALAS):
    sub = localidades[(localidades["escala"] == escala) & (localidades["n_prueba"] >= UMBRAL_GRUPO)]
    sub = sub.sort_values("sesgo_rel_medio_pct_rf").reset_index(drop=True)
    for i, r in sub.iterrows():
        ax.plot([r["sesgo_rel_medio_pct_base"], r["sesgo_rel_medio_pct_rf"]], [i, i], color=EJE, linewidth=1.2, zorder=1)
    ax.scatter(sub["sesgo_rel_medio_pct_base"], sub.index, s=70, color=COLOR_BASE, zorder=3, label=NOMBRES["lineal_base"])
    ax.scatter(sub["sesgo_rel_medio_pct_rf"], sub.index, s=70, color=COLOR_RF, zorder=3, label=NOMBRES["random_forest"])
    ax.axvline(0, color=TINTA_SECUNDARIA, linewidth=1)
    ax.set_yticks(sub.index, [f"{l.title()} (n={n:,})" for l, n in zip(sub["localidad"], sub["n_prueba"])], fontsize=12)
    ax.set_title(TITULO_ESCALA[escala], loc="left", fontsize=16, color=TINTA)
    ax.set_xlabel("Error relativo medio con signo (%)\n+ sobrevalorada · − subvalorada")
    estilo_ejes(ax)
axes[0].legend(loc="lower right", fontsize=13)
fig.tight_layout()
guardar(fig, "06_sesgo_localidad.png")

print(f"Figuras escritas en {FIGURAS.relative_to(RAIZ)}:")
for ruta in sorted(FIGURAS.glob("06_*.png")):
    print(f"  {ruta.name}")
