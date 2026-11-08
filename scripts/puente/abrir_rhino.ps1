# Abre un Rhino nuevo con un archivo, arranca el puente al inicio y espera a que responda.
# Uso:  .\abrir_rhino.ps1 -Archivo "C:\...\plano.3dm"   (devuelve PID y puerto; luego rhino.ps1 -Id <pid>)
param([Parameter(Mandatory)][string]$Archivo, [int]$Espera = 180)
$rhino = "C:\Program Files\Rhino 8\System\Rhino.exe"
$ini = Join-Path $PSScriptRoot "puente_iniciar.py"
if (-not (Test-Path $Archivo)) { Write-Output "No existe: $Archivo"; exit 2 }
if ($ini -match ' ') { Write-Output "La ruta de puente_iniciar.py no puede tener espacios"; exit 2 }
$p = Start-Process $rhino -ArgumentList "/nosplash", "/runscript=`"_-RunPythonScript $ini`"", "`"$Archivo`"" -PassThru
$reg = Join-Path $env:LOCALAPPDATA "puente_rhino\$($p.Id).json"
$t = 0
while (-not (Test-Path $reg) -and $t -lt $Espera) { Start-Sleep 2; $t += 2; if ($p.HasExited) { Write-Output "Rhino se cerró al arrancar"; exit 1 } }
if (-not (Test-Path $reg)) { Write-Output "Rhino abierto (PID $($p.Id)) pero el puente no respondió en $Espera s"; exit 1 }
$e = Get-Content $reg -Raw | ConvertFrom-Json
Write-Output "Rhino PID $($e.pid) | puerto $($e.port) | $([IO.Path]::GetFileName($Archivo)) | $t s"
