"""
00_main.py

Corre el pipeline completo en orden: todos los scripts numerados de 02_Scripts/
(01_, 02_, ...), con el mismo intérprete que ejecuta este archivo. Se detiene en
el primer script que falle.

Se corre desde la raíz del repo: .venv/bin/python 00_main.py
"""

import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
SCRIPTS = sorted((RAIZ / "02_Scripts").glob("[0-9][0-9]_*.py"))

print(f"Intérprete: {sys.executable}")
print(f"Scripts a correr ({len(SCRIPTS)}): {', '.join(s.name for s in SCRIPTS)}")
inicio = time.time()
for script in SCRIPTS:
    print("\n" + "#" * 78)
    print(f"# {script.relative_to(RAIZ)}")
    print("#" * 78, flush=True)
    t0 = time.time()
    subprocess.run([sys.executable, str(script)], check=True, cwd=RAIZ)
    print(f"\n[{script.name} terminó en {(time.time() - t0) / 60:.1f} min]", flush=True)
print(f"\nPipeline completo en {(time.time() - inicio) / 60:.1f} min")
