#! python3
"""<nombre>.py — <qué hace en una línea>.
Contrato: ver scripts/INDEX.md. Genérico: nada de un proyecto concreto; todo por parámetros o normas.
Ej: import <nombre>; <nombre>.main(...)"""
import rhinoscriptsyntax as rs
import scriptcontext as sc
import os, sys
_S = r"C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller\scripts"
for _d in [os.path.join(_S, x) for x in os.listdir(_S)]:
    if os.path.isdir(_d) and _d not in sys.path: sys.path.insert(0, _d)   # import util desde cualquier subcarpeta
import util

def main(aplicar=True):
    """Si el script modifica objetos existentes, el defecto debe ser aplicar=False (solo informa)."""
    n = util.normas(sc.doc.Path)          # normas generales + del proyecto
    hechos, avisos = 0, []
    rs.EnableRedraw(False)
    try:
        pass                              # <- trabajo
    finally:
        rs.EnableRedraw(True)
    r = util.resumen(hechos=hechos, avisos=avisos or "ninguno")
    print(r); return r                    # siempre una línea, nunca listas largas
