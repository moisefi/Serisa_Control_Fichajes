from __future__ import annotations

from errores import ErrorBaseDeDatos


class RepositorioAutenticacion:
    def __init__(self, repositorio_bd) -> None:
        self.repositorio_bd = repositorio_bd

    def obtener_usuario_por_username(self, username: str) -> dict | None:
        consulta = """
            SELECT id, username, password_hash, rol, activo
            FROM auth_usuarios
            WHERE username = %s
            LIMIT 1
        """

        with self.repositorio_bd.cursor() as cursor:
            cursor.execute(consulta, (username,))
            fila = cursor.fetchone()

        if fila is None:
            return None

        return {
            "id": fila[0],
            "username": fila[1],
            "password_hash": fila[2],
            "rol": fila[3],
            "activo": fila[4],
        }

    def crear_usuario(self, username: str, password_hash: str, rol: str, activo: bool = True) -> None:
        consulta = """
            INSERT INTO auth_usuarios (username, password_hash, rol, activo)
            VALUES (%s, %s, %s, %s)
        """
        with self.repositorio_bd.cursor() as cursor:
            cursor.execute(consulta, (username, password_hash, rol, activo))

    def actualizar_password(self, user_id: int, password_hash: str) -> None:
        consulta = """
            UPDATE auth_usuarios
            SET password_hash = %s
            WHERE id = %s
        """
        with self.repositorio_bd.cursor() as cursor:
            cursor.execute(consulta, (password_hash, user_id))