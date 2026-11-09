"""
09_texto_limpieza.py

Limpieza del texto de 'descripcion' antes de cualquier modelo de texto, y variables por
palabras clave (alternativa A1 de 05_Notas/alternativas_aprendizaje_profundo_descripcion.md).
No estima ningún modelo ni usa la partición: las reglas son fijas (no se aprenden de los
datos), así que se aplican igual a todas las viviendas.

Insumo:
    01_Datos/02_Limpios/apartamentos_venta_limpio.csv

Salidas:
    01_Datos/02_Limpios/descripcion_limpia.csv           codigo, texto enmascarado y variables por palabras clave
    03_Resultados/Tablas/09_enmascaramiento.csv          descripciones modificadas por cada regla
    03_Resultados/Tablas/09_variables_palabras_clave.csv  patrón y % de viviendas con cada variable

Pasos:
    1. Enmascara en el texto, en este orden, los correos (<correo>), los teléfonos (<telefono>)
       y las cifras de dinero (<cifra_dinero>): precio, administración, canon, renta, predial,
       en dígitos o en palabras. El precio publicado en el texto es fuga directa del objetivo, y
       la administración y el canon están muy ligados al precio sin ser características físicas.
    2. Control: cuenta las descripciones que contienen el precio publicado (±2%) antes y
       después de enmascarar. Una cifra cuenta como precio si (a) trae unidad (millones, mil),
       (b) va después de '$' (se prueba en pesos, miles y millones) o (c) es el precio en pesos.
    3. Variables por palabras clave sobre el texto ya enmascarado: atributos de la vivienda que
       no están en las columnas (vista, piso, remodelación, etc.). No se crean variables de
       negociación ("negociable", "remate"), de barrio ni de estrato: describen al vendedor o la
       ubicación, no la vivienda.

Notas:
    - El texto de la base viene en minúsculas y sin tildes, por eso los patrones no llevan tildes.
    - Las palabras clave son una aproximación: no capturan todos los sinónimos y solo manejan
      negaciones simples ("sin balcon", "no tiene balcon").
    - Los nombres de barrio no se enmascaran (decisión pendiente con el equipo); las variables de
      este script no los usan.

Se corre desde la raíz del repo: python 02_Scripts/09_texto_limpieza.py
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Rutas (ancladas a la raíz del proyecto, que es la carpeta padre de 02_Scripts)
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
RUTA_LIMPIA = RAIZ / "01_Datos" / "02_Limpios" / "apartamentos_venta_limpio.csv"
RUTA_SALIDA = RAIZ / "01_Datos" / "02_Limpios" / "descripcion_limpia.csv"
DIR_TABLAS = RAIZ / "03_Resultados" / "Tablas"

# ---------------------------------------------------------------------------
# Parámetros
# ---------------------------------------------------------------------------
OBJETIVO = "precio_venta"
# Tolerancia para decir que una cifra del texto es el precio publicado
TOLERANCIA_PRECIO = 0.02

# Piezas de las expresiones regulares
NUM = r"\d+(?:[.,']\d+)*"                                  # 850 | 1.250 | 1,750 | 8'000.000 | 11,5
SIN_DIGITO_ANTES = r"(?<!\d)(?<!\d[.,'])"                  # no empieza dentro de otro número
SIN_DIGITO_DESPUES = r"(?![.,']?\d)"                       # no termina dentro de otro número
PALABRA_NUM = (r"(?:un|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|trece|catorce|"
               r"quince|dieci\w+|veinte|veinti\w+|treinta|cuarenta|cincuenta|sesenta|setenta|ochenta|noventa|"
               r"cien|ciento|doscientos|trescientos|cuatrocientos|quinientos|seiscientos|setecientos|"
               r"ochocientos|novecientos|mil|cero)")
PALABRAS_NUM = rf"{PALABRA_NUM}(?:\s+(?:y\s+)?{PALABRA_NUM})*"  # "novecientos noventa y cinco"
UNIDAD = r"(?:mil\s+millones|mill\w*|mil\b)"                # millones, millon, mill, millo (errores de digitación)
# Palabras tras las que una cifra con separador de miles (o de 5 o más dígitos) es dinero
CONTEXTO_DINERO = (r"(?:valor|precio|venta|adm\w*|canon|arriendo|arrendamiento|renta|cuota|predial|vale|cuesta|"
                   r"solo|desde|pagando)")
MILES = r"(?:\d{1,3}(?:[.,']\d{3})+|\d{5,})(?!\s*(?:m2|mts|mt|metros|m\b))"  # no es un área
SEP_TEL = r"[\s._-]*"

# Reglas de enmascaramiento, en orden: (tipo, patrón, reemplazo). Los teléfonos van antes que el
# dinero para que un celular no se lea como cifra; los correos antes que todo.
REGLAS = [
    ("correo", r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", "<correo>"),
    ("telefono", rf"{SIN_DIGITO_ANTES}(?:\+?57{SEP_TEL})?3\d{{2}}{SEP_TEL}\d{{3}}{SEP_TEL}\d{{2}}{SEP_TEL}\d{{2}}"
                 rf"{SIN_DIGITO_DESPUES}", "<telefono>"),                                  # celular
    ("telefono", rf"{SIN_DIGITO_ANTES}(?:\+?57{SEP_TEL})?60\d{SEP_TEL}\d{{3}}{SEP_TEL}\d{{4}}"
                 rf"{SIN_DIGITO_DESPUES}", "<telefono>"),                                  # fijo
    ("telefono", rf"\b(?P<ctx>(?:celular|cel|telefono|whatsapp|informes|inf)\.?\s+(?:al\s+)?){PALABRAS_NUM}",
     r"\g<ctx><telefono>"),                                                                # en palabras
    ("dinero", rf"\$\s*(?:{NUM}|{PALABRAS_NUM})(?:\s*{UNIDAD})?", "<cifra_dinero>"),       # $850 millones
    ("dinero", rf"\b{NUM}\s*{UNIDAD}", "<cifra_dinero>"),                                  # 425 millones, 390 mil
    ("dinero", rf"\b{PALABRAS_NUM}\s+(?:mil\s+millones|millones|millon)\b", "<cifra_dinero>"),  # seiscientos millones
    ("dinero", rf"{SIN_DIGITO_ANTES}\d{{1,3}}(?:[.,']\d{{3}}){{2,}}{SIN_DIGITO_DESPUES}", "<cifra_dinero>"),  # 470.000.000
    ("dinero", rf"\b(?P<ctx>{CONTEXTO_DINERO}[^\d<]{{0,20}}?){MILES}", r"\g<ctx><cifra_dinero>"),  # adm 812.000
]

# Variables por palabras clave: (nombre, patrón). Se buscan en el texto enmascarado.
NO_NEGADO = r"(?<!sin )(?<!no tiene )(?<!no hay )"
PALABRAS_CLAVE = [
    ("txt_vista", rf"{NO_NEGADO}\bvista\b(?! interior)"),
    ("txt_exterior", r"\bexterior\b"),
    ("txt_interior", r"vista interior|\b(?:apartamento|apto|piso \w+) interior\b"),
    ("txt_balcon", rf"{NO_NEGADO}\bbalcon"),
    ("txt_remodelado", r"\bremodelad[oa]s?\b|\bremodelacion (?:total|completa|reciente)"),
    ("txt_para_remodelar", r"(?:para|por|a|requiere|necesita) remodela(?:r|cion)|remodelar a (?:su )?gusto"),
    ("txt_iluminado", r"\biluminad[oa]\b|iluminacion|luz natural|luminos[oa]"),
    ("txt_duplex", r"\bduplex\b"),
    ("txt_penthouse", r"\bpent ?-?house\b"),
    ("txt_estudio", rf"{NO_NEGADO}(?<!aparta )\bestudio\b"),
    ("txt_deposito", rf"{NO_NEGADO}\bdeposito"),
    ("txt_cuarto_servicio", r"(?:cuarto|alcoba|habitacion)(?: y bano)? de servicio|\bcbs\b"),
    ("txt_chimenea", rf"{NO_NEGADO}\bchimenea"),
    ("txt_esquinero", r"\besquiner[oa]\b"),
    ("txt_piso_alto", r"\bpiso alto\b|\bultimo piso\b"),
]

# Número de piso: "piso 4", "4to piso", "piso 12", "quinto piso", "piso quinto"
ORDINALES = {"primer": 1, "primero": 1, "segundo": 2, "tercer": 3, "tercero": 3, "cuarto": 4, "quinto": 5,
             "sexto": 6, "septimo": 7, "octavo": 8, "noveno": 9, "decimo": 10}
ORDINAL = "|".join(ORDINALES)
PATRONES_PISO = [
    r"\bpiso\s*(?:n[o°º.]?\s*)?(\d{1,2})[a-z°º]{0,3}\b(?!\s*(?:m\b|m2|mt|me|ne|anos))",  # no es área ni edad
    r"\b(\d{1,2})[a-z°º.]{0,4}\s+piso\b(?!s)",
    rf"\b({ORDINAL})\s+piso\b(?!s)",
    rf"\bpiso\s+({ORDINAL})\b",
]
PISO_MAXIMO = 60  # el edificio residencial más alto de Bogotá tiene menos pisos: más es un error de lectura


# ---------------------------------------------------------------------------
# Funciones auxiliares
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


def a_numero(cifra):
    """Convierte '1.250', '1,750', "8'000.000" o '11,5' a número. Si el último grupo no tiene
    3 dígitos, el último separador es decimal; si no, todos son separadores de miles."""
    partes = re.split(r"[.,']", cifra)
    if len(partes) > 1 and len(partes[-1]) != 3:
        return float("".join(partes[:-1]) + "." + partes[-1])
    return float("".join(partes))


def menciona_precio(texto, precio):
    """True si alguna cifra del texto coincide con el precio publicado (±TOLERANCIA_PRECIO)."""
    for m in re.finditer(rf"(\$\s*)?({NUM})\s*({UNIDAD})?", texto):
        valor = a_numero(m.group(2))
        if m.group(3):
            unidad = m.group(3)
            factor = 1e9 if " " in unidad else 1e3 if unidad == "mil" else 1e6
            candidatos = [valor * factor]
        elif m.group(1):
            candidatos = [valor, valor * 1e3, valor * 1e6]
        else:
            candidatos = [valor]
        if any(abs(c - precio) <= TOLERANCIA_PRECIO * precio for c in candidatos):
            return True
    return False


def piso_mencionado(texto):
    """Número de piso de la primera mención en el texto (0 si no menciona ninguno)."""
    menciones = []  # (posición, piso) de cada coincidencia de cualquier patrón
    for patron in PATRONES_PISO:
        for m in re.finditer(patron, texto):
            valor = m.group(1)
            piso = ORDINALES[valor] if valor in ORDINALES else int(valor)
            if 1 <= piso <= PISO_MAXIMO:
                menciones.append((m.start(), piso))
    return min(menciones)[1] if menciones else 0


# ---------------------------------------------------------------------------
# 1. Lectura
# ---------------------------------------------------------------------------
titulo("1. LECTURA")
df = pd.read_csv(RUTA_LIMPIA, usecols=["codigo", "descripcion", OBJETIVO])
texto_original = df["descripcion"].fillna("").astype(str)
print(f"Viviendas en la base limpia: {len(df):,}")

# ---------------------------------------------------------------------------
# 2. Enmascaramiento de correos, teléfonos y cifras de dinero
# ---------------------------------------------------------------------------
titulo("2. ENMASCARAMIENTO")
texto = texto_original.copy()
modificada_por = {}  # tipo -> Serie booleana: la regla de ese tipo cambió la descripción
n_reemplazos = {}
for tipo, patron, reemplazo in REGLAS:
    n = texto.str.count(patron)
    nuevo = texto.str.replace(patron, reemplazo, regex=True)
    modificada_por[tipo] = modificada_por.get(tipo, False) | (nuevo != texto)
    n_reemplazos[tipo] = n_reemplazos.get(tipo, 0) + int(n.sum())
    texto = nuevo
modificada = texto != texto_original

# Control: descripciones con el precio publicado antes y después de enmascarar
precio_antes = np.array([menciona_precio(t, p) for t, p in zip(texto_original, df[OBJETIVO])])
precio_despues = np.array([menciona_precio(t, p) for t, p in zip(texto, df[OBJETIVO])])

filas = [{"medida": f"descripciones con {tipo} enmascarado", "n": int(modificada_por[tipo].sum()),
          "reemplazos": n_reemplazos[tipo]} for tipo in ["correo", "telefono", "dinero"]]
filas += [
    {"medida": "descripciones modificadas (alguna regla)", "n": int(modificada.sum()), "reemplazos": np.nan},
    {"medida": "descripciones con el precio publicado, antes de enmascarar", "n": int(precio_antes.sum()),
     "reemplazos": np.nan},
    {"medida": "descripciones con el precio publicado, después de enmascarar", "n": int(precio_despues.sum()),
     "reemplazos": np.nan},
]
enmascaramiento = pd.DataFrame(filas)
enmascaramiento.insert(1, "viviendas", len(df))
enmascaramiento["pct"] = (100 * enmascaramiento["n"] / len(df)).round(2)
print(enmascaramiento.to_string(index=False))
if precio_despues.any():
    print("\nDescripciones que aún contienen el precio (revisar las reglas):")
    for c in df.loc[precio_despues, "codigo"]:
        print(f"  - {c}")

# ---------------------------------------------------------------------------
# 3. Variables por palabras clave (A1)
# ---------------------------------------------------------------------------
titulo("3. VARIABLES POR PALABRAS CLAVE")
salida = pd.DataFrame({"codigo": df["codigo"], "descripcion_limpia": texto,
                       "texto_modificado": modificada, "precio_en_texto_original": precio_antes})
for nombre, patron in PALABRAS_CLAVE:
    salida[nombre] = texto.str.contains(patron, regex=True).astype(int)
salida["txt_piso_numero"] = texto.map(piso_mencionado)
salida["txt_menciona_piso"] = (salida["txt_piso_numero"] > 0).astype(int)
VARIABLES = [n for n, _ in PALABRAS_CLAVE] + ["txt_piso_numero", "txt_menciona_piso"]

descripcion = pd.DataFrame({
    "variable": VARIABLES,
    "patron": [p for _, p in PALABRAS_CLAVE] + [" | ".join(PATRONES_PISO), "txt_piso_numero > 0"],
    "pct_viviendas": [round(100 * (salida[v] > 0).mean(), 1) for v in VARIABLES],
})
print(descripcion[["variable", "pct_viviendas"]].to_string(index=False))
pisos = salida.loc[salida["txt_piso_numero"] > 0, "txt_piso_numero"]
print(f"\nPiso mencionado: mediana {pisos.median():.0f}, percentil 90 {pisos.quantile(0.9):.0f}, máximo {pisos.max()}")

# ---------------------------------------------------------------------------
# 4. Guardado
# ---------------------------------------------------------------------------
titulo("4. GUARDADO")
assert salida["codigo"].is_unique and len(salida) == len(df)
salida.to_csv(RUTA_SALIDA, index=False, encoding="utf-8")
print(f"  -> {RUTA_SALIDA.relative_to(RAIZ)} ({len(salida):,} filas x {salida.shape[1]} columnas)")
guardar_tabla(enmascaramiento, "09_enmascaramiento.csv")
guardar_tabla(descripcion, "09_variables_palabras_clave.csv")
