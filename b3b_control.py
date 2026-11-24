# Control de calidad del catálogo (solo lectura)
import os
import pandas as pd  # pandas: leer el catálogo y filtrar

from config import DATOS as carpeta   # carpeta de datos del pipeline (ver config.py)
cat = pd.read_excel(os.path.join(carpeta, "catalogo_biblioteca.xlsx"), sheet_name="Catálogo", dtype=str)

print("=== Nombres que recibieron sufijo -2 / -3 por repetirse ===")
base = cat["Archivo nuevo"].str.replace(r"-\d(\.\w+)$", r"\1", regex=True)
rep = cat[base.duplicated(keep=False) & base.str.match(r"^\d{3}_")]
for _, r in rep.sort_values("Archivo nuevo").iterrows():
    print(f"  {r['Archivo nuevo']:60.60} <- {r['Archivo original'][:70]}")

print("\n=== Audios ===")
for n in cat.loc[cat["Formato"] == ".mp3", "Archivo nuevo"].head(4):
    print("  ", n)

print("\n=== Muestra al azar (40) ===")
for _, r in cat.sample(40, random_state=11).sort_values("Archivo nuevo").iterrows():
    print(f"  {r['Archivo nuevo'][:62]:62} | {str(r['Título completo'])[:55]}")

print("\n=== Largo de nombres: máx", cat["Archivo nuevo"].str.len().max(), "| promedio", round(cat["Archivo nuevo"].str.len().mean()))
print("\n=== Divisiones con más libros ===")
print(cat["Signatura"].value_counts().head(15).to_string())
