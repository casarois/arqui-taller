# Cliente del puente: envia codigo Python a un Rhino abierto con puente_rhino.py.
# Uso:  .\rhino.ps1 -Codigo 'print(sc.doc.Name)'      .\rhino.ps1 -Archivo script.py
#       .\rhino.ps1 -Lista                            (Rhinos con puente y su documento)
#       -Doc "parte milan"  o  -Id 1234              (elegir Rhino si hay varios)
#       .\rhino.ps1 -Id 1234 -Cerrar [-Guardar]       (cierre normal; sin -Guardar descarta lo no guardado)
param([string]$Codigo, [string]$Archivo, [switch]$Lista, [string]$Doc, [int]$Id = 0, [int]$Puerto = 0,
      [switch]$Cerrar, [switch]$Guardar)

function Enviar([int]$p, [string]$code) {
    $json = @{ code = $code } | ConvertTo-Json -Compress
    $bytes = (New-Object Text.UTF8Encoding $false).GetBytes($json)
    $c = New-Object Net.Sockets.TcpClient
    try { $c.Connect("127.0.0.1", $p) } catch { return $null }
    $s = $c.GetStream(); $s.Write($bytes, 0, $bytes.Length); $c.Client.Shutdown([Net.Sockets.SocketShutdown]::Send)
    $txt = (New-Object IO.StreamReader($s, [Text.Encoding]::UTF8)).ReadToEnd(); $c.Close()
    return ($txt | ConvertFrom-Json)
}

# Rhinos registrados y vivos (borra registros de Rhinos cerrados)
$reg = Join-Path $env:LOCALAPPDATA "puente_rhino"
$vivos = @()
if (-not $Puerto) {
    foreach ($f in Get-ChildItem $reg -Filter *.json -ErrorAction SilentlyContinue) {
        $e = Get-Content $f.FullName -Raw | ConvertFrom-Json
        if (Get-Process -Id $e.pid -ErrorAction SilentlyContinue) {
            $r = Enviar $e.port 'print((sc.doc.Name or "(sin guardar)") + "|" + (sc.doc.Path or ""))'
            if ($r) { $n, $ruta = $r.out.Trim() -split '\|', 2
                      $vivos += [pscustomobject]@{ Pid = $e.pid; Puerto = $e.port; Documento = $n; Ruta = $ruta } }
        } else { Remove-Item $f.FullName -ErrorAction SilentlyContinue }
    }
}
if ($Lista) { if ($vivos) { $vivos | Format-Table -AutoSize | Out-String -Width 250 } else { "Ningun Rhino con puente" }; exit 0 }

if (-not $Puerto) {
    $sel = $vivos
    if ($Id) { $sel = @($vivos | Where-Object Pid -eq $Id) }
    if ($Doc) { $sel = @($vivos | Where-Object { $_.Documento -like "*$Doc*" -or $_.Ruta -like "*$Doc*" }) }
    if ($sel.Count -eq 0) { Write-Output "Ningun Rhino con puente coincide. Arranca puente_rhino.py en Rhino."; exit 2 }
    if ($sel.Count -gt 1) { Write-Output "Hay varios Rhinos; elige con -Doc o -Id:"; $sel | Format-Table -AutoSize | Out-String -Width 250; exit 3 }
    $Puerto = $sel[0].Puerto
    $PidSel = $sel[0].Pid
}

if ($Cerrar) {
    if (-not $PidSel) { Write-Output "Para -Cerrar elige el Rhino con -Id o -Doc (no con -Puerto)"; exit 2 }
    $g = if ($Guardar) { "Rhino.RhinoApp.RunScript('_-Save _Enter', False)`n" } else { "" }
    $code = "import Rhino`nd = Rhino.RhinoDoc.ActiveDoc`n$g" + "d.Modified = False`nRhino.RhinoApp.RunScript('_-Exit _Enter', False)"
    Enviar $Puerto $code | Out-Null
    $p = Get-Process -Id $PidSel -ErrorAction SilentlyContinue
    if ($p) { $null = $p.WaitForExit(30000) }
    if (Get-Process -Id $PidSel -ErrorAction SilentlyContinue) { Write-Output "Rhino $PidSel sigue abierto tras 30 s: cierralo a mano (no lo mates a la fuerza)"; exit 1 }
    Write-Output ("Rhino $PidSel cerrado" + $(if ($Guardar) { " (guardado)" } else { " (sin guardar cambios)" })); exit 0
}

if ($Archivo) { $Codigo = [IO.File]::ReadAllText($Archivo) }
$o = Enviar $Puerto $Codigo
if (-not $o) { Write-Output "Sin conexion en el puerto $Puerto"; exit 2 }
if ($o.out) { Write-Output $o.out.TrimEnd() }
if (-not $o.ok) { Write-Output "ERROR:`n$($o.error)"; exit 1 }
