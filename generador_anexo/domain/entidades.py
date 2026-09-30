# -*- coding: utf-8 -*-
"""Capa de DOMINIO: entidades tipadas de la exogena y el anexo."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Tope:
    """Un 'Tope' del encabezado de la exogena (ej. Tope 1 - Ingresos)."""
    nombre: str
    valor: float


@dataclass(frozen=True)
class Concepto:
    """Un concepto tal como viene en la exogena (una fila del reporte)."""
    fila: int
    tercero: str
    detalle: str
    valor: float
    uso: str
    info: str


@dataclass(frozen=True)
class Consultante:
    """Datos de identificacion del consultante (quien declara).

    Se extraen de la parte superior del formato COMPLETO de la exogena
    (bloque "Identificacion del consultante") antes de la limpieza.
    """
    tipo_documento: str
    identificacion: str
    nombres: str


@dataclass
class InformeExogena:
    """Contenido normalizado del archivo exogena.

    El lector adapta cualquier variante (completa o ya editada) a esta
    estructura para que el dominio siempre trabaje igual.
    """
    topes: list[Tope] = field(default_factory=list)
    conceptos: list[Concepto] = field(default_factory=list)
    consultante: Consultante | None = None


__all__ = ["Tope", "Concepto", "Consultante", "InformeExogena"]