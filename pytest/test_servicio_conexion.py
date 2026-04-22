from __future__ import annotations

from configuracion import ConfiguracionAplicacion
from servicios.servicio_conexion import ServicioConexion


class RepoBDFake:
    def __init__(self):
        self.conectada_a = None
        self.desconectado = False
        self.verificada = True

    def conectar(self, ip):
        self.conectada_a = ip

    def desconectar(self):
        self.desconectado = True

    def verificar_conexion_activa(self):
        return self.verificada


class RepoConfigFake:
    def __init__(self):
        self.guardado = None

    def guardar(self, configuracion):
        self.guardado = configuracion


class EscanerFake:
    def __init__(self, ip="192.168.1.30"):
        self.ip = ip

    def buscar_ip_raspberry(self):
        return self.ip


def test_buscar_ip_devuelve_valor_del_escaner():
    service = ServicioConexion(
        repositorio_bd=RepoBDFake(),
        repositorio_configuracion=RepoConfigFake(),
        configuracion=ConfiguracionAplicacion(),
        escaner_red=EscanerFake(ip="10.0.0.7"),
    )
    assert service.buscar_ip() == "10.0.0.7"


def test_conectar_a_ip_actualiza_repo_y_config():
    repo_bd = RepoBDFake()
    repo_cfg = RepoConfigFake()
    cfg = ConfiguracionAplicacion()
    service = ServicioConexion(repo_bd, repo_cfg, cfg, EscanerFake())

    ip = service.conectar_a_ip("192.168.1.20")

    assert ip == "192.168.1.20"
    assert repo_bd.conectada_a == "192.168.1.20"
    assert cfg.ip_bd == "192.168.1.20"
    assert repo_cfg.guardado is cfg


def test_desconectar_y_verificar_conexion():
    repo_bd = RepoBDFake()
    service = ServicioConexion(repo_bd, RepoConfigFake(), ConfiguracionAplicacion(), EscanerFake())

    service.desconectar()
    assert repo_bd.desconectado is True
    assert service.verificar_conexion_activa() is True

