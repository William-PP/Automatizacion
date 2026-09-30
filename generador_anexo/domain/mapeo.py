# -*- coding: utf-8 -*-
"""Capa de DOMINIO: reglas de negocio de mapeo.

Convierte los conceptos leidos (capa de datos) en grupos de valor a
escribir en el anexo, aplicando las reglas tipificadas (Regla).
"""

from collections import defaultdict
import re

from .entidades import Concepto
from .reglas import Regla


def mapear(conceptos, reglas, info_patterns):
    """Clasifica cada concepto en una regla del anexo.

    Devuelve (asignados, no_mapeados) donde:
      - asignados:   [(Concepto, Regla)] con los que tienen casilla.
      - no_mapeados: [(Concepto, es_informativo)] sin casilla en el anexo.
    """
    asignados = []
    no_mapeados = []
    for c in conceptos:
        for regla in reglas:
            if regla.coincide(c):
                asignados.append((c, regla))
                break
        else:
            es_info = any(p in c.detalle for p in info_patterns)
            no_mapeados.append((c, es_info))
    return asignados, no_mapeados


def parse_avaloo(info):
    """Extrae matricula, placa y porcentaje de participacion de un avaluo."""
    matricula = ""
    m = re.search(r"Matricula:\s*([^|\n]+)", info or "")
    if m:
        matricula = m.group(1).strip()
    placa = ""
    p = re.search(r"Placa:\s*([^|\n]+)", info or "")
    if p:
        placa = p.group(1).strip()
    pct = 100.0
    q = re.search(r"Participaci[oó]n:\s*([\d.,]+)", info or "")
    if q:
        try:
            pct = float(q.group(1).replace(",", "."))
        except ValueError:
            pct = 100.0
    return matricula, pct, placa


def agrupar(asignados):
    """Agrupa los conceptos asignados por regla y agrega sus valores.

    Devuelve una lista de (Regla, grupos):
      - agregar="total"   -> grupos = [(None, suma_total)]
      - agregar="tercero" -> grupos = [(nombre_tercero, valor)] orden segun
                             aparicion en la exogena.
      - agregar="detalle" -> grupos = [(meta, valor)] donde meta = dict
                             {tercero, matricula, pct} (ej. avaluos).
    """
    por_regla = defaultdict(list)
    for c, regla in asignados:
        por_regla[id(regla)].append((c, regla))
    resultado = []
    for lista in por_regla.values():
        regla = lista[0][1]
        if regla.agregar == "total":
            total = sum(c.valor for c, _ in lista)
            resultado.append((regla, [(None, total)]))
        elif regla.agregar == "detalle":
            seen = {}
            for c, _ in lista:
                matricula, pct, placa = parse_avaloo(c.info)
                key = (matricula, pct, placa)
                if key in seen:
                    seen[key][0] += c.valor
                else:
                    seen[key] = [c.valor, c.tercero]
            grupos = []
            for (matricula, pct, placa), (valor, tercero) in seen.items():
                grupos.append(
                    (dict(tercero=tercero, matricula=matricula, pct=pct,
                          placa=placa), valor))
            resultado.append((regla, grupos))
        else:
            terceros = defaultdict(float)
            for c, _ in lista:
                if not getattr(c, "tercero", "") or c.tercero == "(sin nombre)":
                    continue
                if c.tercero not in terceros:
                    terceros[c.tercero] = c.valor
                else:
                    terceros[c.tercero] += c.valor
            grupos = list(terceros.items())
            resultado.append((regla, grupos))
    return resultado


__all__ = ["mapear", "parse_avaloo", "agrupar"]