# ============================================================
# PROCESO B2: Separar archivos y extraer la ficha de cada libro (solo lectura)
# Insumo:    inventario_biblioteca.csv (Proceso B1) y los archivos de D:\1_Lib
# Resultado: fichas.csv (todos los archivos con su destino y metadatos)
#            + clasificacion\bloque_1..3.csv (solo libros, para la clasificación Dewey)
# ============================================================
import os
import re
import hashlib                       # hashlib: "huella digital" del contenido para detectar copias idénticas
import zipfile                       # zipfile: leer la ficha interna de los EPUB y el contenido del zip
import warnings
import pandas as pd                  # pandas: tabla de fichas
import pymupdf                       # pymupdf: leer metadatos y texto de PDF, EPUB y MOBI

warnings.filterwarnings("ignore")
pymupdf.TOOLS.mupdf_display_errors(False)   # no llenar la pantalla con avisos de PDFs mal formados
from config import DATOS as carpeta   # carpeta de datos del pipeline (ver config.py)
inv = pd.read_csv(os.path.join(carpeta, "inventario_biblioteca.csv"))
inv.insert(0, "id", range(1, len(inv) + 1))
EXT_LIBRO = [".pdf", ".epub", ".djvu", ".mobi", ".azw3"]

# --- Paso B2.1: Destino de cada archivo ---
def destino(r):
    if r["nombre"].startswith("._") or "__MACOSX" in r["ruta"]:
        return "revisar", "basura de Mac"
    if r["ext"] == ".part":
        return "revisar", "descarga incompleta"
    if r["bytes"] == 0:
        return "revisar", "archivo vacío (0 bytes)"
    if r["ext"] == ".zip":
        return "revisar", "zip ya descomprimido"     # se confirma en el paso B2.2
    if r["ext"] == ".mp3" and "Hal Leonard" in r["ruta"]:
        return "biblioteca", "audio del libro Hal Leonard"
    if r["ext"] in EXT_LIBRO:
        return "biblioteca", "libro"
    return "_otros", "no es libro"
inv[["destino", "motivo"]] = inv.apply(lambda r: pd.Series(destino(r)), axis=1)

# --- Paso B2.2: Confirmar que el zip ya está descomprimido ---
for i in inv.index[inv["ext"] == ".zip"]:
    # Se compara por tamaño exacto en bytes: los nombres dentro de un zip hecho en Mac traen las tildes
    # en otra codificación (p. ej. "Cinturo╠ün") y no coinciden con los nombres en disco
    with zipfile.ZipFile(inv.at[i, "ruta"]) as z:
        dentro = {x.file_size for x in z.infolist() if x.filename.lower().endswith(".pdf") and "__MACOSX" not in x.filename}
    fuera = set(inv.loc[inv["ext"] == ".pdf", "bytes"])
    if not dentro or not dentro <= fuera:
        inv.loc[i, ["destino", "motivo"]] = ["_otros", "zip con contenido no descomprimido"]
    print(f"Zip {inv.at[i, 'nombre']}: {len(dentro)} PDF dentro, todos ya descomprimidos: {dentro <= fuera}")

# --- Paso B2.3: Copias idénticas (mismo tamaño y misma huella SHA-256) ---
def huella(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()

libros = inv[(inv["motivo"] == "libro")]
candidatos = libros[libros["bytes"].duplicated(keep=False)]
inv["huella"] = None
for i in candidatos.index:
    inv.at[i, "huella"] = huella(inv.at[i, "ruta"])
n_dup = 0
for _, grupo in inv[inv["huella"].notna()].groupby("huella"):
    if len(grupo) < 2:
        continue
    # Se conserva la copia sin "(1)" en el nombre y, entre esas, la de nombre más informativo (más largo)
    orden = grupo.assign(con_copia=grupo["base"].str.contains(r"\(\d\)$"), largo=grupo["nombre"].str.len())
    orden = orden.sort_values(["con_copia", "largo"], ascending=[True, False])
    for j in orden.index[1:]:
        inv.loc[j, ["destino", "motivo"]] = ["revisar", f"copia idéntica de id {orden.index[0] + 1}"]
        n_dup += 1
print("Copias idénticas confirmadas (van a revisar):", n_dup)

# --- Paso B2.4: Ficha de cada libro (metadatos internos, ISBN y comienzo del texto) ---
patron = inv["base"].str.contains(" - ") | inv["base"].str.contains(r"\{.+\}\(", regex=True)
inv["nombre_con_patron"] = patron
re_isbn = re.compile(r"ISBN[^\dX]{0,15}((?:97[89][-\s]?)?(?:\d[-\s]?){9}[\dX])")

def ficha_epub(ruta):
    try:
        with zipfile.ZipFile(ruta) as z:
            opf = next((n for n in z.namelist() if n.endswith(".opf")), None)
            t = z.read(opf).decode("utf-8", "ignore") if opf else ""
        campo = lambda c: "; ".join(re.findall(rf"<dc:{c}[^>]*>([^<]+)<", t))[:200]
        return {"meta_titulo": campo("title"), "meta_autor": campo("creator"), "meta_fecha": campo("date")[:10],
                "idioma": campo("language")[:10], "editorial": campo("publisher")[:80]}
    except Exception:
        return {}

def ficha(r):
    datos = {"paginas": None, "meta_titulo": "", "meta_autor": "", "meta_fecha": "", "idioma": "",
             "editorial": "", "isbn": "", "texto_inicio": ""}
    if r["ext"] == ".epub":
        datos.update(ficha_epub(r["ruta"]))
    if r["ext"] in (".pdf", ".epub", ".mobi"):
        try:
            with pymupdf.open(r["ruta"]) as doc:
                datos["paginas"] = doc.page_count
                m = doc.metadata or {}
                datos["meta_titulo"] = datos["meta_titulo"] or (m.get("title") or "")[:200]
                datos["meta_autor"] = datos["meta_autor"] or (m.get("author") or "")[:200]
                fecha = m.get("creationDate") or ""
                datos["meta_fecha"] = datos["meta_fecha"] or (fecha[2:6] if fecha.startswith("D:") else "")
                texto = " ".join(doc[p].get_text() for p in range(min(6, doc.page_count)))
                encontrado = re_isbn.search(texto)
                datos["isbn"] = re.sub(r"[-\s]", "", encontrado.group(1)) if encontrado else ""
                if not r["nombre_con_patron"]:
                    datos["texto_inicio"] = re.sub(r"\s+", " ", texto)[:450]
        except Exception as e:
            datos["texto_inicio"] = f"(no se pudo leer: {type(e).__name__})"
    return pd.Series(datos)

es_libro = inv["motivo"] == "libro"
print("Leyendo fichas de", es_libro.sum(), "libros...")
fichas = inv.loc[es_libro].apply(ficha, axis=1)
inv = inv.join(fichas)

# --- Paso B2.5: Guardar y armar los bloques para clasificar ---
inv.to_csv(os.path.join(carpeta, "fichas.csv"), index=False, encoding="utf-8-sig")
print("\nDestino de los archivos:")
print(inv.groupby(["destino", "motivo"]).size().to_string())

a_clasificar = inv[es_libro & (inv["destino"] == "biblioteca")].copy()
a_clasificar["carpeta_origen"] = a_clasificar["carpeta"]
cols = ["id", "carpeta_origen", "nombre", "paginas", "meta_titulo", "meta_autor", "meta_fecha",
        "idioma", "editorial", "isbn", "texto_inicio"]
os.makedirs(os.path.join(carpeta, "clasificacion"), exist_ok=True)
for k in range(3):
    bloque = a_clasificar.iloc[k::3][cols]
    bloque.to_csv(os.path.join(carpeta, "clasificacion", f"bloque_{k + 1}.csv"), index=False, encoding="utf-8")
    print(f"bloque_{k + 1}.csv: {len(bloque)} libros")
print("Con ISBN encontrado:", (a_clasificar["isbn"] != "").sum(), "| sin nombre claro:", (~a_clasificar["nombre_con_patron"]).sum())
