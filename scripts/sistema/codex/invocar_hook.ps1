# Entrada Windows independiente del shell que use Codex para ejecutar el hook.
param([Parameter(Mandatory)][string]$Taller, [string]$Registro)
$ErrorActionPreference = 'Stop'
$pythonHook = 'C:\Program Files\QGIS 3.44.14\apps\Python312\python.exe'
$scriptHook = Join-Path $PSScriptRoot 'hook_equipo.py'
# PS 5.1 usa ASCII para las tuberias nativas por defecto: preservar JSON UTF-8.
$OutputEncoding = New-Object System.Text.UTF8Encoding $false
[Console]::InputEncoding = $OutputEncoding
[Console]::OutputEncoding = $OutputEncoding
$jsonHook = [Console]::In.ReadToEnd()
$argsHook = @('-X', 'utf8', $scriptHook, '--taller', $Taller)
if ($Registro) { $argsHook += @('--registro', $Registro) }
$jsonHook | & $pythonHook @argsHook
exit $LASTEXITCODE
