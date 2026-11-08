# Hook PreToolUse (Agent) del equipo de arquitectura.
# - Bloquea (exit 2) cualquier lanzamiento de subagente que intente fijar 'model' (saltaria el modelo del archivo del subagente).
# - Bloquea subagentes genericos (general-purpose, claude, fork o sin tipo).
# - Registra cada encargo en arqui-taller\registro\equipo.log
$ErrorActionPreference = "Stop"
$raw = [Console]::In.ReadToEnd()
try { $d = $raw | ConvertFrom-Json } catch { exit 0 }
# Solo actua en sesiones dentro de arqui-taller (el hook vive en la configuracion de usuario).
$raiz = "C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller"
if (-not ([string]$d.cwd).StartsWith($raiz, [StringComparison]::OrdinalIgnoreCase)) { exit 0 }
$ti = $d.tool_input
$tipo = [string]$ti.subagent_type
$log = Join-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) "registro\equipo.log"
$linea = "{0} | {1} | model={2} | effort={3} | {4}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), ($(if ($tipo) { $tipo } else { "(sin tipo)" })), $ti.model, $ti.effort, $ti.description

# Separador cuando cambia la sesion: identificador corto + titulo de la sesion + carpeta
$sesionId = [string]$d.session_id
$ultimaArch = Join-Path (Split-Path $log -Parent) "equipo_ultima_sesion.txt"
$ultima = if (Test-Path $ultimaArch) { (Get-Content $ultimaArch -Raw).Trim() } else { "" }
if ($sesionId -and $sesionId -ne $ultima) {
    $titulo = ""
    if ($d.transcript_path) {
        $tituloArch = Join-Path ([string]$d.transcript_path -replace '\.jsonl$', '') "custom-title.json"
        if (Test-Path $tituloArch) { try { $titulo = (Get-Content $tituloArch -Raw -Encoding UTF8 | ConvertFrom-Json).customTitle } catch {} }
    }
    $corto = $sesionId.Substring(0, [Math]::Min(8, $sesionId.Length))
    $cab = "==================== SESION {0}{1} ====================" -f $corto, $(if ($titulo) { " | " + $titulo } else { "" })
    Add-Content -Path $log -Value @("", $cab, ("  carpeta: {0}   |   desde: {1}   |   id: {2}" -f $d.cwd, (Get-Date -Format "yyyy-MM-dd HH:mm"), $sesionId)) -Encoding UTF8
    Set-Content -Path $ultimaArch -Value $sesionId -Encoding UTF8
}

$prohibidos = @("", "general-purpose", "claude", "fork")
if ($ti.model) {
    Add-Content -Path $log -Value ("BLOQUEADO (model) " + $linea) -Encoding UTF8
    [Console]::Error.WriteLine("BLOQUEADO: no pases 'model' al lanzar un subagente. El modelo es obligatorio y lo fija .claude/agents/$tipo.md. Repite la llamada sin 'model'.")
    exit 2
}
if ($prohibidos -contains $tipo) {
    Add-Content -Path $log -Value ("BLOQUEADO (tipo) " + $linea) -Encoding UTF8
    [Console]::Error.WriteLine("BLOQUEADO: '$tipo' no es del equipo. Usa el subagente que toque segun la tabla 'Equipo (OBLIGATORIO)' de CLAUDE.md (o Explore para buscar archivos).")
    exit 2
}
Add-Content -Path $log -Value $linea -Encoding UTF8
exit 0
