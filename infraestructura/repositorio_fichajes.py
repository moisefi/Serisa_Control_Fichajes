from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterator, Optional

import psycopg2
from psycopg2 import OperationalError, InterfaceError
from psycopg2.extensions import connection as ConexionPostgreSQL

from errores import ErrorBaseDeDatos, ErrorConexionBaseDeDatos


class RepositorioFichajes:
    def __init__(self, usuario: str, contrasena: str, nombre_bd: str, puerto: int) -> None:
        self.usuario = usuario
        self.contrasena = contrasena
        self.nombre_bd = nombre_bd
        self.puerto = puerto
        self.conexion: Optional[ConexionPostgreSQL] = None
        self.ip_actual: Optional[str] = None
        self.logger = logging.getLogger("aplicacion_fichajes")

    def conectar(self, ip: str) -> None:
        self.desconectar()
        try:
            self.logger.info("Intentando conexión PostgreSQL con %s:%s", ip, self.puerto)
            self.conexion = psycopg2.connect(
                host=ip,
                port=self.puerto,
                user=self.usuario,
                password=self.contrasena,
                dbname=self.nombre_bd,
                connect_timeout=3,
            )
            self.ip_actual = ip
            self.logger.info("Conexión PostgreSQL establecida con %s:%s", ip, self.puerto)
        except OperationalError as error:
            self.conexion = None
            self.ip_actual = None
            self.logger.error("Error operacional al conectar con %s:%s: %s", ip, self.puerto, error)
            raise ErrorConexionBaseDeDatos(str(error)) from error
        except Exception as error:
            self.conexion = None
            self.ip_actual = None
            self.logger.exception("Error general al conectar con %s:%s", ip, self.puerto)
            raise ErrorConexionBaseDeDatos(str(error)) from error

    def desconectar(self) -> None:
        if self.conexion:
            try:
                self.conexion.close()
                self.logger.info("Conexión con la base de datos cerrada")
            except Exception:
                self.logger.exception("Error al cerrar la conexión")
        self.conexion = None
        self.ip_actual = None

    def esta_conectado(self) -> bool:
        return self.conexion is not None and getattr(self.conexion, "closed", 1) == 0

    def verificar_conexion_activa(self) -> bool:
        if not self.esta_conectado():
            return False
        try:
            with self.conexion.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return True
        except (OperationalError, InterfaceError):
            self.logger.error("Conexión perdida con la base de datos durante la verificación")
            self.desconectar()
            return False
        except Exception:
            self.logger.exception("Error al verificar la conexión activa")
            self.desconectar()
            return False

    @contextmanager
    def cursor(self) -> Iterator[Any]:
        if not self.conexion:
            raise ErrorBaseDeDatos("No hay conexión con la base de datos")
        cursor = self.conexion.cursor()
        try:
            yield cursor
            self.conexion.commit()

        except (OperationalError, InterfaceError) as error:
            self.logger.error("Conexión perdida con la base de datos")
            self.desconectar()
            raise ErrorConexionBaseDeDatos("Conexión perdida con la base de datos") from error

        except Exception as error:
            self.conexion.rollback()
            self.logger.exception("Error al ejecutar una consulta")
            raise ErrorBaseDeDatos(str(error)) from error

        finally:
            cursor.close()

    def ejecutar_consulta(self, consulta: str, parametros: Optional[tuple] = None, devolver: bool = False) -> list[Any]:
        with self.cursor() as cursor:
            cursor.execute(consulta, parametros or ())
            return cursor.fetchall() if devolver else []

    def obtener_usuarios(self) -> list[tuple]:
        consulta = """
            SELECT id, nombre, uid_tarjeta
            FROM usuarios
            ORDER BY nombre ASC
        """
        return self.ejecutar_consulta(consulta, devolver=True)

    def registrar_usuario(self, nombre: str, uid_tarjeta: str) -> None:
        consulta = """
            INSERT INTO usuarios (nombre, uid_tarjeta)
            VALUES (%s, %s)
        """
        self.ejecutar_consulta(consulta, (nombre, uid_tarjeta))

    def dar_baja_usuario(self, uid_tarjeta: str) -> None:
        consulta = """
            DELETE FROM usuarios
            WHERE uid_tarjeta = %s
        """
        self.ejecutar_consulta(consulta, (uid_tarjeta,))


    def actualizar_fecha_hora_registro(self, id_registro: int, nueva_fecha_hora: str) -> None:
        consulta = """
            UPDATE registros
            SET fecha_hora = %s
            WHERE id = %s
        """
        self.ejecutar_consulta(consulta, (nueva_fecha_hora, id_registro))

    def actualizar_tipo_registro(self, id_registro: int, nuevo_tipo: str) -> None:
        consulta = """
            UPDATE registros
            SET tipo = %s
            WHERE id = %s
        """
        self.ejecutar_consulta(consulta, (nuevo_tipo, id_registro))


    def _construir_consulta_registros(
        self,
        usuario: Optional[str] = None,
        uid_tarjeta: Optional[str] = None,
        fecha_desde: Optional[datetime | str] = None,
        fecha_hasta: Optional[datetime | str] = None,
        tipo: Optional[str] = None,
        limite: Optional[int] = None,
    ) -> tuple[str, tuple[Any, ...]]:
        consulta = """
            SELECT
                r.id,
                COALESCE(
                    a.nombre_usuario,
                    (
                        SELECT u.nombre
                        FROM usuarios u
                        WHERE u.uid_tarjeta = r.uid_tarjeta
                        LIMIT 1
                    ),
                    'Sin asignar'
                ) AS usuario,
                r.uid_tarjeta,
                r.fecha_hora,
                r.tipo
            FROM registros r
            LEFT JOIN asignaciones_tarjetas a
                ON a.uid_tarjeta = r.uid_tarjeta
                AND r.fecha_hora >= a.fecha_inicio
                AND (a.fecha_fin IS NULL OR r.fecha_hora <= a.fecha_fin)
            WHERE 1 = 1
        """

        parametros: list[Any] = []

        if usuario:
            consulta += """
                AND COALESCE(
                    a.nombre_usuario,
                    (
                        SELECT u.nombre
                        FROM usuarios u
                        WHERE u.uid_tarjeta = r.uid_tarjeta
                        LIMIT 1
                    ),
                    'Sin asignar'
                ) = %s
            """
            parametros.append(usuario)

        if uid_tarjeta:
            consulta += " AND r.uid_tarjeta = %s"
            parametros.append(uid_tarjeta)

        if fecha_desde:
            consulta += " AND r.fecha_hora >= %s"
            parametros.append(fecha_desde)

        if fecha_hasta:
            consulta += " AND r.fecha_hora <= %s"
            parametros.append(fecha_hasta)

        if tipo:
            consulta += " AND r.tipo = %s"
            parametros.append(tipo)

        consulta += " ORDER BY r.fecha_hora DESC"

        if limite is not None:
            consulta += " LIMIT %s"
            parametros.append(limite)

        return consulta, tuple(parametros)

    def obtener_registros_con_filtros_tabla(
        self,
        usuario: Optional[str] = None,
        uid_tarjeta: Optional[str] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        tipo: Optional[str] = None,
        limite: int = 200,
    ) -> list[tuple]:
        consulta, parametros = self._construir_consulta_registros(
            usuario=usuario,
            uid_tarjeta=uid_tarjeta,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            tipo=tipo,
            limite=limite,
        )
        return self.ejecutar_consulta(consulta, parametros, devolver=True)

    def obtener_registros_filtrados(
        self,
        usuario: Optional[str] = None,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        uid_tarjeta: Optional[str] = None,
    ) -> list[tuple]:
        consulta, parametros = self._construir_consulta_registros(
            usuario=usuario,
            uid_tarjeta=uid_tarjeta,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )
        return self.ejecutar_consulta(consulta, parametros, devolver=True)

    def obtener_uids_sin_asignar(self) -> list[tuple]:
        consulta = """
            SELECT DISTINCT r.uid_tarjeta
            FROM registros r
            LEFT JOIN usuarios u ON u.uid_tarjeta = r.uid_tarjeta
            WHERE u.uid_tarjeta IS NULL
            ORDER BY r.uid_tarjeta
        """
        return self.ejecutar_consulta(consulta, devolver=True)

    def obtener_usuarios_asignados(self) -> list[tuple]:
        consulta = """
            SELECT nombre, uid_tarjeta
            FROM usuarios
            ORDER BY nombre ASC, uid_tarjeta ASC
        """
        return self.ejecutar_consulta(consulta, devolver=True)

    def obtener_tipos_registro(self) -> list[tuple]:
        consulta = """
            SELECT DISTINCT tipo
            FROM registros
            WHERE tipo IS NOT NULL AND TRIM(tipo) <> ''
            ORDER BY tipo
        """
        return self.ejecutar_consulta(consulta, devolver=True)
