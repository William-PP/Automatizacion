# -*- coding: utf-8 -*-
"""Entry point de la interfaz grafica (GUI).

Delega en el paquete `generador_anexo` (capa de presentacion:
generador_anexo.presentation.gui).

Uso:
    py interfaz_anexo.py

Requiere: openpyxl (y tkinter, que ya viene con Python en Windows).
"""

import sys

from generador_anexo.presentation.gui import main

if __name__ == "__main__":
    sys.exit(main())