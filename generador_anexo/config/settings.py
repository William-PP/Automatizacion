# -*- coding: utf-8 -*-
"""Capa CONFIG: rutas y definiciones de reglas de mapeo.

Solo datos de configuracion; ninguna logica de negocio.
"""

import os

# Carpeta raiz del proyecto (padre del paquete): donde viven los .xlsx.
CARPETA = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

# Nombre de la hoja de la exogena y del modelo (contrato con el archivo).
HOJA_EXOGENA = "Reporte"
HOJA_MODELO = "Borrador 210"

# Conceptos que NO tienen casilla en el anexo: solo referencia.
# (viven en config.reglas_anexo.py junto con las reglas de mapeo)