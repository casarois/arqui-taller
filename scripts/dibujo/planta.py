#! python3
"""planta.py — corte horizontal del modelo 3D (capas 3D_) y paso a 2D en capas de planta_edificio.
Contrato: ver scripts/INDEX.md. Genérico: nada de un proyecto concreto; todo por parámetros o normas.
- nivel: cota del suelo de la planta en METROS (número; misma referencia de Z que el modelo).
  altura: altura del plano de corte sobre el nivel, en metros. Corte a z = nivel + altura.
  Ambos se convierten a las unidades del documento (mm, cm, m...).
- Lo cortado (Brep/Extrusión/Malla de capas 3D_*) -> PLANTA_10_MUROS_CORTE (curvas unidas).
  Lo visto por debajo del corte (Make2D en planta, aristas visibles) -> PLANTA_13_VISTA.
  No separa pilares (_11) ni dibuja lo superior (_14_PROYECCIONES): eso queda a mano.
- El 2D se coloca en el plano z = 0 del documento, con las mismas X,Y que el modelo.
- Solo usa objetos visibles (capas ocultas = excluidas). Bloques y SubD se omiten (se cuentan).
- No modifica objetos existentes: solo añade curvas. Cada ejecución añade otra copia.
Ej: import planta; planta.main(191.5)  |  planta.main(0, altura=1.20)"""
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

CORTE, VISTA = "PLANTA_10_MUROS_CORTE", "PLANTA_13_VISTA"

def _capa(nombre, defs):
    """Crea la capa si falta, con color/grosor/tipo de línea de normas. Devuelve su índice."""
    if not rs.IsLayer(nombre):
        rgb, grosor, linea = defs[nombre]
        rs.AddLayer(nombre, sd.Color.FromArgb(*rgb))
        rs.LayerPrintColor(nombre, sd.Color.FromArgb(*rgb)); rs.LayerPrintWidth(nombre, grosor)
        try: rs.LayerLinetype(nombre, linea)
        except Exception: pass
    i = sc.doc.Layers.FindByFullPath(nombre, -1)
    return i if i >= 0 else sc.doc.Layers.FindName(nombre).Index

def _es_3d(o):
    return any(s.upper().startswith("3D_") for s in sc.doc.Layers[o.Attributes.LayerIndex].FullPath.split("::"))

def main(nivel, altura=1.20):
    try: nivel = float(nivel); altura = float(altura)
    except (TypeError, ValueError):
        r = "error: nivel y altura deben ser números en metros (nivel=%r)" % (nivel,); print(r); return r
    n = util.normas(sc.doc.Path)
    defs = util.capas_de("planta_edificio", n=n)
    u = sc.doc.ModelUnitSystem
    k = Rhino.RhinoMath.UnitScale(Rhino.UnitSystem.Meters, u)
    z = (nivel + altura) * k
    tol = sc.doc.ModelAbsoluteTolerance
    plano = rg.Plane(rg.Point3d(0, 0, z), rg.Vector3d.ZAxis)
    bajar = rg.Transform.Translation(0, 0, -z)
    aplanar = rg.Transform.PlanarProjection(rg.Plane.WorldXY)

    objs = [o for o in sc.doc.Objects if o.IsNormal or o.IsLocked]
    objs = [o for o in objs if _es_3d(o)]
    cortadas, omitidos, vista_geo = [], 0, []
    for o in objs:
        g = o.Geometry
        if isinstance(g, rg.Extrusion): g = g.ToBrep()
        bb = g.GetBoundingBox(True)
        if isinstance(g, (rg.Brep, rg.Mesh, rg.Curve)):
            if bb.Min.Z < z: vista_geo.append(g)
        else:
            omitidos += 1; continue
        if isinstance(g, rg.Curve) or not (bb.Min.Z <= z <= bb.Max.Z): continue
        if isinstance(g, rg.Brep):
            ok, crvs, pts = Rhino.Geometry.Intersect.Intersection.BrepPlane(g, plano, tol)
            crvs = list(crvs) if ok and crvs else []
        else:
            crvs = [pl.ToNurbsCurve() for pl in (Rhino.Geometry.Intersect.Intersection.MeshPlane(g, plano) or [])]
        if crvs: cortadas.extend(rg.Curve.JoinCurves(crvs, tol) or crvs)

    rs.EnableRedraw(False)
    n_corte = n_vista = 0
    aviso_vista = "ninguno"
    try:
        if cortadas:
            at = Rhino.DocObjects.ObjectAttributes(); at.LayerIndex = _capa(CORTE, defs)
            for c in cortadas:
                c.Transform(bajar)
                if sc.doc.Objects.AddCurve(c, at) != System.Guid.Empty: n_corte += 1
        if vista_geo:
            vis = _vista(vista_geo, z, tol, aplanar)
            if vis is None: aviso_vista = "Make2D falló: sin vista"
            elif vis:
                at = Rhino.DocObjects.ObjectAttributes(); at.LayerIndex = _capa(VISTA, defs)
                for c in vis:
                    if sc.doc.Objects.AddCurve(c, at) != System.Guid.Empty: n_vista += 1
    finally:
        rs.EnableRedraw(True)
    if not objs: aviso_vista = "no hay objetos visibles en capas 3D_"
    elif not cortadas: aviso_vista = "el plano z=%.3f no corta nada" % z
    r = util.resumen(z_corte="%.3f %s" % (z, u), corte=n_corte, vista=n_vista,
                     omitidos_bloques_subd=omitidos, proyecciones_14="no (a mano)", avisos=aviso_vista)
    print(r); return r

def _vista(geos, z, tol, aplanar):
    """Make2D desde arriba con plano de recorte en z (se ve lo de debajo). Devuelve curvas en z=0."""
    bb = rg.BoundingBox.Empty
    for g in geos: bb.Union(g.GetBoundingBox(True))
    c = bb.Center
    w, h = max(bb.Max.X - bb.Min.X, 1.0), max(bb.Max.Y - bb.Min.Y, 1.0)
    alto = bb.Max.Z - bb.Min.Z
    vp = Rhino.DocObjects.ViewportInfo()
    vp.ChangeToParallelProjection(True)
    vp.SetCameraLocation(rg.Point3d(c.X, c.Y, bb.Max.Z + alto * 0.1 + 1.0))
    vp.SetCameraDirection(-rg.Vector3d.ZAxis)
    vp.SetCameraUp(rg.Vector3d.YAxis)
    vp.SetFrustum(-w * 0.55, w * 0.55, -h * 0.55, h * 0.55, 0.5, alto * 1.2 + 2.0)
    p = rg.HiddenLineDrawingParameters()
    p.AbsoluteTolerance = tol
    p.IncludeTangentEdges = False
    p.IncludeHiddenCurves = False
    p.SetViewport(vp)
    p.AddClippingPlane(rg.Plane(rg.Point3d(0, 0, z), rg.Vector3d.ZAxis))
    for g in geos: p.AddGeometry(g, None)
    try: hld = rg.HiddenLineDrawing.Compute(p, True)
    except Exception: return None
    if hld is None: return None
    inv = hld.WorldToHiddenLine.TryGetInverse()[1]
    segs = []
    for s in hld.Segments:
        if s.SegmentVisibility != rg.HiddenLineDrawingSegment.Visibility.Visible: continue
        pc = s.ParentCurve
        if pc is None or pc.SilhouetteType == rg.SilhouetteType.SectionCut: continue
        cv = s.CurveGeometry.DuplicateCurve()
        cv.Transform(inv); cv.Transform(aplanar)
        segs.append(cv)
    return list(rg.Curve.JoinCurves(segs, tol)) if segs else []
