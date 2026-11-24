# ============================================================
# PASO B2c: Clasificar los libros con Claude (Dewey de 3 cifras y datos de catálogo)
# Insumo:    datos\clasificacion\bloque_1..3.csv (Proceso B2)
# Resultado: datos\clasificacion\resultado_1..3.tsv (los lee el Proceso B3)
# Requiere:  Claude Code instalado (comando "claude") con la sesión iniciada
# Nota:      en la primera ejecución (23/11/2026) este paso lo hicieron 3 agentes dentro de
#            una sesión de Claude Code con el mismo prompt; este script lo automatiza con "claude -p".
# ============================================================

$repo = $PSScriptRoot
$plantilla = Get-Content (Join-Path $repo "prompts\clasificar_dewey.md") -Raw -Encoding UTF8
$bloques = Get-ChildItem (Join-Path $repo "datos\clasificacion") -Filter "bloque_*.csv"
if (-not $bloques) { throw "No hay bloques: corre antes b2_fichas.py" }

# --- Paso B2c.1: Un proceso de Claude por bloque, en paralelo ---
# Start-Job: lanza cada bloque en segundo plano para que los 3 avancen a la vez.
# El prompt va por la entrada estándar (|) para que sus comillas y saltos de línea lleguen intactos.
# --allowedTools "Read,Write": Claude solo puede leer el bloque y escribir su resultado.
$trabajos = foreach ($bloque in $bloques) {
    $n = $bloque.BaseName -replace "bloque_", ""
    $salida = Join-Path $bloque.DirectoryName "resultado_$n.tsv"
    $prompt = $plantilla.Replace("{ENTRADA}", $bloque.FullName).Replace("{SALIDA}", $salida)
    Start-Job -Name "bloque_$n" -ScriptBlock {
        param($texto)
        $texto | claude -p --model sonnet --allowedTools "Read,Write"
    } -ArgumentList $prompt
}

# --- Paso B2c.2: Esperar a los 3 y mostrar el informe de cada uno ---
$trabajos | Wait-Job | ForEach-Object {
    "=== $($_.Name) ==="
    Receive-Job $_
}

# --- Paso B2c.3: Verificar que existan los 3 resultados ---
$resultados = Get-ChildItem (Join-Path $repo "datos\clasificacion") -Filter "resultado_*.tsv"
"Resultados escritos: $($resultados.Count) de $($bloques.Count)"
