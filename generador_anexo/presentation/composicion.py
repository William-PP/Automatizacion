# -*- coding: utf-8 -*-
"""Capa de PRESENTACION: composicion de dependencias.

Aqui se ensamblan las dependencias concretas (adaptadores de
infraestructura) y se expone la funcion `procesar` con la misma firma
que la API historica del paquete menos el modelo (ya no se usa):
    reporte, salida, resumen = procesar(exo_file, salida)

Tambien expone `leer_encabezado` y `leer_nombre_salida` para que la GUI
pueda pre-llenar datos al elegir un archivo, y `leer_preliminares`, que
devuelve ambos con una sola lectura del libro.
"""

from ..application.caso_uso import (construir_nombre_salida, procesar_anexo)
from ..domain.encabezado import componer_encabezado
from ..infrastructure.excel.anexo_escritor import EscritorAnexoExcel
from ..infrastructure.excel.lector import LectorExogenaExcel
from .reporte import construir_reporte


def procesar(exo_file, salida, actividad="", encabezado="",
              venta_activos_mas_2_anos=False, subcontrato_2_mas=False):
    """Genera el anexo y devuelve (reporte, ruta_final, resumen)."""
    resultado = procesar_anexo(
        LectorExogenaExcel(),
        EscritorAnexoExcel(),
        exo_file,
        salida,
        actividad=actividad,
        encabezado=encabezado,
         venta_activos_mas_2_anos=venta_activos_mas_2_anos,
         subcontrato_2_mas=subcontrato_2_mas,
    )
    return construir_reporte(resultado), resultado.salida, resultado.resumen


def leer_preliminares(exo_file):
    """Devuelve (linea_identificacion, nombre_sugerido) con una sola lectura
    del libro, para que la GUI no abra el .xlsx dos veces por cada exogena
    elegida. Ambas salidas son cadena vacia si el archivo no trae consultante."""
    informe = LectorExogenaExcel().leer(exo_file)
    if not informe.consultante:
        return "", ""
    return (componer_encabezado(informe.consultante),
            construir_nombre_salida(informe.consultante))


def leer_encabezado(exo_file):
    """Devuelve la linea de identificacion del consultante para pre-llenar
    la GUI (o cadena vacia si el archivo no la trae)."""
    return leer_preliminares(exo_file)[0]


def leer_nombre_salida(exo_file):
    """Devuelve el nombre de archivo sugerido desde el consultante
    (Anexo_Declaracion_de_renta_<Nombre>).xlsx, o cadena vacia si el
    archivo no trae consultante (para preguntarlo manualmente en la GUI)."""
    return leer_preliminares(exo_file)[1]


__all__ = ["procesar", "leer_encabezado", "leer_nombre_salida",
           "leer_preliminares"]