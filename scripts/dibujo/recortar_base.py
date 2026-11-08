#! python3
"""recortar_base.py — recorta curvas contra un contorno cerrado (en planta).
Contrato: ver scripts/INDEX.md. Genérico: nada de un proyecto concreto; todo por parámetros o normas.
- ambito: id de una curva cerrada (Guid o texto) o rectángulo (x0,y0,x1,y1) en unidades del doc.
- lado="fuera": borra lo exterior (recortar la base a un ámbito). lado="dentro": borra lo interior (agua, curvas de
  nivel u orillas que quedan bajo una huella nueva).
- margen: las líneas que se cortan terminan a esa distancia del borde, del lado que se conserva (el contorno se
  desfasa margen hacia ese lado, con esquinas redondeadas: distancia exacta también en las esquinas).
- capas: nombres o prefijos de capa (texto o tupla). None = todas las capas visibles salvo la del contorno.
- fragmento_min: los trozos resultantes más cortos que esto se cuentan y, con aplicar, no se conservan.
- Hatch de las capas afectadas que tocan la zona borrada: se cuentan por capa, no se recortan.
- Solo curvas planas horizontales (en planta); el resto se cuenta como ignoradas. Objetos bloqueados: no se tocan.
aplicar=False solo informa. Ej: import recortar_base; recortar_base.main((0,0,594,420), margen=0.2, aplicar=True)"""
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

def _contorno(ambito, tol):
    """(curva cerrada en z=0, id del objeto o None, índice de capa o None) o (None, error)."""
    if isinstance(ambito, (tuple, list)) and len(ambito) == 4:
        x0, y0, x1, y1 = [float(v) for v in ambito]
        if abs(x1 - x0) < tol or abs(y1 - y0) < tol: return None, "rectángulo sin superficie", None
        rc = rg.Rectangle3d(rg.Plane.WorldXY, rg.Point3d(min(x0, x1), min(y0, y1), 0), rg.Point3d(max(x0, x1), max(y0, y1), 0))
        return rc.ToNurbsCurve(), None, None
    try: gid = ambito if isinstance(ambito, System.Guid) else System.Guid(str(ambito))
    except Exception: return None, "ambito no es un id ni un rectángulo (x0,y0,x1,y1)", None
    o = sc.doc.Objects.FindId(gid)
    if o is None or not isinstance(o.Geometry, rg.Curve): return None, "el id no es una curva del documento", None
    c = o.Geometry.DuplicateCurve()
    if not c.IsClosed or not c.IsPlanar(tol): return None, "el contorno debe ser una curva cerrada y plana", None
    bb = c.GetBoundingBox(False)
    if bb.Max.Z - bb.Min.Z > tol:
        c = rg.Curve.ProjectToPlane(c, rg.Plane.WorldXY)
    elif abs(bb.Min.Z) > tol:
        c.Translate(rg.Vector3d(0, 0, -bb.Min.Z))
    return c, gid, o.Attributes.LayerIndex

def _area(c):
    a = rg.AreaMassProperties.Compute(c)
    return a.Area if a else 0.0

def _desfase(c, d, fuera, tol):
    """Desfasa la curva cerrada d hacia fuera (fuera=True) o hacia dentro. None si no sale una única curva."""
    if d <= 0: return c
    a0, cands = _area(c), []
    for s in (d, -d):
        r = c.Offset(rg.Plane.WorldXY, s, tol, rg.CurveOffsetCornerStyle.Round)
        if r and len(r) > 1: r = rg.Curve.JoinCurves(r, tol * 10)
        if r and len(r) == 1 and r[0].IsClosed: cands.append(r[0])
    cands = [x for x in cands if (_area(x) > a0) == fuera]
    return cands[0] if cands else None

def _capas_afectadas(capas, excluir):
    pref = (capas,) if isinstance(capas, str) else (tuple(capas) if capas else None)
    out = set()
    for ly in sc.doc.Layers:
        if ly.IsDeleted: continue
        if pref is None:
            if ly.IsVisible and ly.Index != excluir: out.add(ly.Index)
        elif any(ly.Name.startswith(p) or ly.FullPath.startswith(p) for p in pref):
            out.add(ly.Index)
    return out

def _dentro(borde, p, tol):
    r = borde.Contains(rg.Point3d(p.X, p.Y, 0), rg.Plane.WorldXY, tol)
    return r == rg.PointContainment.Inside

def _trozos(c, borde_z, borde, tol):
    """[(trozo, esta_dentro)] de la curva c cortada por el borde (a la z de c)."""
    ev = rg.Intersect.Intersection.CurveCurve(c, borde_z, tol, tol)
    ts = []
    if ev:
        for e in ev:
            ts.append(e.ParameterA)
            if e.IsOverlap: ts.append(e.OverlapA.Max)
    ts = sorted(set(t for t in ts if not (c.IsClosed is False and (abs(t - c.Domain.Min) < 1e-9 or abs(t - c.Domain.Max) < 1e-9))))
    pz = list(c.Split(ts)) if ts else []
    if not pz: pz = [c]
    out = []
    for t in pz:
        if t.GetLength() < tol: continue
        out.append((t, _dentro(borde, t.PointAt(t.Domain.Mid), tol)))
    return out

def main(ambito, margen=0, lado="fuera", capas=None, fragmento_min=0, aplicar=False):
    tol = sc.doc.ModelAbsoluteTolerance
    if lado not in ("fuera", "dentro"):
        r = 'error: lado debe ser "fuera" o "dentro"'; print(r); return r
    base, gid, capa_c = _contorno(ambito, tol)
    if base is None:
        r = "error: " + gid; print(r); return r
    borde = _desfase(base, float(margen), lado == "dentro", tol)          # se borra lo de dentro: crece; si no, encoge
    if borde is None:
        r = "error: no se puede desfasar el contorno %s (margen demasiado grande o forma compleja)" % margen; print(r); return r
    bbb = borde.GetBoundingBox(False)
    li_af = _capas_afectadas(capas, capa_c)
    if not li_af:
        r = "error: ninguna capa coincide con %s" % (capas,); print(r); return r
    cuenta = dict(recortadas=0, borradas=0, trozos=0, cortos=0, ignoradas=0, bloqueadas=0)
    hatch = {}
    cambios = []                                              # (objeto, [curvas que quedan])
    bordes_z = {}
    for li in li_af:
        for o in sc.doc.Objects.FindByLayer(sc.doc.Layers[li]) or []:
            if o.IsDeleted or (gid and o.Id == gid): continue
            g = o.Geometry
            bb = g.GetBoundingBox(False)
            toca = not (bb.Max.X < bbb.Min.X or bb.Min.X > bbb.Max.X or bb.Max.Y < bbb.Min.Y or bb.Min.Y > bbb.Max.Y)
            if isinstance(g, rg.Hatch):
                if lado == "fuera" or toca:
                    cs = list(g.Get3dCurves(True) or [])
                    sobra = [(_dentro(borde, cv.PointAtStart, tol) == (lado == "dentro")) for cv in cs]
                    cruza = toca and any(rg.Intersect.Intersection.CurveCurve(_a_z(borde, cv, bordes_z), cv, tol, tol) for cv in cs)
                    if cruza or (sobra and all(sobra)):           # cruza el borde o queda entero en el lado que se borra
                        nom = sc.doc.Layers[li].Name; hatch[nom] = hatch.get(nom, 0) + 1
                continue
            if not isinstance(g, rg.Curve): continue
            if not toca:
                if lado == "fuera":
                    if o.IsLocked: cuenta["bloqueadas"] += 1
                    else: cambios.append((o, [])); cuenta["borradas"] += 1
                continue
            if bb.Max.Z - bb.Min.Z > tol:
                cuenta["ignoradas"] += 1; continue
            if o.IsLocked: cuenta["bloqueadas"] += 1; continue
            pz = _trozos(g, _a_z(borde, g, bordes_z), borde, tol)
            quitar = (lambda d: d) if lado == "dentro" else (lambda d: not d)
            quedan = [t for t, d in pz if not quitar(d)]
            if len(quedan) == len(pz) and len(pz) == 1: continue        # no se toca
            if not quedan:
                cambios.append((o, [])); cuenta["borradas"] += 1; continue
            j = list(rg.Curve.JoinCurves(quedan, tol)) if len(quedan) > 1 else quedan
            buenos = [c for c in j if c.GetLength() >= fragmento_min]
            cuenta["cortos"] += len(j) - len(buenos)
            cambios.append((o, buenos if aplicar else j)); cuenta["recortadas"] += 1; cuenta["trozos"] += len(buenos)
    hechos = 0
    if aplicar and cambios:
        rs.EnableRedraw(False)
        try:
            for o, nuevas in cambios:
                at = o.Attributes.Duplicate()
                for c in nuevas: sc.doc.Objects.AddCurve(c, at)
                sc.doc.Objects.Delete(o, True); hechos += 1
        finally:
            rs.EnableRedraw(True)
    h_txt = "%d (%s)" % (sum(hatch.values()), ", ".join("%s:%d" % kv for kv in sorted(hatch.items()))) if hatch else "0"
    r = util.resumen(modo="aplicado" if aplicar else "solo informe (aplicar=False)", lado=lado, margen=margen,
                     curvas_recortadas=cuenta["recortadas"], curvas_borradas_enteras=cuenta["borradas"],
                     trozos_que_quedan=cuenta["trozos"], fragmentos_cortos=cuenta["cortos"],
                     hatch_afectados_sin_recortar=h_txt, ignoradas_no_planas=cuenta["ignoradas"],
                     bloqueadas=cuenta["bloqueadas"], capas=len(li_af))
    print(r); return r

def _a_z(borde, g, cache):
    """El borde (z=0) llevado a la z de la curva g."""
    z = round(g.GetBoundingBox(False).Min.Z, 6)
    if z not in cache:
        b = borde.DuplicateCurve(); b.Translate(rg.Vector3d(0, 0, z)); cache[z] = b
    return cache[z]
