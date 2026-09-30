# -*- coding: utf-8 -*-
"""Capa de DOMINIO: reglas de mapeo concepto -> anexo.

Las reglas TIPIFICADAS (Regla) se construyen desde los datos de
config.reglas_anexo para evitar accesos con claves sueltas. Contiene el
matcheo entre un Concepto de la exogena y la casilla del anexo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


# "Valor avalúo vehicular (Concepto: 1480)" -> "1480"
_RE_CODIGO = re.compile(r"Concepto:\s*(\d+)")


def codigo_concepto(detalle: str) -> str:
    """Extrae el codigo de concepto de la exogena ("Concepto: 1480")."""
    m = _RE_CODIGO.search(detalle or "")
    return m.group(1) if m else ""


@dataclass(frozen=True)
class Regla:
    """Instruccion de escritura para un concepto.

    nombre    : descripcion (solo para el resumen/reporte)
    match_c   : texto que debe aparecer en la columna C "Detalle"
    match_codigo:
                codigo de concepto de la exogena ("1480"), tal como viene
                en el detalle. Es la clave estable con la DIAN: ancla la
                regla aunque cambie la redaccion del texto. OJO: un mismo
                codigo puede traer varios conceptos distintos (p.ej. 4070
                = "Retencion distribuida" e "Ingreso distribuido"), por eso
                NO reemplaza a match_c: se combinan (codigo Y texto).
    match_e   : texto que debe aparecer en la columna E "Uso declaracion sugerida"
    fila      : fila del anexo donde empieza a escribir
    bloque    : fila del TITULO que abre el bloque donde cae la regla.
                Si se informa (y agregar es "tercero"/"detalle"), la regla ya
                NO tiene fila fija: recibe sus filas DENTRO de ese bloque, en
                el orden en que aparecen las reglas, y el planificador
                inserta las filas que falten justo antes del siguiente
                titulo. Ver infrastructure.excel.planificador.
    agregar   : "total"   -> suma en una sola celda
                "tercero" -> una fila POR CADA tercero
                "detalle" -> una fila por matricula (ej. avaluos)
    max_filas : filas disponibles en el modelo (si no caben, se INSERTAN mas)
    col       : columna destino (default "B" = PARCIAL)
    formula_c : formula opcional para columna C. Admite {row} y {factor}.
                None => la columna C no se toca (queda como en el modelo).
    decimales : True -> numero con dos decimales (ej. avaluos)
    espejo    : True -> C = B (dejar de lado el factor)
    plantilla_detalle:
                texto opcional para col A cuando agregar="detalle".
                Admite {matricula}, {valor} y {pct} (ej. avaluos).
    plantilla_tercero:
                texto opcional para col A cuando agregar="tercero".
                Admite {tercero} (ej. documentos soporte por no obligados).
    """
    nombre: str
    match_c: Optional[str] = None
    match_codigo: Optional[str] = None
    match_e: Optional[str] = None
    fila: int = 0
    bloque: Optional[int] = None
    agregar: str = "total"
    max_filas: int = 1
    col: str = "B"
    formula_c: Optional[str] = "=B{row}"
    decimales: Optional[bool] = False
    espejo: bool = True
    plantilla_detalle: Optional[str] = None
    plantilla_tercero: Optional[str] = None

    def coincide(self, concepto) -> bool:
        """True si este concepto de la exogena cae en esta regla."""
        if self.match_codigo and self.match_codigo != codigo_concepto(
                concepto.detalle):
            return False
        if self.match_c and self.match_c not in concepto.detalle:
            return False
        if self.match_e and self.match_e not in concepto.uso:
            return False
        return True


def construir_reglas(definiciones) -> list[Regla]:
    """Convierte los dicts de config.reglas_anexo en objetos Regla."""
    return [Regla(**d) for d in definiciones]


def aplicar_venta_activos(definiciones, mas_2_anos: bool) -> list[dict]:
    """Elige la variante de la regla de venta de activos fijos.

    Por defecto (<2 anos o sin dato de antiguedad) el valor va a RENTAS NO
    LABORALES (fila 116). Si `mas_2_anos` es True se sabe que el activo se
    poseyo mas de 2 anos, asi que se sustituye por la variante de GANANCIA
    OCASIONAL (fila 173) conservando la posicion en la lista de reglas.
    """
    if not mas_2_anos:
        return list(definiciones)
    from ..config.reglas_anexo import REGLA_VENTA_ACTIVOS_FIJOS_MAS2
    return [
        REGLA_VENTA_ACTIVOS_FIJOS_MAS2
        if d.get("nombre") == "Venta de activos fijos (<2 anos) -> Renta no laboral"
        else d
        for d in definiciones
    ]


def aplicar_subcontratacion(definiciones, subcontrato_2_mas: bool) -> list[dict]:
    """Aplica la condicion de la Seccion B de la cedula general.

    Seccion B: honorarios, comisiones y servicios (5002/5003/5004) son renta
    de trabajo solo si el contribuyente NO subcontrato 2 o mas personas por al
    menos 90 dias. Ese dato no viene en la exogena, asi que lo indica el
    usuario. Si `subcontrato_2_mas` es True se sustituyen las tres reglas de
    trabajo por sus variantes, que escriben en RENTAS NO LABORALES.
    """
    if not subcontrato_2_mas:
        return list(definiciones)
    from ..config import reglas_anexo as cfg
    sustitutos = {
        "Honorarios (R43) -> Honorarios": cfg.REGLA_HONORARIOS_SUB,
        "Comisiones (R43) -> Comisiones": cfg.REGLA_COMISIONES_SUB,
        "Servicios (R43) -> Servicios": cfg.REGLA_SERVICIOS_SUB,
    }
    return [sustitutos.get(d.get("nombre"), d) for d in definiciones]


__all__ = ["Regla", "construir_reglas", "aplicar_venta_activos",
           "aplicar_subcontratacion", "codigo_concepto"]