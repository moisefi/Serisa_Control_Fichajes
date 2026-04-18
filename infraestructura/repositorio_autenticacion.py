from __future__ import annotations


class RepositorioAutenticacion:
    def __init__(self, repositorio_bd) -> None:
        self.repositorio_bd = repositorio_bd

    def obtener_usuario_por_username(self, username: str) -> dict | None:
        consulta = """
            SELECT id, username, password_hash, rol, activo, usuario_rfid
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
            "usuario_rfid": fila[5],
        }

    def listar_usuarios(self) -> list[dict]:
        consulta = """
            SELECT id, username, rol, activo, creado_en, usuario_rfid
            FROM auth_usuarios
            ORDER BY username ASC
        """

        with self.repositorio_bd.cursor() as cursor:
            cursor.execute(consulta)
            filas = cursor.fetchall()

        return [
            {
                "id": fila[0],
                "username": fila[1],
                "rol": fila[2],
                "activo": fila[3],
                "creado_en": fila[4],
                "usuario_rfid": fila[5],
            }
            for fila in filas
        ]

    def crear_usuario(
        self,
        username: str,
        password_hash: str,
        rol: str,
        activo: bool = True,
        usuario_rfid: str | None = None,
    ) -> None:
        consulta = """
            INSERT INTO auth_usuarios (username, password_hash, rol, activo, usuario_rfid)
            VALUES (%s, %s, %s, %s, %s)
        """
        with self.repositorio_bd.cursor() as cursor:
            cursor.execute(consulta, (username, password_hash, rol, activo, usuario_rfid))

    def actualizar_usuario(
        self,
        user_id: int,
        rol: str,
        activo: bool,
        usuario_rfid: str | None,
    ) -> None:
        consulta = """
            UPDATE auth_usuarios
            SET rol = %s,
                activo = %s,
                usuario_rfid = %s
            WHERE id = %s
        """
        with self.repositorio_bd.cursor() as cursor:
            cursor.execute(consulta, (rol, activo, usuario_rfid, user_id))

    def actualizar_password(self, user_id: int, password_hash: str) -> None:
        consulta = """
            UPDATE auth_usuarios
            SET password_hash = %s
            WHERE id = %s
        """
        with self.repositorio_bd.cursor() as cursor:
            cursor.execute(consulta, (password_hash, user_id))

    def eliminar_usuario_por_username(self, username: str) -> None:
        consulta = """
            DELETE FROM auth_usuarios
            WHERE username = %s
        """
        with self.repositorio_bd.cursor() as cursor:
            cursor.execute(consulta, (username,))