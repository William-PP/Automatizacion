# -*- coding: utf-8 -*-
"""Capa de DOMINIO: composicion del encabezado del consultante.

Transforma los datos extraidos de la exogena (Consultante) en la linea
que se escribe en la fila 2 del anexo, con el formato histórico:

    RAMIRO GONZALO RUEDA PANIAGUA CC 71268670
"""


def _normalizar_tipo(tipo):
    """'C. C.' / 'c.c' / 'cc' -> 'CC'; 'NIT'/'Nit' -> 'NIT'. Agrupa letras."""
    limpio = "".join(c for c in (tipo or "") if c.isalnum()).upper()
    equivalencias = {"NIT": "NIT"}
    return equivalencias.get(limpio, limpio or "")


def componer_encabezado(consultante) -> str:
    """Devuelve la linea de identificacion para la fila 2 del anexo."""
    tipo = _normalizar_tipo(consultante.tipo_documento)
    partes = [consultante.nombres]
    if tipo:
        partes.append(tipo)
    if consultante.identificacion:
        partes.append(consultante.identificacion)
    return " ".join(partes)


__all__ = ["componer_encabezado"]