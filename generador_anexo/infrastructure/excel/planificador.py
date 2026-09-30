# -*- coding: utf-8 -*-
"""Capa de INFRAESTRUCTURA (excel): donde escribe cada regla y que filas faltan.

El modelo oficial del anexo NO tiene un numero fijo de filas por concepto: son
bloques. Cada bloque abre con una fila de TITULO (tiene etiqueta en la columna
A) y sigue con N filas de DETALLE (columna A vacia) donde van las descripciones.

Una regla de tipo "tercero"/"detalle" puede declarar `bloque` = fila del titulo
que la alberga. Con eso la regla deja de tener fila fija: el planificador le
reserva sus filas DENTRO del bloque, en el orden de las reglas, e inserta
automaticamente las filas que falten justo ANTES del siguiente titulo. Asi un
bloque con 3 filas de detalle puede recibir 6 conceptos sin que nadie tenga que
duplicar filas a mano en el modelo.

Las reglas sin `bloque` conservan el comportamiento anterior: arrancan en
`fila` y, si sus grupos no caben en `max_filas`, insertan el excedente en
`fila + max_filas`.
"""

from .formulas import corrimiento


def es_fila_titulo(ws, fila: int) -> bool:
    """True si la fila es un TITULO de bloque (etiqueta en la columna A).

    Las filas de detalle vienen con la columna A vacia en la plantilla; los
    titulos traen su texto. Es la misma senal que usa totales.recalcular_totales
    para localizar secciones por etiqueta.
    """
    v = ws.cell(fila, 1).value
    return isinstance(v, str) and v.strip() != ""


def siguiente_titulo(ws, titulo: int) -> int:
    """Fila del proximo titulo despues de `titulo` (o el final de la hoja)."""
    for r in range(titulo + 1, ws.max_row + 1):
        if es_fila_titulo(ws, r):
            return r
    return ws.max_row + 1


def _es_bloque(regla) -> bool:
    return regla.bloque and regla.agregar in ("tercero", "detalle")


def plan_filas(ws, por_regla: list, inserts_base: list):
    """Devuelve (inserts, inicio) con la fila FINAL donde escribe cada regla.

    por_regla    : lista de (regla, grupos) ya en orden de escritura.
    inserts_base : inserciones obligatorias (p.ej. la fila del encabezado).
    inicio       : dict id(regla) -> fila final (ya desplazada por inserts).
    """
    # --- 1) cuantas filas de detalle pide cada bloque en total --------------
    pedidos = {}   # bloque -> [fila del siguiente titulo, grupos totales]
    for regla, grupos in por_regla:
        if not _es_bloque(regla):
            continue
        b = regla.bloque
        if b not in pedidos:
            pedidos[b] = [siguiente_titulo(ws, b), 0]
        pedidos[b][1] += len(grupos)

    inserts = list(inserts_base)

    # --- 2) el bloque recibe las filas que le sobran, antes del proximo titulo
    for titulo, (sig, total) in pedidos.items():
        existentes = sig - (titulo + 1)      # filas de detalle del modelo
        if total > existentes:
            inserts.append((sig, total - existentes))

    # --- 3) reglas con fila fija: se comportan como siempre ----------------
    for regla, grupos in por_regla:
        if _es_bloque(regla):
            continue
        if regla.agregar in ("tercero", "detalle"):
            extra = len(grupos) - regla.max_filas
            if extra > 0:
                inserts.append((regla.fila + regla.max_filas, extra))

    inserts.sort(reverse=True)

    # --- 4) asignacion final: dentro del bloque, en cascada y sin huecos ----
    # Las filas se reparten por ORDEN DE REGLA (columna `fila`) y no por el
    # orden en que los conceptos aparecen en la exogena: asi dos corridas con
    # los mismos datos producen siempre el mismo anexo, y `fila` sigue siendo
    # la clave estable de "que va antes que que".
    inicio = {}
    for regla, _grupos in por_regla:
        if not _es_bloque(regla) and regla.agregar in ("tercero", "detalle"):
            inicio[id(regla)] = regla.fila + corrimiento(regla.fila, inserts)

    cursor = {}
    orden = {id(regla): i for i, (regla, _) in enumerate(por_regla)}
    for regla, grupos in sorted(
            ((r, g) for r, g in por_regla if _es_bloque(r)),
            key=lambda rg: (rg[0].fila, orden[id(rg[0])])):
        b = regla.bloque
        if b not in cursor:
            cursor[b] = b + 1 + corrimiento(b + 1, inserts)
        inicio[id(regla)] = cursor[b]
        cursor[b] += len(grupos)

    return inserts, inicio


__all__ = ["es_fila_titulo", "siguiente_titulo", "plan_filas"]
