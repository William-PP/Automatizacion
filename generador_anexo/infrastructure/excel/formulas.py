# -*- coding: utf-8 -*-
"""Capa de INFRAESTRUCTURA (excel): manejo de filas y formulas.

openpyxl mueve las celdas al insertar filas pero NO reescribe las
formulas. Como las formulas del modelo usan filas absolutas (C103+C108,
SUM(B181), ...) hay que traducir esas referencias tras cada insercion.
"""

import re


def corrimiento_orig(fila, inserts):
    """Cuanto se movio (hacia abajo) una fila ORIGINAL tras las inserciones."""
    return sum(n for at, n in inserts if at <= fila)


def corrimiento(fila, inserts):
    return corrimiento_orig(fila, inserts)


def traducir_formulas(ws, inserts):
    """Reescribe las referencias de fila de TODAS las formulas del modelo,
    para que sigan apuntando a las mismas celdas despues de insertar filas."""
    ref = re.compile(r"([A-Z]{1,3})(\$?)(\d+)")

    def reemplazar(m):
        letra, dolar, fila = m.group(1), m.group(2), int(m.group(3))
        return f"{letra}{dolar}{fila + corrimiento_orig(fila, inserts)}"

    for row in ws.iter_rows():
        for celda in row:
            v = celda.value
            if isinstance(v, str) and v.startswith("="):
                celda.value = ref.sub(reemplazar, v)


__all__ = ["corrimiento_orig", "corrimiento", "traducir_formulas"]