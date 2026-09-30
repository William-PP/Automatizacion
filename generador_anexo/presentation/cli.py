# -*- coding: utf-8 -*-
"""Capa de PRESENTACION: interfaz de linea de comandos (CLI).

Como se usa:
    py generar_anexo.py
    py generar_anexo.py ruta_exogena.xlsx
                        [--salida nombre.xlsx]
                        [--actividad 8010] [--consultante "NOMBRE CC 123"]
                        [--venta-activos-mas2]
                        [--subcontrato-2-mas]
"""

import glob
import os
import sys

from ..config.settings import CARPETA
from .composicion import leer_nombre_salida, procesar


def _parsear_args():
    """Devuelve (posicionales, {flag: valor}) sin mezclar ambos."""
    args = sys.argv[1:]
    posicionales = []
    opciones = {}
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--"):
            clave = a[2:]
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                opciones[clave] = args[i + 1]
                i += 2
                continue
            opciones[clave] = True
            i += 1
            continue
        posicionales.append(a)
        i += 1
    return posicionales, opciones


def _elegir_exogena():
    candidatos = glob.glob(os.path.join(CARPETA, "*Exogena*.xlsx"))
    if not candidatos:
        print("No se encontro el archivo de la exogena (*Exogena*.xlsx).")
        return None
    return max(candidatos, key=os.path.getmtime)


def main():
    posicionales, opciones = _parsear_args()

    exo_file = posicionales[0] if posicionales else _elegir_exogena()
    if not exo_file:
        return 1

    salida = opciones.get("salida") or os.path.join(
        CARPETA, leer_nombre_salida(exo_file) or "Anexo_Declaracion_de_renta.xlsx")

    reporte, _salida, _resumen = procesar(
        exo_file, salida,
        actividad=opciones.get("actividad", ""),
        encabezado=opciones.get("consultante", ""),
            venta_activos_mas_2_anos=("venta-activos-mas2" in opciones),
            subcontrato_2_mas=("subcontrato-2-mas" in opciones))
    print(reporte)
    return 0


__all__ = ["main"]