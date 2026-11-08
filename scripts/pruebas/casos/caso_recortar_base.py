#! python3
# Caso: dibujo/recortar_base.py con un contorno cuadrado girado creado en la copia (capa PRUEBA_CONTORNO).
# Después mide, en las capas afectadas: curvas que quedan dentro del cuadrado (o lo cortan) y distancia mínima al cuadrado.
import math
import System, System.Drawing
import recortar_base
_tol = sc.doc.ModelAbsoluteTolerance
_cx, _cy = PARAMS["centro"]
_h, _a = PARAMS["lado"] / 2.0, math.radians(PARAMS.get("giro_grados", 0))
_pts = []
for _sx, _sy in ((-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1)):
    _x, _y = _sx * _h, _sy * _h
    _pts.append(rg.Point3d(_cx + _x * math.cos(_a) - _y * math.sin(_a), _cy + _x * math.sin(_a) + _y * math.cos(_a), 0))
_cuadrado = rg.PolylineCurve(_pts)
_li = sc.doc.Layers.FindByFullPath("PRUEBA_CONTORNO", -1)
if _li < 0: _li = sc.doc.Layers.Add("PRUEBA_CONTORNO", System.Drawing.Color.Red)
_at = Rhino.DocObjects.ObjectAttributes(); _at.LayerIndex = _li
_gid = sc.doc.Objects.AddCurve(_cuadrado, _at)
_capas = tuple(PARAMS["capas"])
_r = recortar_base.main(_gid, margen=PARAMS["margen"], lado=PARAMS["lado_recorte"], capas=_capas,
                        fragmento_min=PARAMS.get("fragmento_min", 0), aplicar=PARAMS.get("aplicar", True))
# medir
_bb = _cuadrado.GetBoundingBox(False); _bb.Inflate(PARAMS["margen"] * 10 + 1.0)
_dentro, _cerca, _dmin = 0, 0, None
for _ly in sc.doc.Layers:
    if _ly.IsDeleted or not any(_ly.Name.startswith(p) or _ly.FullPath.startswith(p) for p in _capas): continue
    for _o in sc.doc.Objects.FindByLayer(_ly) or []:
        if _o.IsDeleted or not isinstance(_o.Geometry, rg.Curve): continue
        _c = en_planta(_o.Geometry, _tol)
        _b = _c.GetBoundingBox(False)
        if _b.Max.X < _bb.Min.X or _b.Min.X > _bb.Max.X or _b.Max.Y < _bb.Min.Y or _b.Min.Y > _bb.Max.Y: continue
        _cerca += 1
        _corta = rg.Intersect.Intersection.CurveCurve(_c, _cuadrado, _tol, _tol)
        _ins = _cuadrado.Contains(_c.PointAt(_c.Domain.Mid), rg.Plane.WorldXY, _tol) == rg.PointContainment.Inside
        if (_corta and _corta.Count > 0) or _ins: _dentro += 1
        _ok, _pa, _pb = _c.ClosestPoints(_cuadrado)
        if _ok:
            _d = _pa.DistanceTo(_pb)
            if _dmin is None or _d < _dmin: _dmin = _d
resultado(unidades=unidades(),
          curvas_recortadas=numero(campo(_r, "curvas_recortadas")),
          curvas_borradas_enteras=numero(campo(_r, "curvas_borradas_enteras")),
          ignoradas_no_planas=numero(campo(_r, "ignoradas_no_planas")),
          bloqueadas=numero(campo(_r, "bloqueadas")),
          curvas_cerca=_cerca,
          curvas_dentro=_dentro,
          distancia_min=round(_dmin, 4) if _dmin is not None else None,
          error=_r if _r.startswith("error") else None)
