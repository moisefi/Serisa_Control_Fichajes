from __future__ import annotations

import logging
from datetime import datetime

from infraestructura import registro_logs


def test_crear_carpeta_logs_del_dia(tmp_path, monkeypatch):
    monkeypatch.setattr(registro_logs, "RUTA_BASE_LOGS", tmp_path)
    ruta = registro_logs._crear_carpeta_logs_del_dia()
    assert ruta.exists()
    assert ruta.parent == tmp_path


def test_eliminar_logs_antiguos(tmp_path, monkeypatch):
    monkeypatch.setattr(registro_logs, "RUTA_BASE_LOGS", tmp_path)
    monkeypatch.setattr(registro_logs, "DIAS_A_CONSERVAR", 7)

    (tmp_path / "2020-01-01").mkdir()
    (tmp_path / "2999-01-01").mkdir()
    (tmp_path / "carpeta_invalida").mkdir()

    registro_logs._eliminar_logs_antiguos()

    assert not (tmp_path / "2020-01-01").exists()
    assert (tmp_path / "2999-01-01").exists()
    assert (tmp_path / "carpeta_invalida").exists()


def test_configurar_logger_crea_handlers_y_archivo(tmp_path, monkeypatch):
    monkeypatch.setattr(registro_logs, "RUTA_BASE_LOGS", tmp_path)
    monkeypatch.setattr(registro_logs, "NOMBRE_LOGGER", "aplicacion_fichajes_test")
    monkeypatch.setattr(registro_logs, "NOMBRE_LOG", "app_test.log")

    logger = logging.getLogger("aplicacion_fichajes_test")
    logger.handlers.clear()

    out = registro_logs.configurar_logger()
    assert out is logger
    assert len(out.handlers) == 2

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    assert (tmp_path / fecha_hoy / "app_test.log").exists()

