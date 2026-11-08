#! python3
"""Igual que puente_rhino.py (que ya solo arranca). Se mantiene por compatibilidad."""
import os
ruta = os.path.join(r"C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller\scripts\puente", "puente_rhino.py")
exec(compile(open(ruta, encoding="utf-8").read(), ruta, "exec"), {"__name__": "__main__"})
