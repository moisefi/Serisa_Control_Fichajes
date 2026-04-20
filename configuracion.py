from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from errores import ErrorConfiguracion


RUTA_CONFIGURACION = Path("config.json")


@dataclass(slots=True)
class ConfiguracionAplicacion:
    ip_bd: str = ""
    hostname_raspberry: str = "rpi-fichajes"
    puerto_bd: int = 5432
    usuario_bd: str = ""
    contrasena_bd: str = ""
    nombre_bd: str = "postgres"
    intervalo_refresco_ms: int = 60000

    @classmethod
    def desde_dict(cls, datos: dict) -> "ConfiguracionAplicacion":
        base = asdict(cls())
        base.update(datos or {})
        base["usuario_bd"] = os.getenv("DB_USER", base.get("usuario_bd", ""))
        base["contrasena_bd"] = os.getenv("DB_PASSWORD", base.get("contrasena_bd", ""))
        return cls(**base)

    def a_dict(self) -> dict:
        # Nunca persistimos credenciales en disco.
        datos = asdict(self)
        datos.pop("usuario_bd", None)
        datos.pop("contrasena_bd", None)
        return datos


class RepositorioConfiguracion:
    def __init__(self, ruta: Path = RUTA_CONFIGURACION) -> None:
        self.ruta = ruta

    def cargar(self) -> ConfiguracionAplicacion:
        if not self.ruta.exists():
            configuracion = ConfiguracionAplicacion()
            self.guardar(configuracion)
            return configuracion

        try:
            with self.ruta.open("r", encoding="utf-8") as archivo:
                datos = json.load(archivo)
            return ConfiguracionAplicacion.desde_dict(datos)
        except Exception as error:
            configuracion = ConfiguracionAplicacion()
            self.guardar(configuracion)
            raise ErrorConfiguracion(
                "El archivo de configuración estaba dañado. Se ha restaurado la configuración por defecto."
            ) from error

    def guardar(self, configuracion: ConfiguracionAplicacion) -> None:
        with self.ruta.open("w", encoding="utf-8") as archivo:
            json.dump(configuracion.a_dict(), archivo, indent=4, ensure_ascii=False)
