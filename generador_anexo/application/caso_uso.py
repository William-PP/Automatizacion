# -*- coding: utf-8 -*-
"""Capa de APLICACION: caso de uso que orquesta la generacion del anexo.

Depende SOLO de los puertos (LectorExogena, EscritorAnexo) y del dominio.
No importa openpyxl ni tkinter. Las reglas y patrones de mapeo se
inyectan desde la capa de presentacion (composicion).
"""

import os
import re

from ..config.reglas_anexo import EXENTA_CESANTIAS, REGLA_CESANTIAS_FONDO
from ..config.settings import CARPETA
from ..domain.cesantias import (RUBRO_CESANTIAS_FONDO, cesantias_exentas,
                                nota_deduplicacion,
                                unificar_cesantias_fondo)
from ..domain.encabezado import componer_encabezado
from ..domain.mapeo import agrupar, mapear
from ..domain.reglas import (aplicar_subcontratacion, aplicar_venta_activos,
                             construir_reglas)
from .puertos import EscritorAnexo, LectorExogena, Resultado


def _rango(valor):
    """Cifra con separador de miles, para los mensajes del dominio."""
    return f"{valor:,.0f}"


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


def agregar_exenta_cesantias(por_regla):
    """Anade al renglon 36 la renta exenta de las cesantias al fondo.

    El mismo concepto 2276 que entra al renglon 32 tambien es renta exenta
    (numeral 3 del Art. 206 E.T.), pero `mapear` es "gana la primera regla" y
    ese concepto ya quedo asignado a REGLA_CESANTIAS_FONDO. Aqui se deriva la
    fila del renglon 36 a partir del MISMO total ya deduplicado, de modo que
    el gravado y la exenta nunca puedan discrepar.

    Las cesantias pagadas directamente NO aportan exenta: la exogena no las
    marca como tales y no trae el promedio salarial que el Art. 206 exige
    para el tope, asi que no se prorratea (ver domain.cesantias).

    Si el Rubro no esta en la exogena, no se crea la fila: una exenta en 0
    ensuciaria el renglon 36 sin aportar nada.
    """
    # Nombre EXACTO de la regla del renglon 32: la del renglon 36 empieza con
    # el mismo texto, asi que un match por contenido los confundiria.
    nombre_r32 = REGLA_CESANTIAS_FONDO["nombre"]

    exenta_total = 0.0
    grupos_exenta = []
    for regla, grupos in por_regla:
        if regla.nombre != nombre_r32:
            continue
        for tercero, valor in grupos:
            exento = cesantias_exentas(RUBRO_CESANTIAS_FONDO, valor)
            if exento:
                exenta_total += exento
                grupos_exenta.append((tercero, exento))
    if not grupos_exenta:
        return por_regla, 0.0
    return por_regla + [(construir_reglas([EXENTA_CESANTIAS])[0],
                         grupos_exenta)], exenta_total


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

    # Las cesantias consignadas llegan dos veces (empleador 2276 y fondo).
    # Se deja un solo registro ANTES de mapear, para que ni el renglon 32 ni
    # el 36 sumen el mismo dinero dos veces.
    conceptos, descartados = unificar_cesantias_fondo(informe.conceptos,
                                                      _rango)
    asignados, no_mapeados = mapear(conceptos, reglas, info_patterns)
    por_regla = agrupar(asignados)
    por_regla, exenta_cesantias = agregar_exenta_cesantias(por_regla)

    total_ret, n_ret = extraer_retenciones(por_regla)
    salida_final = escritor.escribir(salida, por_regla,
                                     total_ret, n_ret,
                                     encabezado=encabezado,
                                     actividad=actividad)

    notas = []
    nota_dedup = nota_deduplicacion(descartados, _rango)
    if nota_dedup:
        notas.append(nota_dedup)
    if exenta_cesantias:
        notas.append(
            f"R36 otras rentas exentas (Art. 206 num. 3 E.T.): "
            f"{_rango(exenta_cesantias)} de cesantias consignadas al fondo, "
            "exentas al 100% sin prorrateo.")

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
        notas=notas,
    )


__all__ = ["procesar_anexo", "construir_resumen", "extraer_retenciones",
           "agregar_exenta_cesantias", "construir_nombre_salida"]