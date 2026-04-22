from __future__ import annotations

from datetime import datetime

from servicios.servicio_fichajes import FiltrosRegistros, ServicioFichajes


class RepoFichajesFake:
    def __init__(self):
        self.called = {}

    def registrar_usuario(self, nombre, uid):
        self.called["registrar_usuario"] = (nombre, uid)

    def dar_baja_usuario(self, uid):
        self.called["dar_baja_usuario"] = uid

    def obtener_registros_con_filtros_tabla(self, **kwargs):
        self.called["obtener_registros_con_filtros_tabla"] = kwargs
        return [("fila",)]

    def obtener_registros_filtrados(self, **kwargs):
        self.called["obtener_registros_filtrados"] = kwargs
        return [("fila_export",)]

    def actualizar_fecha_hora_registro(self, id_registro, nueva_fecha_hora):
        self.called["actualizar_fecha_hora_registro"] = (id_registro, nueva_fecha_hora)

    def actualizar_tipo_registro(self, id_registro, nuevo_tipo):
        self.called["actualizar_tipo_registro"] = (id_registro, nuevo_tipo)

    def obtener_uids_sin_asignar(self):
        return [("U1",), ("U2",)]

    def obtener_usuarios_asignados(self):
        return [("Ana", "U1")]

    def obtener_tipos_registro(self):
        return [("entrada",), ("salida",)]


def test_registrar_usuario_valida_campos():
    repo = RepoFichajesFake()
    service = ServicioFichajes(repo)

    try:
        service.registrar_usuario(" ", "U1")
        assert False, "Debe lanzar ValueError"
    except ValueError:
        pass

    service.registrar_usuario(" Ana ", " U1 ")
    assert repo.called["registrar_usuario"] == ("Ana", "U1")


def test_dar_baja_usuario_valida_uid():
    repo = RepoFichajesFake()
    service = ServicioFichajes(repo)

    try:
        service.dar_baja_usuario(" ")
        assert False, "Debe lanzar ValueError"
    except ValueError:
        pass

    service.dar_baja_usuario(" U1 ")
    assert repo.called["dar_baja_usuario"] == "U1"


def test_obtener_registros_envia_filtros_al_repo():
    repo = RepoFichajesFake()
    service = ServicioFichajes(repo)
    filtros = FiltrosRegistros(
        usuario="Ana",
        uid_tarjeta="U1",
        fecha_desde=datetime(2026, 1, 1),
        fecha_hasta=datetime(2026, 1, 2),
        tipo="entrada",
        limite=50,
    )

    out = service.obtener_registros(filtros)

    assert out == [("fila",)]
    assert repo.called["obtener_registros_con_filtros_tabla"]["usuario"] == "Ana"
    assert repo.called["obtener_registros_con_filtros_tabla"]["limite"] == 50


def test_exportacion_y_actualizaciones():
    repo = RepoFichajesFake()
    service = ServicioFichajes(repo)

    rows = service.obtener_registros_para_exportacion(usuario="Ana")
    assert rows == [("fila_export",)]
    assert repo.called["obtener_registros_filtrados"]["usuario"] == "Ana"

    service.actualizar_fecha_hora_registro(1, "2026-04-01 08:00:00")
    assert repo.called["actualizar_fecha_hora_registro"] == (1, "2026-04-01 08:00:00")

    service.actualizar_tipo_registro(1, "SALIDA")
    assert repo.called["actualizar_tipo_registro"] == (1, "salida")


def test_obtener_datos_desplegables_mapea_formato():
    repo = RepoFichajesFake()
    service = ServicioFichajes(repo)

    out = service.obtener_datos_desplegables()

    assert out["uids_sin_asignar"] == ["U1", "U2"]
    assert out["usuarios_asignados"] == [("Ana", "U1")]
    assert out["tipos"] == ["entrada", "salida"]

