#! python3
"""Exporta con nombres estándar: Lamina_<FORMATO>_<Tema>_editable.3dm/.dwg, .pdf y _preview.png.
Carpeta de salida: `carpeta` si se da; si el documento ya está en una carpeta de versión (vN, la que crea
version.main) se exporta ahí mismo; si no, en <carpeta del documento>\\<version>.
- editable=False: no crea la copia 3dm (útil si el archivo de trabajo ya está en la carpeta de salida).
- Con layouts: PDF de una página por layout y preview de la vista activa (como siempre).
- Sin layouts y con capa de papel (LAMINA_00_PAPEL): PDF del rectángulo del papel a escala 1:1 (layout temporal del
  tamaño del papel con un detail superior 1:1 que se borra al acabar; colores de impresión) y preview =
  captura.main() del papel a normas export.preview_px de ancho.
Ej: exportar.main("Situacion", formato="A2")"""
import os, re
import System
import Rhino
import Rhino.Geometry as rg
import scriptcontext as sc
import rhinoscriptsyntax as rs
import util

PAPEL = "LAMINA_00_PAPEL"

def _destino(version, carpeta):
    if carpeta:
        destino = carpeta
    else:
        dir_doc = os.path.dirname(sc.doc.Path)
        destino = dir_doc if re.match(r"^v\d+$", os.path.basename(dir_doc)) else os.path.join(dir_doc, version)
    os.makedirs(destino, exist_ok=True)
    return destino

def _vista_modelo():
    """Activa una vista de modelo (no layout) y devuelve la vista que estaba activa para restaurarla."""
    antes = sc.doc.Views.ActiveView
    if isinstance(antes, Rhino.Display.RhinoPageView):
        modelos = list(sc.doc.Views.GetViewList(True, False))
        if modelos: sc.doc.Views.ActiveView = modelos[0]
    return antes

def _papel():
    """BoundingBox de los objetos de la capa de papel, o None."""
    li = sc.doc.Layers.FindByFullPath(PAPEL, -1)
    if li < 0: return None
    bb = rg.BoundingBox.Empty
    for o in sc.doc.Objects.FindByLayer(sc.doc.Layers[li]) or []:
        if not o.IsDeleted: bb.Union(o.Geometry.GetBoundingBox(True))
    return bb if bb.IsValid and bb.Max.X - bb.Min.X > 0 and bb.Max.Y - bb.Min.Y > 0 else None

def _pdf_papel(bb, ruta, dpi):
    """PDF 1:1 del rectángulo bb (modelo) por un layout temporal. Devuelve (ok, texto)."""
    doc = sc.doc
    mu, pu = doc.ModelUnitSystem, doc.PageUnitSystem
    k = Rhino.RhinoMath.UnitScale(mu, pu)                        # unidades de papel por unidad de modelo (1:1)
    w, h = (bb.Max.X - bb.Min.X) * k, (bb.Max.Y - bb.Min.Y) * k
    antes, mod = doc.Views.ActiveView, doc.Modified
    pv = None
    try:
        pv = doc.Views.AddPageView("_tmp_exportar_pdf", w, h)
        if pv is None: return False, "no se pudo crear el layout temporal"
        det = pv.AddDetailView("_tmp", rg.Point2d(0, 0), rg.Point2d(w, h), Rhino.Display.DefinedViewportProjection.Top)
        if det is None: return False, "no se pudo crear el detail"
        pv.SetActiveDetail(det.Id)
        c = bb.Center; c.Z = 0
        det.Viewport.SetCameraLocations(c, c + rg.Vector3d(0, 0, 100))
        det.CommitViewportChanges()
        det.DetailGeometry.SetScale(1.0, mu, k, pu)            # 1 unidad de modelo = su misma longitud en papel
        det.DetailGeometry.IsProjectionLocked = True
        det.CommitChanges()
        pv.SetPageAsActive(); pv.Redraw()
        ok, l, r, b, t, nn, ff = det.Viewport.GetFrustum()      # comprobación del encaje
        cam = det.Viewport.CameraLocation
        err = max(abs(cam.X + l - bb.Min.X), abs(cam.X + r - bb.Max.X), abs(cam.Y + b - bb.Min.Y), abs(cam.Y + t - bb.Max.Y))
        s = Rhino.Display.ViewCaptureSettings(pv, dpi)
        s.OutputColor = Rhino.Display.ViewCaptureSettings.ColorMode.PrintColor
        f = Rhino.FileIO.FilePdf.Create()
        f.AddPage(s)
        f.Write(ruta)
        txt = "pdf(papel %.0fx%.0f %s 1:1%s)" % (w, h, pu, "" if err < 1e-4 * (bb.Max.X - bb.Min.X) else ", DESAJUSTE %.6g unidades" % err)
        return os.path.exists(ruta), txt
    finally:
        if pv is not None:
            try: pv.Close()
            except Exception: pass
        if antes is not None:
            try: doc.Views.ActiveView = antes
            except Exception: pass
        doc.Modified = mod

def main(tema, formato="A2", version="v1", carpeta=None, pdf=True, dwg=True, preview=True, editable=True):
    if not sc.doc.Path:
        r = "error: guarda el documento antes de exportar"; print(r); return r
    n = util.normas(sc.doc.Path)["export"]          # generales + proyecto
    destino = _destino(version, carpeta)
    nombre = "Lamina_{}_{}".format(formato, tema)
    hecho = []
    pages = sorted(sc.doc.Views.GetPageViews(), key=lambda p: p.PageNumber)
    papel = None if pages else _papel()             # solo sin layouts

    # 1. Copia editable 3dm (no cambia el archivo abierto)
    if editable:
        p3dm = os.path.join(destino, nombre + "_editable.3dm")
        opts = Rhino.FileIO.FileWriteOptions(); opts.SuppressAllInput = True
        if sc.doc.WriteFile(p3dm, opts): hecho.append("3dm")

    # 2. DWG de todo lo visible del modelo (desde una vista de modelo, no de layout)
    if dwg:
        pdwg = os.path.join(destino, nombre + "_editable.dwg")
        antes = _vista_modelo()
        rs.UnselectAllObjects(); rs.Command("_SelAll", False)
        rs.Command('_-Export "{}" _Enter _Enter'.format(pdwg), False)
        rs.UnselectAllObjects()
        sc.doc.Views.ActiveView = antes
        if os.path.exists(pdwg): hecho.append("dwg")

    # 3. PDF: una página por layout, en orden de página; sin layouts, el papel 1:1 desde espacio modelo
    if pdf:
        ppdf = os.path.join(destino, nombre + ".pdf")
        if pages:
            f = Rhino.FileIO.FilePdf.Create()
            for pv in pages:
                f.AddPage(Rhino.Display.ViewCaptureSettings(pv, n["dpi_pdf"]))
            f.Write(ppdf); hecho.append("pdf({} pág)".format(len(pages)))
        elif papel is not None:
            ok, txt = _pdf_papel(papel, ppdf, n["dpi_pdf"])
            hecho.append(txt if ok else "pdf: error (%s)" % txt)
        else:
            hecho.append("pdf: sin layouts ni capa %s" % PAPEL)

    # 4. Preview PNG: vista activa; sin layouts y con papel, captura del papel
    if preview:
        ppng = os.path.join(destino, nombre + "_preview.png")
        if papel is not None:
            import captura
            res = captura.capturar(zona=(papel.Min.X, papel.Min.Y, papel.Max.X, papel.Max.Y), salida=ppng, ancho_px=n["preview_px"])
            hecho.append("png(papel %dx%d)" % res["px"] if "ruta" in res else "png: error (%s)" % res.get("error"))
        else:
            v = sc.doc.Views.ActiveView
            w = n["preview_px"]; h = int(w * v.Size.Height / max(v.Size.Width, 1))
            bmp = v.CaptureToBitmap(System.Drawing.Size(w, h))
            if bmp:
                bmp.Save(ppng); hecho.append("png")

    r = util.resumen(carpeta=destino, exportado=", ".join(hecho))
    print(r); return r
