# -*- coding: utf-8 -*-
"""Capa de INFRAESTRUCTURA (excel): totales y ajustes de liquidacion.

Reescribe las formulas de totales que dependen de filas insertadas y
aplica los ajustes de la seccion de retenciones / liquidacion.
"""

from ..util.formato import fmt_valor


def recalcular_totales(ws):
    def buscar(texto):
        for row in ws.iter_rows(min_col=1, max_col=1):
            v = row[0].value
            if isinstance(v, str) and v.strip() == texto:
                return row[0].row
        return None

    def buscar_despues(texto, base):
        for r in range(base + 1, ws.max_row + 1):
            v = ws.cell(r, 1).value
            if isinstance(v, str) and v.strip() == texto:
                return r
        return None

    def fin_detalle(base, cierres):
        """Ultima fila del bloque de detalle que sigue a `base`.

        Las filas de detalle las escribe el generador y llevan su propia
        descripcion en la columna A, asi que no se distinguen de un titulo
        por tener o no texto. El corte se hace por los titulos CONOCIDOS que
        cierran el bloque, que son fijos de la plantilla.
        """
        for r in range(base + 1, ws.max_row + 1):
            v = ws.cell(r, 1).value
            if isinstance(v, str) and v.strip() in cierres:
                return r - 1
        return ws.max_row

    pt = buscar("TOTAL PATRIMONIO BRUTO")
    pat = buscar("PATRIMONIO")      # inicio de la seccion de patrimonio
    if pt and pat:
        ws.cell(pt, 3).value = f"=SUM(C{pat + 1}:C{pt - 1})"
    rv1 = buscar("Revaluación Inmuebles")
    rv2 = buscar("Revaluación Vehículos")
    pj = buscar("TOTAL PATRIMONIO AJUSTADO")
    if pt and rv1 and rv2 and pj:
        ws.cell(pj, 3).value = f"=C{pt}+C{rv1}+C{rv2}"
    deu = buscar("DEUDAS")
    deu_tot = buscar("TOTAL DEUDAS")
    if deu and deu_tot:
        ws.cell(deu_tot, 3).value = f"=SUM(C{deu + 1}:C{deu_tot - 1})"
    pl = buscar("TOTAL PATRIMONIO LÍQUIDO")
    if pj and deu_tot and pl:
        ws.cell(pl, 3).value = f"=C{pj}-C{deu_tot}"

    hon = buscar("HONORARIOS")
    hon_tot = hon and buscar_despues("TOTAL HONORARIOS", hon)
    if hon and hon_tot:
        ws.cell(hon_tot, 3).value = f"=SUM(C{hon + 1}:C{hon_tot - 1})"

    rend = buscar("RENDIMIENTOS FINANCIEROS")
    cap_tot = rend and buscar_despues("TOTAL INGRESOS BRUTOS", rend)
    if rend and cap_tot:
        ws.cell(cap_tot, 3).value = f"=SUM(C{rend + 1}:C{cap_tot - 1})"

    nolab = buscar("RENTAS NO LABORALES")
    nolab_tot = nolab and buscar_despues("TOTAL INGRESOS BRUTOS", nolab)
    if nolab and nolab_tot:
        ws.cell(nolab_tot, 3).value = f"=SUM(C{nolab + 1}:C{nolab_tot - 1})"

    compras = nolab_tot and buscar_despues(
        "COSTOS DERIVADOS DE LA ACTIVIDAD ECONÓMICA (COMPRAS)", nolab_tot)
    renta_liq = compras and buscar_despues("RENTA LIQUIDA", compras)
    if nolab_tot and compras and renta_liq:
        ws.cell(renta_liq, 3).value = f"=C{nolab_tot}+C{compras}"

    # --- RENTAS DE TRABAJO -------------------------------------------------
    # "INGRESOS BRUTOS POR RENTAS DE TRABAJO (SALARIOS)" abre el bloque de
    # detalle (fila 41 en la plantilla) y lo cierra "TOTAL SALARIOS". El
    # detalle son varias filas (salarios, prestaciones, cesantias...), asi que
    # el total se arma con SUM en vez de quedar la referencia a una sola fila.
    trab = buscar("INGRESOS BRUTOS POR RENTAS DE TRABAJO (SALARIOS)")
    trab_tot = trab and buscar_despues("TOTAL SALARIOS", trab)
    if trab and trab_tot:
        ws.cell(trab_tot, 3).value = f"=SUM(C{trab + 1}:C{trab_tot - 1})"

    # "RENTA LIQUIDA" de las laborales. En la plantilla su formula era
    # "=C42", apuntando a la UNICA fila de detalle del bloque; con varias
    # filas de detalle (salarios, prestaciones, cesantias) esa referencia
    # solo sumaria la primera. Se reapunta al TOTAL SALARIOS, que es lo que
    # la plantilla queria expresar: el total del bloque de rentas de
    # trabajo. Se toma la primera "RENTA LIQUIDA" despues del bloque, que es
    # la de las laborales (las demas secciones traen otros titulos).
    rl_trab = trab_tot and buscar_despues("RENTA LIQUIDA", trab_tot)
    if trab_tot and rl_trab:
        ws.cell(rl_trab, 3).value = f"=C{trab_tot}"

    # "OTRAS RENTAS EXENTAS" (laborales): su celda viene en 0 en la plantilla
    # y hay que igualarla al detalle que se escribio (cesantias consignadas
    # al fondo exentas, Art. 206 num. 3 E.T.). Se toma la PRIMERA
    # ocurrencia, que es la de las laborales; el bloque de honorarios tiene su
    # propio par de titulos mas abajo. El rango se corta en "INTERESES DE
    # VIVIENDA": las filas que siguen ya traen su propia celda y meterlas
    # dentro de la exenta las sumaria de mas.
    exentas = buscar("OTRAS RENTAS EXENTAS")
    if exentas:
        fin = fin_detalle(exentas, ("INTERESES DE VIVIENDA",))
        if fin > exentas:
            ws.cell(exentas, 3).value = f"=SUM(C{exentas + 1}:C{fin})"


def ajustes_retenciones(ws, total_ret, n_ret):
    """Detalle de retenciones: total en la cabecera y valor en la liquidacion."""
    liq = None
    det = None
    for r in range(1, ws.max_row + 1):
        v = ws.cell(r, 1).value
        if isinstance(v, str) and v.strip() == "LIQUIDACIÓN / DATOS DE CIERRE":
            liq = r
        if isinstance(v, str) and v.strip() == "RETENCIONES PRACTICADAS":
            if det is None:
                det = r
    if det is not None and n_ret > 0:
        fin = det + n_ret
        ws.cell(det, 3).value = f"=SUM(B{det + 1}:B{fin})"
    if liq is not None and total_ret:
        for r in range(liq + 1, ws.max_row + 1):
            v = ws.cell(r, 1).value
            if isinstance(v, str) and v.strip() == "RETENCIONES PRACTICADAS":
                ws.cell(r, 2).value = fmt_valor(total_ret)
                break


__all__ = ["recalcular_totales", "ajustes_retenciones"]