# -*- coding: utf-8 -*-
"""Capa de UTILIDADES: formateo de numeros para reporte y celdas."""


def fmt_valor(v):
    """Numero entero redondeado para escribir en una celda del anexo."""
    return int(round(v))


def num(v):
    """Numero formateado con miles para el reporte por consola."""
    if isinstance(v, (int, float)):
        return f"{v:,.0f}"
    return str(v)


def render_pct(pct):
    return f"{pct:g}" if float(pct).is_integer() else f"{pct:g}"


__all__ = ["fmt_valor", "num", "render_pct"]