from __future__ import annotations

from types import SimpleNamespace
import tkinter as tk

import pytest
from errores import ErrorConexionBaseDeDatos
from interfaz.ventana_login import SesionUsuario
from interfaz.ventana_principal import VentanaPrincipal


class LoggerFake:
    def exception(self, *_args, **_kwargs):
        return

    def warning(self, *_args, **_kwargs):
        return


class RepoConnFake:
    def __init__(self, connected=True):
        self.connected = connected

    def esta_conectado(self):
        return self.connected


class ServicioFichajesFake:
    def __init__(self, connected=True):
        self.repositorio = RepoConnFake(connected=connected)

    def obtener_datos_desplegables(self):
        return {"uids_sin_asignar": [], "usuarios_asignados": [], "tipos": []}

    def obtener_registros(self, _filtros):
        return []


class ServicioConexionFake:
    def verificar_conexion_activa(self):
        return True

    def desconectar(self):
        return

    def buscar_ip(self):
        return None

    def conectar_a_ip(self, _ip):
        return


class ServicioAuthFake:
    def __init__(self, error=None):
        self.error = error
        self.calls = 0

    def listar_usuarios(self):
        self.calls += 1
        if self.error:
            raise self.error
        return []


@pytest.fixture(autouse=True)
def _skip_si_tk_no_disponible():
    try:
        root = tk.Tk()
        root.destroy()
    except tk.TclError:
        pytest.skip("Tkinter no disponible en este entorno de pruebas")


def _build_app(monkeypatch, rol="admin", connected=True, auth_error=None):
    monkeypatch.setattr(VentanaPrincipal, "_intentar_conexion_inicial", lambda self: None)
    monkeypatch.setattr(VentanaPrincipal, "_inicializar_sin_panel_conexion", lambda self: None)

    try:
        app = VentanaPrincipal(
            configuracion=SimpleNamespace(intervalo_refresco_ms=60000, hostname_raspberry="rpi-fichajes", puerto_bd=5432),
            servicio_conexion=ServicioConexionFake(),
            servicio_fichajes=ServicioFichajesFake(connected=connected),
            servicio_autenticacion=ServicioAuthFake(error=auth_error),
            logger=LoggerFake(),
            sesion=SesionUsuario(id_usuario=1, username="u", rol=rol),
        )
    except tk.TclError:
        pytest.skip("Tkinter/Tcl no disponible en este entorno de pruebas")
    app.withdraw()
    return app


def test_admin_no_permitido_para_no_admin(monkeypatch):
    warnings = []
    monkeypatch.setattr("interfaz.ventana_principal.messagebox.showwarning", lambda *args, **kwargs: warnings.append(args))
    app = _build_app(monkeypatch, rol="basic")
    try:
        app._abrir_ventana_administracion()
        assert warnings
        assert warnings[0][0] == "Acceso denegado"
    finally:
        app.destroy()


def test_admin_no_abre_si_sin_conexion(monkeypatch):
    warnings = []
    monkeypatch.setattr("interfaz.ventana_principal.messagebox.showwarning", lambda *args, **kwargs: warnings.append(args))
    app = _build_app(monkeypatch, rol="admin", connected=False)
    try:
        app._abrir_ventana_administracion()
        assert warnings
        assert warnings[0][0] == "Sin conexión"
        assert app.estado_conexion.get() == "Desconectado"
    finally:
        app.destroy()


def test_admin_abre_ventana_cuando_validacion_ok(monkeypatch):
    warnings = []
    monkeypatch.setattr("interfaz.ventana_principal.messagebox.showwarning", lambda *args, **kwargs: warnings.append(args))
    monkeypatch.setattr("interfaz.ventana_principal.messagebox.showerror", lambda *args, **kwargs: None)

    # Hilo inmediato
    class ThreadImmediate:
        def __init__(self, target=None, daemon=None):
            self._target = target
            self._alive = False

        def start(self):
            self._alive = True
            if self._target:
                self._target()
            self._alive = False

        def is_alive(self):
            return self._alive

    monkeypatch.setattr("interfaz.ventana_principal.threading.Thread", ThreadImmediate)

    app = _build_app(monkeypatch, rol="admin", connected=True)
    created = {"ok": False}

    class AdminFake:
        def __init__(self, **kwargs):
            created["ok"] = True

        def grab_set(self):
            return

    monkeypatch.setattr("interfaz.ventana_principal.VentanaAdministracion", AdminFake)
    monkeypatch.setattr(app, "_mostrar_dialogo_espera_admin", lambda: None)
    monkeypatch.setattr(app, "_cerrar_dialogo_espera_admin", lambda: None)
    monkeypatch.setattr(app, "after", lambda _ms, cb=None: cb() if cb else None)

    try:
        app._abrir_ventana_administracion()
        assert created["ok"] is True
        assert not warnings
    finally:
        app.destroy()


def test_admin_maneja_error_conexion_en_validacion(monkeypatch):
    warnings = []
    monkeypatch.setattr("interfaz.ventana_principal.messagebox.showwarning", lambda *args, **kwargs: warnings.append(args))
    monkeypatch.setattr("interfaz.ventana_principal.messagebox.showerror", lambda *args, **kwargs: None)

    class ThreadImmediate:
        def __init__(self, target=None, daemon=None):
            self._target = target
            self._alive = False

        def start(self):
            self._alive = True
            if self._target:
                self._target()
            self._alive = False

        def is_alive(self):
            return self._alive

    monkeypatch.setattr("interfaz.ventana_principal.threading.Thread", ThreadImmediate)

    app = _build_app(monkeypatch, rol="admin", connected=True, auth_error=ErrorConexionBaseDeDatos("down"))
    desconexion = {"ok": False}
    monkeypatch.setattr(app, "_manejar_desconexion", lambda: desconexion.__setitem__("ok", True))
    monkeypatch.setattr(app, "_mostrar_dialogo_espera_admin", lambda: None)
    monkeypatch.setattr(app, "_cerrar_dialogo_espera_admin", lambda: None)
    monkeypatch.setattr(app, "after", lambda _ms, cb=None: cb() if cb else None)

    try:
        app._abrir_ventana_administracion()
        assert desconexion["ok"] is True
        assert warnings
        assert warnings[0][0] == "Sin conexión"
    finally:
        app.destroy()
