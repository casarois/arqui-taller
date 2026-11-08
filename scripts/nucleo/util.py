#! python3
"""Helpers comunes (sin dependencias de Rhino: se pueden probar fuera).
- normas(desde): normas generales + normas_proyecto.json más cercano a 'desde' (subiendo carpetas).
- capas_de(plantilla, prefijo, reducir): {nombre: (rgb, grosor_mm, tipo_linea)}.
- clasificar(nombres): ok / renombrar / sin_equivalente / por_defecto.
- nueva_version(ruta): ruta equivalente en la carpeta vN+1.
"""
import json, os, re, fnmatch

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # scripts\nucleo\util.py -> arqui-taller
NORMAS = os.path.join(RAIZ, "normas", "grafismo.json")
PREFIJOS_P = r"(?:ALZADO_[A-Z0-9]+(?:_[A-Z0-9]+)?|SECCION_LONG|SECCION_TRANS|SECCION_[A-Z0-9]+)"
POR_DEFECTO = {"Default", "Predefinito", "Por defecto", "Predeterminado", "Capa 01", "Layer 01"}

def _merge(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict): _merge(a[k], v)
        else: a[k] = v
    return a

def proyecto_json(desde):
    d = desde if (desde and os.path.isdir(desde)) else os.path.dirname(desde or "")
    for _ in range(6):
        if not d: break
        f = os.path.join(d, "normas_proyecto.json")
        if os.path.isfile(f): return f
        nd = os.path.dirname(d)
        if nd == d: break
        d = nd
    return None

def normas(desde=None):
    with open(NORMAS, encoding="utf-8") as f: n = json.load(f)
    pj = proyecto_json(desde) if desde else None
    if pj:
        with open(pj, encoding="utf-8") as f: _merge(n, json.load(f))
        n["_proyecto"] = pj
    return n

def _color(v, paleta):
    if isinstance(v, str): v = paleta[v]
    return (v, v, v) if isinstance(v, int) else tuple(v)

def _resolver(d, n, reducir=False):
    g = n["grosores_mm"][d[0]]
    if reducir: g = n["reduccion_conjunto"].get("%.2f" % g, g)
    lt = n["lineas"][d[2]] if len(d) > 2 else n["lineas"]["continua"]
    return (_color(d[1], n["paleta"]), g, lt)

def capas_de(plantilla, prefijo=None, reducir=False, n=None):
    n = n or normas()
    tabla = n["plantillas"][plantilla]
    if any("{P}" in k for k in tabla) and not prefijo:
        raise ValueError("La plantilla '%s' necesita prefijo (ej. SECCION_LONG, ALZADO_NORTE)" % plantilla)
    out = {}
    for nombre, d in tabla.items():
        if nombre.startswith("_") or "*" in nombre: continue
        out[nombre.replace("{P}", prefijo or "")] = _resolver(d, n, reducir)
    return out

def _todas(n):
    """[(regex, plantilla, definicion)] de todas las capas de normas (incluye {P} y *)."""
    out = []
    for pl, tabla in n["plantillas"].items():
        for nombre, d in tabla.items():
            if nombre.startswith("_"): continue
            rx = re.escape(nombre).replace(re.escape("{P}"), PREFIJOS_P).replace(r"\*", "[A-Z0-9_]+")
            out.append((re.compile("^" + rx + "$"), pl, d))
    return out

def definicion(nombre, n=None):
    n = n or normas()
    for rx, pl, d in _todas(n):
        if rx.match(nombre): return pl, d
    return None

def equivalente(nombre, n=None):
    n = n or normas()
    eq = {k: v for k, v in n.get("equivalencias_antiguas", {}).items() if not k.startswith("_")}
    for pat in sorted(eq, key=lambda p: len(p.replace("*", "")), reverse=True):
        rx = "^" + re.escape(pat).replace(r"\*", "(.*)") + "$"
        m = re.match(rx, nombre)
        if m:
            dest = eq[pat]
            for g in m.groups(): dest = dest.replace("*", g, 1)
            return dest
    return None

def clasificar(nombres, n=None):
    n = n or normas()
    r = {"ok": [], "renombrar": {}, "sin_equivalente": [], "por_defecto": []}
    for nom in nombres:
        base = nom.split("::")[-1]
        if base in POR_DEFECTO: r["por_defecto"].append(nom); continue
        if definicion(base, n): r["ok"].append(nom); continue
        dest = equivalente(base, n)
        if dest and definicion(dest, n): r["renombrar"][nom] = dest
        else: r["sin_equivalente"].append(nom)
    return r

def diferencias(nombre, rgb, grosor, n=None, reducir=False):
    """Compara color y grosor de una capa con su definición. Devuelve dict de cambios o {}."""
    n = n or normas()
    df = definicion(nombre, n)
    if not df: return {}
    c, g, _ = _resolver(df[1], n, reducir)
    out = {}
    if tuple(rgb)[:3] != c: out["color"] = c
    if abs(float(grosor) - g) > 0.001: out["grosor_mm"] = g
    return out

def nueva_version(ruta):
    """.../vN/archivo.3dm -> .../vN+1/archivo.3dm ; si no hay vN -> .../v1/archivo.3dm"""
    d, f = os.path.split(ruta)
    m = re.match(r"^v(\d+)$", os.path.basename(d))
    return os.path.join(os.path.dirname(d), "v%d" % (int(m.group(1)) + 1), f) if m else os.path.join(d, "v1", f)

def resumen(**datos):
    return " | ".join("{}: {}".format(k, v) for k, v in datos.items())
