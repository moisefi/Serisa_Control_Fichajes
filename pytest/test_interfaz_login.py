from __future__ import annotations

from types import SimpleNamespace
import tkinter as tk

import pytest
from interfaz.ventana_login import VentanaLogin


class LoggerFake:
    def __init__(self):
        self.warnings = []
        self.exceptions = []

    def warning(self, msg):
        self.warnings.append(msg)

    def exception(self, msg):
        self.exceptions.append(msg)


class ServicioConexionFake:
    def __init__(self):
        self.configuracion = SimpleNamespace(hostname_raspberry="rpi-fichajes", ip_bd="192.168.1.20")
        self.activa = True
        self.desconectado = False
        self.ip_conectada = None

    def verificar_conexion_activa(self):
        return self.activa

    def desconectar(self):
        self.desconectado = True

    def conectar_a_ip(self, ip):
        self.ip_conectada = ip
        return

    def buscar_ip(self):
        return "192.168.1.20"


class ServicioAuthFake:
    def __init__(self, usuario=None):
        self.usuario = usuario

    def autenticar(self, _username, _password):
        return self.usuario


@pytest.fixture(autouse=True)
def _skip_si_tk_no_disponible():
    try:
        root = tk.Tk()
        root.destroy()
    except tk.TclError:
        pytest.skip("Tkinter no disponible en este entorno de pruebas")


def _build_login(monkeypatch, servicio_auth=None, servicio_conexion=None):
    # Evita auto inicialización asíncrona durante el test.
    monkeypatch.setattr(VentanaLogin, "after", lambda self, _ms, _cb=None: None)
    try:
        login = VentanaLogin(
            servicio_autenticacion=servicio_auth or ServicioAuthFake(),
            servicio_conexion=servicio_conexion or ServicioConexionFake(),
            logger=LoggerFake(),
        )
    except tk.TclError:
        pytest.skip("Tkinter/Tcl no disponible en este entorno de pruebas")
    login.withdraw()
    return login


def test_login_warn_si_no_hay_conexion(monkeypatch):
    llamados = []
    monkeypatch.setattr("interfaz.ventana_login.messagebox.showwarning", lambda *args, **kwargs: llamados.append(args))
    login = _build_login(monkeypatch)
    try:
        login.conexion_ok = False
        login._iniciar_sesion()
        assert llamados
        assert llamados[0][0] == "Sin conexión"
    finally:
        login.destroy()


def test_login_warn_si_faltan_campos(monkeypatch):
    llamados = []
    monkeypatch.setattr("interfaz.ventana_login.messagebox.showwarning", lambda *args, **kwargs: llamados.append(args))
    login = _build_login(monkeypatch)
    try:
        login.conexion_ok = True
        login.var_usuario.set("")
        login.var_password.set("")
        login._iniciar_sesion()
        assert llamados
        assert llamados[0][0] == "Campos obligatorios"
    finally:
        login.destroy()


def test_login_error_si_credenciales_incorrectas(monkeypatch):
    errores = []
    monkeypatch.setattr("interfaz.ventana_login.messagebox.showerror", lambda *args, **kwargs: errores.append(args))
    login = _build_login(monkeypatch, servicio_auth=ServicioAuthFake(usuario=None))
    try:
        login.conexion_ok = True
        login.var_usuario.set("admin")
        login.var_password.set("bad")
        login._iniciar_sesion()
        assert errores
        assert errores[0][0] == "Acceso denegado"
        assert login.var_password.get() == ""
    finally:
        login.destroy()


def test_login_ok_crea_sesion(monkeypatch):
    usuario = {"id": 1, "username": "admin", "rol": "admin", "usuario_rfid": None}
    login = _build_login(monkeypatch, servicio_auth=ServicioAuthFake(usuario=usuario))
    destruida = {"ok": False}
    monkeypatch.setattr(login, "destroy", lambda: destruida.__setitem__("ok", True))
    try:
        login.conexion_ok = True
        login.var_usuario.set("admin")
        login.var_password.set("admin")
        login._iniciar_sesion()
        assert login.sesion is not None
        assert login.sesion.username == "admin"
        assert destruida["ok"] is True
    finally:
        try:
            login.destroy()
        except Exception:
            pass


def test_conectar_por_ip_manual_rechaza_ip_invalida(monkeypatch):
    errores = []
    servicio_conexion = ServicioConexionFake()
    monkeypatch.setattr("interfaz.ventana_login.messagebox.showerror", lambda *args, **kwargs: errores.append(args))
    login = _build_login(monkeypatch, servicio_conexion=servicio_conexion)
    try:
        login.var_ip_manual.set("999.999.999.999")
        login._conectar_por_ip_manual()

        assert errores
        assert errores[0][0] == "IP inválida"
        assert servicio_conexion.ip_conectada is None
    finally:
        login.destroy()
