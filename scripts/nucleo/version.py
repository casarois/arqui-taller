#! python3
"""Guarda el documento en la carpeta vN+1 (mismo nombre) y sigue trabajando en la copia."""
import os
import rhinoscriptsyntax as rs
import scriptcontext as sc
import util

def main():
    actual = sc.doc.Path
    if not actual:
        r = "error: el documento no está guardado"; print(r); return r
    nuevo = util.nueva_version(actual)
    os.makedirs(os.path.dirname(nuevo), exist_ok=True)
    b, e = os.path.splitext(nuevo); i = 2
    while os.path.exists(nuevo):                     # nunca sobrescribir: _2, _3, ...
        nuevo = "{}_{}{}".format(b, i, e); i += 1
    rs.Command('_-SaveAs "{}" _Enter'.format(nuevo), False)
    r = util.resumen(antes=actual, ahora=sc.doc.Path or nuevo)
    print(r); return r
