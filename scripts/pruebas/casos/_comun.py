#! python3
# _comun.py — se antepone a cada caso (lo hace probar.ps1). Antes vienen definidas:
#   NOMBRE_PRUEBA, SALIDA (carpeta de salida de esta prueba), ESPERADO (ruta de esperado.json).
# Da PARAMS (los "parametros" de la prueba en esperado.json) y utilidades. El caso termina con resultado(...).
import json, os, re, struct, zlib
import scriptcontext as sc
import Rhino
import Rhino.Geometry as rg

with open(ESPERADO, encoding="utf-8") as _f:
    PARAMS = [p for p in json.load(_f)["pruebas"] if p["nombre"] == NOMBRE_PRUEBA][0].get("parametros", {})
os.makedirs(SALIDA, exist_ok=True)

def resultado(**d):
    """Única línea que lee probar.ps1."""
    print("RESULTADO " + json.dumps(d, ensure_ascii=True))

def campo(resumen, clave):
    """Valor de 'clave: valor' en una línea de util.resumen ('a: 1 | b: 2'), o None."""
    for parte in (resumen or "").split(" | "):
        k, _, v = parte.partition(": ")
        if k.strip() == clave: return v.strip()
    return None

def numero(txt):
    m = re.search(r"-?\d+(?:\.\d+)?", txt or "")
    return float(m.group(0)) if m else None

def unidades():
    return str(sc.doc.ModelUnitSystem)

def png_tam(ruta):
    """(ancho, alto) leídos de la cabecera IHDR del PNG."""
    with open(ruta, "rb") as f: cab = f.read(24)
    if cab[:8] != b"\x89PNG\r\n\x1a\n": return None
    return struct.unpack(">II", cab[16:24])

def tinta(ruta, paso=4):
    """Fracción (0-1) de píxeles no blancos, muestreando 1 de cada 'paso' en x e y (detecta capturas en blanco)."""
    import System.Drawing as sd
    bmp = sd.Bitmap(ruta)
    try:
        n = t = 0
        for y in range(0, bmp.Height, paso):
            for x in range(0, bmp.Width, paso):
                c = bmp.GetPixel(x, y); n += 1
                if c.R < 245 or c.G < 245 or c.B < 245: t += 1
        return round(float(t) / max(n, 1), 4)
    finally:
        bmp.Dispose()

def pdf_paginas(ruta):
    """(nº de páginas, [(ancho_mm, alto_mm) de cada MediaBox]) leyendo el PDF (también streams comprimidos)."""
    data = open(ruta, "rb").read()
    trozos = [data]
    for m in re.finditer(rb"stream\r?\n", data):
        fin = data.find(b"endstream", m.end())
        if fin < 0: continue
        try: trozos.append(zlib.decompressobj().decompress(data[m.end():fin]))
        except Exception: pass
    paginas, cajas = 0, []
    for t in trozos:
        paginas += len(re.findall(rb"/Type\s*/Page(?![A-Za-z])", t))
        for c in re.findall(rb"/MediaBox\s*\[\s*([-0-9.\s]+?)\s*\]", t):
            v = [float(x) for x in c.split()]
            if len(v) == 4: cajas.append((abs(v[2] - v[0]) / 72.0 * 25.4, abs(v[3] - v[1]) / 72.0 * 25.4))
    return paginas, cajas

def archivos(carpeta, excluir=None):
    """Conjunto de rutas relativas de los archivos bajo carpeta (sin los que estén bajo 'excluir')."""
    out = set()
    ex = os.path.normcase(os.path.abspath(excluir)) if excluir else None
    for raiz, _, fs in os.walk(carpeta):
        if ex and os.path.normcase(os.path.abspath(raiz)).startswith(ex): continue
        for f in fs: out.add(os.path.relpath(os.path.join(raiz, f), carpeta))
    return out

def en_planta(c, tol):
    """Curva llevada a z=0 (traslada si es horizontal, proyecta si no)."""
    bb = c.GetBoundingBox(False)
    if bb.Max.Z - bb.Min.Z <= tol:
        if abs(bb.Min.Z) > tol:
            c = c.DuplicateCurve(); c.Translate(rg.Vector3d(0, 0, -bb.Min.Z))
        return c
    return rg.Curve.ProjectToPlane(c, rg.Plane.WorldXY) or c
