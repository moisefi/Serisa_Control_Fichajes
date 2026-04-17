from __future__ import annotations

import bcrypt


class ServicioAutenticacion:
    def __init__(self, repositorio_autenticacion) -> None:
        self.repositorio_autenticacion = repositorio_autenticacion

    def hash_password(self, password_plano: str) -> str:
        password_plano = password_plano.strip()
        if not password_plano:
            raise ValueError("La contraseña no puede estar vacía")

        password_hash = bcrypt.hashpw(
            password_plano.encode("utf-8"),
            bcrypt.gensalt(),
        )
        return password_hash.decode("utf-8")

    def verificar_password(self, password_plano: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(
                password_plano.encode("utf-8"),
                password_hash.encode("utf-8"),
            )
        except Exception:
            return False

    def autenticar(self, username: str, password_plano: str) -> dict | None:
        username = username.strip()
        if not username or not password_plano:
            return None

        usuario = self.repositorio_autenticacion.obtener_usuario_por_username(username)
        if usuario is None:
            return None

        if not usuario["activo"]:
            return None

        if not self.verificar_password(password_plano, usuario["password_hash"]):
            return None

        return {
            "id": usuario["id"],
            "username": usuario["username"],
            "rol": usuario["rol"],
        }

    def crear_usuario(self, username: str, password_plano: str, rol: str, activo: bool = True) -> None:
        username = username.strip()
        rol = rol.strip().lower()

        if not username:
            raise ValueError("El username es obligatorio")
        if not rol:
            raise ValueError("El rol es obligatorio")

        password_hash = self.hash_password(password_plano)
        self.repositorio_autenticacion.crear_usuario(username, password_hash, rol, activo)

    def cambiar_password(self, user_id: int, nueva_password: str) -> None:
        password_hash = self.hash_password(nueva_password)
        self.repositorio_autenticacion.actualizar_password(user_id, password_hash)