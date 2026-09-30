# -*- coding: utf-8 -*-
"""Capa de INFRAESTRUCTURA (excel): adaptador que llena el anexo.

Implementa el puerto EscritorAnexo. NO depende del .xlsx modelo: dibuja la
hoja desde la plantilla congelada (config/anexo_layout.json), inserta filas
cuando faltan casillas (terceros/avaluos) y tambien el separador del nuevo
encabezado (fila 4 en blanco), traduce formulas, escribe los valores con su
formato, reaplica merges/alturas (openpyxl no los mueve al insertar) y
guarda en la ruta pedida (con respaldo si el archivo esta abierto).
"""

import os
from datetime import date, datetime

from ...application.puertos import EscritorAnexo
from ...config.settings import CARPETA, HOJA_MODELO
from ..util.formato import fmt_valor
from .escritor import escribir_filas, escribir_total
from .estilos import capturar_estilo
from .formulas import corrimiento, traducir_formulas
from .planificador import _es_bloque, plan_filas
from .plantilla import (cargar_plantilla, construir_workbook,
                        reaplicar_alturas, reaplicar_merges)
from .totales import ajustes_retenciones, recalcular_totales

# El anexo generado separa la zona del encabezado del cuerpo con una fila:
#   fila 1 titulo, 2 consultante, 3 actividad, 4 EN BLANCO, 5 encabezados
#   de tabla, 6+ cuerpo. La plantilla congela el modelo ORIGINAL (encabezado
#   en fila 4, cuerpo desde fila 5), asi que insertamos UNA fila base en 4.
FILA_INSERT_BASE = 4


class EscritorAnexoExcel(EscritorAnexo):

    def escribir(self, ruta_salida: str, por_regla: list,
                 total_ret: int, n_ret: int,
                 encabezado: str = "", actividad: str = "") -> str:
        plantilla = cargar_plantilla()
        wb, ws = construir_workbook(plantilla)

        self._escribir_encabezado(ws, encabezado, actividad)

        # --- plan: que filas se insertan y donde escribe cada regla --------
        inserts, inicio = plan_filas(ws, por_regla,
                                     [(FILA_INSERT_BASE, 1)])

        # estilos del modelo (antes de insertar; luego las celdas se mueven).
        # Una regla de bloque toma el estilo de la primera fila de detalle del
        # bloque, no de un numero de fila fijo.
        estilos = {}
        for regla, _grupos in por_regla:
            base = regla.bloque + 1 if _es_bloque(regla) else regla.fila
            estilos[id(regla)] = capturar_estilo(ws, base)

        for at, n in inserts:
            ws.insert_rows(at, n)

        # corregir todas las referencias de las formulas de la plantilla
        traducir_formulas(ws, inserts)

        # escribir valores
        for regla, grupos in por_regla:
            est = estilos[id(regla)]
            if regla.agregar in ("tercero", "detalle"):
                escribir_filas(ws, regla, grupos, inicio[id(regla)], est)
            else:
                fila = regla.fila + corrimiento(regla.fila, inserts)
                escribir_total(ws, regla, grupos[0][1], fila, est)

        reaplicar_merges(ws, plantilla, inserts)
        reaplicar_alturas(ws, plantilla, inserts)

        recalcular_totales(ws)
        ajustes_retenciones(ws, total_ret, n_ret)

        return self._guardar(wb, ruta_salida)

    @staticmethod
    def _escribir_encabezado(ws, encabezado: str, actividad: str):
        """Rellena la zona superior del anexo:
        A2 = nombres + tipo documento + identificacion del consultante
        A3 = 'Actividad economica <codigo>' (codigo agregado por el usuario)."""
        if encabezado:
            ws.cell(2, 1).value = encabezado
        if actividad:
            base = str(ws.cell(3, 1).value or "Actividad economica ").rstrip()
            ws.cell(3, 1).value = f"{base} {actividad}".strip()

    @staticmethod
    def _guardar(wb, salida):
        try:
            wb.save(salida)
        except PermissionError:
            salida = os.path.join(
                CARPETA,
                f"Anexo 210 - {date.today().isoformat()} "
                f"{datetime.now().strftime('%H%M%S')}.xlsx")
            wb.save(salida)
        return salida


__all__ = ["EscritorAnexoExcel", "fmt_valor"]