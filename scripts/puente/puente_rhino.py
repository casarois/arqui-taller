#! python3
"""Puente local Rhino <-> Claude (sustituye a rhino-mcp/MCP4Rhino en Rhino 8.5 / .NET 7).
Arranque en Rhino:  _-RunPythonScript "C:\\Users\\2402l\\Documents\\UNI\\CLAUDE\\arqui-taller\\scripts\\puente\\puente_rhino.py"
Escucha SOLO en 127.0.0.1, primer puerto libre de 4250-4259 (uno por Rhino abierto);
se registra en %LOCALAPPDATA%\\puente_rhino\\<pid>.json para que rhino.ps1 lo encuentre. Recibe JSON {"code": "..."} y lo ejecuta en el hilo de Rhino.
Responde JSON {"ok": bool, "out": stdout, "error": traceback}.
Solo arranca: si ya está activo no hace nada. Para pararlo: puente_parar.py. Se cierra solo al cerrar Rhino.
"""
import socket, threading, json, io, os, sys, traceback
import System, Rhino, scriptcontext as sc

HOST, PORT = "127.0.0.1", 4250
CLAVE = "puente_claude"
SCRIPTS = r"C:\Users\2402l\Documents\UNI\CLAUDE\arqui-taller\scripts"
# Todas las subcarpetas de scripts\ (nucleo, dibujo, lamina...) quedan importables: import util, import capas...
for _sub in [SCRIPTS] + sorted(os.path.join(SCRIPTS, d) for d in os.listdir(SCRIPTS) if os.path.isdir(os.path.join(SCRIPTS, d)) and not d.startswith("_")):
    if _sub not in sys.path: sys.path.insert(0, _sub)

ENTORNO = {"__name__": "__puente__", "Rhino": Rhino, "sc": sc, "System": System}

def _ejecutar(code):
    res = {"ok": True, "out": "", "error": ""}
    buf, viejo = io.StringIO(), sys.stdout
    sys.stdout = buf
    try:
        sc.doc = Rhino.RhinoDoc.ActiveDoc
        exec(compile(code, "<claude>", "exec"), ENTORNO)
        if sc.doc: sc.doc.Views.Redraw()
    except Exception:
        res["ok"] = False
        res["error"] = traceback.format_exc()
    finally:
        sys.stdout = viejo
    res["out"] = buf.getvalue()
    return res

def _en_hilo_rhino(code):
    caja, listo = {}, threading.Event()
    def tarea():
        try: caja["r"] = _ejecutar(code)
        finally: listo.set()
    Rhino.RhinoApp.InvokeOnUiThread(System.Action(tarea), System.Array[System.Object]([]))
    if not listo.wait(600):
        return {"ok": False, "out": "", "error": "timeout (600 s)"}
    return caja["r"]

def _atender(con):
    try:
        datos = b""
        while True:
            t = con.recv(65536)
            if not t: break
            datos += t
        code = json.loads(datos.decode("utf-8-sig"))["code"]
        r = _en_hilo_rhino(code)
    except Exception:
        r = {"ok": False, "out": "", "error": traceback.format_exc()}
    try: con.sendall(json.dumps(r, ensure_ascii=False).encode("utf-8"))
    finally: con.close()

def _servir(srv, estado):
    while estado["activo"]:
        try: con, _ = srv.accept()
        except OSError: break
        threading.Thread(target=_atender, args=(con,), daemon=True).start()

REGISTRO = os.path.join(os.environ["LOCALAPPDATA"], "puente_rhino")

def main():
    previo = sc.sticky.get(CLAVE)
    if previo and previo.get("activo"):
        print("[puente] ya estaba activo en el puerto %s" % previo.get("puerto", "?")); return
    srv = None
    for puerto in range(PORT, PORT + 10):   # un puerto libre por cada Rhino abierto
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind((HOST, puerto)); srv = s; break
        except OSError:
            s.close()
    if not srv:
        print("[puente] sin puertos libres %d-%d" % (PORT, PORT + 9)); return
    srv.listen(4)
    pid = System.Diagnostics.Process.GetCurrentProcess().Id
    if not os.path.isdir(REGISTRO): os.makedirs(REGISTRO)
    fichero = os.path.join(REGISTRO, "%d.json" % pid)
    with open(fichero, "w", encoding="utf-8") as f:
        json.dump({"pid": pid, "port": puerto}, f)
    estado = {"activo": True, "srv": srv, "fichero": fichero, "puerto": puerto}
    sc.sticky[CLAVE] = estado
    def _al_cerrar(sender, e):   # al cerrar Rhino: cerrar puerto y borrar registro
        estado["activo"] = False
        try: srv.close()
        except Exception: pass
        try: os.remove(fichero)
        except Exception: pass
    Rhino.RhinoApp.Closing += _al_cerrar
    threading.Thread(target=_servir, args=(srv, estado), daemon=True).start()
    print("[puente] escuchando en %s:%d (para pararlo: puente_parar.py)" % (HOST, puerto))

main()
