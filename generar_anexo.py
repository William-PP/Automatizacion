# -*- coding: utf-8 -*-
"""Entry point de linea de comandos (CLI).

Delega en el paquete `generador_anexo` (capa de presentacion:
generador_anexo.presentation.cli).

Uso:
    py generar_anexo.py
    py generar_anexo.py ruta_exogena.xlsx [--salida nombre.xlsx]

Requiere: openpyxl  ->  py -m pip install openpyxl
"""

import sys

from generador_anexo.presentation.cli import main

if __name__ == "__main__":
    sys.exit(main())