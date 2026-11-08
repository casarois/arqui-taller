#! python3
# Caso: nucleo/captura.py de una zona a ppmm dados, a la carpeta de la prueba. Mide el PNG real.
import captura
_mod = sc.doc.Modified
_r = captura.main(zona=tuple(PARAMS["zona"]), salida=SALIDA, ppmm=PARAMS.get("ppmm", 10))
_png = campo(_r, "png")
_tam = png_tam(_png) if _png and os.path.isfile(_png) else None
resultado(unidades=unidades(),
          png_existe=bool(_tam),
          ancho_px=_tam[0] if _tam else None,
          alto_px=_tam[1] if _tam else None,
          px_resumen=campo(_r, "px"),
          tinta=tinta(_png) if _tam else None,
          dentro_de_salida=bool(_png) and os.path.normcase(os.path.abspath(_png)).startswith(os.path.normcase(os.path.abspath(SALIDA))),
          doc_modificado=(sc.doc.Modified and not _mod))
