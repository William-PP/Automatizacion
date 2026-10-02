# -*- coding: utf-8 -*-
"""Capa de DOMINIO: reglas de negocio de cesantias (Art. 206 numeral 3 E.T.).

Las cesantias consignadas al fondo se reportan DOS veces en la misma exogena:

  1. Por el EMPLEADOR, en el formato 2276, concepto 2276, con el detalle
     "Cesantias consignadas al fondo de cesantias (Concepto: 2276)".
  2. Por el FONDO DE CESANTIAS, con el detalle "Valor total de las cesantias
     abonadas en el periodo. (Formato del fondo de cesantias). Empleado".

Es el MISMO dinero visto desde dos reportadores. La propia DIAN lo advierte en
la columna de uso: "este valor puede ser reportado por el empleador y el fondo
de cesantias, el sistema toma un solo registro para evitar duplicidad".

Sumar los dos duplicaria el ingreso en el renglon 32 y la renta exenta en el
renglon 36. Este modulo conserva UN solo registro de cesantias consignadas.

Que se conserva: el del EMPLEADOR (concepto 2276), porque es el que la DIAN
asocia al 2276 y trae la nota de uso que senala el renglon 36. La fila del
fondo no se suma, pero se reporta para que se vea lo que se descarto y por que.
"""

from .reglas import codigo_concepto

# Rubros del 2276 que van al renglon 32 (ingresos brutos por rentas de
# trabajo). El orden de las tuplas es el orden en que se listan en el anexo.
RUBRO_SALARIOS = "salarios"
RUBRO_PRESTACIONES = "prestaciones"
RUBRO_CESANTIAS_PAGADAS = "cesantias_pagadas"
RUBRO_CESANTIAS_FONDO = "cesantias_fondo"

# Texto que ancla cada rubro dentro del detalle de la exogena. El ancla de
# texto es obligatoria: el codigo 2276 solo no alcanza, porque "Cesantias e
# intereses pagadas al empleado", "Cesantias consignadas al fondo", "Aportes a
# salud" y "Aportes a pensiones" comparten ese mismo codigo.
_ANCLAS = {
    RUBRO_SALARIOS: "pagos por salarios",
    RUBRO_PRESTACIONES: "pagos por prestaciones sociales",
    RUBRO_CESANTIAS_PAGADAS: "cesantias e intereses de cesantias pagadas "
                             "al empleado",
    RUBRO_CESANTIAS_FONDO: "cesantias consignadas al fondo de cesantias",
}

# El reporte del FONDO no trae "Concepto: 2276" (codigo_concepto devuelve ""),
# asi que se reconoce por su propio texto.
_ANCLA_FONDO = "formato del fondo de cesantias"

# Margen de deduplicacion: dos cifras se consideran el mismo valor si difieren
# menos que esto. Cubre el redondeo entre los dos reportes sin llegar a fundir
# importes que son realmente distintos.
TOLERANCIA_DEDUP = 1.0


def _normalizar(texto: str) -> str:
    """Minusculas y sin tildes, para comparar el texto de la exogena."""
    plano = (texto or "").lower()
    for con, sin in (("\u00e1", "a"), ("\u00e9", "e"), ("\u00ed", "i"),
                     ("\u00f3", "o"), ("\u00fa", "u"), ("\u00fc", "u"),
                     ("\u00f1", "n")):
        plano = plano.replace(con, sin)
    return plano.strip()


def es_rubro_2276(detalle: str, rubro: str) -> bool:
    """True si el detalle corresponde al rubro indicado del concepto 2276."""
    if codigo_concepto(detalle) != "2276":
        return False
    return _ANCLAS[rubro] in _normalizar(detalle)


def es_reporte_fondo(detalle: str) -> bool:
    """True si el detalle viene del reporte del FONDO de cesantias.

    A diferencia de los rubros del 2276, estas filas no traen codigo de
    concepto: son las del "Formato del fondo de cesantias".
    """
    return _ANCLA_FONDO in _normalizar(detalle)


def clasificar_rubro(detalle: str) -> str:
    """Devuelve el rubro 2276 del detalle, o cadena vacia si no es de estos."""
    for rubro in _ANCLAS:
        if es_rubro_2276(detalle, rubro):
            return rubro
    return ""


def unificar_cesantias_fondo(conceptos, rango):
    """Deja un solo registro de cesantias consignadas.

    `conceptos` : lista de Concepto de la exogena.
    `rango`     : callable(valor) -> str, describe una cifra como "237.900".

    Devuelve (conceptos_filtrados, descartados):
      - conceptos_filtrados : los conceptos SIN la fila del fondo que
                              duplica el aporte del empleador. Si no hay
                              duplicado, se devuelve la lista original intacta.
      - descartados          : [(concepto, motivo)] con lo que no se sumo,
                              para que el reporte lo muestre.
    """
    de_empleador = [c for c in conceptos
                    if es_rubro_2276(c.detalle, RUBRO_CESANTIAS_FONDO)]
    de_fondo = [c for c in conceptos if es_reporte_fondo(c.detalle)]

    # Sin contraparte del fondo (o sin contraparte del empleador) no hay nada
    # que deduplicar: no se toca la lista.
    if not de_empleador or not de_fondo:
        return list(conceptos), []

    total_empleador = sum(c.valor for c in de_empleador)
    a_quitar = set()
    descartados = []
    for c in de_fondo:
        if abs(c.valor - total_empleador) <= TOLERANCIA_DEDUP:
            a_quitar.add(id(c))
            descartados.append(
                (c, f"duplica el aporte del empleador "
                    f"({rango(total_empleador)})"))
        else:
            descartados.append(
                (c, f"el fondo reporta {rango(c.valor)} y el empleador "
                    f"{rango(total_empleador)}; se conserva el del "
                    "empleador"))
    if not a_quitar:
        return list(conceptos), descartados
    return [c for c in conceptos if id(c) not in a_quitar], descartados


def cesantias_exentas(rubro: str, total: float) -> float:
    """Parte del valor de cesantias que va al renglon 36 como renta exenta.

    La exogena reporta "Cesantias e intereses de cesantias pagadas al
    empleado" como un valor unico, SIN desglosar el auxilio de cesantias del
    interes sobre cesantias, y SIN el promedio salarial del trabajador que
    Art. 206 E.T. exige para el tope. Por eso NO se prorratea:

      - Cesantias CONSIGNADAS al fondo: el 100% del valor unificado es renta
        exenta (numeral 3 del Art. 206 E.T.) -> renglon 36.
      - Cesantias PAGADAS directamente al empleado: solo se exenta lo que la
        propia exogena marque como exento. Como la DIAN no lo marca, el valor
        va integro y gravado al renglon 32 y al renglon 36 no llega nada.

    Se deja el prorrateo explicito, no como parametro, para que no se aplique
    por accidente sin el dato del promedio salarial que lo sustenta.
    """
    return total if rubro == RUBRO_CESANTIAS_FONDO else 0.0


def nota_deduplicacion(descartados, rango) -> str:
    """Linea de reporte que explica que no se sumo y por que."""
    if not descartados:
        return ""
    detalle = "; ".join(f"{rango(c.valor)} de '{c.tercero}': {motivo}"
                        for c, motivo in descartados)
    return ("Cesantias del fondo de cesantias NO sumadas al renglon 32 "
            f"para no duplicar el aporte del empleador -> {detalle}")


__all__ = ["RUBRO_SALARIOS", "RUBRO_PRESTACIONES", "RUBRO_CESANTIAS_PAGADAS",
           "RUBRO_CESANTIAS_FONDO", "TOLERANCIA_DEDUP",
           "es_rubro_2276", "es_reporte_fondo", "clasificar_rubro",
           "unificar_cesantias_fondo", "cesantias_exentas",
           "nota_deduplicacion"]