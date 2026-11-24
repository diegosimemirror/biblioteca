# Prueba de que PyMuPDF puede leer los libros (solo lectura)
import pymupdf  # pymupdf: abrir PDF, EPUB y MOBI y leer sus metadatos y texto
import sys

print("Versión de PyMuPDF:", pymupdf.__version__)
for ruta in sys.argv[1:]:
    with pymupdf.open(ruta) as doc:
        print("\n", ruta[-70:])
        print("  páginas:", doc.page_count, "| metadatos:", {k: v for k, v in doc.metadata.items() if v and k in ("title", "author", "creationDate", "format")})
        print("  texto pág. 1:", doc[0].get_text()[:200].replace("\n", " "))
