"""
10_texto_embeddings.py

Vectores (embeddings) de la descripción de cada vivienda con un Transformer preentrenado y
congelado (alternativa C1 de 05_Notas/alternativas_aprendizaje_profundo_descripcion.md).
El modelo NO se entrena con nuestros datos ni ve el precio: convierte cada texto en un vector
de 768 números que resume su contenido. Se calcula una sola vez para todas las viviendas y se
guarda en disco; los modelos de precio (11_modelos_texto.py) leen los vectores de ahí.

Insumo:
    01_Datos/02_Limpios/descripcion_limpia.csv   (lo produce 09_texto_limpieza.py)

Salidas:
    01_Datos/02_Limpios/embeddings_e5_base.npz   codigo y vectores (float16, normalizados a norma 1)
    03_Resultados/Tablas/10_embeddings_resumen.csv  modelo, revisión, largo en tokens y tiempo

Pasos:
    1. Lee el texto enmascarado de 09 y quita los marcadores (<cifra_dinero>, <telefono>, <correo>):
       el modelo de texto no debe aprender si el anuncio menciona una cifra.
    2. Cuenta los tokens de cada descripción con el tokenizador del modelo (el modelo lee hasta
       512; las más largas se truncarían).
    3. Calcula los vectores con el prefijo "query: ", el que recomienda la documentación de e5
       para usar los vectores como variables, y los normaliza a norma 1.
    4. Si el archivo de vectores ya existe con los mismos códigos, modelo y revisión, no lo
       recalcula (tarda unos 10 minutos en un M1). Para forzarlo: --recalcular.

Herramienta nueva (aprobada por Santiago Muñoz el 2026-11-09, pendiente de confirmar con el equipo):
    sentence-transformers (Hugging Face), que descarga el modelo preentrenado y calcula los vectores.

Se corre desde la raíz del repo: python 02_Scripts/10_texto_embeddings.py [--recalcular]
"""

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# Rutas (ancladas a la raíz del proyecto, que es la carpeta padre de 02_Scripts)
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
RUTA_TEXTO = RAIZ / "01_Datos" / "02_Limpios" / "descripcion_limpia.csv"
RUTA_SALIDA = RAIZ / "01_Datos" / "02_Limpios" / "embeddings_e5_base.npz"
DIR_TABLAS = RAIZ / "03_Resultados" / "Tablas"

# ---------------------------------------------------------------------------
# Parámetros
# ---------------------------------------------------------------------------
MODELO = "intfloat/multilingual-e5-base"
# Revisión exacta (commit en Hugging Face) para que los vectores sean reproducibles
REVISION = "d128750597153bb5987e10b1c3493a34e5a4502a"
PREFIJO = "query: "
MARCADORES = r"<(?:cifra_dinero|telefono|correo)>"
TAMANO_LOTE = 32
# GPU del Mac (MPS) si está disponible; si no, CPU. Los vectores no cambian de forma relevante entre ambas.
DISPOSITIVO = "mps" if torch.backends.mps.is_available() else "cpu"


def titulo(texto):
    print("\n" + "=" * 78)
    print(texto)
    print("=" * 78)


# ---------------------------------------------------------------------------
# 1. Lectura y preparación del texto
# ---------------------------------------------------------------------------
titulo("1. LECTURA")
if not RUTA_TEXTO.exists():
    raise SystemExit(f"No existe {RUTA_TEXTO.relative_to(RAIZ)}: corra antes 02_Scripts/09_texto_limpieza.py")
df = pd.read_csv(RUTA_TEXTO, usecols=["codigo", "descripcion_limpia"])
texto = df["descripcion_limpia"].str.replace(MARCADORES, " ", regex=True).str.split().str.join(" ")
print(f"Descripciones: {len(df):,}")

if RUTA_SALIDA.exists() and "--recalcular" not in sys.argv:
    guardado = np.load(RUTA_SALIDA, allow_pickle=False)
    if (str(guardado["modelo"]) == MODELO and str(guardado["revision"]) == REVISION
            and np.array_equal(guardado["codigo"], df["codigo"].astype(str).to_numpy(dtype="U"))):
        print(f"{RUTA_SALIDA.relative_to(RAIZ)} ya existe con los mismos códigos, modelo y revisión: no se recalcula.")
        print("Use --recalcular para forzar el cálculo.")
        sys.exit(0)
    print("El archivo de vectores no coincide con la base actual: se recalcula.")

# ---------------------------------------------------------------------------
# 2. Modelo y largo en tokens
# ---------------------------------------------------------------------------
titulo("2. MODELO Y LARGO EN TOKENS")
modelo = SentenceTransformer(MODELO, revision=REVISION, device=DISPOSITIVO)
entradas = (PREFIJO + texto).tolist()
n_tokens = np.array([len(ids) for ids in modelo.tokenizer(entradas)["input_ids"]])
n_truncadas = int((n_tokens > modelo.max_seq_length).sum())
print(f"Modelo: {MODELO} (revisión {REVISION[:10]}), {modelo.get_embedding_dimension()} dimensiones, "
      f"máximo {modelo.max_seq_length} tokens, dispositivo {DISPOSITIVO}")
print(f"Tokens por descripción: mediana {np.median(n_tokens):.0f}, percentil 99 {np.percentile(n_tokens, 99):.0f}, "
      f"máximo {n_tokens.max()}; truncadas: {n_truncadas}")

# ---------------------------------------------------------------------------
# 3. Vectores
# ---------------------------------------------------------------------------
titulo("3. VECTORES")
t0 = time.time()
vectores = modelo.encode(entradas, batch_size=TAMANO_LOTE, normalize_embeddings=True, show_progress_bar=True)
segundos = time.time() - t0
assert vectores.shape == (len(df), modelo.get_embedding_dimension()) and np.isfinite(vectores).all()
print(f"Vectores: {vectores.shape[0]:,} x {vectores.shape[1]} en {segundos / 60:.1f} min")

# ---------------------------------------------------------------------------
# 4. Guardado (float16: la mitad del tamaño, sin pérdida relevante para vectores de norma 1)
# ---------------------------------------------------------------------------
titulo("4. GUARDADO")
np.savez_compressed(RUTA_SALIDA, codigo=df["codigo"].astype(str).to_numpy(dtype="U"), vectores=vectores.astype(np.float16),
                    modelo=MODELO, revision=REVISION)
print(f"  -> {RUTA_SALIDA.relative_to(RAIZ)} ({RUTA_SALIDA.stat().st_size / 1e6:.1f} MB)")
resumen = pd.DataFrame([
    ("modelo", MODELO), ("revision", REVISION), ("prefijo", PREFIJO.strip()),
    ("dimensiones", vectores.shape[1]), ("viviendas", len(df)), ("tokens_maximo_modelo", modelo.max_seq_length),
    ("tokens_mediana", float(np.median(n_tokens))), ("tokens_percentil_99", float(np.percentile(n_tokens, 99))),
    ("tokens_maximo", int(n_tokens.max())), ("descripciones_truncadas", n_truncadas),
    ("dispositivo", DISPOSITIVO), ("minutos_calculo", round(segundos / 60, 1)),
], columns=["medida", "valor"])
DIR_TABLAS.mkdir(parents=True, exist_ok=True)
resumen.to_csv(DIR_TABLAS / "10_embeddings_resumen.csv", index=False, encoding="utf-8")
print(f"  -> {(DIR_TABLAS / '10_embeddings_resumen.csv').relative_to(RAIZ)}")
