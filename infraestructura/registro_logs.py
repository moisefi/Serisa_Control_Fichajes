from __future__ import annotations

import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path


RUTA_BASE_LOGS = Path("logs")
NOMBRE_LOG = "aplicacion.log"
DIAS_A_CONSERVAR = 7
NOMBRE_LOGGER = "aplicacion_fichajes"


def _crear_carpeta_logs_del_dia() -> Path:
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    ruta_carpeta = RUTA_BASE_LOGS / fecha_hoy
    ruta_carpeta.mkdir(parents=True, exist_ok=True)
    return ruta_carpeta


def _eliminar_logs_antiguos() -> None:
    if not RUTA_BASE_LOGS.exists():
        return

    limite = datetime.now() - timedelta(days=DIAS_A_CONSERVAR)
    for carpeta in RUTA_BASE_LOGS.iterdir():
        if not carpeta.is_dir():
            continue
        try:
            fecha_carpeta = datetime.strptime(carpeta.name, "%Y-%m-%d")
        except ValueError:
            continue
        if fecha_carpeta < limite:
            shutil.rmtree(carpeta, ignore_errors=True)


def configurar_logger() -> logging.Logger:
    RUTA_BASE_LOGS.mkdir(parents=True, exist_ok=True)
    _eliminar_logs_antiguos()

    ruta_log = _crear_carpeta_logs_del_dia() / NOMBRE_LOG
    logger = logging.getLogger(NOMBRE_LOGGER)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formato = logging.Formatter("%(asctime)s | %(levelname)s | %(module)s | %(message)s")

    manejador_archivo = logging.FileHandler(ruta_log, encoding="utf-8")
    manejador_archivo.setLevel(logging.INFO)
    manejador_archivo.setFormatter(formato)

    manejador_consola = logging.StreamHandler()
    manejador_consola.setLevel(logging.INFO)
    manejador_consola.setFormatter(formato)

    logger.addHandler(manejador_archivo)
    logger.addHandler(manejador_consola)
    logger.info("Logger inicializado correctamente")
    return logger
