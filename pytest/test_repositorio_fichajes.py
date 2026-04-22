from __future__ import annotations

from datetime import datetime

from psycopg2 import InterfaceError, OperationalError

from errores import ErrorBaseDeDatos, ErrorConexionBaseDeDatos
from infraestructura.repositorio_fichajes import RepositorioFichajes


class CursorFake:
    def __init__(self, fail_execute=None, fetchall_value=None, fetchone_value=(1,)):
        self.fail_execute = fail_execute
        self.fetchall_value = fetchall_value or []
        self.fetchone_value = fetchone_value
        self.executed = []
        self.closed = False

    def execute(self, query, params=None):
        if self.fail_execute:
            raise self.fail_execute
        self.executed.append((query, params))

    def fetchall(self):
        return self.fetchall_value

    def fetchone(self):
        return self.fetchone_value

    def close(self):
        self.closed = True


class ConnectionFake:
    def __init__(self, cursor: CursorFake, closed=0):
        self._cursor = cursor
        self.closed = closed
        self.committed = False
        self.rolled_back = False
        self.closed_called = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed_called = True
        self.closed = 1


def _repo_with_conn(conn: ConnectionFake) -> RepositorioFichajes:
    repo = RepositorioFichajes(usuario="u", contrasena="p", nombre_bd="db", puerto=5432)
    repo.conexion = conn
    return repo


def test_esta_conectado_true_false():
    repo = RepositorioFichajes(usuario="u", contrasena="p", nombre_bd="db", puerto=5432)
    assert repo.esta_conectado() is False
    repo.conexion = ConnectionFake(CursorFake(), closed=0)
    assert repo.esta_conectado() is True
    repo.conexion.closed = 1
    assert repo.esta_conectado() is False


def test_cursor_commit_ok():
    conn = ConnectionFake(CursorFake())
    repo = _repo_with_conn(conn)
    with repo.cursor() as cur:
        cur.execute("SELECT 1")
    assert conn.committed is True
    assert cur.closed is True


def test_cursor_error_operational_reenvia_conexion():
    conn = ConnectionFake(CursorFake(fail_execute=OperationalError("down")))
    repo = _repo_with_conn(conn)
    try:
        with repo.cursor() as cur:
            cur.execute("SELECT 1")
        assert False, "Debe lanzar ErrorConexionBaseDeDatos"
    except ErrorConexionBaseDeDatos:
        pass
    assert repo.conexion is None


def test_cursor_error_generico_hace_rollback():
    conn = ConnectionFake(CursorFake(fail_execute=RuntimeError("boom")))
    repo = _repo_with_conn(conn)
    try:
        with repo.cursor() as cur:
            cur.execute("SELECT 1")
        assert False, "Debe lanzar ErrorBaseDeDatos"
    except ErrorBaseDeDatos:
        pass
    assert conn.rolled_back is True


def test_ejecutar_consulta_fetchall():
    cur = CursorFake(fetchall_value=[("a",)])
    repo = _repo_with_conn(ConnectionFake(cur))
    out = repo.ejecutar_consulta("SELECT * FROM t", devolver=True)
    assert out == [("a",)]
    assert cur.executed[0][0].strip().startswith("SELECT")


def test_verificar_conexion_activa_maneja_interface_error():
    cur = CursorFake(fail_execute=InterfaceError("lost"))
    repo = _repo_with_conn(ConnectionFake(cur))
    assert repo.verificar_conexion_activa() is False
    assert repo.conexion is None


def test_construir_consulta_registros_agrega_condiciones():
    repo = RepositorioFichajes(usuario="u", contrasena="p", nombre_bd="db", puerto=5432)
    consulta, params = repo._construir_consulta_registros(
        usuario="Ana",
        uid_tarjeta="U1",
        fecha_desde=datetime(2026, 1, 1),
        fecha_hasta=datetime(2026, 1, 2),
        tipo="entrada",
        limite=200,
    )

    assert "r.uid_tarjeta = %s" in consulta
    assert "r.fecha_hora >= %s" in consulta
    assert "r.fecha_hora <= %s" in consulta
    assert "r.tipo = %s" in consulta
    assert "LIMIT %s" in consulta
    assert params[-1] == 200
    assert params[0] == "Ana"

