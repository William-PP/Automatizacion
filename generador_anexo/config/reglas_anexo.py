# -*- coding: utf-8 -*-
"""Definiciones de las reglas de mapeo concepto -> anexo.

SON SOLO DATOS: no contienen logica. Se convierten en objetos Regla
(domain.reglas) al arrancar. Para anadir/ajustar una regla, edite aqui.

Cada dict tiene las claves que documenta domain.reglas.Regla.
Si los conceptos de la exogena cambian, es lo unico que debe tocar.

------------------------------------------------------------------------------
NOTA SOBRE LOS CODIGOS DE CONCEPTO (importante)
------------------------------------------------------------------------------
Existe una "cedula general" (tabla de referencia DIAN) que clasifica los
ingresos por CONCEPTO, pero NO comparte el espacio de codigos con lo que
reporta la Informacion Exogena. Ejemplos verificados en los archivos reales:

  codigo  cedula general          exogena (texto real)          destino real
  2204    Prestamos bancarios     Activos Impuestos gravamenes  Patrimonio
  1315    Clientes                Cuentas por pagar de clientes Deudas (R30)
  5016    Otros costos            Otros ingresos                R74 (renta no lab.)
  5002    Honorarios              Honorarios                    R43
  5004    Servicios               Servicios                     R43

Por eso `match_codigo` usa SIEMPRE el codigo que trae la exogena, nunca el
de la cedula general. Y como un codigo puede traer varios conceptos (4070 =
"Retencion distribuida al tercero" = R132  vs  "Ingreso distribuido al
tercero" = R74), el codigo NO reemplaza al texto: se combinan (codigo Y
texto) para no ambiguar. Ver domain.reglas.Regla.coincide.
"""

REGLA_AVALUO = dict(
    nombre="Avaluo catastral -> Activos fijos (por matricula)",
    match_c="avalúo catastral", match_codigo="1476",
    fila=15, agregar="detalle", max_filas=4,
    formula_c="=B{row}*{factor}", decimales=True,
    plantilla_detalle=("Avaluo catastral correspondiente a matricula "
                       "{matricula} por un valor total de {valor} por un "
                       "porcentaje de participacion del {pct}%"))

REGLA_AVALUO_VEHICULAR = dict(
    nombre="Avaluo vehicular -> Vehiculos (por placa)",
    match_c="avalúo vehículo", match_codigo="1480",
    fila=20, agregar="detalle", max_filas=1,
    formula_c="=B{row}*{factor}",
    plantilla_detalle="Avaluo vehiculo Placa: {placa}")

REGLA_CUENTAS_POR_COBRAR = dict(
    nombre="Activos impuestos gravamenes y tasas -> Cuentas por cobrar",
    match_c="Activos Impuestos gravámenes y tasas", match_codigo="2204",
    fila=23, agregar="tercero", max_filas=3)

REGLA_BANCOS = dict(
    nombre="Saldos bancarios positivos -> Efectivo/Bancos (patrimonio)",
    match_c="Saldo cuentas bancarias", fila=7, agregar="tercero", max_filas=3)

REGLA_DEUDAS = dict(
    nombre="Cuentas por pagar clientes -> Deudas",
    match_c="Cuentas por pagar de clientes", match_codigo="1315",
    fila=33, agregar="tercero", max_filas=2)

REGLA_INGRESOS_TRABAJO = dict(
    nombre="Salarios/prestaciones/otros pagos -> Ingresos trabajo (R32)",
    match_e="R32", match_codigo="2276", fila=41, agregar="total")

# --- Salarios, prestaciones y cesantias (concepto 2276) --------------------
# Los cuatro rubros que pide la especificacion van al renglon 32, cada uno en
# SU PROPIA fila de detalle para que se vea el desglose y no una sola suma.
# Bloque 40 = "INGRESOS BRUTOS POR RENTAS DE TRABAJO (SALARIOS)"; su unica
# fila de detalle en el modelo es la 41, asi que el planificador inserta las
# que falten antes de "TOTAL SALARIOS" (fila 42).
#
# El match es codigo 2276 + texto del detalle: el codigo solo no alcanza,
# porque salud, pensiones, cesantias pagadas y cesantias consignadas
# comparten el 2276. Los anclas de texto son las de domain.cesantias.
# `fila` fija el ORDEN dentro del bloque (el planificador ordena por fila).
REGLA_SALARIOS = dict(
    nombre="Pagos por salarios (R32) -> Salarios",
    match_codigo="2276", match_c="Pagos por salarios",
    fila=41, bloque=40, agregar="tercero",
    plantilla_tercero="{tercero} (Pago por salarios)")

REGLA_PRESTACIONES_SOCIALES = dict(
    nombre="Pagos por prestaciones sociales (R32) -> Prestaciones sociales",
    match_codigo="2276", match_c="Pagos por prestaciones sociales",
    fila=42, bloque=40, agregar="tercero",
    plantilla_tercero="{tercero} (Prestaciones Sociales)")

REGLA_CESANTIAS_PAGADAS = dict(
    nombre="Cesantias e intereses pagadas al empleado (R32) -> Cesantias",
    match_codigo="2276",
    match_c="Cesantías e intereses de cesantías pagadas al empleado",
    fila=43, bloque=40, agregar="tercero",
    plantilla_tercero="{tercero} (Cesantias e intereses)")

# Cesantias consignadas al fondo: gravadas en R32 y 100% exentas en R36
# (numeral 3 del Art. 206 E.T.). Las dos reglas anclan en el mismo texto;
# domain.cesantias deduplica contra el reporte del fondo antes de mapear.
REGLA_CESANTIAS_FONDO = dict(
    nombre="Cesantias consignadas al fondo (R32) -> Cesantias al fondo",
    match_codigo="2276", match_c="Cesantías consignadas al fondo de cesantías",
    fila=44, bloque=40, agregar="tercero",
    plantilla_tercero="{tercero} (Cesantias consignadas al fondo)")

# Renglon 36 "OTRAS RENTAS EXENTAS" (laborales). Bloque 51, fila de detalle
# 52. Se escribe con espejo=False para RESPETAR la formula del modelo
# "=-(B52)": la renta exenta va en negativo y la resta de la renta liquida
# (C57 = C47 + C52). Poner C = BPOSITIVO sumaria la exenta en vez de
    # restarla.
REGLA_CESANTIAS_FONDO_EXENTA = dict(
    nombre="Cesantias consignadas al fondo (R36) -> Otras rentas exentas",
    match_codigo="2276", match_c="Cesantías consignadas al fondo de cesantías",
    fila=52, bloque=51, agregar="tercero", espejo=False, formula_c=None,
    plantilla_tercero="{tercero} (Cesantias consignadas al fondo)")

REGLA_SALUD_TRABAJADOR = dict(
    nombre="Aportes salud trabajador (R33) -> Aportes salud trabajo",
    match_c="salud", fila=45, agregar="total")

REGLA_PENSION_TRABAJADOR = dict(
    nombre="Aporte pension trabajador (R33) -> Aportes pension trabajo",
    match_c="fondos pensiones", fila=46, agregar="total")

REGLA_PENSION_INDEPENDIENTE = dict(
    nombre="Aporte pension independiente (R44) -> Aportes pension honorarios",
    match_c="Aporte pensión obligatoria efectuado", match_codigo="2277",
    fila=75, agregar="total")

REGLA_HONORARIOS = dict(
    nombre="Honorarios (R43) -> Honorarios",
    match_e="R43", match_codigo="5002", fila=62, agregar="tercero",
    max_filas=1)

REGLA_SERVICIOS = dict(
    nombre="Servicios (R43) -> Servicios",
    match_e="R43", match_codigo="5004", fila=66, agregar="tercero",
    max_filas=1)

# Comisiones (5003) no traen codigo de uso propio en la exogena; se ancla al
# texto + R43 como los otros ingresos por servicios independientes. La fila 70
# es la de detalle del bloque COMISIONES POR VENTAS (69) del modelo, la misma
# que usa TOTAL COMISIONES (=C70) para totalizar.
REGLA_COMISIONES = dict(
    nombre="Comisiones (R43) -> Comisiones",
    match_e="R43", match_codigo="5003", fila=70, agregar="tercero",
    max_filas=1)

# RENDIMIENTOS y OTROS_INGRESOS se dejan SOLO por match_e (R58 / R74): son
# catch-all amplios y la cedula general define mas de un codigo de rendimientos
# (8036, 4003) o ingresos (4001, 4002). Anclarlos a un unico codigo los
# dejaria fuera.
REGLA_RENDIMIENTOS = dict(
    nombre="Intereses y rendimientos financieros (R58) -> Rentas de capital",
    match_e="R58", fila=93, agregar="tercero", max_filas=3)

REGLA_DOCUMENTOS_SOPORTE = dict(
    nombre="Ingresos documentos soporte por no obligados a facturar -> Renta no laboral",
    match_c="Documentos soporte", fila=114, bloque=113, agregar="tercero",
    max_filas=1,
    plantilla_tercero="{tercero} (Documentos soporte no obligados a facturar)")

REGLA_OTROS_INGRESOS = dict(
    nombre="Otros ingresos / ingresos distribuidos (R74) -> Rentas no laborales",
    match_e="R74", fila=115, bloque=113, agregar="tercero", max_filas=1)

# --- Venta de activos fijos -------------------------------------------------
# El concepto llega como "Base retencion venta de activos fijos ante
# autoridades de transito". Por DEFECTO va a RENTAS NO LABORALES (fila 116,
# tercera linea de "OTROS INGRESOS DERIVADOS DE LA ACTIVIDAD ECONOMICA"),
# porque solo si se sabe que el activo se poseyo MAS DE 2 anos corresponde
# ganancia ocasional. Con el flag venta_activos_mas_2_anos=True se usa la
# variante MAS2 (fila 173, VENTA DE ACTIVOS CON MAS DE 2 ANOS).
REGLA_VENTA_ACTIVOS_FIJOS = dict(
    nombre="Venta de activos fijos (<2 anos) -> Renta no laboral",
    match_c="venta de activos fijos", match_codigo="5046",
    fila=116, bloque=113, agregar="tercero", max_filas=1,
    plantilla_tercero="{tercero} (Venta activos fijos)")

REGLA_VENTA_ACTIVOS_FIJOS_MAS2 = dict(
    nombre="Venta de activos fijos (mas de 2 anos) -> Ganancia ocasional",
    match_c="venta de activos fijos", match_codigo="5046",
    fila=173, agregar="total", max_filas=1)

# --- Subcontratacion (Seccion B de la cedula general) ----------------------
# Honorarios, comisiones y servicios (5002/5003/5004) son renta de TRABAJO
# solo si el contribuyente NO subcontrato 2 o mas personas por al menos 90
# dias. La exogena no informa ese dato, asi que se pregunta en la GUI: con
# subcontrato_2_mas=True estas reglas sustituyen a las de arriba y llevan el
# valor a RENTAS NO LABORALES. Va al bloque 113 (OTROS INGRESOS DERIVADOS DE
# LA ACTIVIDAD ECONOMICA) y el planificador inserta las filas que falten, sin
# tocar el modelo a mano.
REGLA_HONORARIOS_SUB = dict(
    nombre="Honorarios (R43) -> Renta no laboral (subcontrato 2+ personas)",
    match_e="R43", match_codigo="5002", fila=117, bloque=113,
    agregar="tercero", max_filas=1,
    plantilla_tercero="{tercero} (Honorarios - subcontrato)")

REGLA_COMISIONES_SUB = dict(
    nombre="Comisiones (R43) -> Renta no laboral (subcontrato 2+ personas)",
    match_e="R43", match_codigo="5003", fila=118, bloque=113,
    agregar="tercero", max_filas=1,
    plantilla_tercero="{tercero} (Comisiones - subcontrato)")

REGLA_SERVICIOS_SUB = dict(
    nombre="Servicios (R43) -> Renta no laboral (subcontrato 2+ personas)",
    match_e="R43", match_codigo="5004", fila=119, bloque=113,
    agregar="tercero", max_filas=1,
    plantilla_tercero="{tercero} (Servicios - subcontrato)")

REGLA_COMPRAS = dict(
    nombre="Compras factura electronica (Tope 5) -> Costos renta no laboral",
    match_c="Monto total de facturación electrónica susceptible de beneficio",
    fila=130, agregar="total", formula_c="=-(B{row})")

REGLA_NOTA_AJUSTE = dict(
    nombre="Suma facturas tras ajustes por notas -> NOTA ajuste",
    match_c="Suma valor total facturas tras ajustes por notas",
    fila=131, agregar="total", formula_c=None)

REGLA_RETENCIONES = dict(
    nombre="Retenciones distribuidos (R132) -> Retenciones practicadas",
    match_e="R132", fila=181, agregar="tercero", max_filas=1, espejo=False)

REGLA_SALDO_FAVOR = dict(
    nombre="Saldo a favor anio anterior (R131)",
    match_c="Total saldo a favor", fila=189, agregar="total", formula_c=None)

# Orden importa: se evaluan en el orden de esta lista; gana la primera
# regla que coincida con el concepto.
#
# REGLA_INGRESOS_TRABAJO va DESPUES de los cuatro rubros del 2276 porque es
# un catch-all (match_e="R32" + codigo 2276): si fuera primero se llevaria
# tambien los salarios, prestaciones y cesantias y no se verian desglosados.
RULES = [
    REGLA_AVALUO,
    REGLA_AVALUO_VEHICULAR,
    REGLA_CUENTAS_POR_COBRAR,
    REGLA_BANCOS,
    REGLA_DEUDAS,
    REGLA_SALARIOS,
    REGLA_PRESTACIONES_SOCIALES,
    REGLA_CESANTIAS_PAGADAS,
    REGLA_CESANTIAS_FONDO,
    REGLA_INGRESOS_TRABAJO,
    REGLA_SALUD_TRABAJADOR,
    REGLA_PENSION_TRABAJADOR,
    REGLA_PENSION_INDEPENDIENTE,
    REGLA_HONORARIOS,
    REGLA_SERVICIOS,
    REGLA_COMISIONES,
    REGLA_RENDIMIENTOS,
    REGLA_DOCUMENTOS_SOPORTE,
    REGLA_OTROS_INGRESOS,
    REGLA_VENTA_ACTIVOS_FIJOS,
    REGLA_COMPRAS,
    REGLA_NOTA_AJUSTE,
    REGLA_RETENCIONES,
    REGLA_SALDO_FAVOR,
]

# La exenta de cesantias (renglon 36) NO va en RULES: el mismo concepto 2276
# ya lo captura REGLA_CESANTIAS_FONDO para el renglon 32 y el mapeo es
# "gana la primera". El caso de uso deriva la fila exenta desde el total ya
# deduplicado (ver domain.cesantias y application.caso_uso).
EXENTA_CESANTIAS = REGLA_CESANTIAS_FONDO_EXENTA

# Conceptos que NO tienen casilla en el anexo: solo referencia.
INFO_PATTERNS = [
    "Total patrimonio bruto declarado en el año anterior",
    "Valor total de los movimientos en cuentas",
    "Total consumos o gastos con tarjeta",
    # El 2276 lo reporta como apoyo del calculo del tope del Art. 206 E.T.
    # No es un ingreso: se muestra como referencia y no se suma a ningun
    # renglon (no se prorratea cesantias).
    "Valor ingreso laboral promedio",
]

__all__ = ["RULES", "INFO_PATTERNS", "EXENTA_CESANTIAS",
           "REGLA_SALARIOS", "REGLA_PRESTACIONES_SOCIALES",
           "REGLA_CESANTIAS_PAGADAS", "REGLA_CESANTIAS_FONDO",
           "REGLA_VENTA_ACTIVOS_FIJOS_MAS2"]