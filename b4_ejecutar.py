# ============================================================
# PROCESO B4: Mover y renombrar según el plan (SÍ modifica D:\1_Lib)
# Insumo:    plan_movimientos.csv (Proceso B3), aprobado por el usuario
# Resultado: biblioteca ordenada en una sola carpeta + revisar\ + _otros\
#            registro_movimientos.csv (cada movimiento hecho, para poder deshacerlo con B5)
# ============================================================
import os
import csv
import pandas as pd   # pandas: leer el plan y verificar

from config import DATOS as carpeta, RAIZ   # rutas comunes del pipeline (ver config.py)
plan = pd.read_csv(os.path.join(carpeta, "plan_movimientos.csv"))
ruta_registro = os.path.join(carpeta, "registro_movimientos.csv")

# --- Paso B4.1: Comprobaciones antes de tocar nada ---
falta_origen = plan[~plan["origen"].map(os.path.exists)]
cambia = plan[plan["origen"] != plan["destino"]]
ya_ocupado = cambia[cambia["destino"].map(os.path.exists)]
bytes_antes = sum(os.path.getsize(r) for r in plan["origen"])
print(f"Archivos en el plan: {len(plan)} | sin origen: {len(falta_origen)} | destino ya ocupado: {len(ya_ocupado)}")
assert falta_origen.empty and ya_ocupado.empty, "El plan no es seguro: no se movió nada"
assert not os.path.exists(ruta_registro), "Ya existe un registro: ¿se ejecutó antes? No se movió nada"

# --- Paso B4.2: Mover uno por uno y anotar cada movimiento en el registro ---
# os.rename(): cambia nombre y ubicación sin copiar el contenido (mismo disco).
#   Si el destino ya existe, falla en vez de sobrescribir.
os.makedirs(os.path.join(RAIZ, "revisar"), exist_ok=True)
os.makedirs(os.path.join(RAIZ, "_otros"), exist_ok=True)
hechos = 0
with open(ruta_registro, "w", newline="", encoding="utf-8-sig") as f:
    registro = csv.writer(f)
    registro.writerow(["id", "origen", "destino"])
    for r in cambia.itertuples():
        os.rename(r.origen, r.destino)
        registro.writerow([r.id, r.origen, r.destino])
        f.flush()
        hechos += 1
print("Movidos o renombrados:", hechos)

# --- Paso B4.3: Borrar las carpetas que quedaron vacías (solo si están vacías) ---
borradas = 0
for actual, subcarpetas, archivos in os.walk(RAIZ, topdown=False):
    if actual in (RAIZ, os.path.join(RAIZ, "revisar"), os.path.join(RAIZ, "_otros")):
        continue
    try:
        os.rmdir(actual)        # os.rmdir() falla si la carpeta tiene algo: no puede borrar archivos
        borradas += 1
    except OSError:
        pass
print("Carpetas vacías eliminadas:", borradas)

# --- Paso B4.4: Verificar ---
existen = plan["destino"].map(os.path.exists).sum()
bytes_despues = sum(os.path.getsize(r) for r in plan["destino"])
sueltos = [n for n in os.listdir(RAIZ) if os.path.isfile(os.path.join(RAIZ, n))]
print(f"Destinos que existen: {existen} de {len(plan)} | bytes antes = después: {bytes_antes == bytes_despues}")
print(f"En la raíz: {len(sueltos)} | en revisar: {len(os.listdir(os.path.join(RAIZ, 'revisar')))} | "
      f"en _otros: {len(os.listdir(os.path.join(RAIZ, '_otros')))} | "
      f"subcarpetas que quedan: {[d for d in os.listdir(RAIZ) if os.path.isdir(os.path.join(RAIZ, d))]}")
