# Autores con libros en más de una clase Dewey (solo lectura; para revisar coherencia entre bloques)
import os
import pandas as pd  # pandas: agrupar por autor

from config import DATOS as carpeta   # carpeta de datos del pipeline (ver config.py)
cat = pd.read_excel(os.path.join(carpeta, "catalogo_biblioteca.xlsx"), sheet_name="Catálogo", dtype=str)
cat = cat[cat["Formato"] != ".mp3"]
cat["apellido"] = cat["Archivo nuevo"].str.split("_").str[1]
varias = cat.groupby("apellido")["Signatura"].nunique()
for apellido in varias[varias > 1].index:
    print(f"\n{apellido}:")
    for _, r in cat[cat["apellido"] == apellido].iterrows():
        print(f"   {r['Signatura']} | {str(r['Título completo'])[:80]}")
