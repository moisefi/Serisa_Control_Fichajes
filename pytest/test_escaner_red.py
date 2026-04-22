from __future__ import annotations

import socket

from infraestructura.escaner_red import EscanerRed


def test_resolver_ip_ok(monkeypatch):
    esc = EscanerRed(nombre_host="rpi")
    monkeypatch.setattr(socket, "gethostbyname", lambda _h: "192.168.1.10")
    assert esc.resolver_ip_por_hostname() == "192.168.1.10"


def test_resolver_ip_falla(monkeypatch):
    esc = EscanerRed(nombre_host="rpi")

    def _raise(_h):
        raise socket.gaierror()

    monkeypatch.setattr(socket, "gethostbyname", _raise)
    assert esc.resolver_ip_por_hostname() is None


class SocketFake:
    def __init__(self, connect_ex_result=0, raises=False):
        self.connect_ex_result = connect_ex_result
        self.raises = raises
        self.closed = False

    def settimeout(self, _timeout):
        return

    def connect_ex(self, _addr):
        if self.raises:
            raise RuntimeError("socket error")
        return self.connect_ex_result

    def close(self):
        self.closed = True


def test_comprobar_puerto_abierto_true(monkeypatch):
    fake = SocketFake(connect_ex_result=0)
    monkeypatch.setattr(socket, "socket", lambda *_args, **_kwargs: fake)
    esc = EscanerRed(puerto_bd=5432)
    assert esc.comprobar_puerto_abierto("1.1.1.1") is True
    assert fake.closed is True


def test_comprobar_puerto_abierto_false_por_exception(monkeypatch):
    fake = SocketFake(raises=True)
    monkeypatch.setattr(socket, "socket", lambda *_args, **_kwargs: fake)
    esc = EscanerRed(puerto_bd=5432)
    assert esc.comprobar_puerto_abierto("1.1.1.1") is False
    assert fake.closed is True


def test_buscar_ip_raspberry_retorna_none_si_no_resuelve(monkeypatch):
    esc = EscanerRed()
    monkeypatch.setattr(esc, "resolver_ip_por_hostname", lambda: None)
    assert esc.buscar_ip_raspberry() is None

