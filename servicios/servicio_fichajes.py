from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from infraestructura.repositorio_fichajes import RepositorioFichajes


@dataclass(slots=True)
class FiltrosRegistros:
    usuario: Optional[str] = None
    uid_tarjeta: Optional[str] = None
    fecha_desde: Optional[datetime] = None
    fecha_hasta: Optional[datetime] = None
    tipo: Optional[str] = None
    limite: int = 200


class ServicioFichajes:
    def __init__(self, repositorio: RepositorioFichajes) -> None:
        self.repositorio = repositorio

    def registrar_usuario(self, nombre: str, uid: str) -> None:
        nombre = nombre.strip()
        uid = uid.strip()
        if not nombre or not uid:
            raise ValueError("Debes introducir nombre y UID")
        self.repositorio.registrar_usuario(nombre, uid)

    def dar_baja_usuario(self, uid: str) -> None:
        uid = uid.strip()
        if not uid:
            raise ValueError("Debes indicar el UID del usuario a dar de baja")
        self.repositorio.dar_baja_usuario(uid)

    def obtener_registros(self, filtros: FiltrosRegistros) -> list[tuple]:
        return self.repositorio.obtener_registros_con_filtros_tabla(
            usuario=filtros.usuario,
            uid_tarjeta=filtros.uid_tarjeta,
            fecha_desde=filtros.fecha_desde,
            fecha_hasta=filtros.fecha_hasta,
            tipo=filtros.tipo,
            limite=filtros.limite,
        )

    def obtener_registros_para_exportacion(
        self,
        usuario: Optional[str] = None,
        uid_tarjeta: Optional[str] = None,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
    ) -> list[tuple]:
        return self.repositorio.obtener_registros_filtrados(
            usuario=usuario,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            uid_tarjeta=uid_tarjeta,
        )

    def actualizar_fecha_hora_registro(self, id_registro: int, nueva_fecha_hora: str) -> None:
        self.repositorio.actualizar_fecha_hora_registro(id_registro, nueva_fecha_hora)

    def actualizar_tipo_registro(self, id_registro: int, nuevo_tipo: str) -> None:
        self.repositorio.actualizar_tipo_registro(id_registro, nuevo_tipo.lower())

    def obtener_datos_desplegables(self) -> dict:
        uids_sin_asignar = [fila[0] for fila in self.repositorio.obtener_uids_sin_asignar()]
        usuarios_asignados = self.repositorio.obtener_usuarios_asignados()
        tipos = [fila[0] for fila in self.repositorio.obtener_tipos_registro()]
        return {
            "uids_sin_asignar": uids_sin_asignar,
            "usuarios_asignados": usuarios_asignados,
            "tipos": tipos,
        }
