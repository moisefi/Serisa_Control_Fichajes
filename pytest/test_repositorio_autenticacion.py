from __future__ import annotations

from infraestructura.repositorio_autenticacion import RepositorioAutenticacion


class CursorFake:
    def __init__(self, fetchone_value=None, fetchall_value=None):
        self.fetchone_value = fetchone_value
        self.fetchall_value = fetchall_value or []
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return self.fetchone_value

    def fetchall(self):
        return self.fetchall_value


class RepoBDFake:
    def __init__(self, cursor: CursorFake):
        self._cursor = cursor

    class _Ctx:
        def __init__(self, cursor):
            self.cursor = cursor

        def __enter__(self):
            return self.cursor

        def __exit__(self, exc_type, exc, tb):
            return False

    def cursor(self):
        return self._Ctx(self._cursor)


def test_obtener_usuario_por_username_devuelve_dict():
    cur = CursorFake(fetchone_value=(1, "admin", "hash", "admin", True, "Ana"))
    repo = RepositorioAutenticacion(RepoBDFake(cur))

    out = repo.obtener_usuario_por_username("admin")

    assert out["id"] == 1
    assert out["username"] == "admin"
    assert out["usuario_rfid"] == "Ana"
    assert cur.executed[0][1] == ("admin",)


def test_obtener_usuario_por_username_none():
    cur = CursorFake(fetchone_value=None)
    repo = RepositorioAutenticacion(RepoBDFake(cur))
    assert repo.obtener_usuario_por_username("x") is None


def test_listar_usuarios_mapea_filas():
    cur = CursorFake(
        fetchall_value=[
            (1, "admin", "admin", True, "2026-01-01", None),
            (2, "rrhh", "rrhh", False, "2026-01-02", "Ana"),
        ]
    )
    repo = RepositorioAutenticacion(RepoBDFake(cur))

    out = repo.listar_usuarios()
    assert len(out) == 2
    assert out[0]["username"] == "admin"
    assert out[1]["usuario_rfid"] == "Ana"


def test_operaciones_escritura_llaman_execute():
    cur = CursorFake()
    repo = RepositorioAutenticacion(RepoBDFake(cur))

    repo.crear_usuario("u", "h", "basic", True, "Ana")
    repo.actualizar_usuario(5, "rrhh", False, None)
    repo.actualizar_password(5, "nuevo_hash")
    repo.eliminar_usuario_por_username("u")

    assert len(cur.executed) == 4
    assert cur.executed[0][1] == ("u", "h", "basic", True, "Ana")
    assert cur.executed[3][1] == ("u",)

