Tarea: catalogar libros de una biblioteca personal como lo haría un bibliotecólogo, asignando a cada uno su clase Dewey (DDC 23) de 3 cifras y sus datos de catálogo. Es trabajo de juicio: lee cada fila y decide con tu conocimiento bibliográfico (qué libro es, de qué trata, cómo lo clasificaría la Library of Congress/OCLC). NO escribas un script de reglas ni de palabras clave. No navegues por internet.

ENTRADA: {ENTRADA} (CSV con comillas). Columnas: id, carpeta_origen (carpeta donde el dueño lo tenía: pista temática), nombre (nombre del archivo; casi siempre "Autor - Título (año, editorial)"), paginas, meta_titulo, meta_autor, meta_fecha, idioma, editorial, isbn, texto_inicio (comienzo del texto del libro; solo viene cuando el nombre del archivo no es claro: úsalo para identificar el libro).

SALIDA: escribe {SALIDA}, separado por TABULADORES, con este encabezado exacto:
id	dewey	apellido	anio	titulo_corto	autor_completo	titulo_completo	editorial	idioma	confianza
Una fila por cada id de la entrada (mismo número de filas, ninguno omitido ni repetido). Ningún valor puede contener tabuladores ni saltos de línea. No uses comillas.

REGLAS POR COLUMNA
- dewey: exactamente 3 cifras como texto (p. ej. 004, 193, 833). Elige la sección de 3 cifras que correspondería según la práctica de LC/OCLC con DDC 23.
- apellido: apellido del primer autor. Si es una obra colectiva sin autor, el primer editor (p. ej. un "Heidegger-Handbuch" editado por Thomä → Thomä). Si es una edición de las obras de un autor clásico (Nietzsche, Sämtliche Briefe, ed. Colli) → el autor de la obra (Nietzsche). Autores antiguos por su nombre común (Plato, Plotinus, Heraclitus, Aristotle). Autor institucional → sigla o nombre corto (OECD, UN, FAO, PMI, IMF, World Bank, CEPAL, MINSA). Apellidos compuestos tal cual (Vargas Llosa, van de Walle). Sin autor identificable → primera palabra significativa del título.
- anio: año de ESTA edición (4 cifras), tomado del nombre o de los metadatos; si hay dos años como "(2017_2008)" usa el primero; si no se puede saber, escribe sf. No completes el año de memoria.
- titulo_corto: solo el título principal (sin subtítulo ni colección), en el idioma original, máximo 6 palabras. Si es un volumen de una obra en varios tomos, agrega el número (p. ej. "Gesammelte Schriften 5", "The Analytic Tradition in Philosophy 3", "Musik und Mathematik I 2").
- autor_completo: "Apellido, Nombre; Apellido, Nombre" (máximo 3, luego "et al."). Agrega " (ed.)" a cada editor.
- titulo_completo: título con subtítulo, idioma original.
- editorial: nombre corto de la editorial (o vacío si no se sabe).
- idioma: código ISO 639-1 del texto del libro (es, en, de, fr, it, pt, la...).
- confianza: alta, o baja si dudas de la clase Dewey o no pudiste identificar el libro.

GUÍA DEWEY
- Filósofos individuales y obras sobre ellos van por época y país: 182 presocráticos (Heráclito), 183 sofistas y Sócrates, 184 Platón, 185 Aristóteles, 186 escépticos y neoplatónicos (Plotino), 188 estoicos, 189 filosofía medieval; 191 EE. UU./Canadá, 192 Islas Británicas, 193 Alemania y Austria (Kant, Fichte, Hegel, Schelling, Schopenhauer, Nietzsche, Husserl, Heidegger, Adorno, Gabriel...), 194 Francia, 195 Italia, 196 España y Portugal, 197 Rusia, 199 otros (América Latina). Sigue la práctica de LC en casos dudosos (p. ej. Wittgenstein suele ir a 192).
- Filosofía por tema: 100 general, 101 teoría, 109 historia de la filosofía en general, 110/111 metafísica y ontología, 121 epistemología y filosofía del lenguaje, 128 filosofía de la mente/ser humano, 146 filosofía analítica, 160 lógica, 170 ética; filosofía política 320; estética 111.85 o 701 según el enfoque; filosofía de la matemática 510.
- 000: 001 conocimiento e investigación, 003 sistemas y decisión, 004 informática, 005 programación y software, 006 IA y temas especiales, 020 bibliotecología, 070 periodismo y medios.
- 300: 301-306 sociología y cultura (303 cambio social y tecnología, 306 cultura e instituciones), 320 ciencia política, 323 derechos, 325 migración, 327 relaciones internacionales, 330 economía, 332 finanzas, 338 economía de la producción y del desarrollo, 339 macroeconomía y pobreza, 340s derecho (341 organismos internacionales), 350-354 administración pública (351 administración pública general, 352 aspectos generales de la gestión pública), 355 asuntos militares, 362 problemas sociales y servicios de salud/bienestar, 363 seguridad pública y drogas, 364 crimen, 370 educación.
- 500: 501 filosofía de la ciencia, 510 matemática, 511 lógica matemática, 519 probabilidad y estadística, 530 física, 570 biología, 571 fisiología y biología del desarrollo, 576 evolución.
- 600: 610 medicina, 614 salud pública, 650-658 gestión empresarial (658 dirección, proyectos, procesos, calidad).
- 700: 701 filosofía del arte, 709 historia del arte, 720 arquitectura, 741 dibujo y cómic, 745 diseño, 750 pintura, 770 fotografía, 780 música (781 teoría, armonía, géneros como el jazz y los play-along; 787 instrumentos de cuerda, guitarra), 791 cine, 792 teatro.
- 800: idioma + forma: 810 EE. UU., 820 inglés, 830 alemán, 839 otras germánicas (noruego, sueco), 840 francés, 850 italiano, 860 español (incluye América Latina), 869 portugués, 880 griego/latín clásicos; última cifra = forma: 1 poesía, 2 teatro, 3 ficción, 4 ensayo, 8 misceláneos. Teoría y crítica literaria 801/809.
- 900: 901 filosofía de la historia, 909 historia universal, 930 mundo antiguo, 940 Europa (943 Alemania), 970 América del Norte, 980 América del Sur (985 Perú).

Al terminar responde solo con: filas escritas (y confirma que coinciden con la entrada), conteo por centena Dewey (000, 100, ... 900) y cuántas filas con confianza baja.
