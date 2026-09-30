# -*- coding: utf-8 -*-
"""Capa de INFRAESTRUCTURA (excel): construccion del anexo desde plantilla.

Reemplaza la carga del .xlsx modelo. La plantilla es un JSON congelado
(config/anexo_layout.json) que describe TODA la hoja 'Borrador 210':
celdas (valor + estilo), merges, anchos de columna, alturas de fila y
paginacion. Con esto el generador NO depende del archivo modelo.

openpyxl al insertar filas mueve valores/estilos/formulas de las celdas
pero NO mueve los merges ni las alturas de fila; por eso los merges y las
alturas se aplican SIEMPRE AL FINAL via reaplicar_* con el corrimiento
acumulado de los inserts.
"""

import json
import os

from openpyxl import Workbook
from openpyxl.styles import (Alignment, Border, Color, Font, PatternFill,
                             Side)
from openpyxl.utils import column_index_from_string, get_column_letter
from openpyxl.utils.cell import range_boundaries

from ...config.settings import HOJA_MODELO
from .formulas import corrimiento_orig


def cargar_plantilla(ruta=None) -> dict:
    """Carga el JSON de la plantilla (default: config/anexo_layout.json)."""
    if ruta is None:
        ruta = os.path.join(os.path.dirname(__file__), "..", "..", "config",
                            "anexo_layout.json")
    with open(ruta, encoding="utf-8") as fh:
        return json.load(fh)


# ----------------------------------------------------------------------
# Reconstruccion de estilos openpyxl desde los dicts de la plantilla.
# ----------------------------------------------------------------------

def _color(info):
    """info -> Color | None. Soporta rgb, theme+tint e indexed."""
    if not info:
        return None
    if "rgb" in info:
        return Color(rgb=info["rgb"])
    if "theme" in info:
        return Color(theme=info["theme"], tint=info.get("tint", 0))
    if "indexed" in info:
        return Color(indexed=info["indexed"])
    return None


def _font(ed):
    return Font(
        name=ed.get("name"), size=ed.get("size"), bold=bool(ed.get("bold")),
        italic=bool(ed.get("italic")), underline=ed.get("underline"),
        color=_color(ed.get("color")))


def _fill(ed):
    if not ed or not ed.get("pattern"):
        return PatternFill()
    return PatternFill(
        patternType=ed.get("pattern"),
        fgColor=_color(ed.get("fg")), bgColor=_color(ed.get("bg")))


def _border(ed):
    lados = {}
    for lado in ("left", "right", "top", "bottom"):
        s = (ed or {}).get(lado) or {}
        lados[lado] = Side(style=s.get("style") or None,
                           color=_color(s.get("color")))
    return Border(**lados)


def _align(ed):
    return Alignment(
        horizontal=ed.get("h"), vertical=ed.get("v"),
        wrap_text=bool(ed.get("wrap")), shrink_to_fit=bool(ed.get("shrink")))


def aplicar_estilo(celda, sd):
    """Aplica un dict de estilo de la plantilla a una celda."""
    if not sd:
        return
    celda.font = _font(sd.get("font") or {})
    celda.fill = _fill(sd.get("fill"))
    celda.border = _border(sd.get("border"))
    celda.alignment = _align(sd.get("align"))
    celda.number_format = sd.get("number_format") or "General"


# ----------------------------------------------------------------------
# Construccion del workbook / hoja.
# ----------------------------------------------------------------------

def construir_workbook(plantilla=None):
    """Crea un Workbook NUEVO con la hoja del anexo dibujada desde la
    plantilla (valores, estilos, anchos, paginacion). NO aplica merges ni
    alturas de fila: se reaplican al final con el corrimiento (ver
    reaplicar_*). Devuelve (wb, ws)."""
    plantilla = plantilla or cargar_plantilla()
    wb = Workbook()
    ws = wb.active
    ws.title = HOJA_MODELO

    for coord, cel in plantilla.get("celdas", {}).items():
        fila, col = (int(x) for x in coord.split(":"))
        if col > 3:
            continue
        celda = ws.cell(fila, col)
        if "v" in cel:
            celda.value = cel["v"]
        if "st" in cel:
            idx = int(cel["st"][1:])
            aplicar_estilo(celda, plantilla["estilos"][idx])

    for col, ancho in plantilla.get("ancho_cols", {}).items():
        icol = column_index_from_string(col)
        ws.column_dimensions[get_column_letter(icol)].width = ancho

    _aplicar_paginacion(ws, plantilla)
    return wb, ws


def _aplicar_paginacion(ws, plantilla):
    pag = plantilla.get("paginacion") or {}
    try:
        ws.sheet_view.showGridLines = bool(pag.get("show_gridlines", True))
    except Exception:
        pass
    freeze = pag.get("freeze")
    if freeze:
        try:
            ws.freeze_panes = freeze
        except Exception:
            pass
    try:
        ws.sheet_properties.pageSetUpPr.fitToPage = bool(pag.get("fit_to_page"))
    except Exception:
        pass
    ws.page_setup.fitToWidth = pag.get("fit_to_width")
    ws.page_setup.fitToHeight = pag.get("fit_to_height")
    ws.page_setup.orientation = pag.get("orientation")
    margins = pag.get("margins")
    if margins:
        for k, v in margins.items():
            setattr(ws.page_margins, k, v)


# ----------------------------------------------------------------------
# Aplicacion posterior a los inserts (merges y alturas no se mueven solos).
# ----------------------------------------------------------------------

def reaplicar_merges(ws, plantilla, inserts):
    """Reaplica los merges de la plantilla desplazados por los inserts."""
    for rango in plantilla.get("merges", []):
        min_col, min_row, max_col, max_row = range_boundaries(rango)
        corr = corrimiento_orig(min_row, inserts)
        a = f"{get_column_letter(min_col)}{min_row + corr}"
        b = f"{get_column_letter(max_col)}{max_row + corr}"
        ws.merge_cells(f"{a}:{b}")


def reaplicar_alturas(ws, plantilla, inserts):
    """Reaplica las alturas de fila de la plantilla desplazadas por inserts."""
    for fila_str, altura in plantilla.get("altura_filas", {}).items():
        fila = int(fila_str) + corrimiento_orig(int(fila_str), inserts)
        ws.row_dimensions[fila].height = altura


__all__ = ["cargar_plantilla", "construir_workbook", "reaplicar_merges",
           "reaplicar_alturas", "aplicar_estilo"]