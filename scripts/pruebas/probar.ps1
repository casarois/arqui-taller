# Pruebas de regresion de los scripts "listos" del taller.
# Uso:  .\probar.ps1                 (todas)
#       .\probar.ps1 -Solo holgura   (las pruebas con ese nombre o de ese script; admite comodines: -Solo "holgura_*")
# Por cada archivo de prueba hace una copia nueva en salida\<aaaammdd_hhmmss>\, la abre con abrir_rhino.ps1, ejecuta
# los casos (casos\*.py, imprimen "RESULTADO {json}"), compara con esperado.json y cierra ese Rhino sin guardar.
# Las pruebas de solo lectura del mismo archivo comparten Rhino; las que modifican (modifica=true) van en su copia.
# Salida: una linea por prueba (OK / FALLO) y "PRUEBAS: n OK, m FALLO". Codigo 0 si todo OK, 1 si no, 2 si no hay pruebas.
#       -Esperado otro.json      (otra lista de pruebas; por defecto esperado.json de esta carpeta)
param([string]$Solo = "", [string]$Esperado = "")

$raiz    = $PSScriptRoot
$puente  = Join-Path (Split-Path $raiz -Parent) "puente"
$abrir   = Join-Path $puente "abrir_rhino.ps1"
$rhino   = Join-Path $puente "rhino.ps1"
$espRuta = if ($Esperado) { (Resolve-Path $Esperado).Path } else { Join-Path $raiz "esperado.json" }
$casos   = Join-Path $raiz "casos"
$utf8    = New-Object Text.UTF8Encoding $false
$inv     = [Globalization.CultureInfo]::InvariantCulture
$t0      = Get-Date

function Fmt($v) {
    if ($null -eq $v) { return "null" }
    if ($v -is [double] -or $v -is [decimal] -or $v -is [single]) { return ([double]$v).ToString("0.####", $inv) }
    return [string]::Format($inv, "{0}", $v)
}

function Comparar($esperado, $obt) {
    # Devuelve @(okTodo, [lista de textos]) comparando cada clave esperada con el JSON obtenido
    $textos = @(); $ok = $true
    foreach ($pr in $esperado.PSObject.Properties) {
        $k = $pr.Name; $e = $pr.Value
        $prop = $obt.PSObject.Properties[$k]
        if ($null -eq $prop) { $ok = $false; $textos += "$k=FALTA"; continue }
        $v = $prop.Value; $bien = $true; $desc = ""
        if ($null -ne $e.PSObject.Properties["valor"]) {
            $tol = 0.0; if ($null -ne $e.PSObject.Properties["tol"]) { $tol = [double]$e.tol }
            if ($null -eq $v) { $bien = $false } else { $bien = ([math]::Abs([double]$v - [double]$e.valor) -le ($tol + 1e-9)) }
            $desc = "$(Fmt $e.valor) +-$(Fmt $tol)"
        } elseif ($null -ne $e.PSObject.Properties["igual"]) {
            $bien = ((Fmt $v) -eq (Fmt $e.igual)); $desc = "= $(Fmt $e.igual)"
        } else {
            $partes = @()
            if ($null -ne $e.PSObject.Properties["min"]) { $partes += ">= $(Fmt $e.min)"; if ($null -eq $v -or [double]$v -lt [double]$e.min) { $bien = $false } }
            if ($null -ne $e.PSObject.Properties["max"]) { $partes += "<= $(Fmt $e.max)"; if ($null -eq $v -or [double]$v -gt [double]$e.max) { $bien = $false } }
            $desc = $partes -join " y "
        }
        if ($bien) { $textos += "$k=$(Fmt $v)" } else { $ok = $false; $textos += "$k=$(Fmt $v) (esperado $desc)" }
    }
    return @($ok, $textos)
}

$cfg = [IO.File]::ReadAllText($espRuta, $utf8) | ConvertFrom-Json
$pruebas = @($cfg.pruebas)
if ($Solo) { $pruebas = @($pruebas | Where-Object { $_.nombre -like $Solo -or $_.script -like $Solo }) }
if ($pruebas.Count -eq 0) { Write-Output "Ninguna prueba coincide con '$Solo'"; exit 2 }

# Grupos: un Rhino por archivo para las de solo lectura; uno por prueba para las que modifican
$grupos = New-Object System.Collections.ArrayList
$porArchivo = @{}
foreach ($p in $pruebas) {
    if ($p.modifica) { [void]$grupos.Add([pscustomobject]@{ Nombre = $p.nombre; Archivo = $p.archivo; Pruebas = @($p) }); continue }
    if ($porArchivo.ContainsKey($p.archivo)) { $porArchivo[$p.archivo].Pruebas += $p; continue }
    $g = [pscustomobject]@{ Nombre = ([IO.Path]::GetFileNameWithoutExtension($p.archivo) + "_lectura"); Archivo = $p.archivo; Pruebas = @($p) }
    $porArchivo[$p.archivo] = $g; [void]$grupos.Add($g)
}

$sello = Get-Date -Format "yyyyMMdd_HHmmss"
$base = Join-Path (Join-Path $raiz "salida") $sello
New-Item -ItemType Directory -Force $base | Out-Null
$comun = [IO.File]::ReadAllText((Join-Path $casos "_comun.py"), $utf8)
$resultados = New-Object System.Collections.ArrayList
Write-Output "Pruebas en $base"

foreach ($g in $grupos) {
    $dirG = Join-Path $base $g.Nombre
    New-Item -ItemType Directory -Force $dirG | Out-Null
    $orig = Join-Path (Join-Path $raiz "archivos") $g.Archivo
    $rp = 0; $fallo_grupo = ""
    try {
        if (-not (Test-Path $orig)) { throw "no existe el archivo de prueba $orig" }
        $copia = Join-Path $dirG $g.Archivo
        Copy-Item $orig $copia -ErrorAction Stop
        (Get-Item $copia -ErrorAction Stop).IsReadOnly = $false                      # solo la copia; el original sigue en solo lectura
        $sal = (& $abrir -Archivo $copia) -join " "
        if ($sal -match "PID (\d+)") { $rp = [int]$Matches[1] }
        if ($sal -notmatch "puerto \d+") { throw "no abre Rhino: $sal" }
        Write-Output "  $($g.Nombre): Rhino $rp abierto"
        foreach ($p in $g.Pruebas) {
            $dirP = Join-Path $dirG $p.nombre
            $pre = "NOMBRE_PRUEBA = r'$($p.nombre)'`nSALIDA = r'$dirP'`nESPERADO = r'$espRuta'`n"
            $codigo = $pre + $comun + "`n" + [IO.File]::ReadAllText([IO.Path]::Combine($casos, $p.caso), $utf8)
            $ti = Get-Date
            $out = @((@(& $rhino -Id $rp -Codigo $codigo) -join "`n") -split "\r?\n")
            $seg = [int]((Get-Date) - $ti).TotalSeconds
            $linea = $out | Where-Object { $_ -match "^RESULTADO " } | Select-Object -Last 1
            if (-not $linea) {
                $err = ((@($out | Where-Object { $_.Trim() }) | Select-Object -Last 3) -join " / ")
                [void]$resultados.Add([pscustomobject]@{ Nombre = $p.nombre; Ok = $false; Texto = "sin RESULTADO: $err"; Seg = $seg }); continue
            }
            $obt = $linea.Substring(10) | ConvertFrom-Json
            $c = Comparar $p.esperado $obt
            [void]$resultados.Add([pscustomobject]@{ Nombre = $p.nombre; Ok = $c[0]; Texto = ($c[1] -join ", "); Seg = $seg })
        }
    } catch {
        $fallo_grupo = $_.Exception.Message
    } finally {
        if ($rp) {
            $cer = (& $rhino -Id $rp -Cerrar) -join " "
            if ($cer -notmatch "cerrado") { Write-Output "  AVISO: $cer" }
        }
    }
    if ($fallo_grupo) {
        foreach ($p in $g.Pruebas) {
            if (-not ($resultados | Where-Object Nombre -eq $p.nombre)) {
                [void]$resultados.Add([pscustomobject]@{ Nombre = $p.nombre; Ok = $false; Texto = "error: $fallo_grupo"; Seg = 0 })
            }
        }
    }
}

Write-Output ""
$nOk = 0; $nMal = 0
foreach ($r in $resultados) {
    if ($r.Ok) { $nOk++; $e = "OK   " } else { $nMal++; $e = "FALLO" }
    Write-Output ("{0} {1,-22} {2,3} s  {3}" -f $e, $r.Nombre, $r.Seg, $r.Texto)
}
Write-Output ("Tiempo total: {0} s | salida: {1}" -f [int]((Get-Date) - $t0).TotalSeconds, $base)
Write-Output "PRUEBAS: $nOk OK, $nMal FALLO"
if ($nMal -gt 0) { exit 1 } else { exit 0 }
