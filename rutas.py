from __future__ import annotations

import os
import sys
from pathlib import Path


NOMBRE_APLICACION = "SERISA"


def obtener_directorio_base() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def obtener_recurso(*partes: str) -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS, *partes)
    return obtener_directorio_base().joinpath(*partes)


def obtener_directorio_datos_usuario() -> Path:
    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata) / NOMBRE_APLICACION
    return Path.home() / f".{NOMBRE_APLICACION.lower()}"


def obtener_directorio_logs() -> Path:
    return obtener_directorio_datos_usuario() / "logs"
