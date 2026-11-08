#! python3
# Caso: revision/holgura.py con zona y parámetros de esperado.json (resto por defecto). No modifica.
import holgura
_kw = dict(PARAMS)
if "zona" in _kw: _kw["zona"] = tuple(_kw["zona"])
if "contexto" in _kw and isinstance(_kw["contexto"], list): _kw["contexto"] = tuple(_kw["contexto"])
_mod = sc.doc.Modified
_r = holgura.main(**_kw)
resultado(unidades=unidades(),
          distancia_min_mm=numero(campo(_r, "distancia_min_mm")),
          cumple=campo(_r, "cumple"),
          error=campo(_r, "error"),
          doc_modificado=(sc.doc.Modified and not _mod))
