from __future__ import annotations

import logging
import socket
from typing import Optional


class EscanerRed:
    def __init__(self, puerto_bd: int = 5432, nombre_host: str = "rpi-fichajes") -> None:
        self.puerto_bd = puerto_bd
        self.nombre_host = nombre_host
        self.logger = logging.getLogger("aplicacion_fichajes")

    def resolver_ip_por_hostname(self) -> Optional[str]:
        try:
            ip = socket.gethostbyname(self.nombre_host)
            self.logger.info("Hostname %s resuelto a %s", self.nombre_host, ip)
            return ip
        except socket.gaierror:
            self.logger.warning("No se pudo resolver el hostname %s", self.nombre_host)
            return None

    def comprobar_puerto_abierto(self, ip: str) -> bool:
        socket_prueba = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_prueba.settimeout(2)
        try:
            resultado = socket_prueba.connect_ex((ip, self.puerto_bd))
            abierto = resultado == 0
            self.logger.info("Comprobación de puerto %s:%s -> %s", ip, self.puerto_bd, abierto)
            return abierto
        except Exception:
            self.logger.exception("Error comprobando el puerto %s:%s", ip, self.puerto_bd)
            return False
        finally:
            socket_prueba.close()

    def buscar_ip_raspberry(self) -> str | None:
        ip = self.resolver_ip_por_hostname()
        if not ip:
            return None

        if not self.comprobar_puerto_abierto(ip):
            return None

        return ip

