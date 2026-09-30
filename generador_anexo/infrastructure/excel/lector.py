# -*- coding: utf-8 -*-
"""Capa de INFRAESTRUCTURA (excel): lector de la Informacion Exogena.

Adaptador concreto del puerto LectorExogena. Detecta dos variantes del
archivo y las normaliza a InformeExogena (topes, conceptos, consultante):

  - COMPLETO (descargado de la DIAN): tiene bloque "Identificacion del
    consultante" (filas 5-8), una imagen y columnas extra (A=NIT, B=Nombre
    tercero, C=NIT consultante, D=Nombre consultante, E=Detalle, F=Valor,
    G=Uso, H=Info). Los topes viven en E/F.
  - EDITADO (ya depurado a mano): son las 6 columnas A/B/C/D/E/F y los
    topes en C/D.

Solo se lee lo necesario (en memoria); la imagen y columnas extra jamas
se copian al anexo.
"""

from openpyxl import load_workbook

from ...application.puertos import LectorExogena
from ...config.settings import HOJA_EXOGENA
from ...domain.entidades import Concepto, Consultante, InformeExogena, Tope


class LectorExogenaExcel(LectorExogena):

    def leer(self, ruta_archivo: str) -> InformeExogena:
        wb = load_workbook(ruta_archivo, data_only=True)
        try:
            ws = wb[HOJA_EXOGENA]
            if self._es_completo(ws):
                return self._leer_completo(ws)
            return self._leer_editado(ws)
        finally:
            wb.close()

    # ------------------------------------------------------------------
    @staticmethod
    def _es_completo(ws) -> bool:
        # El formato completo trae el bloque de identificacion y la
        # columna H ("Información Adicional") con contenido en filas de datos.
        for r in range(1, min(ws.max_row, 12)):
            v = ws.cell(r, 1).value
            if isinstance(v, str) and "Identificación del consultante" in v:
                return True
        return False

    # ------------------------------------------------------------------
    def _leer_completo(self, ws) -> InformeExogena:
        topes = []
        for r in range(14, ws.max_row + 1):
            nombre = ws.cell(r, 5).value   # col E
            valor = ws.cell(r, 6).value    # col F
            if isinstance(nombre, str) and nombre.strip().startswith("Tope"):
                topes.append(Tope(nombre=nombre.strip(), valor=valor))

        conceptos = []
        for r in range(14, ws.max_row + 1):
            detalle = ws.cell(r, 5).value   # col E
            valor = ws.cell(r, 6).value     # col F
            if detalle is None and valor is None:
                continue
            if isinstance(detalle, str) and detalle.strip().startswith("Tope"):
                continue
            if isinstance(detalle, str) and detalle.strip() in ("Detalle", "Valor"):
                continue
            try:
                valor_num = float(valor or 0)
            except (TypeError, ValueError):
                continue
            conceptos.append(Concepto(
                fila=r,
                tercero=str(ws.cell(r, 2).value or "(sin nombre)"),
                detalle=str(detalle or ""),
                valor=valor_num,
                uso=str(ws.cell(r, 7).value or ""),
                info=str(ws.cell(r, 8).value or ""),
            ))

        return InformeExogena(
            topes=topes,
            conceptos=conceptos,
            consultante=self._leer_consultante(ws),
        )

    @staticmethod
    def _leer_consultante(ws) -> Consultante | None:
        tipo = ""
        ident = ""
        nombres = ""
        for r in range(5, 9):
            etiqueta = str(ws.cell(r, 1).value or "")
            if "Tipo de documento" in etiqueta:
                tipo = str(ws.cell(r, 3).value or "").strip()
            elif "Identificación" in etiqueta and "Identificación del" not in etiqueta:
                ident = str(ws.cell(r, 3).value or "").strip()
            elif "Nombres" in etiqueta or "Razón social" in etiqueta:
                nombres = str(ws.cell(r, 3).value or "").strip()
        if not (tipo or ident or nombres):
            return None
        return Consultante(tipo_documento=tipo, identificacion=ident,
                           nombres=nombres)

    # ------------------------------------------------------------------
    def _leer_editado(self, ws) -> InformeExogena:
        topes = []
        for r in range(3, 8):
            nombre = ws.cell(r, 3).value   # col C
            valor = ws.cell(r, 4).value    # col D
            if nombre:
                topes.append(Tope(nombre=nombre, valor=valor))
        conceptos = []
        for r in range(8, ws.max_row + 1):
            detalle = ws.cell(r, 3).value  # col C
            valor = ws.cell(r, 4).value    # col D
            if detalle is None and valor is None:
                continue
            conceptos.append(Concepto(
                fila=r,
                tercero=str(ws.cell(r, 1).value or "(sin nombre)"),
                detalle=str(detalle or ""),
                valor=float(valor or 0),
                uso=str(ws.cell(r, 5).value or ""),
                info=str(ws.cell(r, 6).value or ""),
            ))
        return InformeExogena(topes=topes, conceptos=conceptos)


__all__ = ["LectorExogenaExcel"]