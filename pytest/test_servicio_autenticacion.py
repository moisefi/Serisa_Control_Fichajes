from __future__ import annotations

from servicios.servicio_autenticacion import ServicioAutenticacion


class RepoAuthFake:
    def __init__(self):
        self.users = {}
        self.created = None
        self.updated = None
        self.updated_password = None
        self.deleted = None

    def obtener_usuario_por_username(self, username):
        return self.users.get(username)

    def listar_usuarios(self):
        return list(self.users.values())

    def crear_usuario(self, **kwargs):
        self.created = kwargs

    def actualizar_usuario(self, **kwargs):
        self.updated = kwargs

    def actualizar_password(self, user_id, password_hash):
        self.updated_password = (user_id, password_hash)

    def eliminar_usuario_por_username(self, username):
        self.deleted = username


def test_hash_y_verificacion_password():
    repo = RepoAuthFake()
    service = ServicioAutenticacion(repo)

    hashed = service.hash_password("secreto123")
    assert hashed != "secreto123"
    assert service.verificar_password("secreto123", hashed) is True
    assert service.verificar_password("otro", hashed) is False


def test_hash_password_vacio_lanza_error():
    service = ServicioAutenticacion(RepoAuthFake())
    try:
        service.hash_password("   ")
        assert False, "Debe lanzar ValueError"
    except ValueError:
        pass


def test_autenticar_ok():
    repo = RepoAuthFake()
    service = ServicioAutenticacion(repo)
    pw_hash = service.hash_password("clave")
    repo.users["admin"] = {
        "id": 1,
        "username": "admin",
        "password_hash": pw_hash,
        "rol": "admin",
        "activo": True,
        "usuario_rfid": None,
    }

    out = service.autenticar("admin", "clave")
    assert out is not None
    assert out["username"] == "admin"
    assert out["rol"] == "admin"


def test_autenticar_rechaza_inactivo_o_password_incorrecta():
    repo = RepoAuthFake()
    service = ServicioAutenticacion(repo)
    pw_hash = service.hash_password("clave")

    repo.users["u1"] = {
        "id": 2,
        "username": "u1",
        "password_hash": pw_hash,
        "rol": "basic",
        "activo": False,
        "usuario_rfid": "Ana",
    }
    assert service.autenticar("u1", "clave") is None

    repo.users["u1"]["activo"] = True
    assert service.autenticar("u1", "mala") is None


def test_crear_usuario_basic_requiere_rfid():
    service = ServicioAutenticacion(RepoAuthFake())
    try:
        service.crear_usuario("basic01", "1234", "basic", usuario_rfid=" ")
        assert False, "Debe lanzar ValueError"
    except ValueError:
        pass


def test_crear_usuario_ok_llama_repo():
    repo = RepoAuthFake()
    service = ServicioAutenticacion(repo)
    service.crear_usuario("rrhh01", "1234", "rrhh", activo=True, usuario_rfid=None)

    assert repo.created is not None
    assert repo.created["username"] == "rrhh01"
    assert repo.created["rol"] == "rrhh"
    assert isinstance(repo.created["password_hash"], str)


def test_actualizar_usuario_normaliza_rol_y_rfid():
    repo = RepoAuthFake()
    service = ServicioAutenticacion(repo)
    service.actualizar_usuario(user_id=7, rol=" BASIC ", activo=True, usuario_rfid=" Ana ")

    assert repo.updated == {
        "user_id": 7,
        "rol": "basic",
        "activo": True,
        "usuario_rfid": "Ana",
    }


def test_cambiar_password_y_eliminar_usuario():
    repo = RepoAuthFake()
    service = ServicioAutenticacion(repo)

    service.cambiar_password(9, "nueva")
    assert repo.updated_password is not None
    assert repo.updated_password[0] == 9

    service.eliminar_usuario("  user1  ")
    assert repo.deleted == "user1"

