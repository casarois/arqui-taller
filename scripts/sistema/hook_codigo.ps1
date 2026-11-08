# Hook PreToolUse (Write|Edit) del taller: anota el codigo improvisado.
# - Si en una sesion de arqui-taller se escribe o edita un .py FUERA de arqui-taller\scripts\,
#   lo anota en arqui-taller\registro\codigo_improvisado.log (fecha | agente | herramienta | ruta | lineas | primera linea).
# - Nunca bloquea (siempre exit 0). El orquestador pasa estas lineas a scripts\MEJORAS.md (regla 8 de CLAUDE.md).
$ErrorActionPreference = "Stop"
try {
    $raw = [Console]::In.ReadToEnd()
    $d = $raw | ConvertFrom-Json
    $raiz = "C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller"
    if (-not ([string]$d.cwd).StartsWith($raiz, [StringComparison]::OrdinalIgnoreCase)) { exit 0 }
    $ti = $d.tool_input
    $ruta = [string]$ti.file_path
    if (-not $ruta -or -not $ruta.EndsWith(".py", [StringComparison]::OrdinalIgnoreCase)) { exit 0 }
    $completa = [System.IO.Path]::GetFullPath($ruta)
    $scripts = (Join-Path $raiz "scripts") + "\"
    if ($completa.StartsWith($scripts, [StringComparison]::OrdinalIgnoreCase)) { exit 0 }

    $agente = [string]$d.agent_type
    if (-not $agente) { $agente = "(principal o sin tipo)" }
    $texto = if ($d.tool_name -eq "Write") { [string]$ti.content } else { [string]$ti.new_string }
    $lineas = @($texto -split "`n")
    $primera = ($lineas | Where-Object { $_.Trim() } | Select-Object -First 1)
    if ($primera) { $primera = $primera.Trim() } else { $primera = "" }
    if ($primera.Length -gt 100) { $primera = $primera.Substring(0, 100) + "..." }
    $linea = "{0} | {1} | {2} | {3} | {4} lineas | {5}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $agente, $d.tool_name, $completa, $lineas.Count, $primera

    $log = Join-Path $raiz "registro\codigo_improvisado.log"
    Add-Content -Path $log -Value $linea -Encoding UTF8
} catch { }
exit 0
