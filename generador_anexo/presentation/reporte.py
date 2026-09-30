# -*- coding: utf-8 -*-
"""Capa de PRESENTACION: construccion del reporte de texto.

Toma el DTO Resultado del caso de uso y lo formatea como el reporte
historico del script (mismo formato que la version monolítica).
"""

from ..infrastructure.util.formato import num, render_pct


def construir_reporte(res) -> str:
    lineas = []
    if res.encabezado:
        lineas.append(res.encabezado)
        if res.actividad:
            lineas.append(f"Actividad economica {res.actividad}")
        lineas.append("=" * 78)
    lineas.append("TOPES DE LA EXOGENA")
    for t in res.topes:
        lineas.append(f"  {t.nombre:<22} {num(t.valor):>16}")

    lineas.append("=" * 78)
    lineas.append("MAPEO CONCEPTO -> ANEXO")
    for regla, grupos in res.por_regla:
        if regla.agregar in ("tercero", "detalle"):
            lineas.append(f"  -> {regla.nombre}")
            for meta, valor in grupos:
                if regla.agregar == "detalle":
                    plantilla = regla.plantilla_detalle
                    if plantilla:
                        lineas.append(
                            "       " + plantilla.format(
                                matricula=meta.get('matricula', ""),
                                placa=meta.get('placa', ""),
                                valor=f"${int(round(valor)):,}",
                                pct=render_pct(meta.get('pct', 100))))
                    else:
                        lineas.append(
                            f"       matricula {meta['matricula']:<12} "
                            f"{num(valor):>16} ({render_pct(meta['pct'])}%)  "
                            f"[{meta['tercero']}]")
                else:
                    lineas.append(f"       {num(valor):>16}  {meta}")
        else:
            lineas.append(f"  -> {regla.nombre:<58} {num(grupos[0][1]):>16}")

    lineas.append("=" * 78)
    lineas.append("SIN CASILLA EN EL ANEXO (referencia / revisar)")
    for c, es_info in res.no_mapeados:
        tag = "informativo" if es_info else "SIN MAPEO"
        lineas.append(f"  [{tag:<11}] {num(c.valor):>16}  {c.detalle[:95]}")

    lineas.append("=" * 78)
    lineas.append("RESUMEN POR SECCION DEL ANEXO")
    for nombre, total in res.resumen:
        lineas.append(f"  {total:>16,.0f}  {nombre}")

    if res.salida != res.salida_solicitada:
        lineas.append("")
        lineas.append("OJO: el archivo con la fecha de hoy estaba abierto en Excel,")
        lineas.append("      asi que se creo este otro para no sobrescribirlo.")

    lineas.append("=" * 78)
    lineas.append(f"Archivo generado: {res.salida}")
    return "\n".join(lineas)


__all__ = ["construir_reporte"]