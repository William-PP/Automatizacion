# -*- coding: utf-8 -*-
"""Capa de APLICACION: puertos (interfaces) y DTOs.

La aplicacion solo conoce interfaces (Protocol) sobre los adaptadores de
infraestructura; no importa openpyxl ni tkinter.
"""

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from ..domain.entidades import Concepto, Consultante, InformeExogena, Tope


@runtime_checkable
class LectorExogena(Protocol):
    """Puerto de entrada: lee la exogena y entrega datos normalizados."""
    def leer(self, ruta_archivo: str) -> InformeExogena:
        """Devuelve el informe (topes, conceptos, consultante)."""
        ...


@runtime_checkable
class EscritorAnexo(Protocol):
    """Puerto de salida: escribe los datos en el anexo y lo guarda."""
    def escribir(self, ruta_salida: str, por_regla: list, total_ret: int,
                 n_ret: int, encabezado: str = "", actividad: str = "") -> str:
        """Llena la hoja del anexo (dibujada desde la plantilla interna,
        sin depender del .xlsx modelo) y devuelve la ruta final guardada
        (puede diferir de ruta_salida si esta abierto en Excel)."""
        ...


@dataclass
class Resultado:
    """DTO que entrega el caso de uso a la capa de presentacion."""
    topes: list[Tope]
    por_regla: list                     # [(Regla, grupos)]
    no_mapeados: list                   # [(Concepto, es_informativo)]
    resumen: list                       # [(nombre_seccion, total)]
    salida: str                         # ruta final guardada
    salida_solicitada: str = ""         # ruta que se pidio (detecta respaldo)
    encabezado: str = ""                 # linea de identificacion (fila 2)
    actividad: str = ""                 # codigo de actividad economica (fila 3)
    archivo_exogena: str = ""
    notas: list = field(default_factory=list)   # decisiones de negocio a revisar


__all__ = ["LectorExogena", "EscritorAnexo", "Resultado",
           "Concepto", "Tope"]