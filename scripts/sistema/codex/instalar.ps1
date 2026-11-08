# Instala una entrada local sin copiar ni mover las fuentes comunes.
param(
    [string]$Paquete = "C:\Users\2402l\Documents\UNI\CLAUDE\migracion-codex\paquete",
    [string]$Destino = "C:\Users\2402l\Documents\UNI\CODEX\arqui-taller"
)
$ErrorActionPreference = "Stop"
$central = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\..\.."))
$permitido = [IO.Path]::GetFullPath("C:\Users\2402l\Documents\UNI\CODEX\arqui-taller")
$final = [IO.Path]::GetFullPath($Destino).TrimEnd('\')
if (-not [string]::Equals($final, $permitido, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Destino fuera de la carpeta expresamente elegida: $final"
}
if (-not (Test-Path -LiteralPath (Join-Path $Paquete "AGENTS.md"))) { throw "Falta paquete preparado" }

# No se sobrescribe ningun archivo local existente, ni se borra o mueve nada.
$files = @(Get-ChildItem -LiteralPath $Paquete -Recurse -File -Force)
foreach ($file in $files) {
    $rel = [IO.Path]::GetRelativePath($Paquete, $file.FullName)
    $out = Join-Path $final $rel
    if (Test-Path -LiteralPath $out) {
        if ((Get-FileHash -LiteralPath $out).Hash -ne (Get-FileHash -LiteralPath $file.FullName).Hash) {
            throw "Ya existe un archivo distinto; no se sobrescribe: $out"
        }
    }
}
New-Item -ItemType Directory -Path $final -Force | Out-Null
foreach ($file in $files) {
    $rel = [IO.Path]::GetRelativePath($Paquete, $file.FullName)
    $out = Join-Path $final $rel
    New-Item -ItemType Directory -Path (Split-Path $out -Parent) -Force | Out-Null
    if (-not (Test-Path -LiteralPath $out)) { Copy-Item -LiteralPath $file.FullName -Destination $out }
}

function Enlazar([string]$ruta, [string]$fuente) {
    $fuente = [IO.Path]::GetFullPath($fuente).TrimEnd('\')
    if (-not (Test-Path -LiteralPath $fuente -PathType Container)) { throw "Falta fuente: $fuente" }
    $item = Get-Item -LiteralPath $ruta -Force -ErrorAction SilentlyContinue
    if ($item) {
        $target = [string](@($item.Target)[0])
        if ($item.LinkType -ne "Junction" -or -not [string]::Equals($target.TrimEnd('\'), $fuente, [StringComparison]::OrdinalIgnoreCase)) {
            throw "No se sustituye un directorio o enlace diferente: $ruta"
        }
    } else {
        New-Item -ItemType Directory -Path (Split-Path $ruta -Parent) -Force | Out-Null
        New-Item -ItemType Junction -Path $ruta -Target $fuente | Out-Null
    }
}
foreach ($name in @('scripts', 'normas', 'proyectos')) {
    Enlazar (Join-Path $final $name) (Join-Path $central $name)
}
$registro = Join-Path $central "registro\codex"
New-Item -ItemType Directory -Path $registro -Force | Out-Null
Enlazar (Join-Path $final 'registro') $registro
$skills = Join-Path $central '.claude\skills'
foreach ($skill in Get-ChildItem -LiteralPath $skills -Directory) {
    if (Test-Path -LiteralPath (Join-Path $skill.FullName 'SKILL.md')) {
        Enlazar (Join-Path $final ".agents\skills\$($skill.Name)") $skill.FullName
    }
}
Enlazar (Join-Path $final '.agents\skills\control-uso') (Join-Path $central 'adaptadores\codex\skills\control-uso')
Write-Output "Instalado: $final | fuentes compartidas por Junction; ningun original sustituido"
