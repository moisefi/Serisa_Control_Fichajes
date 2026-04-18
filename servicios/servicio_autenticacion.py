from __future__ import annotations

import bcrypt


class ServicioAutenticacion:
    ROLES_VALIDOS = {"admin", "rrhh", "basic"}

    def __init__(self, repositorio_autenticacion) -> None:
        self.repositorio_autenticacion = repositorio_autenticacion

    def _validar_rol(self, rol: str) -> str:
        rol_normalizado = rol.strip().lower()
        if rol_normalizado not in self.ROLES_VALIDOS:
            raise ValueError("Rol no válido")
        return rol_normalizado

    def _normalizar_usuario_rfid(self, usuario_rfid: str | None) -> str | None:
        if usuario_rfid is None:
            return None
        usuario_rfid = usuario_rfid.strip()
        return usuario_rfid or None

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
            "usuario_rfid": usuario["usuario_rfid"],
        }

    def listar_usuarios(self) -> list[dict]:
        return self.repositorio_autenticacion.listar_usuarios()

    def crear_usuario(
        self,
        username: str,
        password_plano: str,
        rol: str,
        activo: bool = True,
        usuario_rfid: str | None = None,
    ) -> None:
        username = username.strip()
        rol = self._validar_rol(rol)
        usuario_rfid = self._normalizar_usuario_rfid(usuario_rfid)

        if not username:
            raise ValueError("El username es obligatorio")

        if rol == "basic" and not usuario_rfid:
            raise ValueError("Los usuarios basic deben tener un usuario RFID asociado")

        existente = self.repositorio_autenticacion.obtener_usuario_por_username(username)
        if existente is not None:
            raise ValueError("Ya existe un usuario con ese nombre")

        password_hash = self.hash_password(password_plano)
        self.repositorio_autenticacion.crear_usuario(
            username=username,
            password_hash=password_hash,
            rol=rol,
            activo=activo,
            usuario_rfid=usuario_rfid,
        )

    def actualizar_usuario(
        self,
        user_id: int,
        rol: str,
        activo: bool,
        usuario_rfid: str | None,
    ) -> None:
        rol = self._validar_rol(rol)
        usuario_rfid = self._normalizar_usuario_rfid(usuario_rfid)

        if rol == "basic" and not usuario_rfid:
            raise ValueError("Los usuarios basic deben tener un usuario RFID asociado")

        self.repositorio_autenticacion.actualizar_usuario(
            user_id=user_id,
            rol=rol,
            activo=activo,
            usuario_rfid=usuario_rfid,
        )

    def cambiar_password(self, user_id: int, nueva_password: str) -> None:
        password_hash = self.hash_password(nueva_password)
        self.repositorio_autenticacion.actualizar_password(user_id, password_hash)

    def eliminar_usuario(self, username: str) -> None:
        username = username.strip()
        if not username:
            raise ValueError("Debes indicar un nombre de usuario")
        self.repositorio_autenticacion.eliminar_usuario_por_username(username)