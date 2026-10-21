"""
05_analisis_errores_impacto.py

Análisis de errores por estrato y localidad (IA responsable) y traducción de los
errores de prueba a costo para el usuario, como insumo de la evaluación de impacto.
Compara la línea base lineal con el Random Forest, en las dos escalas del objetivo
(log y niveles). No reestima ningún modelo: usa las predicciones de prueba que
guardó 04_estimacion_modelos.py.

Insumos:
    03_Resultados/Tablas/04_predicciones_prueba.csv   (lo produce 04_estimacion_modelos.py)

Salidas:
    03_Resultados/Tablas/05_errores_por_estrato.csv
    03_Resultados/Tablas/05_errores_por_localidad.csv
    03_Resultados/Tablas/05_costo_esperado_por_estrato.csv   (RF frente a línea base, con total)
    03_Resultados/Tablas/05_comparacion_por_localidad.csv
    03_Resultados/Tablas/05_diseno_ab.csv
    03_Resultados/Figuras/05_costo_esperado_por_estrato.png
    03_Resultados/Figuras/05_sesgo_por_localidad.png

Pasos:
    1. Lee las predicciones de prueba y arma el error de cada vivienda por modelo y escala.
    2. Errores por estrato y localidad: RMSE, MAE y sesgo en pesos, sesgo relativo con su
       error estándar y proporción de viviendas sobre y subvaloradas. Los grupos con menos
       de N_MINIMO_GRUPO_PRUEBA viviendas en prueba se marcan.
    3. Costo esperado por vivienda para el usuario, suponiendo que sigue el precio del modelo:
       el comprador paga de más cuando el modelo sobrevalora y el vendedor pierde cuando
       subvalora. Se compara el Random Forest con la línea base.
    4. Diseño de la prueba A/B (lineal vs. Random Forest) en lo que se calcula con estos datos:
       tamaño de muestra por brazo para detectar la reducción de error de precio observada y
       efecto mínimo detectable para tamaños fijos. Lo demás queda como propuesta.

Se corre desde la raíz del repo: python 02_Scripts/05_analisis_errores_impacto.py
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
RUTA_PREDICCIONES = RAIZ / "03_Resultados" / "Tablas" / "04_predicciones_prueba.csv"
DIR_TABLAS = RAIZ / "03_Resultados" / "Tablas"
DIR_FIGURAS = RAIZ / "03_Resultados" / "Figuras"

# ---------------------------------------------------------------------------
# Parámetros
# ---------------------------------------------------------------------------
OBJETIVO = "precio_venta"
ESCALAS = ["log", "niveles"]
BASE = "lineal_base"
PRINCIPAL = "random_forest"
MODELOS = [BASE, PRINCIPAL]
NOMBRES = {BASE: "Lineal (base)", PRINCIPAL: "Random Forest"}
# Mismo umbral que 04_estimacion_modelos.py: los grupos más pequeños se marcan, no se omiten
N_MINIMO_GRUPO_PRUEBA = 30

# Prueba A/B: dos colas, nivel de significancia de 0.05 y potencia de 0.80 (valores de la
# normal estándar, escritos como constantes para no depender de scipy)
Z_ALFA = 1.96
Z_POTENCIA = 0.8416
# Tamaños por brazo con los que se reporta el efecto mínimo detectable (supuestos del diseño)
N_POR_BRAZO = [100, 500, 1000]

# Colores de las figuras (misma paleta que 04_estimacion_modelos.py)
SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
GRILLA = "#e1e0d9"
EJE = "#c3c2b7"
COLOR_MODELO = {BASE: "#2a78d6", PRINCIPAL: "#eda100"}


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
# 1. Lectura de las predicciones de prueba y error por vivienda
# ---------------------------------------------------------------------------
titulo("1. LECTURA Y ERROR POR VIVIENDA")
predicciones = pd.read_csv(RUTA_PREDICCIONES)
print(f"Viviendas en prueba: {len(predicciones):,}")

# Formato largo: una fila por vivienda, modelo y escala. error = predicción - precio publicado
# (positivo = el modelo sobrevalora, negativo = subvalora)
bloques = []
for escala in ESCALAS:
    for modelo in MODELOS:
        bloque = predicciones[["codigo", "estrato", "localidad", OBJETIVO]].copy()
        bloque["modelo"] = modelo
        bloque["escala"] = escala
        bloque["pred"] = predicciones[f"pred_{modelo}_{escala}"]
        bloques.append(bloque)
errores = pd.concat(bloques, ignore_index=True)
errores = errores.rename(columns={OBJETIVO: "precio"})
errores["error"] = errores["pred"] - errores["precio"]
errores["error_abs"] = errores["error"].abs()
errores["error_cuadrado"] = errores["error"] ** 2
errores["error_rel_pct"] = 100 * errores["error"] / errores["precio"]
errores["error_abs_rel_pct"] = errores["error_rel_pct"].abs()
errores["sobrevalorada"] = errores["error"] > 0
errores["subvalorada"] = errores["error"] < 0
errores["sobrecosto"] = errores["error"].clip(lower=0)       # lo que paga de más el comprador
errores["perdida"] = (-errores["error"]).clip(lower=0)        # lo que deja de recibir el vendedor
errores["pred_no_positiva"] = errores["pred"] <= 0
errores["todas"] = "TODAS"
print(f"Filas modelo x escala x vivienda: {len(errores):,}")


# ---------------------------------------------------------------------------
# 2. Errores por estrato y localidad
# ---------------------------------------------------------------------------
titulo("2. ERRORES DE PRUEBA POR ESTRATO Y LOCALIDAD")


def errores_por_grupo(grupo):
    """Métricas de error de prueba por modelo, escala y grupo (estrato, localidad o todas)."""
    g = errores.groupby(["modelo", "escala", grupo])
    tabla = g.agg(
        n_prueba=("error", "size"),
        precio_mediano=("precio", "median"),
        rmse=("error_cuadrado", lambda s: np.sqrt(s.mean())),
        mae=("error_abs", "mean"),
        error_abs_mediano=("error_abs", "median"),
        error_abs_p90=("error_abs", lambda s: s.quantile(0.9)),
        sesgo_cop=("error", "mean"),
        mape=("error_abs_rel_pct", "mean"),
        sesgo_rel_medio_pct=("error_rel_pct", "mean"),
        sesgo_rel_mediano_pct=("error_rel_pct", "median"),
        sesgo_rel_error_estandar_pct=("error_rel_pct", lambda s: s.std(ddof=1) / np.sqrt(len(s))),
        prop_sobrevalorada_pct=("sobrevalorada", lambda s: 100 * s.mean()),
        prop_subvalorada_pct=("subvalorada", lambda s: 100 * s.mean()),
        sobrecosto_comprador_cop=("sobrecosto", "mean"),
        perdida_vendedor_cop=("perdida", "mean"),
        n_pred_no_positivas=("pred_no_positiva", "sum"),
    ).reset_index()
    tabla["mae_pct_precio_mediano"] = 100 * tabla["mae"] / tabla["precio_mediano"]
    tabla["sobrecosto_pct_precio_mediano"] = 100 * tabla["sobrecosto_comprador_cop"] / tabla["precio_mediano"]
    tabla["perdida_pct_precio_mediano"] = 100 * tabla["perdida_vendedor_cop"] / tabla["precio_mediano"]
    tabla["n_prueba_menor_minimo"] = tabla["n_prueba"] < N_MINIMO_GRUPO_PRUEBA
    return tabla


err_estrato = errores_por_grupo("estrato")
err_localidad = errores_por_grupo("localidad")
err_total = errores_por_grupo("todas").rename(columns={"todas": "estrato"})

guardar_tabla(err_estrato, "05_errores_por_estrato.csv")
guardar_tabla(err_localidad, "05_errores_por_localidad.csv")

n_chicos_estrato = err_estrato.query("modelo == @BASE and escala == 'log'")["n_prueba_menor_minimo"].sum()
n_chicos_localidad = err_localidad.query("modelo == @BASE and escala == 'log'")["n_prueba_menor_minimo"].sum()
print(f"\nGrupos con menos de {N_MINIMO_GRUPO_PRUEBA} viviendas en prueba: "
      f"{n_chicos_estrato} de {err_estrato['estrato'].nunique()} estratos y "
      f"{n_chicos_localidad} de {err_localidad['localidad'].nunique()} localidades")

with pd.option_context("display.width", 200, "display.float_format", "{:,.1f}".format):
    for escala in ESCALAS:
        print(f"\nPor estrato, objetivo en {escala} (sesgo relativo medio %, MAPE %, MAE en millones):")
        sub = err_estrato.query("escala == @escala").copy()
        sub["mae_millones"] = sub["mae"] / 1e6
        print(sub.pivot_table(index=["estrato", "n_prueba"], columns="modelo",
                              values=["sesgo_rel_medio_pct", "mape", "mae_millones"])
              .reindex(columns=MODELOS, level=1).to_string())


# ---------------------------------------------------------------------------
# 3. Costo esperado por vivienda para el usuario (Random Forest frente a línea base)
# ---------------------------------------------------------------------------
titulo("3. COSTO ESPERADO POR VIVIENDA: RANDOM FOREST FRENTE A LA LÍNEA BASE")
print("Supuesto: el usuario sigue el precio del modelo. El precio de referencia es el publicado,\n"
      "no el de transacción, así que esto aproxima el costo del error de precio, no un ahorro real.")

COLUMNAS_COMPARACION = ["n_prueba", "precio_mediano", "mae", "mape", "sesgo_rel_medio_pct",
                        "sobrecosto_comprador_cop", "perdida_vendedor_cop"]


def comparar(tabla, grupo):
    """Una fila por escala y grupo con la línea base y el Random Forest lado a lado."""
    base = tabla.query("modelo == @BASE").set_index(["escala", grupo])
    rf = tabla.query("modelo == @PRINCIPAL").set_index(["escala", grupo])
    salida = pd.DataFrame({"n_prueba": base["n_prueba"], "precio_mediano": base["precio_mediano"]})
    for col in COLUMNAS_COMPARACION[2:]:
        salida[f"{col}_base"] = base[col]
        salida[f"{col}_rf"] = rf[col]
    # Reducción = lo que deja de costar el error con el Random Forest (positivo = reduce)
    salida["reduccion_mae_cop"] = base["mae"] - rf["mae"]
    salida["reduccion_mae_pct"] = 100 * salida["reduccion_mae_cop"] / base["mae"]
    salida["reduccion_sobrecosto_comprador_cop"] = base["sobrecosto_comprador_cop"] - rf["sobrecosto_comprador_cop"]
    salida["reduccion_perdida_vendedor_cop"] = base["perdida_vendedor_cop"] - rf["perdida_vendedor_cop"]
    salida["n_prueba_menor_minimo"] = base["n_prueba_menor_minimo"]
    return salida.reset_index()


comp_estrato = pd.concat([comparar(err_estrato, "estrato"),
                          comparar(err_total, "estrato")], ignore_index=True)
comp_estrato["estrato"] = comp_estrato["estrato"].astype(str)
comp_localidad = comparar(err_localidad, "localidad")
guardar_tabla(comp_estrato, "05_costo_esperado_por_estrato.csv")
guardar_tabla(comp_localidad, "05_comparacion_por_localidad.csv")

with pd.option_context("display.width", 220, "display.float_format", "{:,.1f}".format):
    for escala in ESCALAS:
        sub = comp_estrato.query("escala == @escala").set_index("estrato")
        vista = pd.DataFrame({
            "n": sub["n_prueba"],
            "mae_base_M": sub["mae_base"] / 1e6, "mae_rf_M": sub["mae_rf"] / 1e6,
            "reduccion_M": sub["reduccion_mae_cop"] / 1e6, "reduccion_%": sub["reduccion_mae_pct"],
            "sobrecosto_rf_M": sub["sobrecosto_comprador_cop_rf"] / 1e6,
            "perdida_rf_M": sub["perdida_vendedor_cop_rf"] / 1e6,
        })
        print(f"\nObjetivo en {escala} (millones de COP por vivienda):")
        print(vista.to_string())


# ---------------------------------------------------------------------------
# 4. Diseño de la prueba A/B con lo que se calcula desde los datos
# ---------------------------------------------------------------------------
titulo("4. DISEÑO DE LA PRUEBA A/B (LINEAL VS. RANDOM FOREST)")
print("Resultado calculable: error de precio por vivienda (en pesos y relativo). Cada brazo ve a\n"
      "usuarios distintos, así que la comparación es entre grupos independientes. El tamaño de\n"
      f"muestra usa la normal con alfa 0.05 a dos colas (z = {Z_ALFA}) y potencia 0.80 (z = {Z_POTENCIA}).")

METRICAS_AB = {"error_abs": "error_absoluto_cop", "error_abs_rel_pct": "error_absoluto_relativo_pct"}
suma_z = Z_ALFA + Z_POTENCIA
filas = []
for escala in ESCALAS:
    for grupo, etiqueta in [("estrato", None), ("todas", "TODAS")]:
        sub_escala = errores.query("escala == @escala")
        valores_grupo = [etiqueta] if etiqueta else sorted(sub_escala[grupo].unique())
        for valor in valores_grupo:
            sub = sub_escala if etiqueta else sub_escala.query(f"{grupo} == @valor")
            base = sub.query("modelo == @BASE")
            rf = sub.query("modelo == @PRINCIPAL")
            for columna, nombre_metrica in METRICAS_AB.items():
                media_base, media_rf = base[columna].mean(), rf[columna].mean()
                sd_agrupada = np.sqrt((base[columna].var(ddof=1) + rf[columna].var(ddof=1)) / 2)
                reduccion = media_base - media_rf
                fila = {
                    "escala": escala, "estrato": str(valor), "metrica": nombre_metrica,
                    "n_prueba": len(base), "media_base": media_base, "media_rf": media_rf,
                    "reduccion_observada": reduccion, "sd_agrupada": sd_agrupada,
                    # Con reducción nula o negativa no hay efecto que detectar a favor del RF
                    "n_por_brazo_requerido": (np.ceil(2 * (suma_z * sd_agrupada / reduccion) ** 2)
                                              if reduccion > 0 else np.nan),
                    "n_prueba_menor_minimo": len(base) < N_MINIMO_GRUPO_PRUEBA,
                }
                for n in N_POR_BRAZO:
                    # Efecto mínimo detectable con n usuarios por brazo
                    fila[f"efecto_minimo_detectable_n{n}"] = suma_z * sd_agrupada * np.sqrt(2 / n)
                filas.append(fila)
diseno_ab = pd.DataFrame(filas)
guardar_tabla(diseno_ab, "05_diseno_ab.csv")

with pd.option_context("display.width", 220, "display.float_format", "{:,.1f}".format):
    vista = diseno_ab.query("metrica == 'error_absoluto_relativo_pct'")[
        ["escala", "estrato", "n_prueba", "media_base", "media_rf", "reduccion_observada",
         "sd_agrupada", "n_por_brazo_requerido"] + [f"efecto_minimo_detectable_n{n}" for n in N_POR_BRAZO]]
    print("\nError absoluto relativo (puntos porcentuales):")
    print(vista.to_string(index=False))

print("""
Queda como propuesta (no se puede calcular con estos datos):
  - Resultados del experimento: tiempo de compra/venta y ganancia o ahorro del usuario. El
    precio de la base es el publicado, no el de transacción, y no hay tiempo en el mercado
    confiable (last_view se actualiza con cada corrida del scraper).
  - Asignación: aleatorizar usuarios (compradores y vendedores) entre el modelo lineal y el
    Random Forest, estratificando por estrato y localidad para poder desagregar el efecto.
  - Revisión trimestral: revalidar ambos modelos con anuncios nuevos y repetir esta
    desagregación por estrato y localidad.
  - El tamaño por brazo de arriba dimensiona solo la comparación del error de precio; para los
    resultados de tiempo y ahorro se necesita su varianza, que sale de un piloto.""")


# ---------------------------------------------------------------------------
# 5. Figuras
# ---------------------------------------------------------------------------
titulo("5. FIGURAS")
plt.rcParams.update({"font.family": "sans-serif", "font.size": 9, "text.color": TINTA,
                     "axes.labelcolor": TINTA_SECUNDARIA, "figure.facecolor": SUPERFICIE})

# 5a. Costo esperado por estrato: sobrecosto del comprador (arriba) y pérdida del vendedor
# (abajo), como % del precio mediano del estrato, un panel por escala
estratos = sorted(err_estrato["estrato"].unique())
n_por_estrato = err_estrato.query("modelo == @BASE and escala == 'log'").set_index("estrato")["n_prueba"]
fig, ejes = plt.subplots(1, 2, figsize=(11, 4.4), sharey=True)
ancho = 0.36
for ax, escala in zip(ejes, ESCALAS):
    estilo_ejes(ax)
    ax.grid(axis="x", visible=False)
    for j, modelo in enumerate(MODELOS):
        sub = err_estrato.query("modelo == @modelo and escala == @escala").set_index("estrato").loc[estratos]
        posiciones = np.arange(len(estratos)) + (j - 0.5) * ancho
        ax.bar(posiciones, sub["sobrecosto_pct_precio_mediano"], width=ancho, color=COLOR_MODELO[modelo],
               edgecolor=SUPERFICIE, linewidth=1, label=NOMBRES[modelo])
        ax.bar(posiciones, -sub["perdida_pct_precio_mediano"], width=ancho, color=COLOR_MODELO[modelo],
               edgecolor=SUPERFICIE, linewidth=1)
    ax.axhline(0, color=EJE, linewidth=0.8)
    ax.set_xticks(np.arange(len(estratos)), [f"{e}\nn={n_por_estrato[e]}" for e in estratos])
    ax.set_xlabel("Estrato (n en prueba)")
    ax.set_title(f"Objetivo en {escala}", loc="left", fontsize=10, color=TINTA)
ejes[0].set_ylabel("% del precio mediano del estrato\n↑ comprador paga de más · ↓ vendedor pierde")
ejes[1].legend(frameon=False, fontsize=8, loc="upper right")
fig.suptitle("Costo esperado por vivienda del error de precio en prueba, por estrato",
             x=0.07, ha="left", fontsize=11, color=TINTA)
guardar_figura(fig, "05_costo_esperado_por_estrato.png")

# 5b. Sesgo relativo medio por localidad: base y Random Forest, un panel por escala.
# Marcador vacío = grupo con menos de N_MINIMO_GRUPO_PRUEBA viviendas en prueba
orden = (err_localidad.query("modelo == @PRINCIPAL and escala == 'log'")
         .sort_values("sesgo_rel_medio_pct").reset_index(drop=True))
localidades = orden["localidad"].tolist()
n_por_localidad = orden.set_index("localidad")["n_prueba"]
etiquetas = [f"{loc} (n={n_por_localidad[loc]})" for loc in localidades]
fig, ejes = plt.subplots(1, 2, figsize=(11, 6.2), sharey=True)
for ax, escala in zip(ejes, ESCALAS):
    estilo_ejes(ax)
    ax.grid(axis="y", visible=False)
    for modelo in MODELOS:
        sub = err_localidad.query("modelo == @modelo and escala == @escala").set_index("localidad").loc[localidades]
        chico = sub["n_prueba_menor_minimo"].to_numpy()
        y = np.arange(len(localidades))
        x = sub["sesgo_rel_medio_pct"].to_numpy()
        ax.scatter(x[~chico], y[~chico], s=34, color=COLOR_MODELO[modelo], zorder=3, label=NOMBRES[modelo])
        ax.scatter(x[chico], y[chico], s=34, facecolors=SUPERFICIE, edgecolors=COLOR_MODELO[modelo],
                   linewidths=1.4, zorder=3)
    ax.axvline(0, color=EJE, linewidth=0.8)
    ax.set_yticks(np.arange(len(localidades)), etiquetas, color=TINTA)
    ax.set_xlabel("Error relativo medio (%)\n+ sobrevalora · − subvalora")
    ax.set_title(f"Objetivo en {escala}", loc="left", fontsize=10, color=TINTA)
ejes[0].invert_yaxis()
# Leyenda fuera de los ejes para no tapar puntos
manijas, rotulos = ejes[0].get_legend_handles_labels()
fig.legend(manijas, rotulos, frameon=False, fontsize=9, loc="lower center", ncol=2,
           bbox_to_anchor=(0.5, -0.04))
fig.suptitle(f"Error relativo medio con signo en prueba, por localidad "
             f"(marcador vacío: menos de {N_MINIMO_GRUPO_PRUEBA} viviendas)",
             x=0.07, ha="left", fontsize=11, color=TINTA)
guardar_figura(fig, "05_sesgo_por_localidad.png")

titulo("FIN")
