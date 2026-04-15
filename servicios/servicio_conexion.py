from __future__ import annotations

from configuracion import ConfiguracionAplicacion, RepositorioConfiguracion
from infraestructura.escaner_red import EscanerRed
from infraestructura.repositorio_fichajes import RepositorioFichajes


class ServicioConexion:
    def __init__(
        self,
        repositorio_bd: RepositorioFichajes,
        repositorio_configuracion: RepositorioConfiguracion,
        configuracion: ConfiguracionAplicacion,
        escaner_red: EscanerRed,
    ) -> None:
        self.repositorio_bd = repositorio_bd
        self.repositorio_configuracion = repositorio_configuracion
        self.configuracion = configuracion
        self.escaner_red = escaner_red

    def buscar_ip(self) -> str | None:
        return self.escaner_red.buscar_ip_raspberry()

    def conectar_a_ip(self, ip: str) -> str:
        self.repositorio_bd.conectar(ip)
        self.configuracion.ip_bd = ip
        self.repositorio_configuracion.guardar(self.configuracion)
        return ip


    def desconectar(self) -> None:
        self.repositorio_bd.desconectar()

    def verificar_conexion_activa(self) -> bool:
        return self.repositorio_bd.verificar_conexion_activa()
