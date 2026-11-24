# ============================================================
# Configuración común del pipeline (la usan todos los scripts b1 ... b5)
# ============================================================
import os

# Carpeta de la biblioteca que se va a ordenar.
# Se puede cambiar sin tocar el código con la variable de entorno BIBLIOTECA_RAIZ.
RAIZ = os.environ.get("BIBLIOTECA_RAIZ", r"D:\1_Lib")

# Carpeta donde el pipeline guarda sus tablas intermedias (inventario, fichas, catálogo, plan, registro).
# Está en .gitignore: contiene el listado personal de libros y no se sube a GitHub.
DATOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos")
os.makedirs(os.path.join(DATOS, "clasificacion"), exist_ok=True)
