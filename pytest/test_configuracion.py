from __future__ import annotations

import json
from pathlib import Path

from configuracion import ConfiguracionAplicacion, RepositorioConfiguracion
from errores import ErrorConfiguracion


def test_desde_dict_usa_env_para_credenciales(monkeypatch):
    monkeypatch.setenv("DB_USER", "env_user")
    monkeypatch.setenv("DB_PASSWORD", "env_pass")

    cfg = ConfiguracionAplicacion.desde_dict(
        {
            "ip_bd": "10.0.0.2",
            "usuario_bd": "json_user",
            "contrasena_bd": "json_pass",
        }
    )

    assert cfg.usuario_bd == "env_user"
    assert cfg.contrasena_bd == "env_pass"
    assert cfg.ip_bd == "10.0.0.2"


def test_a_dict_no_persiste_credenciales():
    cfg = ConfiguracionAplicacion(
        ip_bd="1.2.3.4",
        usuario_bd="secret_user",
        contrasena_bd="secret_pass",
    )

    data = cfg.a_dict()
    assert "usuario_bd" not in data
    assert "contrasena_bd" not in data
    assert data["ip_bd"] == "1.2.3.4"


def test_repositorio_cargar_crea_archivo_si_no_existe(tmp_path):
    ruta = tmp_path / "config.json"
    repo = RepositorioConfiguracion(ruta=ruta)

    cfg = repo.cargar()

    assert ruta.exists()
    assert isinstance(cfg, ConfiguracionAplicacion)


def test_repositorio_guardar_no_guarda_credenciales(tmp_path):
    ruta = tmp_path / "config.json"
    repo = RepositorioConfiguracion(ruta=ruta)
    cfg = ConfiguracionAplicacion(
        ip_bd="192.168.1.20",
        usuario_bd="admin",
        contrasena_bd="1234",
    )

    repo.guardar(cfg)
    raw = json.loads(ruta.read_text(encoding="utf-8"))

    assert "usuario_bd" not in raw
    assert "contrasena_bd" not in raw
    assert raw["ip_bd"] == "192.168.1.20"


def test_repositorio_cargar_archivo_danado_lanza_error_y_restaura(tmp_path):
    ruta = tmp_path / "config.json"
    ruta.write_text("{ json roto", encoding="utf-8")
    repo = RepositorioConfiguracion(ruta=ruta)

    try:
        repo.cargar()
        assert False, "Debe lanzar ErrorConfiguracion"
    except ErrorConfiguracion:
        pass

    restaurado = json.loads(ruta.read_text(encoding="utf-8"))
    assert "ip_bd" in restaurado
    assert "usuario_bd" not in restaurado

