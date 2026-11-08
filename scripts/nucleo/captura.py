#! python3
"""captura.py — PNG de una zona del modelo vista en planta, con grosores y colores de impresión y encaje exacto.
Contrato: ver scripts/INDEX.md. Genérico: nada de un proyecto concreto; todo por parámetros o normas.
Método (el que funciona en Rhino 8.5): PrintDisplay activado, vista superior paralela maximizada, ZoomBoundingBox
de la zona, zona real del mundo = frustum + posición de cámara, ViewCapture (sin ejes ni rejilla, ScaleScreenItems
False) con la proporción del viewport y recorte por cálculo a la zona pedida. Restaura PrintDisplay, la vista
y doc.Modified. (La captura de impresión con ViewCaptureSettings sale en blanco en este Rhino: no se usa.)
- zona=None -> rectángulo de la capa de papel (LAMINA_00_PAPEL) o, si no hay, la extensión de lo visible.
- ppmm = píxeles por mm del modelo (se convierte a las unidades del doc); ancho_px manda sobre ppmm.
- salida: carpeta (nombre automático, nunca sobrescribe) o ruta .png (esa ruta exacta). None = carpeta del doc.
Ej: import captura; captura.main((335,150,392,238), ppmm=12)
    captura.lado_a_lado([png_a, png_b], r"...\\comparar.png", titulos=("v7", "solo"))
Tras main(), captura.ULTIMA = ruta del PNG (para encadenar sin leer la línea)."""
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import Rhino.Geometry as rg
import System
import System.Drawing as sd
import System.Drawing.Drawing2D, System.Drawing.Imaging, System.Drawing.Text
import os, sys, math, time
_S = r"C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller\scripts"
for _d in [os.path.join(_S, x) for x in os.listdir(_S)]:
    if os.path.isdir(_d) and _d not in sys.path: sys.path.insert(0, _d)   # import util desde cualquier subcarpeta
import util

PAPEL = "LAMINA_00_PAPEL"
MAX_PX = 16000          # lado máximo de la captura completa (si se pasa, se baja la resolución y se avisa)
ULTIMA = None

# ---------------------------------------------------------------- PrintDisplay (sin API: por comando)
def _prompt_pd(op=""):
    """Ejecuta -PrintDisplay con opciones y devuelve la línea de estado que deja en el historial."""
    Rhino.RhinoApp.RunScript("_-PrintDisplay %s _Enter" % op, True)
    lineas = [l for l in (Rhino.RhinoApp.CommandHistoryWindowText or "").splitlines() if "=" in l]
    return lineas[-1].split(":")[0].strip() if lineas else ""

def _print_on():
    """Activa PrintDisplay (vistas de modelo, color de impresión). Devuelve lo que hay que deshacer."""
    deshacer = []
    p0 = _prompt_pd("")
    for op, inv in (("_Viewport=_Model", "_Viewport=_Layout"), ("_State=_On", "_State=_Off"), ("_Color=_Print", "_Color=_Display")):
        p1 = _prompt_pd(op)
        if p0 and p1 and p1 != p0: deshacer.insert(0, inv)   # comparación de textos: vale en cualquier idioma
        p0 = p1
    return deshacer

def _print_restaurar(deshacer):
    for inv in deshacer: Rhino.RhinoApp.RunScript("_-PrintDisplay %s _Enter" % inv, False)

# ---------------------------------------------------------------- vista
def _es_superior(vp):
    d = vp.CameraDirection; d.Unitize()
    return vp.IsParallelProjection and d.Z < -0.9999 and abs(vp.CameraUp.Y) > 0.9999 and vp.CameraUp.Y > 0

def _vista_superior():
    """(vista, ViewportInfo a restaurar o None). Prefiere la activa; si ninguna es superior paralela, pone una."""
    act = sc.doc.Views.ActiveView
    modelos = [v for v in sc.doc.Views.GetViewList(True, False)]
    if act in modelos: modelos.remove(act); modelos.insert(0, act)
    for v in modelos:
        if _es_superior(v.ActiveViewport): return v, None
    if not modelos: return None, None
    v = modelos[0]
    info = Rhino.DocObjects.ViewportInfo(v.ActiveViewport)
    nombre = v.ActiveViewport.Name
    v.ActiveViewport.SetProjection(Rhino.Display.DefinedViewportProjection.Top, None, False)
    v.ActiveViewport.Name = nombre                      # SetProjection renombra la vista: se deja como estaba
    return v, info

def _zona_defecto():
    li = sc.doc.Layers.FindByFullPath(PAPEL, -1)
    if li >= 0:
        bb = rg.BoundingBox.Empty
        for o in sc.doc.Objects.FindByLayer(sc.doc.Layers[li]) or []:
            if not o.IsDeleted: bb.Union(o.Geometry.GetBoundingBox(True))
        if bb.IsValid: return (bb.Min.X, bb.Min.Y, bb.Max.X, bb.Max.Y), "papel"
    bb = sc.doc.Objects.BoundingBoxVisible
    if bb.IsValid: return (bb.Min.X, bb.Min.Y, bb.Max.X, bb.Max.Y), "extension"
    return None, None

def _ruta(salida, defecto_nombre):
    if salida and salida.lower().endswith(".png"):
        os.makedirs(os.path.dirname(os.path.abspath(salida)), exist_ok=True); return salida
    carpeta = salida or (os.path.dirname(sc.doc.Path) if sc.doc.Path else os.environ.get("TEMP", "."))
    os.makedirs(carpeta, exist_ok=True)
    b = os.path.join(carpeta, defecto_nombre); p = b + ".png"; i = 2
    while os.path.exists(p): p = "%s_%d.png" % (b, i); i += 1
    return p

# ---------------------------------------------------------------- captura
def capturar(zona=None, salida=None, ppmm=10, ancho_px=None, impresion=True):
    """Hace la captura y devuelve un dict (ruta, px, zona_real, avisos) o {'error': ...}."""
    avisos = []
    origen = "parametro"
    if zona is None:
        zona, origen = _zona_defecto()
        if zona is None: return {"error": "documento vacío y sin zona"}
    x0, y0, x1, y1 = float(min(zona[0], zona[2])), float(min(zona[1], zona[3])), float(max(zona[0], zona[2])), float(max(zona[1], zona[3]))
    if x1 - x0 <= 0 or y1 - y0 <= 0: return {"error": "zona sin superficie: %s" % (zona,)}
    mm_por_u = Rhino.RhinoMath.UnitScale(sc.doc.ModelUnitSystem, Rhino.UnitSystem.Millimeters) or 1.0
    s = float(ancho_px) / (x1 - x0) if ancho_px else float(ppmm) * mm_por_u      # píxeles por unidad del doc

    doc_mod = sc.doc.Modified
    act = sc.doc.Views.ActiveView
    vista, info = _vista_superior()
    if vista is None: return {"error": "no hay vistas de modelo"}
    maxim = vista.Maximized
    info_antes = info or Rhino.DocObjects.ViewportInfo(vista.ActiveViewport)
    deshacer = []
    bmp = rec = None
    try:
        if impresion: deshacer = _print_on()
        sc.doc.Views.ActiveView = vista
        if not maxim: vista.Maximized = True
        vista.Redraw(); Rhino.RhinoApp.Wait()
        vp = vista.ActiveViewport
        vp.ZoomBoundingBox(rg.BoundingBox(rg.Point3d(x0, y0, 0), rg.Point3d(x1, y1, 0)))
        vista.Redraw()
        ok, l, r, b, t, nn, ff = vp.GetFrustum()
        cam = vp.CameraLocation
        L, B, W_u, H_u = cam.X + l, cam.Y + b, r - l, t - b                          # zona del mundo que ve la vista
        sz = vp.Size
        W = int(math.ceil(W_u * s)); H = int(round(W * float(sz.Height) / max(sz.Width, 1)))
        if max(W, H) > MAX_PX:
            k = float(MAX_PX) / max(W, H); s *= k; W = int(math.ceil(W_u * s)); H = int(round(W * float(sz.Height) / max(sz.Width, 1)))
            avisos.append("resolución reducida a %.2f px/unidad (máx %d px)" % (s, MAX_PX))
        vc = Rhino.Display.ViewCapture()
        vc.Width, vc.Height = W, H
        vc.ScaleScreenItems = False
        vc.DrawAxes = False; vc.DrawGrid = False; vc.DrawGridAxes = False
        vc.TransparentBackground = False
        bmp = vc.CaptureToBitmap(vista)
        if bmp is None: return {"error": "ViewCapture no devolvió imagen"}
        sx, sy = bmp.Width / W_u, bmp.Height / H_u                                    # px por unidad reales
        px0 = int(math.ceil((x0 - L) * sx - 1e-6)); py0 = int(math.ceil((B + H_u - y1) * sy - 1e-6))   # imagen: y hacia abajo; por dentro de la zona
        pw = int(ancho_px) if ancho_px else int(round((x1 - x0) * sx))
        ph = int(round((y1 - y0) * sy))
        # el recorte no puede salir de la imagen (ZoomBoundingBox deja margen; por seguridad se ajusta)
        cx0, cy0 = max(0, px0), max(0, py0)
        cx1, cy1 = min(bmp.Width, px0 + pw), min(bmp.Height, py0 + ph)
        if (cx0, cy0, cx1, cy1) != (px0, py0, px0 + pw, py0 + ph): avisos.append("recorte ajustado al borde de la vista")
        rec = bmp.Clone(sd.Rectangle(cx0, cy0, cx1 - cx0, cy1 - cy0), bmp.PixelFormat)
        dpi = sx / mm_por_u * 25.4                                                    # px por pulgada de modelo en mm
        try: rec.SetResolution(float(dpi), float(dpi))
        except Exception: pass
        zr = (L + cx0 / sx, B + H_u - cy1 / sy, L + cx1 / sx, B + H_u - cy0 / sy)
        nombre = "captura_%s_%s" % (os.path.splitext(os.path.basename(sc.doc.Path or "sin_nombre"))[0], time.strftime("%Y%m%d_%H%M%S"))
        ruta = _ruta(salida, nombre)
        rec.Save(ruta, sd.Imaging.ImageFormat.Png)
        return {"ruta": ruta, "px": (rec.Width, rec.Height), "zona_real": zr, "origen": origen,
                "px_unidad": sx, "avisos": avisos}
    finally:
        for im in (rec, bmp):
            try:
                if im is not None: im.Dispose()
            except Exception: pass
        try: vista.ActiveViewport.SetViewProjection(info_antes, True)
        except Exception: pass
        if not maxim: vista.Maximized = False
        if act is not None: sc.doc.Views.ActiveView = act
        _print_restaurar(deshacer)
        sc.doc.Views.Redraw()
        sc.doc.Modified = doc_mod

def main(zona=None, salida=None, ppmm=10, ancho_px=None, impresion=True):
    global ULTIMA
    d = capturar(zona, salida, ppmm, ancho_px, impresion)
    if "error" in d:
        r = "error: " + d["error"]; print(r); return r
    ULTIMA = d["ruta"]
    z = d["zona_real"]
    r = util.resumen(png=d["ruta"], px="%dx%d" % d["px"], zona_real="%.6g,%.6g,%.6g,%.6g" % z, origen_zona=d["origen"],
                     px_por_unidad="%.6g" % d["px_unidad"], avisos="; ".join(d["avisos"]) or "ninguno")
    print(r); return r

# ---------------------------------------------------------------- comparar
def lado_a_lado(pngs, salida, titulos=None):
    """Monta varios PNG (misma zona) uno junto a otro, a la misma altura, sobre blanco; títulos opcionales encima.
    salida: ruta .png o carpeta (nombre lado_a_lado_N.png)."""
    pngs = [p for p in (pngs or [])]
    falta = [p for p in pngs if not os.path.isfile(p)]
    if len(pngs) < 2 or falta:
        r = "error: hacen falta 2 o más PNG existentes%s" % ((" (no existe: %s)" % ", ".join(falta)) if falta else ""); print(r); return r
    ims = [sd.Bitmap(p) for p in pngs]
    try:
        h = max(im.Height for im in ims)
        anchos = [int(round(im.Width * float(h) / im.Height)) for im in ims]
        sep = max(4, int(round(0.02 * h)))
        th = int(round(0.05 * h)) if titulos else 0
        W = sum(anchos) + sep * (len(ims) + 1); H = h + th + sep * 2
        out = sd.Bitmap(W, H)
        g = sd.Graphics.FromImage(out)
        g.Clear(sd.Color.White)
        g.InterpolationMode = sd.Drawing2D.InterpolationMode.HighQualityBicubic
        g.TextRenderingHint = sd.Text.TextRenderingHint.AntiAlias
        fuente = sd.Font("Arial", float(max(8, int(th * 0.6))), sd.FontStyle.Regular, sd.GraphicsUnit.Pixel) if th else None
        x = sep
        for i, (im, w) in enumerate(zip(ims, anchos)):
            if fuente and i < len(titulos) and titulos[i]:
                g.DrawString(str(titulos[i]), fuente, sd.Brushes.Black, sd.PointF(float(x), float(sep)))
            g.DrawImage(im, sd.Rectangle(x, sep + th, w, h))
            x += w + sep
        g.Dispose()
        if salida.lower().endswith(".png"):
            os.makedirs(os.path.dirname(os.path.abspath(salida)), exist_ok=True); ruta = salida
        else:
            os.makedirs(salida, exist_ok=True); i = 1
            ruta = os.path.join(salida, "lado_a_lado_%d.png" % i)
            while os.path.exists(ruta): i += 1; ruta = os.path.join(salida, "lado_a_lado_%d.png" % i)
        out.Save(ruta, sd.Imaging.ImageFormat.Png); out.Dispose()
    finally:
        for im in ims: im.Dispose()
    r = util.resumen(png=ruta, px="%dx%d" % (W, H), imagenes=len(pngs))
    print(r); return r
