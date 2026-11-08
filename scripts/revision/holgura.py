#! python3
"""holgura.py — distancia mínima en planta entre las curvas del proyecto y las del contexto, dentro de una zona.
Contrato: ver scripts/INDEX.md. Genérico: nada de un proyecto concreto; todo por parámetros o normas.
- proyecto / contexto: prefijo o tupla de prefijos de capa. Una capa entra si su nombre (o su equivalente en
  normas.equivalencias_antiguas) empieza por el prefijo: PLANTA_06_ARQUITECTURAS cubre PLANTA_06_ARQUITECTURAS_ESCALERAS.
- Solo curvas de capas visibles (hatch, textos y demás se ignoran), proyectadas a z=0.
- zona=(x0,y0,x1,y1): las curvas se recortan al rectángulo; None = todo el documento.
- minimo=None -> normas composicion.holgura_proyecto_contexto_mm (mm del documento; se convierte si no está en mm).
No modifica nada. Ej: import holgura; holgura.main(zona=(338,160,392,238))"""
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import Rhino.Geometry as rg
import System
import os, sys
_S = r"C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller\scripts"
for _d in [os.path.join(_S, x) for x in os.listdir(_S)]:
    if os.path.isdir(_d) and _d not in sys.path: sys.path.insert(0, _d)   # import util desde cualquier subcarpeta
import util

def _tupla(x):
    return (x,) if isinstance(x, str) else tuple(x or ())

def _capas(prefijos, n):
    """{indice: nombre} de las capas visibles cuyo nombre o equivalente empieza por algún prefijo."""
    out = {}
    for ly in sc.doc.Layers:
        if ly.IsDeleted or not ly.IsVisible: continue
        nom = ly.Name
        eq = util.equivalente(nom, n) or ""
        if any(nom.startswith(p) or eq.startswith(p) for p in prefijos): out[ly.Index] = ly.FullPath
    return out

def _plano(c, tol):
    bb = c.GetBoundingBox(False)
    if abs(bb.Min.Z) > tol or abs(bb.Max.Z) > tol:
        c = rg.Curve.ProjectToPlane(c, rg.Plane.WorldXY) or c
    return c

def _recortar(c, rect, rcurva, tol):
    """Trozos de c dentro del rectángulo (BoundingBox 2D). [] si no toca."""
    bb = c.GetBoundingBox(False)
    if bb.Max.X < rect.Min.X or bb.Min.X > rect.Max.X or bb.Max.Y < rect.Min.Y or bb.Min.Y > rect.Max.Y: return []
    if rect.Min.X <= bb.Min.X and bb.Max.X <= rect.Max.X and rect.Min.Y <= bb.Min.Y and bb.Max.Y <= rect.Max.Y: return [c]
    ev = rg.Intersect.Intersection.CurveCurve(c, rcurva, tol, tol)
    ts = sorted(set([e.ParameterA for e in ev] + [e.ParameterA2 for e in ev if e.IsOverlap])) if ev else []
    trozos = c.Split(ts) if ts else None
    trozos = list(trozos) if trozos else [c]
    dentro = []
    for t in trozos:
        m = t.PointAt(t.Domain.Mid)
        if rect.Min.X - tol <= m.X <= rect.Max.X + tol and rect.Min.Y - tol <= m.Y <= rect.Max.Y + tol: dentro.append(t)
    return dentro

def _curvas(capas, rect, rcurva, tol):
    out = []
    for li, nom in capas.items():
        for o in sc.doc.Objects.FindByLayer(sc.doc.Layers[li]) or []:
            if o.IsDeleted or not o.Visible or not isinstance(o.Geometry, rg.Curve): continue
            c = _plano(o.Geometry, tol)
            for t in (_recortar(c, rect, rcurva, tol) if rect else [c]):
                out.append((t, nom))
    return out

def main(proyecto="PLANTA_06_ARQUITECTURAS", contexto=("PLANTA_01_EDIFICIOS",), zona=None, minimo=None):
    n = util.normas(sc.doc.Path)
    tol = sc.doc.ModelAbsoluteTolerance
    mm_u = Rhino.RhinoMath.UnitScale(sc.doc.ModelUnitSystem, Rhino.UnitSystem.Millimeters) or 1.0   # mm por unidad
    avisos = []
    if minimo is None:
        minimo = n.get("composicion", {}).get("holgura_proyecto_contexto_mm")
        if minimo is None: r = "error: falta composicion.holgura_proyecto_contexto_mm en normas; pasa minimo"; print(r); return r
    if mm_u != 1.0: avisos.append("documento en %s: distancias convertidas a mm de modelo" % sc.doc.ModelUnitSystem)
    rect = rcurva = None
    if zona:
        x0, y0, x1, y1 = min(zona[0], zona[2]), min(zona[1], zona[3]), max(zona[0], zona[2]), max(zona[1], zona[3])
        rect = rg.BoundingBox(rg.Point3d(x0, y0, 0), rg.Point3d(x1, y1, 0))
        rcurva = rg.Rectangle3d(rg.Plane.WorldXY, rg.Point3d(x0, y0, 0), rg.Point3d(x1, y1, 0)).ToNurbsCurve()
    cp, cc = _capas(_tupla(proyecto), n), _capas(_tupla(contexto), n)
    comunes = set(cp) & set(cc)
    if comunes:
        avisos.append("capas en proyecto y contexto (se quitan del contexto): %s" % ",".join(cc[i] for i in comunes))
        for i in comunes: cc.pop(i)
    P, C = _curvas(cp, rect, rcurva, tol), _curvas(cc, rect, rcurva, tol)
    if not P or not C:
        r = util.resumen(error="sin curvas de %s en la zona" % ("proyecto" if not P else "contexto"),
                         capas_proyecto=len(cp), capas_contexto=len(cc)); print(r); return r
    arbol = rg.RTree()
    for i, (c, _) in enumerate(C): arbol.Insert(c.GetBoundingBox(False), i)
    mejor = [float("inf"), None, None, None, None]      # dist, pA, pB, capaP, capaC
    bajo = 0
    lim = minimo / mm_u
    for c, capa in P:
        bajo_c = False
        bb = c.GetBoundingBox(False)
        r_busca = max(lim, min(mejor[0], 1e9))
        if r_busca == float("inf"): r_busca = 1e9
        bb.Inflate(r_busca)
        cand = []
        arbol.Search(bb, System.EventHandler[rg.RTreeEventArgs](lambda s, e: cand.append(e.Id)))
        for j in cand:
            d_c, capa_c = C[j]
            ok, pa, pb = c.ClosestPoints(d_c)
            if not ok: continue
            d = pa.DistanceTo(pb)
            if d < lim: bajo_c = True
            if d < mejor[0]: mejor = [d, pa, pb, capa, capa_c]
        bajo += bajo_c
    if mejor[1] is None:
        r = util.resumen(distancia_mm="sin pares", avisos="; ".join(avisos) or "ninguno"); print(r); return r
    d_mm = mejor[0] * mm_u
    p = mejor[1]
    r = util.resumen(distancia_min_mm="%.2f" % d_mm, minimo_mm="%.2f" % minimo, cumple="si" if d_mm >= minimo - 1e-9 else "NO",
                     peor_proyecto=mejor[3], peor_contexto=mejor[4], punto="%.6g,%.6g" % (p.X, p.Y),
                     curvas="%d proyecto / %d contexto" % (len(P), len(C)),
                     curvas_proyecto_bajo_minimo=bajo, avisos="; ".join(avisos) or "ninguno")
    print(r); return r
