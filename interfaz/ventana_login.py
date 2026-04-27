from __future__ import annotations

import ipaddress
import os
import socket
import tkinter as tk
from dataclasses import dataclass
from tkinter import font, messagebox, ttk
from errores import ErrorConexionBaseDeDatos
from rutas import obtener_directorio_base, obtener_recurso

@dataclass(slots=True)
class SesionUsuario:
    id_usuario: int
    username: str
    rol: str
    usuario_rfid: str | None = None


class VentanaLogin(tk.Tk):
    def __init__(self, servicio_autenticacion, servicio_conexion, logger) -> None:
        super().__init__()

        self.servicio_autenticacion = servicio_autenticacion
        self.servicio_conexion = servicio_conexion
        self.logger = logger

        self.sesion: SesionUsuario | None = None
        self.conexion_ok = False
        self.icono_ventana = None
        self.base_dir = str(obtener_directorio_base())

        self.title("Inicio de sesión")
        self.geometry("640x560")
        self.minsize(640, 560)
        self.resizable(False, False)
        self.configure(bg="#eef3f8")

        self.var_usuario = tk.StringVar()
        self.var_password = tk.StringVar()
        self.var_hostname = tk.StringVar(
            value=getattr(self.servicio_conexion.configuracion, "hostname_raspberry", "") or ""
        )
        self.var_ip_manual = tk.StringVar(
            value=getattr(self.servicio_conexion.configuracion, "ip_bd", "") or ""
        )
        self.var_estado_conexion = tk.StringVar(value="Comprobando conexión con la base de datos...")

        self._crear_estilos()
        self._configurar_icono_ventana()
        self._crear_interfaz()
        self._centrar_ventana()

        self.protocol("WM_DELETE_WINDOW", self._cancelar)
        self.after(100, self._inicializar_ventana)

    # =========================
    # ESTILOS
    # =========================
    def _crear_estilos(self) -> None:
        self.fuente_base = font.nametofont("TkDefaultFont").copy()
        self.fuente_base.configure(size=10)

        self.fuente_texto = font.nametofont("TkTextFont").copy()
        self.fuente_texto.configure(size=10)

        self.fuente_titulo = font.nametofont("TkHeadingFont").copy()
        self.fuente_titulo.configure(size=18, weight="bold")

        self.fuente_estado = font.nametofont("TkDefaultFont").copy()
        self.fuente_estado.configure(size=10, weight="bold")

        estilo = ttk.Style(self)
        try:
            if "clam" in estilo.theme_names():
                estilo.theme_use("clam")
        except Exception:
            pass

        estilo.configure("App.TFrame", background="#eef3f8")
        estilo.configure("Card.TFrame", background="#ffffff")

        estilo.configure(
            "Title.TLabel",
            background="#ffffff",
            foreground="#132238",
            font=self.fuente_titulo,
        )
        estilo.configure(
            "Subtitle.TLabel",
            background="#ffffff",
            foreground="#5f6b7a",
            font=self.fuente_texto,
        )
        estilo.configure(
            "Field.TLabel",
            background="#ffffff",
            foreground="#1f2937",
            font=self.fuente_base,
        )
        estilo.configure(
            "StatusOk.TLabel",
            background="#ffffff",
            foreground="#0f766e",
            font=self.fuente_estado,
        )
        estilo.configure(
            "StatusError.TLabel",
            background="#ffffff",
            foreground="#b42318",
            font=self.fuente_estado,
        )
        estilo.configure(
            "Section.TLabelframe",
            background="#ffffff",
            borderwidth=1,
            relief="solid",
        )
        estilo.configure(
            "Section.TLabelframe.Label",
            background="#ffffff",
            foreground="#344054",
            font=self.fuente_base,
        )
        estilo.configure(
            "Primary.TButton",
            font=self.fuente_base,
            padding=(18, 10),
        )

    def _configurar_icono_ventana(self) -> None:
        try:
            ruta_logo = str(obtener_recurso("imagenes", "logo_serisa.png"))
            if os.path.exists(ruta_logo):
                self.icono_ventana = tk.PhotoImage(file=ruta_logo)
                self.iconphoto(True, self.icono_ventana)
        except Exception as e:
            self.logger.warning(f"No se pudo cargar el icono de la ventana: {e}")

    def _centrar_ventana(self) -> None:
        self.update_idletasks()
        ancho = self.winfo_width()
        alto = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.winfo_screenheight() // 2) - (alto // 2)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    # =========================
    # UI
    # =========================
    def _crear_interfaz(self) -> None:
        contenedor = ttk.Frame(self, style="App.TFrame", padding=28)
        contenedor.pack(fill="both", expand=True)

        self.tarjeta = ttk.Frame(contenedor, style="Card.TFrame", padding=28)
        self.tarjeta.pack(expand=True, fill="both", padx=40, pady=28)

        cabecera = ttk.Frame(self.tarjeta, style="Card.TFrame")
        cabecera.pack(fill="x", pady=(0, 18))

        ttk.Label(
            cabecera,
            text="Acceso a la aplicación",
            style="Title.TLabel",
        ).pack(anchor="center")

        ttk.Label(
            cabecera,
            text="Introduce tus credenciales para continuar",
            style="Subtitle.TLabel",
        ).pack(anchor="center", pady=(8, 0))

        self.label_estado = ttk.Label(
            self.tarjeta,
            textvariable=self.var_estado_conexion,
            style="Subtitle.TLabel",
            justify="center",
            anchor="center",
        )
        self.label_estado.pack(fill="x", pady=(0, 18))

        self.frame_conexion = ttk.LabelFrame(
            self.tarjeta,
            text="Conexión con la base de datos",
            style="Section.TLabelframe",
            padding=16,
        )

        ttk.Label(
            self.frame_conexion,
            text="No se ha podido conectar automáticamente. Puedes reintentar o indicar un hostname o una IP manualmente.",
            style="Subtitle.TLabel",
            wraplength=500,
            justify="left",
        ).pack(anchor="w", fill="x", pady=(0, 14))

        fila_auto = ttk.Frame(self.frame_conexion, style="Card.TFrame")
        fila_auto.pack(fill="x", pady=(0, 14))

        ttk.Button(
            fila_auto,
            text="Reintentar conexión automática",
            command=self._reintentar_conexion_automatica,
        ).pack(anchor="w")

        fila_host = ttk.Frame(self.frame_conexion, style="Card.TFrame")
        fila_host.pack(fill="x", pady=(0, 12))

        ttk.Label(fila_host, text="Hostname", style="Field.TLabel").pack(anchor="w")
        ttk.Entry(
            fila_host,
            textvariable=self.var_hostname,
        ).pack(fill="x", pady=(6, 8), ipady=4)

        ttk.Button(
            fila_host,
            text="Conectar por hostname",
            command=self._conectar_por_hostname,
        ).pack(anchor="e")

        fila_ip = ttk.Frame(self.frame_conexion, style="Card.TFrame")
        fila_ip.pack(fill="x")

        ttk.Label(fila_ip, text="IP", style="Field.TLabel").pack(anchor="w")
        ttk.Entry(
            fila_ip,
            textvariable=self.var_ip_manual,
        ).pack(fill="x", pady=(6, 8), ipady=4)

        ttk.Button(
            fila_ip,
            text="Conectar por IP",
            command=self._conectar_por_ip_manual,
        ).pack(anchor="e")

        self.frame_login = ttk.Frame(self.tarjeta, style="Card.TFrame")
        self.frame_login.pack(fill="x", pady=(0, 0))

        ttk.Label(self.frame_login, text="Usuario", style="Field.TLabel").pack(anchor="w")
        self.entry_usuario = ttk.Entry(self.frame_login, textvariable=self.var_usuario)
        self.entry_usuario.pack(fill="x", pady=(6, 14), ipady=5)

        ttk.Label(self.frame_login, text="Contraseña", style="Field.TLabel").pack(anchor="w")
        self.entry_password = ttk.Entry(
            self.frame_login,
            textvariable=self.var_password,
            show="*",
        )
        self.entry_password.pack(fill="x", pady=(6, 20), ipady=5)

        botonera = ttk.Frame(self.frame_login, style="Card.TFrame")
        botonera.pack(fill="x", pady=(4, 0))

        ttk.Button(
            botonera,
            text="Cancelar",
            command=self._cancelar,
        ).pack(side="right")

        self.boton_entrar = ttk.Button(
            botonera,
            text="Entrar",
            style="Primary.TButton",
            command=self._iniciar_sesion,
        )
        self.boton_entrar.pack(side="right", padx=(0, 10))

        self.bind("<Return>", lambda e: self._iniciar_sesion())
        self.bind("<Escape>", lambda e: self._cancelar())

    # =========================
    # CONEXIÓN
    # =========================
    def _inicializar_ventana(self) -> None:
        self._bloquear_login()
        self._ocultar_bloque_conexion()
        self.var_estado_conexion.set("Comprobando conexión con la base de datos...")
        self.label_estado.configure(style="Subtitle.TLabel")
        self.update_idletasks()
        self._intentar_conexion_automatica()

    def _intentar_conexion_automatica(self) -> None:
        if self.servicio_conexion.verificar_conexion_activa():
            self._conexion_ok()
            return

        ip_guardada = getattr(self.servicio_conexion.configuracion, "ip_bd", None)
        if ip_guardada:
            try:
                self.servicio_conexion.conectar_a_ip(ip_guardada)
                self._conexion_ok(ip_guardada)
                return
            except Exception as e:
                self.logger.warning(f"Fallo IP guardada: {e}")

        try:
            ip = self.servicio_conexion.buscar_ip()
            if ip:
                self.servicio_conexion.conectar_a_ip(ip)
                self._conexion_ok(ip)
                return
        except Exception as e:
            self.logger.warning(f"Fallo búsqueda automática: {e}")

        self._conexion_error("No se ha podido establecer la conexión automáticamente.")

    def _reintentar_conexion_automatica(self) -> None:
        try:
            if self.servicio_conexion.verificar_conexion_activa():
                self.servicio_conexion.desconectar()
        except Exception:
            pass

        self.var_estado_conexion.set("Reintentando conexión con la base de datos...")
        self.label_estado.configure(style="Subtitle.TLabel")
        self.update_idletasks()
        self._intentar_conexion_automatica()

    def _conectar_por_hostname(self) -> None:
        hostname = self.var_hostname.get().strip()
        if not hostname:
            messagebox.showwarning("Dato obligatorio", "Introduce un hostname.")
            return

        self.var_estado_conexion.set(f"Resolviendo hostname {hostname}...")
        self.label_estado.configure(style="Subtitle.TLabel")
        self.update_idletasks()

        try:
            ip = socket.gethostbyname(hostname)
            self.var_ip_manual.set(ip)
            self.servicio_conexion.conectar_a_ip(ip)
            self._conexion_ok(ip)
        except Exception as e:
            self._conexion_error(f"No se pudo conectar usando el hostname.\n\n{e}")

    def _conectar_por_ip_manual(self) -> None:
        ip = self.var_ip_manual.get().strip()
        if not ip:
            messagebox.showwarning("Dato obligatorio", "Introduce una IP.")
            return
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            messagebox.showerror("IP inválida", "Introduce una dirección IP válida (ej: 192.168.1.10)")
            return

        self.var_estado_conexion.set(f"Conectando con {ip}...")
        self.label_estado.configure(style="Subtitle.TLabel")
        self.update_idletasks()

        try:
            self.servicio_conexion.conectar_a_ip(ip)
            self._conexion_ok(ip)
        except Exception as e:
            self._conexion_error(f"No se pudo conectar usando la IP indicada.\n\n{e}")

    def _conexion_ok(self, ip: str | None = None) -> None:
        self.conexion_ok = True

        texto = "Conexión establecida correctamente"
        if ip:
            texto += f"\n{ip}"

        self.var_estado_conexion.set(texto)
        self.label_estado.configure(style="StatusOk.TLabel")
        self._ocultar_bloque_conexion()
        self._desbloquear_login()
        self._redimensionar_ventana(640, 560)
        self.entry_usuario.focus_set()

    def _conexion_error(self, detalle: str | None = None) -> None:
        self.conexion_ok = False
        self.var_estado_conexion.set("No se ha podido conectar con la base de datos")
        self.label_estado.configure(style="StatusError.TLabel")
        self._bloquear_login()
        self._mostrar_bloque_conexion()
        self._redimensionar_ventana(900, 900)
        self.var_password.set("")

        if detalle:
            self.logger.warning(detalle)

    def _bloquear_login(self) -> None:
        self.entry_usuario.config(state="disabled")
        self.entry_password.config(state="disabled")
        self.boton_entrar.config(state="disabled")

    def _desbloquear_login(self) -> None:
        self.entry_usuario.config(state="normal")
        self.entry_password.config(state="normal")
        self.boton_entrar.config(state="normal")

    def _mostrar_bloque_conexion(self) -> None:
        if not self.frame_conexion.winfo_ismapped():
            self.frame_conexion.pack(fill="x", pady=(0, 18), before=self.frame_login)

    def _ocultar_bloque_conexion(self) -> None:
        if self.frame_conexion.winfo_ismapped():
            self.frame_conexion.pack_forget()

    # =========================
    # LOGIN
    # =========================
    def _iniciar_sesion(self) -> None:
        if not self.conexion_ok:
            messagebox.showwarning("Sin conexión", "Debes conectarte primero a la base de datos.")
            return

        username = self.var_usuario.get().strip()
        password = self.var_password.get()

        if not username or not password:
            messagebox.showwarning("Campos obligatorios", "Debes introducir usuario y contraseña.")
            return

        try:

            if not self.servicio_conexion.verificar_conexion_activa():
                self._manejar_conexion_perdida()
                return

            usuario = self.servicio_autenticacion.autenticar(username, password)

            if usuario is None:
                messagebox.showerror("Acceso denegado", "Usuario o contraseña incorrectos.")
                self.var_password.set("")
                self.entry_password.focus_set()
                return

            self.sesion = SesionUsuario(
                id_usuario=usuario["id"],
                username=usuario["username"],
                rol=usuario["rol"],
                usuario_rfid=usuario.get("usuario_rfid"),
            )
            self.destroy()

        except ErrorConexionBaseDeDatos as e:
            self.logger.warning(f"Fallo de conexión durante el login: {e}")
            self._manejar_conexion_perdida(str(e))

        except Exception as e:
            self.logger.exception("Error en login")
            messagebox.showerror("Error", str(e))

    def _cancelar(self) -> None:
        self.sesion = None
        self.destroy()

    def mostrar(self) -> SesionUsuario | None:
        self.mainloop()
        return self.sesion

    def _redimensionar_ventana(self, ancho: int, alto: int) -> None:
        self.update_idletasks()

        x = (self.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.winfo_screenheight() // 2) - (alto // 2)

        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    def _manejar_conexion_perdida(self, detalle: str | None = None) -> None:
        self.conexion_ok = False

        self.var_estado_conexion.set("Se ha perdido la conexión con la base de datos")
        self.label_estado.configure(style="StatusError.TLabel")

        self._bloquear_login()
        self._mostrar_bloque_conexion()
        self._redimensionar_ventana(900, 900)

        self.var_password.set("")

        try:
            if self.servicio_conexion.verificar_conexion_activa():
                self.servicio_conexion.desconectar()
        except Exception:
            pass

        if detalle:
            self.logger.warning(f"Conexión perdida en login: {detalle}")

        messagebox.showwarning(
            "Conexión perdida",
            "Se ha perdido la conexión con la base de datos.\n"
            "Vuelve a conectarte para continuar."
        )
