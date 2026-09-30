# -*- coding: utf-8 -*-
"""Paquete `generador_anexo`: generador del anexo del Formulario 210.

Arquitectura limpia por capas:
    config/                 -> configuracion (rutas, reglas de mapeo)
    domain/                 -> entidades y reglas de negocio (sin I/O)
    application/            -> puertos, DTO y caso de uso (orquestacion)
    infrastructure/         -> adaptadores concretos (lectura/escritura Excel)
    presentation/           -> CLI, GUI y composicion de dependencias
"""

from .config.reglas_anexo import INFO_PATTERNS, RULES
from .config.settings import CARPETA
from .presentation.composicion import procesar

__version__ = "3.0.0"

__all__ = [
    "CARPETA", "RULES", "INFO_PATTERNS",
    "procesar",
]