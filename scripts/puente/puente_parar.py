#! python3
"""Para el puente de este Rhino:
_-RunPythonScript "C:\\Users\\2402l\\Documents\\UNI\\CLAUDE\\arqui-taller\\scripts\\puente\\puente_parar.py"
"""
import os, scriptcontext as sc

p = sc.sticky.pop("puente_claude", None)
if p and p.get("activo"):
    p["activo"] = False
    try: p["srv"].close()
    except Exception: pass
    try: os.remove(p["fichero"])
    except Exception: pass
    print("[puente] detenido")
else:
    print("[puente] no estaba activo")
