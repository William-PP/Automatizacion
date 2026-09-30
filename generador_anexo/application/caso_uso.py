# -*- coding: utf-8 -*-
"""Capa de APLICACION: caso de uso que orquesta la generacion del anexo.

Depende SOLO de los puertos (LectorExogena, EscritorAnexo) y del dominio.
No importa openpyxl ni tkinter. Las reglas y patrones de mapeo se
inyectan desde la capa de presentacion (composicion).
"""

import os
import re

from ..config.settings import CARPETA
from ..domain.encabezado import componer_encabezado
from ..domain.mapeo import agrupar, mapear
from ..domain.reglas import (aplicar_subcontratacion, aplicar_venta_activos,
                             construir_reglas)
from .puertos import EscritorAnexo, LectorExogena, Resultado


def _limpiar_nombre(nombres: str) -> str:
    """Solo letras/digitos y separadores de palabra seguros."""
    limpio = re.sub(r"[^0-9A-Za-zÁÉÍÓÚÑáéíóúñ ]+", " ", nombres).strip()
    return re.sub(r"\s+", "_", limpio)


def construir_nombre_salida(consultante) -> str:
    """Nombre de archivo pedido por el usuario:
    Anexo_Declaracion_de_renta_<Nombre>[Ape].xlsx (desde el consultante)."""
    base = _limpiar_nombre(getattr(consultante, "nombres", "") or "")
    if not base:
        base = _limpiar_nombre(getattr(consultante, "identificacion", "") or "")
    if not base:
        return ""
    return f"Anexo_Declaracion_de_renta_{base}.xlsx"


def extraer_retenciones(por_regla):
    """Devuelve (total_retenciones, n_retenciones) de la regla R132,
    si existe entre las reglas mapeadas."""
    total = 0
    n = 0
    for regla, grupos in por_regla:
        if regla.match_e and "R132" in regla.match_e:
            total = sum(v for _, v in grupos)
            n = len(grupos)
    return total, n


def construir_resumen(por_regla):
    """Resumen de totales por seccion, ordenado de mayor a menor."""
    usado = {regla.nombre: sum(v for _, v in grupos)
             for regla, grupos in por_regla}
    return sorted(usado.items(), key=lambda x: -x[1])


def procesar_anexo(lector: LectorExogena, escritor: EscritorAnexo,
                   exo_file: str, salida: str = "",
                   actividad: str = "", encabezado: str = "",
                   venta_activos_mas_2_anos: bool = False,
                   subcontrato_2_mas: bool = False,
                   reglas_def=None, info_patterns=None) -> Resultado:
    """Flujo completo: leer exogena -> mapear conceptos -> escribir anexo.

    `venta_activos_mas_2_anos`: si True, la venta de activos fijos va a
    ganancia ocasional; por defecto va a rentas no laborales.
    `subcontrato_2_mas`: si True, honorarios/comisiones/servicios (5002/5003/
    5004) van a rentas no laborales en vez de a renta de trabajo, porque se
    subcontrato 2 o mas personas por al menos 90 dias (Seccion B).
    """
    if reglas_def is None:
        from ..config.reglas_anexo import RULES
        reglas_def = RULES
    if info_patterns is None:
        from ..config.reglas_anexo import INFO_PATTERNS
        info_patterns = INFO_PATTERNS

    informe = lector.leer(exo_file)
    encabezado = encabezado or (
        componer_encabezado(informe.consultante)
        if informe.consultante else "")

    if not salida:
        nombre = construir_nombre_salida(informe.consultante) \
            if informe.consultante else ""
        if nombre:
            salida = os.path.join(CARPETA, nombre)

    defs = aplicar_subcontratacion(reglas_def, subcontrato_2_mas)
    reglas = construir_reglas(aplicar_venta_activos(defs,
                                                    venta_activos_mas_2_anos))
    asignados, no_mapeados = mapear(informe.conceptos, reglas, info_patterns)
    por_regla = agrupar(asignados)

    total_ret, n_ret = extraer_retenciones(por_regla)
    salida_final = escritor.escribir(salida, por_regla,
                                     total_ret, n_ret,
                                     encabezado=encabezado,
                                     actividad=actividad)

    return Resultado(
        topes=informe.topes,
        por_regla=por_regla,
        no_mapeados=no_mapeados,
        resumen=construir_resumen(por_regla),
        salida=salida_final,
        salida_solicitada=salida,
        encabezado=encabezado,
        actividad=actividad,
        archivo_exogena=exo_file,
    )


__all__ = ["procesar_anexo", "construir_resumen", "extraer_retenciones",
           "construir_nombre_salida"]