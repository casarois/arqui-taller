#! python3
"""rellenos.py — hatch sólido de las curvas cerradas de una capa, por debajo de las líneas.
Contrato: ver scripts/INDEX.md. Genérico: nada de un proyecto concreto; todo por parámetros o normas.
Dos usos:
- Una capa -> otra: main("PLANTA_10_MUROS_CORTE", "PLANTA_10_MUROS_CORTE_RELLENO").
  Si destino=None se deriva de origen y solo vale si el nombre existe en normas o en el documento:
  _ARISTAS->_RELLENOS, _CONTORNO->_RELLENO, origen+_RELLENO, origen+_RELLENOS. Si no, error (pásalo).
  El relleno queda justo detrás de las curvas de origen (DisplayOrder = mínimo de origen - 1).
- Planos de una sección/alzado: main(prefijo="SECCION_LONG") -> cada {P}_0N_..._ARISTAS de las plantillas
  de normas a su {P}_0N_..._RELLENOS. Orden de dibujo por profundidad: aristas 01 > relleno 01 > aristas 02 >
  relleno 02 > aristas 03 > relleno 03 (cambia el DisplayOrder de las aristas 02/03; no toca su geometría).
  Con origen y prefijo, los nombres sin prefijo se completan: main("01_PRIMER_PLANO_ARISTAS", prefijo="ALZADO_N").
Color y patrón: sólido, color por capa; la capa destino se crea con su definición de normas (nunca inventada).
Curvas cerradas dentro de otra cerrada de la misma capa = huecos (patios, interior de muros).
Curvas abiertas y no planas se ignoran y se cuentan. No borra ni modifica geometría; cada ejecución añade otra copia."""
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import Rhino.Geometry as rg
import System
import System.Drawing as sd
import os, sys
_S = r"C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller\scripts"
for _d in [os.path.join(_S, x) for x in os.listdir(_S)]:
    if os.path.isdir(_d) and _d not in sys.path: sys.path.insert(0, _d)   # import util desde cualquier subcarpeta
import util

def _capa(nombre, n):
    """Índice de la capa; si no existe y está en normas la crea con su definición. None si no se puede."""
    if not rs.IsLayer(nombre):
        df = util.definicion(nombre, n)
        if not df: return None
        rgb, grosor, linea = util._resolver(df[1], n)
        rs.AddLayer(nombre, sd.Color.FromArgb(*rgb))
        rs.LayerPrintColor(nombre, sd.Color.FromArgb(*rgb)); rs.LayerPrintWidth(nombre, grosor)
        try: rs.LayerLinetype(nombre, linea)
        except Exception: pass
    i = sc.doc.Layers.FindByFullPath(nombre, -1)
    return i if i >= 0 else sc.doc.Layers.FindName(nombre).Index

def _objetos(nombre):
    return [o for o in (sc.doc.Objects.FindByLayer(nombre) or []) if not o.IsDeleted] if rs.IsLayer(nombre) else []

def _solido():
    for hp in sc.doc.HatchPatterns:
        if not hp.IsDeleted and hp.FillType == Rhino.DocObjects.HatchPatternFillType.Solid: return hp.Index
    return sc.doc.HatchPatterns.Add(Rhino.DocObjects.HatchPattern.Defaults.Solid)

def _derivar(origen, n):
    cands = []
    if origen.endswith("_ARISTAS"): cands.append(origen[:-8] + "_RELLENOS")
    if origen.endswith("_CONTORNO"): cands.append(origen[:-9] + "_RELLENO")
    cands += [origen + "_RELLENO", origen + "_RELLENOS"]
    for c in cands:
        if util.definicion(c, n) or rs.IsLayer(c): return c
    return None

def _grupos(curvas, tol):
    """[(exterior, [huecos])]: profundidad par = contorno exterior, impar = hueco de su padre directo."""
    d = []
    for c in curvas:
        ok, pl = c.TryGetPlane(tol)
        bb = c.GetBoundingBox(True)
        d.append([c, pl, bb, bb.Diagonal.Length, 0, None])   # curva, plano, bbox, tamaño, profundidad, padre
    d.sort(key=lambda x: -x[3])
    for i, a in enumerate(d):
        for b in d[:i]:                                       # solo candidatos más grandes
            if b[3] <= a[3] or not b[2].Contains(a[2], False): continue
            if b[1].Normal.IsParallelTo(a[1].Normal, 0.01) == 0 or abs(b[1].DistanceTo(a[0].PointAtStart)) > tol * 10: continue
            if rg.Curve.PlanarClosedCurveRelationship(b[0], a[0], b[1], tol) == rg.RegionContainment.BInsideA:
                a[4] += 1
                if a[5] is None or b[3] < a[5][3]: a[5] = b
    out = {id(x): (x[0], []) for x in d if x[4] % 2 == 0}
    for x in d:
        if x[4] % 2 == 1 and x[5] is not None and id(x[5]) in out: out[id(x[5])][1].append(x[0])
    return list(out.values())

def _rellenar(origen, destino, n, orden, idx, tol, cuenta):
    """Rellena origen -> destino con DisplayOrder 'orden' (None = mínimo de origen - 1)."""
    objs = [o for o in _objetos(origen) if isinstance(o.Geometry, rg.Curve)]
    cerr = []
    for o in objs:
        c = o.Geometry
        if not c.IsClosed: cuenta["abiertas"] += 1
        elif not c.IsPlanar(tol): cuenta["no_planas"] += 1
        else: cerr.append(c)
    if not cerr: return
    li = _capa(destino, n)
    if li is None: cuenta["avisos"].append("capa %s no existe ni está en normas" % destino); return
    if orden is None: orden = min(o.Attributes.DisplayOrder for o in objs) - 1
    at = Rhino.DocObjects.ObjectAttributes(); at.LayerIndex = li; at.DisplayOrder = orden
    for ext, huecos in _grupos(cerr, tol):
        hs = rg.Hatch.Create([ext] + huecos, idx, 0.0, 1.0, tol) or []
        if not hs and huecos: hs = rg.Hatch.Create(ext, idx, 0.0, 1.0, tol) or []
        if not hs: cuenta["fallidos"] += 1; continue
        cuenta["huecos"] += len(huecos)
        for h in hs:
            if sc.doc.Objects.AddHatch(h, at) != System.Guid.Empty: cuenta["rellenos"] += 1
    cuenta["capas"].append(destino)

def _poner_orden(capa, orden):
    k = 0
    for o in _objetos(capa):
        if o.Attributes.DisplayOrder != orden:
            a = o.Attributes.Duplicate(); a.DisplayOrder = orden
            if sc.doc.Objects.ModifyAttributes(o, a, True): k += 1
    return k

def main(origen=None, destino=None, prefijo=None):
    n = util.normas(sc.doc.Path)
    tol = sc.doc.ModelAbsoluteTolerance
    cuenta = {"rellenos": 0, "huecos": 0, "abiertas": 0, "no_planas": 0, "fallidos": 0, "capas": [], "avisos": []}
    con_p = lambda s: s if (not prefijo or not s or s.startswith(prefijo + "_")) else prefijo + "_" + s
    if not origen and not prefijo:
        r = "error: indica origen (y destino) o prefijo"; print(r); return r
    pares = []
    if origen:
        origen = con_p(origen)
        destino = con_p(destino) if destino else _derivar(origen, n)
        if not destino:
            r = "error: no hay capa de relleno en normas para %s; pasa destino" % origen; print(r); return r
        if not _objetos(origen): cuenta["avisos"].append("capa %s vacía o inexistente" % origen)
        pares = [(origen, destino, None)]
    else:
        nombres = []
        for tabla in n["plantillas"].values():
            for k in tabla:
                if "{P}" in k and k.endswith("_ARISTAS") and k[:-8] + "_RELLENOS" in tabla and k not in nombres:
                    nombres.append(k)
        nombres.sort()
        reord, base, i = 0, None, 0
        for k in nombres:                                     # 01 delante ... 03 detrás
            a, rl = k.replace("{P}", prefijo), (k[:-8] + "_RELLENOS").replace("{P}", prefijo)
            objs = _objetos(a)
            if not objs: continue
            if base is None: base = min(o.Attributes.DisplayOrder for o in objs)
            else: reord += _poner_orden(a, base - 2 * i)
            pares.append((a, rl, base - 2 * i - 1)); i += 1
        if not pares: cuenta["avisos"].append("ninguna capa %s_*_ARISTAS con objetos" % prefijo)
        elif reord: cuenta["avisos"].append("orden de dibujo cambiado en %d aristas" % reord)
    idx = _solido()
    rs.EnableRedraw(False)
    try:
        for o, d, orden in pares: _rellenar(o, d, n, orden, idx, tol, cuenta)
    finally:
        rs.EnableRedraw(True)
    r = util.resumen(rellenos=cuenta["rellenos"], huecos=cuenta["huecos"], capas=",".join(cuenta["capas"]) or "ninguna",
                     abiertas_ignoradas=cuenta["abiertas"], no_planas=cuenta["no_planas"], fallidos=cuenta["fallidos"],
                     avisos="; ".join(cuenta["avisos"]) or "ninguno")
    print(r); return r
