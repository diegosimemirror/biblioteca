# ============================================================
# PROCESO B3: Armar el catálogo y los nombres nuevos (simulación: NO mueve ni renombra nada)
# Insumo:    fichas.csv (Proceso B2) + clasificacion\resultado_1..3.tsv (clasificación Dewey)
# Resultado: catalogo_biblioteca.xlsx (catálogo para revisar)
#            plan_movimientos.csv (origen -> destino de cada uno de los 604 archivos)
# ============================================================
import os
import re
import csv
import unicodedata                                  # unicodedata: quitar tildes (á -> a)
import pandas as pd                                 # pandas: unir tablas y exportar a Excel
from openpyxl.styles import Font                    # openpyxl: formato del Excel
from openpyxl.utils import get_column_letter

from config import DATOS as carpeta, RAIZ   # rutas comunes del pipeline (ver config.py)
fichas = pd.read_csv(os.path.join(carpeta, "fichas.csv"), dtype={"isbn": str})

# --- Paso B3.1: Juntar la clasificación de los 3 bloques ---
partes = [pd.read_csv(os.path.join(carpeta, "clasificacion", f"resultado_{k}.tsv"), sep="\t",
                      dtype=str, quoting=csv.QUOTE_NONE, keep_default_na=False) for k in (1, 2, 3)]
clas = pd.concat(partes, ignore_index=True)
clas["id"] = clas["id"].astype(int)
esperados = set(fichas.loc[fichas["motivo"] == "libro", "id"])
print(f"Clasificados: {len(clas)} | únicos: {clas['id'].nunique()} | esperados: {len(esperados)} | "
      f"faltan: {len(esperados - set(clas['id']))} | sobran: {len(set(clas['id']) - esperados)}")
mal_dewey = ~clas["dewey"].str.fullmatch(r"\d{3}")
mal_anio = ~clas["anio"].str.fullmatch(r"\d{4}|sf")
print("Dewey no válidos:", mal_dewey.sum(), "| años no válidos:", mal_anio.sum())
clas.loc[mal_anio, "anio"] = "sf"

# --- Paso B3.2: Limpiar textos para el nombre del archivo ---
# Antes: "Sämtliche Briefe: Kritische Studienausgabe" | Después: "Saemtliche-Briefe-Kritische-Studienausgabe"
ALEMAN = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue", "ß": "ss"})
def limpiar(texto, maximo=60):
    texto = str(texto).translate(ALEMAN)
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()   # quita tildes y letras no latinas
    texto = texto.replace("'", "").replace("’", "")                                     # Plato's -> Platos
    texto = re.sub(r"[^A-Za-z0-9]+", "-", texto).strip("-")                              # espacios y signos -> guion
    if len(texto) > maximo:                                                              # cortar en un guion, sin partir palabras
        texto = texto[:maximo].rsplit("-", 1)[0]
    return texto or "sin-dato"

# Los metadatos del archivo también traen "editorial" e "idioma": se renombran para que el catálogo use los de la clasificación
libros = (fichas[fichas["motivo"] == "libro"]
          .rename(columns={"editorial": "meta_editorial", "idioma": "meta_idioma"})
          .merge(clas, on="id", how="left"))
# ¿De dónde salió el año? Si no aparece en el nombre ni en los metadatos, lo puso la IA de memoria: se marca "estimado"
def fuente_anio(r):
    if r["anio"] == "sf":
        return "sin fecha"
    if r["anio"] in str(r["nombre"]) or str(r["meta_fecha"]).startswith(r["anio"]):
        return "archivo"
    return "estimado"
libros["anio_fuente"] = libros.apply(fuente_anio, axis=1)
print("Fuente del año:", libros["anio_fuente"].value_counts().to_dict())

# --- Paso B3.1b: Correcciones de coherencia entre bloques (misma obra o mismo tema en clases distintas) ---
titulo = libros["titulo_completo"].fillna("")
correcciones = [
    ("Musik und Mathematik (Kittler) en una sola clase", titulo.str.startswith("Musik und Mathematik"), "dewey", "780"),
    ("Filosofía del lenguaje siempre en 121", titulo.str.contains(r"(?i)^(?:the )?philosophy of language|sprachphilosophie|filosof[ií]a del lenguaje"), "dewey", "121"),
    ("La OCDE (Woodward) con los organismos internacionales", titulo.str.contains(r"(?i)organisation for economic co-operation"), "dewey", "341"),
    ("How to Take Smart Notes en una sola clase", titulo.str.startswith("How to Take Smart Notes"), "dewey", "001"),
    ("Fernando González con un solo apellido", libros["apellido"].str.contains(r"(?i)^gonz[aá]lez ochoa$"), "apellido", "González"),
]
libros["correccion"] = ""
for motivo, filas, campo, valor in correcciones:
    print(f"Corrección «{motivo}»: {filas.sum()} libros")
    libros.loc[filas, campo] = valor
    libros.loc[filas, "correccion"] = motivo
libros["nombre_nuevo"] = (libros["dewey"] + "_" + libros["apellido"].map(lambda t: limpiar(t, 30)) + "_" +
                          libros["anio"] + "_" + libros["titulo_corto"].map(limpiar) + libros["ext"])

# --- Paso B3.3: Los audios de Hal Leonard llevan la signatura de su libro + n.º y nombre de pista ---
# Hal Leonard es también la editorial de otros libros: se toma solo el PDF de la carpeta "Volume 049"
hal = libros[libros["ruta"].str.contains("Volume 049", regex=False) & (libros["ext"] == ".pdf")]
assert len(hal) == 1, "Se esperaba un solo libro de Hal Leonard"
base_hal = os.path.splitext(hal.iloc[0]["nombre_nuevo"])[0]
audios = fichas[fichas["motivo"] == "audio del libro Hal Leonard"].copy()
audios["nombre_nuevo"] = base_hal + "_pista-" + audios["base"].map(lambda b: limpiar(b, 50)) + audios["ext"]
for col in ["dewey", "apellido", "anio", "autor_completo", "editorial"]:
    audios[col] = hal.iloc[0][col]
audios["titulo_completo"] = hal.iloc[0]["titulo_completo"] + " (audio: " + audios["base"] + ")"
biblioteca = pd.concat([libros, audios], ignore_index=True)

# --- Paso B3.4: Evitar nombres repetidos (Windows no distingue mayúsculas) ---
biblioteca["clave"] = biblioteca["nombre_nuevo"].str.lower()
repetidos = biblioteca["clave"].duplicated(keep=False)
print("Nombres nuevos repetidos antes de corregir:", repetidos.sum())
for _, grupo in biblioteca[repetidos].groupby("clave"):
    for n, i in enumerate(grupo.index[1:], start=2):
        base, ext = os.path.splitext(biblioteca.at[i, "nombre_nuevo"])
        biblioteca.at[i, "nombre_nuevo"] = f"{base}-{n}{ext}"
assert not biblioteca["nombre_nuevo"].str.lower().duplicated().any()
assert not biblioteca["nombre_nuevo"].str.contains(" ").any(), "Hay nombres con espacios"

# --- Paso B3.5: Plan de movimientos (origen -> destino) para los 604 archivos ---
biblioteca["destino_ruta"] = biblioteca["nombre_nuevo"].map(lambda n: os.path.join(RAIZ, n))
resto = fichas[fichas["destino"].isin(["revisar", "_otros"])].copy()
resto["destino_ruta"] = resto.apply(lambda r: os.path.join(RAIZ, r["destino"], r["nombre"]), axis=1)
dup_resto = resto["destino_ruta"].str.lower().duplicated(keep=False)
resto.loc[dup_resto, "destino_ruta"] = resto[dup_resto].apply(
    lambda r: os.path.join(RAIZ, r["destino"], f"{r['id']}_{r['nombre']}"), axis=1)
plan = pd.concat([biblioteca[["id", "ruta", "destino_ruta"]], resto[["id", "ruta", "destino_ruta"]]])
plan.columns = ["id", "origen", "destino"]
assert len(plan) == len(fichas) and plan["id"].is_unique, "El plan no cubre los 604 archivos una sola vez"
plan.to_csv(os.path.join(carpeta, "plan_movimientos.csv"), index=False, encoding="utf-8-sig")
print(f"Plan: {len(plan)} archivos | biblioteca: {len(biblioteca)} | revisar: {(resto['destino'] == 'revisar').sum()} | "
      f"_otros: {(resto['destino'] == '_otros').sum()} | ya tienen el nombre final: {(plan['origen'] == plan['destino']).sum()}")

# --- Paso B3.6: Catálogo en Excel ---
DIVISIONES = {
    "000": "Informática y obras generales", "010": "Bibliografías", "020": "Bibliotecología", "030": "Enciclopedias",
    "050": "Publicaciones seriadas", "060": "Asociaciones y museos", "070": "Medios y periodismo", "080": "Colecciones",
    "090": "Manuscritos y libros raros", "100": "Filosofía", "110": "Metafísica", "120": "Epistemología",
    "130": "Parapsicología y ocultismo", "140": "Escuelas filosóficas", "150": "Psicología", "160": "Lógica",
    "170": "Ética", "180": "Filosofía antigua, medieval y oriental", "190": "Filosofía moderna occidental",
    "200": "Religión", "210": "Filosofía de la religión", "220": "Biblia", "230": "Cristianismo",
    "240": "Práctica cristiana", "250": "Órdenes e iglesias", "260": "Teología social", "270": "Historia del cristianismo",
    "280": "Denominaciones cristianas", "290": "Otras religiones", "300": "Ciencias sociales", "310": "Estadísticas",
    "320": "Ciencia política", "330": "Economía", "340": "Derecho", "350": "Administración pública y asuntos militares",
    "360": "Problemas y servicios sociales", "370": "Educación", "380": "Comercio y comunicaciones",
    "390": "Costumbres y folclore", "400": "Lenguas", "410": "Lingüística", "420": "Inglés", "430": "Alemán",
    "440": "Francés", "450": "Italiano", "460": "Español y portugués", "470": "Latín", "480": "Griego",
    "490": "Otras lenguas", "500": "Ciencias", "510": "Matemáticas", "520": "Astronomía", "530": "Física",
    "540": "Química", "550": "Ciencias de la Tierra", "560": "Paleontología", "570": "Biología", "580": "Botánica",
    "590": "Zoología", "600": "Tecnología", "610": "Medicina y salud", "620": "Ingeniería", "630": "Agricultura",
    "640": "Hogar y familia", "650": "Gestión", "660": "Ingeniería química", "670": "Manufactura",
    "680": "Manufactura específica", "690": "Construcción", "700": "Artes", "710": "Urbanismo y paisajismo",
    "720": "Arquitectura", "730": "Escultura", "740": "Dibujo y artes decorativas", "750": "Pintura",
    "760": "Grabado", "770": "Fotografía", "780": "Música", "790": "Recreación y artes escénicas",
    "800": "Literatura", "810": "Literatura estadounidense", "820": "Literatura inglesa", "830": "Literatura alemana",
    "840": "Literatura francesa", "850": "Literatura italiana", "860": "Literatura española y portuguesa",
    "870": "Literatura latina", "880": "Literatura griega", "890": "Otras literaturas", "900": "Historia",
    "910": "Geografía y viajes", "920": "Biografía", "930": "Historia antigua", "940": "Historia de Europa",
    "950": "Historia de Asia", "960": "Historia de África", "970": "Historia de América del Norte",
    "980": "Historia de América del Sur", "990": "Historia de otras regiones",
}
biblioteca["division"] = biblioteca["dewey"].str[:2] + "0"
biblioteca["division_nombre"] = biblioteca["division"].map(DIVISIONES)
biblioteca["clase_nombre"] = (biblioteca["dewey"].str[0] + "00").map(DIVISIONES)
catalogo = biblioteca.sort_values("nombre_nuevo")[[
    "dewey", "division_nombre", "nombre_nuevo", "autor_completo", "titulo_completo", "anio", "anio_fuente",
    "editorial", "idioma", "paginas", "isbn", "ext", "confianza", "correccion", "nombre", "carpeta"]]
catalogo.columns = ["Signatura", "Materia (división Dewey)", "Archivo nuevo", "Autor(es)", "Título completo", "Año",
                    "Fuente del año", "Editorial", "Idioma", "Páginas", "ISBN", "Formato", "Confianza",
                    "Corrección", "Archivo original", "Carpeta original"]
fuera = resto.sort_values(["destino", "motivo"])[["destino", "motivo", "nombre", "carpeta", "bytes"]]
fuera.columns = ["Va a", "Motivo", "Archivo", "Carpeta original", "Bytes"]
resumen = (biblioteca.groupby(["clase_nombre", "division", "division_nombre"]).size()
           .reset_index(name="Archivos").sort_values("division"))
resumen.columns = ["Clase", "División", "Materia", "Archivos"]

ruta_xlsx = os.path.join(carpeta, "catalogo_biblioteca.xlsx")
with pd.ExcelWriter(ruta_xlsx, engine="openpyxl") as xls:
    for nombre, tabla in [("Catálogo", catalogo), ("Resumen por materia", resumen), ("Revisar y otros", fuera)]:
        tabla.to_excel(xls, sheet_name=nombre, index=False)
        hoja = xls.sheets[nombre]
        hoja.freeze_panes = "A2"
        hoja.auto_filter.ref = hoja.dimensions
        for celda in hoja[1]:
            celda.font = Font(bold=True)
        for i, col in enumerate(tabla.columns, start=1):
            largo = max([len(str(col))] + [len(str(v)) for v in tabla[col].head(300)])
            hoja.column_dimensions[get_column_letter(i)].width = min(max(8, largo + 2), 60)
print("Catálogo:", ruta_xlsx)
print("\nPor clase Dewey:")
print(biblioteca.groupby("clase_nombre").size().reindex([DIVISIONES[f"{c}00"] for c in range(10)]).dropna().astype(int).to_string())
print("\nConfianza baja:", (biblioteca["confianza"] == "baja").sum())
print("\nMuestra de nombres nuevos (orden de estante):")
for n in catalogo["Archivo nuevo"].iloc[::45]:
    print("  ", n)
