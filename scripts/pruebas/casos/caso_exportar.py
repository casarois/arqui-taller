#! python3
# Caso: nucleo/exportar.py en un documento sin layouts (rama espacio modelo con LAMINA_00_PAPEL).
# Exporta a SALIDA y comprueba: PDF (páginas y tamaño leídos del archivo), preview PNG, que no queden layouts,
# que no escriba nada fuera de SALIDA (carpeta del documento) y que no marque el documento como modificado.
import exportar
_k = dict(PARAMS)
_tema = _k.pop("tema", "Prueba")
_dir_doc = os.path.dirname(sc.doc.Path)
_antes = archivos(_dir_doc, excluir=SALIDA)
_layouts_antes = len(sc.doc.Views.GetPageViews())
_mod = sc.doc.Modified
_r = exportar.main(_tema, carpeta=SALIDA, **_k)
_fuera = sorted(archivos(_dir_doc, excluir=SALIDA) - _antes)
_nombre = "Lamina_%s_%s" % (_k.get("formato", "A2"), _tema)
_pdf = os.path.join(SALIDA, _nombre + ".pdf")
_png = os.path.join(SALIDA, _nombre + "_preview.png")
_pag, _cajas = pdf_paginas(_pdf) if os.path.isfile(_pdf) else (0, [])
_tam = png_tam(_png) if os.path.isfile(_png) else None
resultado(unidades=unidades(),
          layouts_antes=_layouts_antes,
          pdf_paginas=_pag,
          pdf_ancho_mm=round(_cajas[0][0], 3) if _cajas else None,
          pdf_alto_mm=round(_cajas[0][1], 3) if _cajas else None,
          pdf_cajas_distintas=len(set((round(a, 1), round(b, 1)) for a, b in _cajas)),
          pdf_kb=round(os.path.getsize(_pdf) / 1024.0) if os.path.isfile(_pdf) else None,
          preview_tinta=tinta(_png, 10) if _tam else None,
          preview_ancho_px=_tam[0] if _tam else None,
          preview_alto_px=_tam[1] if _tam else None,
          archivos_en_salida=len(os.listdir(SALIDA)),
          archivos_fuera_de_salida=len(_fuera),
          layouts_despues=len(sc.doc.Views.GetPageViews()),
          doc_modificado=(sc.doc.Modified and not _mod),
          exportado=campo(_r, "exportado"))
