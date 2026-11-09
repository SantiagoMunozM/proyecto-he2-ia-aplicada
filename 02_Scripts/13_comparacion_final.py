"""
13_comparacion_final.py

Comparación final de todos los modelos (paso 5 de la sección 7 de
05_Notas/alternativas_aprendizaje_profundo_descripcion.md): modelos clásicos de 04 y
variantes con texto de 11, todas contra la línea base lineal, con el resumen de sesgos por
estrato y localidad para la sección de IA responsable. No estima nada: solo lee tablas.

El número 12 queda para 12_texto_llm.py (paso 4, extracción con LLM). Si ese script existe y
deja sus tablas 12_metricas_modelos_llm.csv, 12_errores_por_estrato.csv y
12_errores_por_localidad.csv con las mismas columnas que las de 11, entran aquí sin cambios.

Insumos (03_Resultados/Tablas/):
    04_metricas_modelos.csv, 04_errores_por_estrato.csv, 04_errores_por_localidad.csv
    11_metricas_modelos_texto.csv, 11_errores_por_estrato.csv, 11_errores_por_localidad.csv
    12_* (opcionales, ver arriba)

Salidas:
    03_Resultados/Tablas/13_comparacion_modelos.csv   métricas de todas las variantes y cambios
                                                      frente a la base, al RF tabular y a la
                                                      pareja sin texto
    03_Resultados/Tablas/13_errores_por_estrato.csv   errores de prueba por estrato, todos los modelos
    03_Resultados/Tablas/13_resumen_sesgos.csv        brechas por estrato y dispersión por localidad
    03_Resultados/Figuras/13_rmse_todas_variantes.png
    03_Resultados/Figuras/13_mape_estrato_texto.png
    03_Resultados/Figuras/13_sesgo_estrato_texto.png
    03_Resultados/Figuras/13_cambio_texto_vs_pareja.png
    03_Resultados/Figuras/13_ablacion_estrato_localidad.png

Criterio de selección: el menor RMSE de CV (solo entrenamiento). El de prueba se reporta, no
se usa para elegir. Los grupos con menos de 30 viviendas en prueba (columna
n_prueba_menor_minimo de 04 y 11) se reportan, pero no entran en las brechas.

Se corre desde la raíz del repo: python 02_Scripts/13_comparacion_final.py
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

# Tablas de cada script: (métricas, errores por estrato, errores por localidad)
FUENTES = {
    "04": ("04_metricas_modelos.csv", "04_errores_por_estrato.csv", "04_errores_por_localidad.csv"),
    "11": ("11_metricas_modelos_texto.csv", "11_errores_por_estrato.csv", "11_errores_por_localidad.csv"),
    "12": ("12_metricas_modelos_llm.csv", "12_errores_por_estrato.csv", "12_errores_por_localidad.csv"),
}
OBLIGATORIAS = ["04", "11"]

NOMBRES = {
    "lineal_base": "Lineal (base)", "lineal_completo": "Lineal (completo)", "lasso": "Lasso",
    "random_forest": "Random Forest", "xgboost": "XGBoost",
    "rf_palabras_clave": "RF + palabras clave (A1)", "rf_tfidf_pca": "RF + TF-IDF PCA (A2)",
    "rf_e5_pca": "RF + e5 PCA (C1)", "rf_sin_ubicacion": "RF sin estrato ni localidad",
    "rf_e5_pca_sin_ubicacion": "RF + e5 PCA sin estrato ni localidad",
    "ridge_tabular": "Ridge tabular", "ridge_tfidf": "Ridge + TF-IDF (A2)",
    "mlp_tabular": "MLP tabular", "mlp_e5": "MLP + e5 (C1)", "mlp_e5_pca": "MLP + e5 PCA (C1)",
}
# Variantes de 11 que no usan estrato ni localidad (ablación de IA responsable)
SIN_ESTRATO_LOCALIDAD = ["rf_sin_ubicacion", "rf_e5_pca_sin_ubicacion"]
ESCALAS = ["log", "niveles"]
TITULO_ESCALA = {"log": "Objetivo en log(precio)", "niveles": "Objetivo en niveles"}

# ---------------------------------------------------------------------------
# Paleta de la presentación (la de 06_figuras_presentacion.py). Los dos colores nuevos
# (violeta y rosa) se eligieron con un validador de separación para daltonismo y contraste
# sobre el fondo; azul y naranja se conservan para que la base y el RF se vean igual que en 06.
# ---------------------------------------------------------------------------
FONDO = "#051d40"
TINTA = "#ffffff"
TINTA_SECUNDARIA = "#b9cde6"
GRILLA = "#1d3b68"
EJE = "#56718f"
AZUL = "#56aeff"
NARANJA = "#ffa94d"
VIOLETA = "#8f7cf5"
ROSA = "#e0607e"
# Modelos de las figuras por estrato: base, RF tabular y la mejor variante de texto de cada familia
SELECCION = [("lineal_base", AZUL, "o"), ("random_forest", NARANJA, "s"),
             ("rf_e5_pca", VIOLETA, "D"), ("mlp_e5_pca", ROSA, "^")]

plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 15, "text.color": TINTA,
    "axes.labelcolor": TINTA_SECUNDARIA, "figure.facecolor": FONDO, "axes.facecolor": FONDO,
    "axes.edgecolor": EJE, "xtick.color": TINTA_SECUNDARIA, "ytick.color": TINTA,
    "legend.facecolor": FONDO, "legend.edgecolor": EJE, "legend.labelcolor": TINTA,
})


def titulo(texto):
    print("\n" + "=" * 78)
    print(texto)
    print("=" * 78)


def guardar(fig, nombre):
    """Guarda la figura con el fondo de la diapositiva y la cierra."""
    fig.savefig(FIGURAS / nombre, dpi=200, bbox_inches="tight", facecolor=FONDO)
    plt.close(fig)
    print(f"  -> {(FIGURAS / nombre).relative_to(RAIZ)}")


def estilo_ejes(ax, eje_grilla="x"):
    """Quita bordes innecesarios y deja una grilla tenue."""
    for lado in ["top", "right", "left"]:
        ax.spines[lado].set_visible(False)
    ax.tick_params(length=0)
    ax.grid(axis=eje_grilla, color=GRILLA, linewidth=0.8)
    ax.set_axisbelow(True)


# ---------------------------------------------------------------------------
# 1. Lectura
# ---------------------------------------------------------------------------
titulo("1. LECTURA")
metricas, estratos, localidades = [], [], []
for script, archivos in FUENTES.items():
    rutas = [TABLAS / a for a in archivos]
    if not all(r.exists() for r in rutas):
        if script in OBLIGATORIAS:
            faltan = [r.name for r in rutas if not r.exists()]
            raise SystemExit(f"Faltan tablas de {script}: {faltan}. Corra antes el script correspondiente.")
        print(f"Tablas de {script}: no existen, se omiten")
        continue
    m, e, l = (pd.read_csv(r) for r in rutas)
    # 11 repite la línea base y el RF tabular de 04 como referencia: se toman solo de 04
    if script != "04":
        ya = set(metricas[0]["modelo"])
        m, e, l = (t[~t["modelo"].isin(ya)] for t in (m, e, l))
    for t in (m, e, l):
        t.insert(0, "script", script)
    metricas.append(m)
    estratos.append(e)
    localidades.append(l)
    print(f"Tablas de {script}: {m['modelo'].nunique()} modelos x {m['escala'].nunique()} escalas")

columnas_metricas = ["script", "modelo", "escala", "rmse_train", "rmse_cv", "rmse_cv_sd", "rmse_prueba",
                     "mape_train", "mape_cv", "mape_cv_sd", "mape_prueba", "n_pred_negativas_prueba"]
metricas = pd.concat([m.reindex(columns=columnas_metricas + ["sin_texto", "hiperparametros"]) for m in metricas],
                     ignore_index=True)
columnas_grupo = ["script", "modelo", "escala", "n_prueba", "rmse", "mape", "error_relativo_medio_pct",
                  "n_prueba_menor_minimo"]
estratos = pd.concat([e[columnas_grupo[:3] + ["estrato"] + columnas_grupo[3:]] for e in estratos], ignore_index=True)
localidades = pd.concat([l[columnas_grupo[:3] + ["localidad"] + columnas_grupo[3:]] for l in localidades],
                        ignore_index=True)
assert metricas.duplicated(["modelo", "escala"]).sum() == 0
sin_nombre = sorted(set(metricas["modelo"]) - set(NOMBRES))
NOMBRES.update({m: m for m in sin_nombre})  # modelos nuevos (p. ej. de 12) con su nombre interno
print(f"Total: {metricas['modelo'].nunique()} modelos, {len(metricas)} filas (modelo x escala)")

# ---------------------------------------------------------------------------
# 2. Tabla de comparación
# ---------------------------------------------------------------------------
titulo("2. COMPARACIÓN DE TODAS LAS VARIANTES")
metricas["nombre"] = metricas["modelo"].map(NOMBRES)
# Una variante usa texto si y solo si tiene pareja sin texto (así se definió en 11)
metricas["usa_texto"] = metricas["sin_texto"].notna()
metricas["usa_estrato_localidad"] = ~metricas["modelo"].isin(SIN_ESTRATO_LOCALIDAD)


def referencia(columna, modelo_ref):
    """Valor de `columna` del modelo de referencia en la misma escala, fila por fila."""
    ref = metricas[metricas["modelo"] == modelo_ref].set_index("escala")[columna]
    return metricas["escala"].map(ref)


for col in ["rmse_cv", "rmse_prueba"]:
    metricas[f"cambio_{col}_vs_base_pct"] = 100 * (metricas[col] / referencia(col, "lineal_base") - 1)
    metricas[f"cambio_{col}_vs_rf_tabular_pct"] = 100 * (metricas[col] / referencia(col, "random_forest") - 1)
for col in ["mape_cv", "mape_prueba"]:
    metricas[f"cambio_{col}_vs_base_pp"] = metricas[col] - referencia(col, "lineal_base")

# Pareja sin texto (definida en 11): mismo estimador sin el bloque de texto
pareja = metricas.set_index(["modelo", "escala"])
for col in ["rmse_cv", "rmse_prueba"]:
    valor_pareja = [pareja[col].get((s, e), np.nan) if isinstance(s, str) else np.nan
                    for s, e in zip(metricas["sin_texto"], metricas["escala"])]
    metricas[f"cambio_{col}_vs_sin_texto_pct"] = 100 * (metricas[col] / np.array(valor_pareja) - 1)

metricas["orden_rmse_cv"] = metricas.groupby("escala")["rmse_cv"].rank(method="min").astype(int)
metricas["menor_rmse_cv_escala"] = metricas["orden_rmse_cv"] == 1
metricas["menor_rmse_cv_total"] = metricas["rmse_cv"] == metricas["rmse_cv"].min()
metricas = metricas.sort_values(["escala", "rmse_cv"]).reset_index(drop=True)

pd.set_option("display.width", 250)
vista = metricas[["nombre", "escala", "rmse_cv", "rmse_cv_sd", "rmse_prueba", "mape_cv", "mape_prueba",
                  "cambio_rmse_cv_vs_base_pct", "cambio_rmse_cv_vs_rf_tabular_pct",
                  "cambio_rmse_cv_vs_sin_texto_pct"]].copy()
for c in ["rmse_cv", "rmse_cv_sd", "rmse_prueba"]:
    vista[c] = vista[c] / 1e6
print("RMSE en millones de COP; MAPE en %; cambios en % del RMSE. Ordenado por RMSE de CV en cada escala.")
print(vista.round(2).to_string(index=False))
elegido = metricas[metricas["menor_rmse_cv_total"]].iloc[0]
print(f"\nMenor RMSE de CV: {elegido['nombre']} ({elegido['escala']}), "
      f"{elegido['rmse_cv'] / 1e6:,.1f} M (desviación entre folds {elegido['rmse_cv_sd'] / 1e6:,.1f} M)")

# ---------------------------------------------------------------------------
# 3. Sesgos por estrato y localidad
# ---------------------------------------------------------------------------
titulo("3. SESGOS POR ESTRATO Y LOCALIDAD (PRUEBA)")
estratos["estrato"] = estratos["estrato"].astype(int)


def resumen_grupo(df, grupo):
    """Brechas entre grupos con al menos el mínimo de viviendas en prueba."""
    filas = []
    for (modelo, escala), sub in df.groupby(["modelo", "escala"], sort=False):
        validos = sub[~sub["n_prueba_menor_minimo"].astype(bool)]
        peor = validos.loc[validos["error_relativo_medio_pct"].abs().idxmax()]
        filas.append({
            "modelo": modelo, "escala": escala, f"n_{grupo}_validos": len(validos),
            f"n_{grupo}_menor_minimo": len(sub) - len(validos),
            f"mape_min_{grupo}": validos["mape"].min(), f"mape_max_{grupo}": validos["mape"].max(),
            f"brecha_mape_{grupo}_pp": validos["mape"].max() - validos["mape"].min(),
            f"error_con_signo_min_{grupo}_pct": validos["error_relativo_medio_pct"].min(),
            f"error_con_signo_max_{grupo}_pct": validos["error_relativo_medio_pct"].max(),
            f"error_con_signo_sd_{grupo}_pct": validos["error_relativo_medio_pct"].std(),
            f"{grupo}_mayor_error_con_signo": peor[grupo],
        })
    return pd.DataFrame(filas)


sesgos = resumen_grupo(estratos, "estrato").merge(resumen_grupo(localidades, "localidad"), on=["modelo", "escala"])
# Estrato 1 (menos de 30 viviendas en prueba) se reporta aparte, sin entrar en las brechas
pequenos = estratos[estratos["n_prueba_menor_minimo"].astype(bool)]
for estrato, sub in pequenos.groupby("estrato"):
    valores = sub.set_index(["modelo", "escala"])
    sesgos[f"mape_estrato_{estrato}"] = [valores["mape"].get((m, e), np.nan) for m, e in zip(sesgos["modelo"], sesgos["escala"])]
    sesgos[f"error_con_signo_estrato_{estrato}_pct"] = [valores["error_relativo_medio_pct"].get((m, e), np.nan)
                                                       for m, e in zip(sesgos["modelo"], sesgos["escala"])]
sesgos.insert(2, "nombre", sesgos["modelo"].map(NOMBRES))
sesgos = sesgos.merge(metricas[["modelo", "escala", "usa_texto", "usa_estrato_localidad", "mape_prueba"]],
                      on=["modelo", "escala"])
sesgos = sesgos.sort_values(["escala", "mape_prueba"]).reset_index(drop=True)

n_minimo = estratos.loc[~estratos["n_prueba_menor_minimo"].astype(bool), "n_prueba"].min()
print(f"Brechas calculadas con los grupos que no están marcados con menos del mínimo de viviendas en prueba "
      f"(el estrato válido más pequeño tiene {n_minimo:,}).")
cols = ["nombre", "escala", "mape_prueba", "brecha_mape_estrato_pp", "error_con_signo_min_estrato_pct",
        "error_con_signo_max_estrato_pct", "n_localidad_validos", "error_con_signo_sd_localidad_pct",
        "localidad_mayor_error_con_signo"] + [c for c in sesgos if c.startswith("mape_estrato_")]
print(sesgos[cols].round(2).to_string(index=False))

# ---------------------------------------------------------------------------
# 4. Figuras
# ---------------------------------------------------------------------------
titulo("4. FIGURAS")

# 4.1 RMSE de CV (con ± una desviación entre folds) y de prueba, todas las variantes
fig, axes = plt.subplots(1, 2, figsize=(16, 9), sharex=True)
for ax, escala in zip(axes, ESCALAS):
    sub = metricas[metricas["escala"] == escala].sort_values("rmse_cv", ascending=False).reset_index(drop=True)
    y = np.arange(len(sub))
    ax.errorbar(sub["rmse_cv"] / 1e6, y, xerr=sub["rmse_cv_sd"] / 1e6, fmt="o", color=AZUL, ecolor=AZUL,
                elinewidth=2, capsize=0, markersize=9, label="CV (± 1 desviación entre folds)")
    ax.scatter(sub["rmse_prueba"] / 1e6, y, marker="D", s=70, color=NARANJA, zorder=3,
               edgecolor=FONDO, linewidth=2, label="Prueba")
    base = sub.loc[sub["modelo"] == "lineal_base", "rmse_cv"].iloc[0] / 1e6
    ax.axvline(base, color=TINTA_SECUNDARIA, linewidth=1, linestyle="--")
    etiquetas = [n + (" ·texto" if t else "") for n, t in zip(sub["nombre"], sub["usa_texto"])]
    ax.set_yticks(y, etiquetas, fontsize=12)
    for etiqueta, es_elegido in zip(ax.get_yticklabels(), sub["menor_rmse_cv_escala"]):
        if es_elegido:
            etiqueta.set_fontweight("bold")
    ax.set_title(TITULO_ESCALA[escala], loc="left", fontsize=16, color=TINTA)
    ax.set_xlabel("RMSE (millones de COP)")
    estilo_ejes(ax)
handles, textos = axes[0].get_legend_handles_labels()
fig.legend(handles, textos, loc="upper right", ncol=2, fontsize=13, bbox_to_anchor=(1, 1.0))
fig.text(0.0, -0.01, "Línea punteada: RMSE de CV de la línea base. En negrita, el menor RMSE de CV de la escala. "
         "·texto = usa la descripción.", fontsize=12, color=TINTA_SECUNDARIA)
fig.tight_layout(rect=[0, 0, 1, 0.94])
guardar(fig, "13_rmse_todas_variantes.png")

# 4.2 y 4.3 MAPE y error con signo por estrato, modelos seleccionados
ESTRATOS = sorted(estratos["estrato"].unique())
N_ESTRATO = estratos.drop_duplicates("estrato").set_index("estrato")["n_prueba"]
PEQUENO = estratos.drop_duplicates("estrato").set_index("estrato")["n_prueba_menor_minimo"].astype(bool)
ETIQ_ESTRATO = [f"{e}\nn={N_ESTRATO[e]:,}" + ("*" if PEQUENO[e] else "") for e in ESTRATOS]


def lineas_estrato(nombre_figura, columna, ylabel, cero=False):
    """Una línea por modelo seleccionado a lo largo de los estratos, un panel por escala."""
    fig, axes = plt.subplots(1, 2, figsize=(15, 6.4), sharey=True)
    x = np.arange(len(ESTRATOS))
    for ax, escala in zip(axes, ESCALAS):
        for modelo, color, marcador in SELECCION:
            sub = estratos[(estratos["modelo"] == modelo) & (estratos["escala"] == escala)].set_index("estrato")
            valores = sub.loc[ESTRATOS, columna].to_numpy()
            # El RF tabular va más grueso y debajo: RF + e5 casi coincide con él y lo taparía
            grueso = modelo == "random_forest"
            ax.plot(x, valores, color=color, linewidth=6 if grueso else 2, marker=marcador,
                    markersize=14 if grueso else 9, markeredgecolor=FONDO, markeredgewidth=2,
                    zorder=1 if grueso else 2, label=NOMBRES[modelo])
        if cero:
            ax.axhline(0, color=TINTA_SECUNDARIA, linewidth=1)
        for i, e in enumerate(ESTRATOS):
            if PEQUENO[e]:
                ax.axvspan(i - 0.5, i + 0.5, color=GRILLA, alpha=0.6, zorder=0)
        ax.set_xticks(x, ETIQ_ESTRATO)
        ax.set_xlim(-0.5, len(ESTRATOS) - 0.5)
        ax.set_title(TITULO_ESCALA[escala], loc="left", fontsize=16, color=TINTA)
        ax.set_xlabel("Estrato (n en prueba; * = menos de 30 viviendas, sombreado)")
        estilo_ejes(ax, "y")
    axes[0].set_ylabel(ylabel)
    handles, textos = axes[0].get_legend_handles_labels()
    fig.legend(handles, textos, loc="upper right", ncol=4, fontsize=12, bbox_to_anchor=(1, 1.0))
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    guardar(fig, nombre_figura)


lineas_estrato("13_mape_estrato_texto.png", "mape", "MAPE en prueba (%)")
lineas_estrato("13_sesgo_estrato_texto.png", "error_relativo_medio_pct",
               "Error relativo medio con signo (%)\n+ sobrevalorada · − subvalorada", cero=True)


def etiqueta_barra(ax, x, y, texto, margen):
    """Valor escrito al final de la barra, hacia afuera según el signo."""
    ax.text(x + (margen if x >= 0 else -margen), y, texto, va="center",
            ha="left" if x >= 0 else "right", fontsize=12, color=TINTA)


# 4.4 Cambio del RMSE de CV al agregar el texto, frente a la pareja sin texto
con_texto = metricas[metricas["usa_texto"]].copy()
con_texto["etiqueta"] = con_texto["nombre"] + "\nvs. " + con_texto["sin_texto"].map(NOMBRES)
# Mismo orden en los dos paneles: promedio del cambio entre escalas, el mayor aumento arriba
orden = con_texto.groupby("etiqueta")["cambio_rmse_cv_vs_sin_texto_pct"].mean().sort_values().index
limite = 1.4 * con_texto["cambio_rmse_cv_vs_sin_texto_pct"].abs().max()
fig, axes = plt.subplots(1, 2, figsize=(16, 8), sharey=True, sharex=True)
for ax, escala in zip(axes, ESCALAS):
    sub = con_texto[con_texto["escala"] == escala].set_index("etiqueta").loc[orden]
    y = np.arange(len(sub))
    ax.barh(y, sub["cambio_rmse_cv_vs_sin_texto_pct"], height=0.6, color=AZUL)
    for yi, valor in zip(y, sub["cambio_rmse_cv_vs_sin_texto_pct"]):
        etiqueta_barra(ax, valor, yi, f"{valor:+.1f}%", 0.02 * limite)
    ax.axvline(0, color=TINTA_SECUNDARIA, linewidth=1)
    ax.set_yticks(y, sub.index, fontsize=12)
    ax.set_xlim(-limite, limite)
    ax.set_title(TITULO_ESCALA[escala], loc="left", fontsize=16, color=TINTA)
    ax.set_xlabel("Cambio del RMSE de CV frente a la pareja sin texto (%)")
    estilo_ejes(ax)
fig.text(0.0, -0.02, "Negativo: el RMSE de CV baja al agregar el texto. Cada variante se compara con el mismo "
         "estimador sin el bloque de texto (misma grilla y misma CV de 5 folds).", fontsize=12,
         color=TINTA_SECUNDARIA)
fig.tight_layout()
guardar(fig, "13_cambio_texto_vs_pareja.png")

# 4.5 Ablación sin estrato ni localidad: MAPE de prueba y brecha de MAPE entre estratos
ABLACION = ["random_forest"] + SIN_ESTRATO_LOCALIDAD
MEDIDAS = [("mape_prueba", "MAPE de prueba (%)"),
           ("brecha_mape_estrato_pp", "Brecha de MAPE entre estratos (pp)")]
COLOR_ESCALA = {"log": AZUL, "niveles": NARANJA}
excluidos = ", ".join(str(e) for e in ESTRATOS if PEQUENO[e])
fig, axes = plt.subplots(1, 2, figsize=(16, 5.8), sharey=True)
y = np.arange(len(ABLACION))[::-1]  # el RF tabular arriba
for ax, (columna, etiqueta) in zip(axes, MEDIDAS):
    tope = sesgos.loc[sesgos["modelo"].isin(ABLACION), columna].max()
    for desplazamiento, escala in zip([0.19, -0.19], ESCALAS):
        sub = sesgos[sesgos["escala"] == escala].set_index("modelo").loc[ABLACION]
        ax.barh(y + desplazamiento, sub[columna], height=0.36, color=COLOR_ESCALA[escala],
                label=TITULO_ESCALA[escala])
        for yi, valor in zip(y + desplazamiento, sub[columna]):
            etiqueta_barra(ax, valor, yi, f"{valor:.1f}", 0.015 * tope)
    ax.set_yticks(y, [NOMBRES[m] for m in ABLACION], fontsize=13)
    ax.set_xlim(0, 1.15 * tope)
    ax.set_title(etiqueta, loc="left", fontsize=16, color=TINTA)
    estilo_ejes(ax)
handles, textos = axes[0].get_legend_handles_labels()
fig.legend(handles, textos, loc="upper right", ncol=2, fontsize=13, bbox_to_anchor=(1, 1.0))
fig.text(0.0, -0.04, "Brecha: MAPE máximo menos mínimo entre estratos, sin los que tienen menos de 30 viviendas "
         f"en prueba (estrato {excluidos}).\nLas versiones sin estrato ni localidad conservan latitud, longitud "
         "y distancias.", fontsize=12, color=TINTA_SECUNDARIA)
fig.tight_layout(rect=[0, 0, 1, 0.9])
guardar(fig, "13_ablacion_estrato_localidad.png")

# ---------------------------------------------------------------------------
# 5. Guardado de tablas
# ---------------------------------------------------------------------------
titulo("5. GUARDADO")
columnas_salida = (["script", "modelo", "nombre", "escala", "usa_texto", "usa_estrato_localidad", "sin_texto",
                    "hiperparametros", "orden_rmse_cv", "menor_rmse_cv_escala", "menor_rmse_cv_total"]
                   + columnas_metricas[3:] + [c for c in metricas if c.startswith("cambio_")])
salidas = {
    "13_comparacion_modelos.csv": metricas[columnas_salida],
    "13_errores_por_estrato.csv": estratos.sort_values(["escala", "modelo", "estrato"]),
    "13_resumen_sesgos.csv": sesgos,
}
for nombre, tabla in salidas.items():
    tabla.to_csv(TABLAS / nombre, index=False, encoding="utf-8")
    print(f"  -> {(TABLAS / nombre).relative_to(RAIZ)}")
