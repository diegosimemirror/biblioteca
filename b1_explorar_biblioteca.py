# ============================================================
# PROCESO B1: Explorar la biblioteca virtual (solo lectura: no mueve ni renombra nada)
# Insumo:    carpeta D:\1_Lib
# Resultado: inventario_biblioteca.csv + informe en pantalla
# ============================================================
import os
import re
import zipfile                       # zipfile: un EPUB es un ZIP; se lee su ficha interna (metadatos)
import importlib.util
import pandas as pd                  # pandas: armar y resumir el inventario

from config import RAIZ as raiz, DATOS as salida   # rutas comunes del pipeline (ver config.py)

# --- Paso B1.1: ¿Qué paquetes hay para leer PDF? (solo se comprueba, no se instala nada) ---
for paquete in ["pypdf", "PyPDF2", "fitz"]:
    print(f"Paquete {paquete}: {'disponible' if importlib.util.find_spec(paquete) else 'no instalado'}")

# --- Paso B1.2: Inventario de archivos ---
filas = []
for carpeta, _, archivos in os.walk(raiz):
    for nombre in archivos:
        ruta = os.path.join(carpeta, nombre)
        base, ext = os.path.splitext(nombre)
        filas.append({"ruta": ruta, "carpeta": os.path.relpath(carpeta, raiz), "nombre": nombre,
                      "base": base, "ext": ext.lower(), "bytes": os.path.getsize(ruta)})
inv = pd.DataFrame(filas)

# --- Paso B1.3: Clasificar el tipo de nombre ---
libros = inv["ext"].isin([".pdf", ".epub", ".djvu", ".mobi", ".azw3"])
basura_mac = inv["nombre"].str.startswith("._") | inv["ruta"].str.contains("__MACOSX", regex=False)
patron_autor_titulo = inv["base"].str.contains(" - ") | inv["base"].str.contains(r"\{.+\}\(", regex=True)
inv["tipo"] = "otro (no libro)"
inv.loc[libros & patron_autor_titulo, "tipo"] = "libro: nombre con autor y título"
inv.loc[libros & ~patron_autor_titulo, "tipo"] = "libro: nombre sin patrón claro"
inv.loc[basura_mac, "tipo"] = "basura de Mac (._ / __MACOSX)"
print("\n", inv["tipo"].value_counts().to_string())

print("\n--- Libros con nombre sin patrón claro (muestra de 30) ---")
for n in inv.loc[inv["tipo"] == "libro: nombre sin patrón claro", "nombre"].head(30):
    print("  ", n[:110])

print("\n--- Archivos que no son libros ---")
print(inv.loc[~libros | basura_mac, ["carpeta", "nombre", "bytes"]].to_string(max_colwidth=70))

# --- Paso B1.4: Posibles duplicados (mismo tamaño exacto en bytes) ---
reales = inv[libros & ~basura_mac]
mismo_tamano = reales[reales["bytes"].duplicated(keep=False)].sort_values("bytes")
print(f"\n--- Posibles duplicados (mismo tamaño): {len(mismo_tamano)} archivos ---")
print(mismo_tamano[["bytes", "nombre"]].to_string(max_colwidth=90))

# --- Paso B1.5: ¿Los EPUB traen ficha interna (título, autor, idioma, materia)? ---
def ficha_epub(ruta):
    try:
        with zipfile.ZipFile(ruta) as z:
            opf = next((n for n in z.namelist() if n.endswith(".opf")), None)
            texto = z.read(opf).decode("utf-8", "ignore") if opf else ""
        campos = {c: bool(re.search(rf"<dc:{c}[^>]*>[^<]+<", texto)) for c in ["title", "creator", "language", "subject"]}
        return campos
    except Exception:
        return None
epubs = reales[reales["ext"] == ".epub"]
fichas = [ficha_epub(r) for r in epubs["ruta"]]
ok = [f for f in fichas if f]
print(f"\nEPUB con ficha legible: {len(ok)} de {len(epubs)} | con autor: {sum(f['creator'] for f in ok)} | "
      f"con idioma: {sum(f['language'] for f in ok)} | con materia: {sum(f['subject'] for f in ok)}")

inv.to_csv(os.path.join(salida, "inventario_biblioteca.csv"), index=False, encoding="utf-8-sig")
