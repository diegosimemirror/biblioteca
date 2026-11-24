# ============================================================
# PROCESO B5: Deshacer el Proceso B4 (devuelve cada archivo a su nombre y carpeta originales)
# Insumo:    registro_movimientos.csv (Proceso B4)
# Resultado: D:\1_Lib como estaba antes; el registro se renombra a registro_movimientos_deshecho.csv
# Uso:       solo si el usuario lo pide
# ============================================================
import os
import pandas as pd   # pandas: leer el registro

from config import DATOS as carpeta   # carpeta de datos del pipeline (ver config.py)
ruta_registro = os.path.join(carpeta, "registro_movimientos.csv")
registro = pd.read_csv(ruta_registro)

# Se recorre al revés (del último movimiento al primero) y se recrean las carpetas originales
devueltos = 0
for r in registro.iloc[::-1].itertuples():
    if os.path.exists(r.destino) and not os.path.exists(r.origen):
        os.makedirs(os.path.dirname(r.origen), exist_ok=True)
        os.rename(r.destino, r.origen)
        devueltos += 1
print(f"Devueltos a su lugar original: {devueltos} de {len(registro)}")
os.rename(ruta_registro, ruta_registro.replace(".csv", "_deshecho.csv"))
