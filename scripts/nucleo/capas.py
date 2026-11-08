#! python3
"""Crea/actualiza capas desde una plantilla de normas (+ normas_proyecto.json si existe).
Ej: capas.main("planta_urbana") | capas.main("fachada", prefijo="SECCION_LONG", reducir=True)"""
import rhinoscriptsyntax as rs
import scriptcontext as sc
import System.Drawing as sd
import util

def main(plantilla="lamina", prefijo=None, reducir=False, solo=None):
    n = util.normas(sc.doc.Path)
    creadas, actualizadas, sin_linea = 0, 0, []
    for nombre, (rgb, grosor, linea) in util.capas_de(plantilla, prefijo, reducir, n).items():
        if solo and nombre not in solo: continue
        color = sd.Color.FromArgb(*rgb)
        if rs.IsLayer(nombre): actualizadas += 1
        else: rs.AddLayer(nombre); creadas += 1
        rs.LayerColor(nombre, color); rs.LayerPrintColor(nombre, color)
        rs.LayerPrintWidth(nombre, grosor)
        try: rs.LayerLinetype(nombre, linea)
        except Exception: sin_linea.append(nombre)
    r = util.resumen(plantilla=plantilla, creadas=creadas, actualizadas=actualizadas,
                     sin_tipo_linea=sin_linea or "ninguna",
                     normas_proyecto="si" if n.get("_proyecto") else "no")
    print(r); return r
