from __future__ import annotations

import ipaddress
import os
import threading
import tkinter as tk
from datetime import datetime
from tkinter import font as tkfont
from tkinter import messagebox, simpledialog, ttk

from PIL import Image, ImageTk
from tkcalendar import DateEntry

from configuracion import ConfiguracionAplicacion
from errores import ErrorConexionBaseDeDatos
from interfaz.ventana_administracion import VentanaAdministracion
from rutas import obtener_directorio_base, obtener_recurso
from interfaz.ventana_exportacion import VentanaExportacion
from servicios.servicio_conexion import ServicioConexion
from servicios.servicio_fichajes import FiltrosRegistros, ServicioFichajes


class VentanaPrincipal(tk.Tk):
    def __init__(
        self,
        configuracion: ConfiguracionAplicacion,
        servicio_conexion: ServicioConexion,
        servicio_fichajes: ServicioFichajes,
        servicio_autenticacion,
        logger,
        sesion=None,
    ) -> None:
        super().__init__()
        self.configuracion = configuracion
        self.servicio_conexion = servicio_conexion
        self.servicio_fichajes = servicio_fichajes
        self.servicio_autenticacion = servicio_autenticacion
        self.logger = logger
        self.sesion = sesion

        self.base_dir = str(obtener_directorio_base())
        self.lock_bd = threading.Lock()
        self.resultado_cierre = "salir"

        self._inicializar_estado()
        self._configurar_ventana()
        self._crear_estilos()
        self._configurar_icono_ventana()
        self._crear_interfaz()
        if self._es_basic():
            self.resumen_usuarios.set(self._obtener_nombre_usuario_basic())
            self.resumen_tarjetas.set("Sin sincronizar")

        self.protocol("WM_DELETE_WINDOW", self._gestionar_cierre_ventana)

        if self._puede_ver_conexion():
            self.after(200, self._intentar_conexion_inicial)
        else:
            self.after(200, self._inicializar_sin_panel_conexion)

    # =========================
    # INICIALIZACIÓN
    # =========================
    def _inicializar_estado(self) -> None:
        self.estado_conexion = tk.StringVar(value="Desconectado")
        self.ip_base_datos = tk.StringVar(value="Sin conexión")
        self.estado_tabla = tk.StringVar(value="Listo")

        self.var_nombre_usuario = tk.StringVar()
        self.var_uid_tarjeta = tk.StringVar()
        self.var_uid_baja = tk.StringVar()
        self.var_filtro_usuario = tk.StringVar()
        self.var_filtro_uid = tk.StringVar()
        self.var_filtro_tipo = tk.StringVar()

        self.resumen_registros = tk.StringVar(value="0")
        self.resumen_usuarios = tk.StringVar(value="0")
        self.resumen_tarjetas = tk.StringVar(value="0")
        self.resumen_actualizacion = tk.StringVar(value="Sin sincronizar")

        self.lista_usuarios: list[str] = []
        self.lista_uid: list[str] = []
        self.mapa_baja_usuario: dict[str, str] = {}

        self.fecha_desde_filtro = None
        self.fecha_hasta_filtro = None
        self.id_after_refresco = None
        self.editor_tabla_activo = None
        self.token_carga_tabla = 0

        self.marco_acciones_conexion: ttk.Frame | None = None
        self.tabla_registros: ttk.Treeview | None = None
        self.combo_uid_alta: ttk.Combobox | None = None
        self.combo_uid_baja: ttk.Combobox | None = None
        self.combo_filtro_usuario: ttk.Combobox | None = None
        self.combo_filtro_uid: ttk.Combobox | None = None
        self.combo_filtro_tipo: ttk.Combobox | None = None
        self.etiqueta_resumen_fechas: ttk.Label | None = None
        self.etiqueta_estado: ttk.Label | None = None
        self.etiqueta_estado_tabla: ttk.Label | None = None
        self.boton_buscar: ttk.Button | None = None
        self.boton_ip_manual: ttk.Button | None = None

        self.icono_refrescar = None
        self.icono_ventana = None
        self.icono_calendario = None
        self.apertura_admin_en_progreso = False
        self.dialogo_espera_admin: tk.Toplevel | None = None

    def _configurar_ventana(self) -> None:
        self.title("SERISA · Gestión de fichajes")
        self.geometry("1360x1000")
        self.minsize(1240, 860)
        self.configure(bg="#eef3f8")

    # =========================
    # ROLES
    # =========================
    def _rol_actual(self) -> str:
        if not self.sesion:
            return ""
        return getattr(self.sesion, "rol", "").strip().lower()

    def _es_admin(self) -> bool:
        return self._rol_actual() == "admin"

    def _es_rrhh(self) -> bool:
        return self._rol_actual() == "rrhh"

    def _es_basic(self) -> bool:
        return self._rol_actual() == "basic"

    def _puede_gestionar_rfid(self) -> bool:
        return self._rol_actual() in {"rrhh", "admin"}

    def _puede_exportar(self) -> bool:
        return self._rol_actual() in {"rrhh", "admin"}

    def _puede_ver_conexion(self) -> bool:
        return self._rol_actual() in {"rrhh", "admin"}

    def _puede_editar_registros(self) -> bool:
        return self._rol_actual() in {"rrhh", "admin"}

    # =========================
    # ESTILOS / VENTANA
    # =========================
    def _configurar_icono_ventana(self) -> None:
        try:
            ruta_logo = str(obtener_recurso("imagenes", "logo_serisa.png"))
            if os.path.exists(ruta_logo):
                self.icono_ventana = tk.PhotoImage(file=ruta_logo)
                self.iconphoto(True, self.icono_ventana)
        except Exception as e:
            self.logger.warning(f"No se pudo cargar el icono de la ventana: {e}")

    def _crear_estilos(self) -> None:
        estilo = ttk.Style(self)
        try:
            if "clam" in estilo.theme_names():
                estilo.theme_use("clam")
        except Exception:
            pass

        fondo = "#eef3f8"
        superficie = "#ffffff"
        primario = "#0c4f8a"
        primario_hover = "#0a416f"
        secundario = "#e8f1fb"
        borde = "#d9e2ec"
        texto = "#1f2937"
        texto_suave = "#64748b"
        exito = "#1d7f49"
        error = "#b42318"

        self.colores = {
            "fondo": fondo,
            "superficie": superficie,
            "primario": primario,
            "primario_hover": primario_hover,
            "secundario": secundario,
            "borde": borde,
            "texto": texto,
            "texto_suave": texto_suave,
            "exito": exito,
            "error": error,
        }

        fuente_base = tkfont.nametofont("TkDefaultFont").copy()
        fuente_base.configure(size=10)

        fuente_small = tkfont.nametofont("TkDefaultFont").copy()
        fuente_small.configure(size=9)

        fuente_heading = tkfont.nametofont("TkHeadingFont").copy()
        fuente_heading.configure(size=16, weight="bold")

        fuente_bold = tkfont.nametofont("TkDefaultFont").copy()
        fuente_bold.configure(size=10, weight="bold")

        fuente_estado = tkfont.nametofont("TkDefaultFont").copy()
        fuente_estado.configure(size=11, weight="bold")

        self.option_add("*Font", fuente_base)
        self.option_add("*TCombobox*Listbox.font", fuente_base)

        estilo.configure("TFrame", background=fondo)
        estilo.configure("Card.TFrame", background=superficie, relief="flat")
        estilo.configure("TLabelframe", background=superficie, borderwidth=1, relief="solid")
        estilo.configure(
            "TLabelframe.Label",
            background=superficie,
            foreground=texto,
            font=fuente_bold,
        )

        estilo.configure("TLabel", background=fondo, foreground=texto, font=fuente_base)
        estilo.configure("Card.TLabel", background=superficie, foreground=texto, font=fuente_base)

        estilo.configure("HeroTitle.TLabel", background=fondo, foreground=texto, font=fuente_heading)
        estilo.configure("HeroSub.TLabel", background=fondo, foreground=texto_suave, font=fuente_base)
        estilo.configure("SectionTitle.TLabel", background=superficie, foreground=texto, font=fuente_bold)
        estilo.configure("Muted.TLabel", background=superficie, foreground=texto_suave, font=fuente_base)
        estilo.configure(
            "Chip.TLabel",
            background=secundario,
            foreground=primario,
            font=fuente_small,
            padding=(8, 4),
        )
        estilo.configure("MetricValue.TLabel", background=superficie, foreground=texto, font=fuente_heading)
        estilo.configure("MetricLabel.TLabel", background=superficie, foreground=texto_suave, font=fuente_small)
        estilo.configure("Cabecera.TLabel", background=superficie, foreground=texto_suave, font=fuente_bold)
        estilo.configure("EstadoConectado.TLabel", background=superficie, foreground=exito, font=fuente_estado)
        estilo.configure("EstadoDesconectado.TLabel", background=superficie, foreground=error, font=fuente_estado)

        estilo.configure(
            "Primary.TButton",
            font=fuente_bold,
            padding=(14, 10),
            background=primario,
            foreground="white",
            borderwidth=0,
            focusthickness=0,
        )
        estilo.map(
            "Primary.TButton",
            background=[("active", primario_hover), ("disabled", "#bfcad6")],
            foreground=[("disabled", "#ffffff")],
        )

        estilo.configure(
            "Secondary.TButton",
            font=fuente_base,
            padding=(12, 9),
            background=superficie,
            foreground=texto,
            borderwidth=1,
            relief="solid",
        )
        estilo.map("Secondary.TButton", background=[("active", secundario)])

        estilo.configure(
            "IconOnly.TButton",
            padding=(2, 2),
            background=superficie,
            foreground=texto,
            borderwidth=1,
            relief="solid",
        )
        estilo.map("IconOnly.TButton", background=[("active", secundario)])

        estilo.configure(
            "Accent.TButton",
            font=fuente_bold,
            padding=(12, 12),
            background=secundario,
            foreground=primario,
            borderwidth=0,
        )
        estilo.map("Accent.TButton", background=[("active", "#d7e9fb")])

        estilo.configure("TEntry", fieldbackground=superficie, bordercolor=borde, lightcolor=borde, padding=6)
        estilo.configure("TCombobox", fieldbackground=superficie, background=superficie, padding=5)

        estilo.configure(
            "Treeview",
            background=superficie,
            fieldbackground=superficie,
            foreground=texto,
            rowheight=34,
            bordercolor=borde,
            borderwidth=1,
            font=fuente_base,
        )
        estilo.configure(
            "Treeview.Heading",
            background=secundario,
            foreground=texto,
            font=fuente_bold,
            relief="flat",
            padding=(8, 8),
        )
        estilo.map("Treeview.Heading", background=[("active", "#dceaf8")])

    # =========================
    # INTERFAZ
    # =========================
    def _inicializar_sin_panel_conexion(self) -> None:
        try:
            self.actualizar_tabla_registros()
            self._programar_actualizacion_periodica()
        except Exception:
            self.logger.exception("Error al inicializar la aplicación sin panel de conexión")

    def _crear_interfaz(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)

        self._crear_cabecera()

        cuerpo = ttk.Frame(self, padding=(16, 0, 16, 16))
        cuerpo.grid(row=1, column=0, sticky="nsew")

        if self._es_basic():
            cuerpo.columnconfigure(0, weight=1)
            cuerpo.rowconfigure(0, weight=1)

            panel_principal = ttk.Frame(cuerpo)
            panel_principal.grid(row=0, column=0, sticky="nsew")
            panel_principal.columnconfigure(0, weight=1)
            panel_principal.rowconfigure(0, weight=1)

            self._crear_zona_registros(panel_principal)
            return

        cuerpo.columnconfigure(0, weight=0, minsize=440)
        cuerpo.columnconfigure(1, weight=1)
        cuerpo.rowconfigure(0, weight=1)

        panel_lateral = ttk.Frame(cuerpo)
        panel_lateral.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        panel_lateral.columnconfigure(0, weight=1)

        panel_principal = ttk.Frame(cuerpo)
        panel_principal.grid(row=0, column=1, sticky="nsew")
        panel_principal.columnconfigure(0, weight=1)
        panel_principal.rowconfigure(0, weight=1)

        fila_lateral = 0
        if self._puede_gestionar_rfid():
            self._crear_zona_usuarios(panel_lateral, fila_lateral)
            fila_lateral += 1
        if self._puede_exportar():
            self._crear_zona_exportaciones(panel_lateral, fila_lateral)
            fila_lateral += 1
        if self._puede_ver_conexion():
            self._crear_zona_conexion(panel_lateral, fila_lateral)

        self._crear_zona_registros(panel_principal)

    def _crear_cabecera(self) -> None:
        cabecera = ttk.Frame(self, padding=(16, 14, 16, 12))
        cabecera.grid(row=0, column=0, sticky="ew")
        cabecera.columnconfigure(0, weight=1)

        fila_superior = ttk.Frame(cabecera)
        fila_superior.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        fila_superior.columnconfigure(0, weight=1)

        if self._es_admin():
            ttk.Button(
                fila_superior,
                text="Administración",
                command=self._abrir_ventana_administracion,
                style="Secondary.TButton",
            ).grid(row=0, column=0, sticky="w")

        resumen = ttk.Frame(cabecera)
        resumen.grid(row=1, column=0, sticky="ew")
        for i in range(4):
            resumen.columnconfigure(i, weight=1)

        titulo_resumen_usuario = "Usuario" if self._es_basic() else "Usuarios activos"
        titulo_resumen_tarjeta = "Nº Tarjeta" if self._es_basic() else "Tarjetas libres"

        self._crear_tarjeta_resumen(resumen, 0, "Registros visibles", self.resumen_registros)
        self._crear_tarjeta_resumen(resumen, 1, titulo_resumen_usuario, self.resumen_usuarios)
        self._crear_tarjeta_resumen(resumen, 2, titulo_resumen_tarjeta, self.resumen_tarjetas)
        self._crear_tarjeta_resumen(resumen, 3, "Última sincronización", self.resumen_actualizacion)

    def _crear_tarjeta_resumen(
        self,
        contenedor: ttk.Frame,
        columna: int,
        titulo: str,
        variable: tk.StringVar,
    ) -> None:
        tarjeta = ttk.Frame(contenedor, style="Card.TFrame", padding=16)
        tarjeta.grid(row=0, column=columna, sticky="nsew", padx=(0, 10) if columna < 3 else (0, 0))
        tarjeta.columnconfigure(0, weight=1)

        ttk.Label(tarjeta, text=titulo, style="MetricLabel.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(tarjeta, textvariable=variable, style="MetricValue.TLabel").grid(row=1, column=0, sticky="w", pady=(8, 0))

    def _crear_zona_usuarios(self, contenedor: ttk.Frame, fila: int) -> None:
        marco = ttk.LabelFrame(contenedor, text="Gestión de usuarios", padding=16)
        marco.grid(row=fila, column=0, sticky="ew", pady=(0, 12))
        marco.columnconfigure(0, weight=1)

        ttk.Label(
            marco,
            text="Asigna tarjetas nuevas y da de baja usuarios desde el mismo panel.",
            style="Muted.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        sub_alta = ttk.LabelFrame(marco, text="Alta de usuario", padding=14)
        sub_alta.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        sub_alta.columnconfigure(0, weight=0)
        sub_alta.columnconfigure(1, weight=1)

        ttk.Label(sub_alta, text="Nombre completo", style="Card.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 6))
        ttk.Entry(sub_alta, textvariable=self.var_nombre_usuario).grid(row=0, column=1, sticky="ew", pady=(0, 6))

        ttk.Label(sub_alta, text="Tarjeta RFID", style="Card.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(0, 10))
        self.combo_uid_alta = ttk.Combobox(sub_alta, textvariable=self.var_uid_tarjeta, state="normal")
        self.combo_uid_alta.grid(row=1, column=1, sticky="ew", pady=(0, 10))

        ttk.Button(
            sub_alta,
            text="Registrar usuario",
            command=self.registrar_usuario,
            style="Primary.TButton",
        ).grid(row=2, column=0, columnspan=2, sticky="ew")

        sub_baja = ttk.LabelFrame(marco, text="Baja de usuario", padding=14)
        sub_baja.grid(row=2, column=0, sticky="ew")
        sub_baja.columnconfigure(0, weight=0)
        sub_baja.columnconfigure(1, weight=1)

        ttk.Label(sub_baja, text="Selecciona usuario", style="Card.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 10))
        self.combo_uid_baja = ttk.Combobox(sub_baja, textvariable=self.var_uid_baja, state="readonly")
        self.combo_uid_baja.grid(row=0, column=1, sticky="ew", pady=(0, 10))

        ttk.Button(
            sub_baja,
            text="Dar de baja",
            command=self.dar_baja_usuario,
            style="Secondary.TButton",
        ).grid(row=1, column=0, columnspan=2, sticky="ew")

    def _crear_zona_exportaciones(self, contenedor: ttk.Frame, fila: int) -> None:
        marco = ttk.LabelFrame(contenedor, text="Exportaciones", padding=16)
        marco.grid(row=fila, column=0, sticky="ew", pady=(0, 12))
        marco.columnconfigure(0, weight=1)

        ttk.Label(
            marco,
            text="Genera informes filtrados para entregar al instante en Excel o PDF.",
            style="Muted.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        ttk.Button(marco, text="Exportar a Excel", command=self.abrir_ventana_excel, style="Accent.TButton").grid(row=1, column=0, sticky="ew", pady=(0, 10))
        ttk.Button(marco, text="Exportar a PDF", command=self.abrir_ventana_pdf, style="Accent.TButton").grid(row=2, column=0, sticky="ew")

    def _crear_zona_conexion(self, contenedor: ttk.Frame, fila: int) -> None:
        marco = ttk.LabelFrame(contenedor, text="Conexión", padding=16)
        marco.grid(row=fila, column=0, sticky="ew")
        marco.columnconfigure(0, weight=1)

        ttk.Label(marco, text="Estado actual", style="Cabecera.TLabel").grid(row=0, column=0, sticky="w")

        self.etiqueta_estado = ttk.Label(
            marco,
            textvariable=self.estado_conexion,
            style="EstadoDesconectado.TLabel",
        )
        self.etiqueta_estado.grid(row=1, column=0, sticky="w", pady=(4, 2))

        ttk.Label(
            marco,
            textvariable=self.ip_base_datos,
            style="Muted.TLabel",
            wraplength=360,
            justify="left",
        ).grid(row=2, column=0, sticky="ew", pady=(0, 12))

        self.marco_acciones_conexion = ttk.Frame(marco)
        self.marco_acciones_conexion.grid(row=3, column=0, sticky="ew")
        self.marco_acciones_conexion.columnconfigure(0, weight=1)

        self.boton_buscar = ttk.Button(
            self.marco_acciones_conexion,
            text="Buscar por hostname",
            command=self.buscar_y_conectar_en_hilo,
            style="Primary.TButton",
        )
        self.boton_buscar.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self.boton_ip_manual = ttk.Button(
            self.marco_acciones_conexion,
            text="Introducir IP manual",
            command=self.pedir_ip_manual,
            style="Secondary.TButton",
        )
        self.boton_ip_manual.grid(row=1, column=0, sticky="ew")

        self._actualizar_estado_visual()

    def _crear_zona_registros(self, contenedor: ttk.Frame) -> None:
        marco = ttk.LabelFrame(contenedor, text="Registros recientes", padding=16)
        marco.grid(row=0, column=0, sticky="nsew")
        marco.columnconfigure(0, weight=1)
        marco.columnconfigure(1, weight=0)
        marco.rowconfigure(0, weight=0)
        marco.rowconfigure(1, weight=0)
        marco.rowconfigure(2, weight=0)
        marco.rowconfigure(3, weight=1)

        texto_ayuda = "Consulta los registros recientes del sistema."
        if self._puede_editar_registros():
            texto_ayuda = "Aplica filtros combinados y edita fecha/hora o tipo con doble clic sobre la tabla."

        ttk.Label(marco, text=texto_ayuda, style="Muted.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 10))
        self.etiqueta_estado_tabla = ttk.Label(marco, textvariable=self.estado_tabla, style="Muted.TLabel")
        self.etiqueta_estado_tabla.grid(row=0, column=1, sticky="e", pady=(0, 10))

        self._crear_bloque_intervalo_fecha(marco)

        marco_filtros = ttk.Frame(marco)
        marco_filtros.grid(row=2, column=0, columnspan=2, sticky="ew")
        for i in range(3):
            marco_filtros.columnconfigure(i, weight=1)
        marco_filtros.columnconfigure(3, weight=0)
        marco_filtros.columnconfigure(4, weight=0)

        self._crear_bloque_filtro_usuario(marco_filtros)
        self._crear_bloque_filtro_uid(marco_filtros)
        self._crear_bloque_filtro_tipo(marco_filtros)
        self._crear_acciones_filtros(marco_filtros)
        self._crear_tabla_registros(marco)

        if self._es_basic():
            if self.combo_filtro_usuario is not None:
                self.combo_filtro_usuario.configure(state="disabled")
            if self.combo_filtro_uid is not None:
                self.combo_filtro_uid.configure(state="disabled")

    def _crear_bloque_filtro_usuario(self, contenedor: ttk.Frame) -> None:
        bloque_usuario = ttk.Frame(contenedor)
        bloque_usuario.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=(0, 10))
        ttk.Label(bloque_usuario, text="Usuario", style="Muted.TLabel").pack(anchor="w")
        self.combo_filtro_usuario = ttk.Combobox(bloque_usuario, textvariable=self.var_filtro_usuario, state="normal")
        self.combo_filtro_usuario.pack(fill="x", pady=(4, 0))
        self.combo_filtro_usuario.bind("<KeyRelease>", self._filtrar_usuario)

    def _crear_bloque_filtro_uid(self, contenedor: ttk.Frame) -> None:
        bloque_uid = ttk.Frame(contenedor)
        bloque_uid.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=(0, 10))
        ttk.Label(bloque_uid, text="Tarjeta", style="Muted.TLabel").pack(anchor="w")
        self.combo_filtro_uid = ttk.Combobox(bloque_uid, textvariable=self.var_filtro_uid, state="normal")
        self.combo_filtro_uid.pack(fill="x", pady=(4, 0))
        self.combo_filtro_uid.bind("<KeyRelease>", self._filtrar_uid)

    def _crear_bloque_intervalo_fecha(self, contenedor: ttk.LabelFrame) -> None:
        marco_intervalo = ttk.Frame(contenedor)
        marco_intervalo.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        marco_intervalo.columnconfigure(0, weight=1)

        ttk.Label(marco_intervalo, text="Fecha", style="Muted.TLabel").grid(row=0, column=0, sticky="w")

        fila_intervalo = ttk.Frame(marco_intervalo)
        fila_intervalo.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        fila_intervalo.columnconfigure(0, weight=1)
        fila_intervalo.columnconfigure(1, minsize=10)

        self.etiqueta_resumen_fechas = ttk.Label(
            fila_intervalo,
            text="Sin intervalo",
            style="Card.TLabel",
        )
        self.etiqueta_resumen_fechas.grid(row=0, column=0, sticky="w")

        self._crear_boton_calendario(fila_intervalo)
        ttk.Separator(fila_intervalo, orient="vertical").grid(row=0, column=3, sticky="ns", padx=(14, 14))
        self._crear_boton_refresco_intervalo(fila_intervalo)

    def _crear_boton_calendario(self, contenedor: ttk.Frame) -> None:
        ruta_icono_calendario = str(obtener_recurso("imagenes", "calendario.png"))

        try:
            imagen = Image.open(ruta_icono_calendario)
            imagen = imagen.resize((24, 24))
            self.icono_calendario = ImageTk.PhotoImage(imagen)

            ttk.Button(
                contenedor,
                image=self.icono_calendario,
                command=self.abrir_selector_intervalo_fechas,
                style="IconOnly.TButton",
            ).grid(row=0, column=2, sticky="e", padx=(0, 0))

        except Exception:
            ttk.Button(
                contenedor,
                text="Fecha",
                command=self.abrir_selector_intervalo_fechas,
                style="Secondary.TButton",
            ).grid(row=0, column=2, sticky="e", padx=(0, 0))

    def _crear_bloque_filtro_tipo(self, contenedor: ttk.Frame) -> None:
        bloque_tipo = ttk.Frame(contenedor)
        bloque_tipo.grid(row=0, column=2, sticky="ew", padx=(0, 10), pady=(0, 10))
        ttk.Label(bloque_tipo, text="Tipo", style="Muted.TLabel").pack(anchor="w")
        self.combo_filtro_tipo = ttk.Combobox(bloque_tipo, textvariable=self.var_filtro_tipo, state="readonly")
        self.combo_filtro_tipo.pack(fill="x", pady=(4, 0))

    def _crear_acciones_filtros(self, contenedor: ttk.Frame) -> None:
        acciones = ttk.Frame(contenedor)
        acciones.grid(row=0, column=3, sticky="e", pady=(22, 10))

        ttk.Button(
            acciones,
            text="Aplicar filtros",
            command=self.actualizar_tabla_registros,
            style="Primary.TButton",
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            acciones,
            text="Limpiar",
            command=self.limpiar_filtros,
            style="Secondary.TButton",
        ).pack(side="left")

    def _crear_boton_refresco_intervalo(self, contenedor: ttk.Frame) -> None:
        ruta_icono_refrescar = str(obtener_recurso("imagenes", "refresh.png"))
        try:
            imagen = Image.open(ruta_icono_refrescar)
            imagen = imagen.resize((20, 20))
            self.icono_refrescar = ImageTk.PhotoImage(imagen)
            ttk.Button(
                contenedor,
                image=self.icono_refrescar,
                command=self.actualizar_tabla_registros,
                style="IconOnly.TButton",
            ).grid(row=0, column=4, sticky="e")
        except Exception:
            ttk.Button(
                contenedor,
                text="Refrescar",
                command=self.actualizar_tabla_registros,
                style="Secondary.TButton",
            ).grid(row=0, column=4, sticky="e")

    def _crear_tabla_registros(self, contenedor: ttk.LabelFrame) -> None:
        marco_tabla = ttk.Frame(contenedor)
        marco_tabla.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(4, 0))
        marco_tabla.columnconfigure(0, weight=1)
        marco_tabla.rowconfigure(0, weight=1)

        columnas = ("usuario", "uid", "fecha_hora", "tipo")
        self.tabla_registros = ttk.Treeview(marco_tabla, columns=columnas, show="headings")
        self.tabla_registros.heading("usuario", text="Usuario")
        self.tabla_registros.heading("uid", text="Tarjeta")
        self.tabla_registros.heading("fecha_hora", text="Fecha / Hora")
        self.tabla_registros.heading("tipo", text="Tipo")

        self.tabla_registros.column("usuario", width=240, anchor="w")
        self.tabla_registros.column("uid", width=180, anchor="center")
        self.tabla_registros.column("fecha_hora", width=220, anchor="center")
        self.tabla_registros.column("tipo", width=130, anchor="center")

        self.tabla_registros.tag_configure("par", background="#ffffff")
        self.tabla_registros.tag_configure("impar", background="#f8fbff")

        scrollbar_vertical = ttk.Scrollbar(marco_tabla, orient="vertical", command=self.tabla_registros.yview)
        scrollbar_horizontal = ttk.Scrollbar(marco_tabla, orient="horizontal", command=self.tabla_registros.xview)

        self.tabla_registros.configure(
            yscrollcommand=scrollbar_vertical.set,
            xscrollcommand=scrollbar_horizontal.set,
        )

        self.tabla_registros.grid(row=0, column=0, sticky="nsew")
        scrollbar_vertical.grid(row=0, column=1, sticky="ns")
        scrollbar_horizontal.grid(row=1, column=0, sticky="ew")
        self.tabla_registros.bind("<Double-1>", self.editar_celda_tabla)

    # =========================
    # ADMINISTRACIÓN
    # =========================
    def _abrir_ventana_administracion(self) -> None:
        if not self._es_admin():
            messagebox.showwarning(
                "Acceso denegado",
                "Solo los usuarios administradores pueden acceder a esta zona.",
            )
            return
        if self.apertura_admin_en_progreso:
            return

        # Evita comprobaciones de red bloqueantes en el hilo de UI.
        if not self.servicio_fichajes.repositorio.esta_conectado():
            self.estado_conexion.set("Desconectado")
            self.ip_base_datos.set("Sin conexión con la Raspberry / base de datos")
            self._actualizar_estado_visual()
            messagebox.showwarning(
                "Sin conexión",
                "No se puede abrir Administración porque no hay conexión con la base de datos.",
            )
            return

        self.apertura_admin_en_progreso = True
        self._mostrar_dialogo_espera_admin()

        resultado = {"ok": False, "error": None}

        def validar_conexion_admin() -> None:
            try:
                # Valida acceso real a BD en segundo plano para evitar congelar la UI.
                self.servicio_autenticacion.listar_usuarios()
                resultado["ok"] = True
            except Exception as error:
                resultado["error"] = error

        hilo = threading.Thread(target=validar_conexion_admin, daemon=True)
        hilo.start()

        def finalizar_apertura() -> None:
            if hilo.is_alive():
                self.after(100, finalizar_apertura)
                return

            self.apertura_admin_en_progreso = False
            self._cerrar_dialogo_espera_admin()

            if not resultado["ok"]:
                if isinstance(resultado["error"], ErrorConexionBaseDeDatos):
                    self._manejar_desconexion()
                    messagebox.showwarning(
                        "Sin conexión",
                        "No se pudo abrir Administración porque se perdió la conexión con la base de datos.",
                    )
                    return
                self.logger.exception("No se pudo validar la apertura de Administración")
                messagebox.showerror("Error", str(resultado["error"]))
                return

            try:
                ventana = VentanaAdministracion(
                    master=self,
                    servicio_autenticacion=self.servicio_autenticacion,
                    servicio_fichajes=self.servicio_fichajes,
                    logger=self.logger,
                    sesion=self.sesion,
                )
                ventana.grab_set()
            except ErrorConexionBaseDeDatos:
                self._manejar_desconexion()
                messagebox.showwarning(
                    "Sin conexión",
                    "Se perdió la conexión al abrir Administración. Reintenta cuando se recupere.",
                )
            except Exception as error:
                self.logger.exception("No se pudo abrir la ventana de administración")
                messagebox.showerror("Error", str(error))

        self.after(100, finalizar_apertura)

    def _mostrar_dialogo_espera_admin(self) -> None:
        if self.dialogo_espera_admin is not None and self.dialogo_espera_admin.winfo_exists():
            self.dialogo_espera_admin.lift()
            return

        dialogo = tk.Toplevel(self)
        dialogo.title("Administración")
        dialogo.resizable(False, False)
        dialogo.transient(self)
        dialogo.grab_set()
        dialogo.configure(bg=self.colores["fondo"])

        frame = ttk.Frame(dialogo, padding=18)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="Comprobando conexión para abrir Administración...",
            style="HeroSub.TLabel",
            wraplength=320,
            justify="center",
        ).pack(anchor="center", pady=(0, 10))

        barra = ttk.Progressbar(frame, mode="indeterminate", length=240)
        barra.pack(anchor="center")
        barra.start(10)

        dialogo.update_idletasks()
        ancho = dialogo.winfo_width()
        alto = dialogo.winfo_height()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (ancho // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (alto // 2)
        dialogo.geometry(f"{ancho}x{alto}+{x}+{y}")

        self.dialogo_espera_admin = dialogo

    def _cerrar_dialogo_espera_admin(self) -> None:
        if self.dialogo_espera_admin is None:
            return
        try:
            if self.dialogo_espera_admin.winfo_exists():
                self.dialogo_espera_admin.destroy()
        except Exception:
            pass
        finally:
            self.dialogo_espera_admin = None

    # =========================
    # DATOS / UI
    # =========================
    def _actualizar_interfaz_con_datos(self, filas: list[tuple], datos_desplegables: dict) -> None:
        if self.tabla_registros is None:
            return

        for elemento in self.tabla_registros.get_children():
            self.tabla_registros.delete(elemento)

        for indice, (id_registro, usuario, uid, fecha_hora, tipo) in enumerate(filas):
            fecha_hora_texto = fecha_hora.strftime("%Y-%m-%d %H:%M:%S") if fecha_hora else ""
            etiqueta_fila = "par" if indice % 2 == 0 else "impar"
            self.tabla_registros.insert(
                "",
                "end",
                iid=str(id_registro),
                values=(usuario, uid, fecha_hora_texto, tipo),
                tags=(etiqueta_fila,),
            )

        self._aplicar_datos_desplegables(datos_desplegables)
        self.resumen_registros.set(str(len(filas)))
        self.resumen_actualizacion.set(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        self.estado_tabla.set("Listo")

    def _obtener_nombre_usuario_basic(self) -> str:
        if self.sesion is None:
            return ""
        return (getattr(self.sesion, "username", "") or "").strip()

    def _obtener_uid_usuario_basic(self, usuarios_asignados: list[tuple[str, str]]) -> str:
        if self.sesion is None:
            return "Sin asignar"

        usuario_rfid = (getattr(self.sesion, "usuario_rfid", None) or "").strip()
        if not usuario_rfid:
            return "Sin asignar"

        for nombre, uid in usuarios_asignados:
            if nombre == usuario_rfid:
                return uid

        return "Sin asignar"

    def _limpiar_estado_desconectado(self) -> None:
        self.resumen_registros.set("0")
        if self._es_basic():
            self.resumen_usuarios.set(self._obtener_nombre_usuario_basic())
            self.resumen_tarjetas.set("Sin sincronizar")
        else:
            self.resumen_usuarios.set("0")
            self.resumen_tarjetas.set("0")
        self.resumen_actualizacion.set("Sin sincronizar")
        self.estado_tabla.set("Sin conexión")

        self.var_nombre_usuario.set("")
        self.var_uid_tarjeta.set("")
        self.var_uid_baja.set("")
        self.var_filtro_usuario.set("")
        self.var_filtro_uid.set("")
        self.var_filtro_tipo.set("")
        self.fecha_desde_filtro = None
        self.fecha_hasta_filtro = None
        if self.etiqueta_resumen_fechas is not None:
            self.etiqueta_resumen_fechas.configure(text="Sin intervalo")

        self.lista_usuarios = []
        self.lista_uid = []
        self.mapa_baja_usuario = {}

        if self.tabla_registros is not None:
            for elemento in self.tabla_registros.get_children():
                self.tabla_registros.delete(elemento)

        for combo in (self.combo_uid_alta, self.combo_uid_baja, self.combo_filtro_usuario, self.combo_filtro_uid, self.combo_filtro_tipo):
            if combo is not None:
                combo["values"] = ()

    def _aplicar_datos_desplegables(self, datos_desplegables: dict) -> None:
        uids_sin_asignar = datos_desplegables["uids_sin_asignar"]
        usuarios_asignados = datos_desplegables["usuarios_asignados"]
        tipos = datos_desplegables["tipos"]

        if self.combo_uid_alta is not None:
            self.combo_uid_alta["values"] = uids_sin_asignar
            if self.var_uid_tarjeta.get() not in uids_sin_asignar:
                self.var_uid_tarjeta.set("")

        if self.combo_uid_baja is not None:
            self.mapa_baja_usuario = {f"{nombre} ({uid})": uid for nombre, uid in usuarios_asignados}
            opciones_baja = list(self.mapa_baja_usuario.keys())
            self.combo_uid_baja["values"] = opciones_baja
            if self.var_uid_baja.get() not in opciones_baja:
                self.var_uid_baja.set("")

        if self.combo_filtro_usuario is not None:
            self.lista_usuarios = [""] + sorted(list({nombre for nombre, _uid in usuarios_asignados} | {"Sin asignar"}))
            self.combo_filtro_usuario["values"] = self.lista_usuarios
            if self.var_filtro_usuario.get() not in self.lista_usuarios:
                self.var_filtro_usuario.set("")

        if self.combo_filtro_uid is not None:
            self.lista_uid = [""] + sorted(list({uid for _nombre, uid in usuarios_asignados} | set(uids_sin_asignar)))
            self.combo_filtro_uid["values"] = self.lista_uid
            if self.var_filtro_uid.get() not in self.lista_uid:
                self.var_filtro_uid.set("")

        if self.combo_filtro_tipo is not None:
            opciones_tipo = [""] + sorted(list(set(tipos) | {"entrada", "salida"}))
            self.combo_filtro_tipo["values"] = opciones_tipo
            if self.var_filtro_tipo.get() not in opciones_tipo:
                self.var_filtro_tipo.set("")

        if self._es_basic():
            self.resumen_usuarios.set(self._obtener_nombre_usuario_basic())
            self.resumen_tarjetas.set(self._obtener_uid_usuario_basic(usuarios_asignados))
        else:
            self.resumen_usuarios.set(str(len({nombre for nombre, _uid in usuarios_asignados})))
            self.resumen_tarjetas.set(str(len(uids_sin_asignar)))

    def _obtener_datos_pantalla(self) -> tuple[list[tuple], dict]:
        usuario_filtro = self.var_filtro_usuario.get().strip() or None

        if self._es_basic():
            usuario_rfid = None
            if self.sesion is not None:
                usuario_rfid = (getattr(self.sesion, "usuario_rfid", None) or "").strip()

            if not usuario_rfid:
                self.logger.warning("Usuario basic sin usuario_rfid asociado")
                return [], {"uids_sin_asignar": [], "usuarios_asignados": [], "tipos": []}

            usuario_filtro = usuario_rfid

        filtros = FiltrosRegistros(
            usuario=usuario_filtro,
            uid_tarjeta=self.var_filtro_uid.get().strip() or None,
            fecha_desde=self.fecha_desde_filtro,
            fecha_hasta=self.fecha_hasta_filtro,
            tipo=self.var_filtro_tipo.get().strip() or None,
            limite=200,
        )
        with self.lock_bd:
            filas = self.servicio_fichajes.obtener_registros(filtros)
            datos = self.servicio_fichajes.obtener_datos_desplegables()
        return filas, datos

    def _set_estado_tabla(self, texto: str) -> None:
        self.estado_tabla.set(texto)
        try:
            self.update_idletasks()
        except Exception:
            pass

    # =========================
    # REFRESCO / CONEXIÓN
    # =========================
    def _refrescar_datos_en_segundo_plano(self) -> None:
        try:
            with self.lock_bd:
                if not self.servicio_conexion.verificar_conexion_activa():
                    raise ErrorConexionBaseDeDatos("Conexión perdida con la base de datos")

            filas, datos = self._obtener_datos_pantalla()
            self.after(0, lambda: self._actualizar_interfaz_con_datos(filas, datos))
        except ErrorConexionBaseDeDatos:
            self.after(0, self._manejar_desconexion)
        except Exception:
            self.logger.exception("Error al refrescar datos en segundo plano")
            self.after(0, self._manejar_desconexion)
        finally:
            self.after(0, self._reprogramar_actualizacion_periodica)

    def _actualizar_estado_visual(self) -> None:
        conectado = self.estado_conexion.get().strip().lower() == "conectado"

        if self.etiqueta_estado is not None:
            self.etiqueta_estado.configure(
                style="EstadoConectado.TLabel" if conectado else "EstadoDesconectado.TLabel"
            )

        if self.marco_acciones_conexion is not None:
            if conectado:
                self.marco_acciones_conexion.grid_remove()
            else:
                self.marco_acciones_conexion.grid()

    def _intentar_conexion_inicial(self) -> None:
        if not self._puede_ver_conexion():
            return
        self.estado_conexion.set("Conectando...")
        self.ip_base_datos.set("Buscando servidor...")
        self._actualizar_estado_visual()
        self.buscar_y_conectar_en_hilo()

    def buscar_y_conectar_en_hilo(self) -> None:
        if not self._puede_ver_conexion():
            return
        self.estado_conexion.set("Buscando...")
        self.ip_base_datos.set("Resolviendo hostname...")
        self._actualizar_estado_visual()
        threading.Thread(target=self._buscar_y_conectar, daemon=True).start()

    def _buscar_y_conectar(self) -> None:
        try:
            hostname = self.configuracion.hostname_raspberry
            ip = self.servicio_conexion.buscar_ip()

            def gestionar_resultado() -> None:
                if ip:
                    self._conectar_a_ip(ip)
                    return
                self.estado_conexion.set("Desconectado")
                self.ip_base_datos.set(f"{hostname} no resuelto")
                self._actualizar_estado_visual()

            self.after(0, gestionar_resultado)
        except Exception:
            self.logger.exception("Error durante la búsqueda por hostname")
            self.after(0, lambda: self.estado_conexion.set("Desconectado"))
            self.after(0, lambda: self.ip_base_datos.set("Error al buscar el servidor"))
            self.after(0, self._actualizar_estado_visual)

    def _conectar_a_ip(self, ip: str) -> None:
        try:
            self.servicio_conexion.conectar_a_ip(ip)
            self.estado_conexion.set("Conectado")
            self.ip_base_datos.set(f"Servidor activo en {ip}")
            self._actualizar_estado_visual()
            self.cargar_desplegables()
            self.actualizar_tabla_registros()
            self._programar_actualizacion_periodica()
        except ErrorConexionBaseDeDatos as error:
            self.estado_conexion.set("Desconectado")
            self.ip_base_datos.set(f"Sin acceso a {ip}")
            self._actualizar_estado_visual()
            self.logger.error(
                "No se pudo acceder a la base de datos en %s:%s. Error: %s",
                ip,
                self.configuracion.puerto_bd,
                error,
            )
            messagebox.showerror(
                "Error de conexión",
                f"Se ha resuelto el hostname '{self.configuracion.hostname_raspberry}' a la IP {ip}, pero no se ha podido acceder a la base de datos por el puerto {self.configuracion.puerto_bd}.",
            )

    def pedir_ip_manual(self) -> None:
        if not self._puede_ver_conexion():
            return

        ip = simpledialog.askstring("IP manual", "Introduce la IP de la base de datos:")
        if not ip:
            return

        try:
            ipaddress.ip_address(ip)
        except ValueError:
            messagebox.showerror("IP inválida", "Introduce una dirección IP válida (ej: 192.168.1.10)")
            return

        self._conectar_a_ip(ip)

    # =========================
    # RFID
    # =========================
    def registrar_usuario(self) -> None:
        if not self._puede_gestionar_rfid():
            return
        if not self.servicio_fichajes.repositorio.esta_conectado():
            messagebox.showwarning("Sin conexión", "No hay conexión con la base de datos")
            return

        nombre = self.var_nombre_usuario.get().strip()
        uid = self.var_uid_tarjeta.get().strip()

        if not nombre or not uid:
            messagebox.showwarning("Campos obligatorios", "Debes indicar nombre y tarjeta RFID")
            return

        if not messagebox.askyesno(
            "Confirmar alta",
            f"¿Seguro que quieres registrar a '{nombre}' con la tarjeta '{uid}'?",
        ):
            return

        try:
            with self.lock_bd:
                self.servicio_fichajes.registrar_usuario(nombre, uid)
            messagebox.showinfo("Correcto", "Usuario registrado correctamente")
            self.cargar_desplegables()
            self.var_nombre_usuario.set("")
            self.var_uid_tarjeta.set("")
        except ErrorConexionBaseDeDatos:
            self._manejar_desconexion()
        except Exception as error:
            messagebox.showerror("Error", str(error))

    def dar_baja_usuario(self) -> None:
        if not self._puede_gestionar_rfid():
            return
        if not self.servicio_fichajes.repositorio.esta_conectado():
            messagebox.showwarning("Sin conexión", "No hay conexión con la base de datos")
            return

        seleccion = self.var_uid_baja.get().strip()
        uid = self.mapa_baja_usuario.get(seleccion, "")
        if not uid:
            messagebox.showwarning("Campo obligatorio", "Debes indicar el UID del usuario a dar de baja")
            return

        if not messagebox.askyesno("Confirmar baja", f"¿Seguro que quieres dar de baja el UID {uid}?"):
            return

        try:
            with self.lock_bd:
                self.servicio_fichajes.dar_baja_usuario(uid)
            messagebox.showinfo("Correcto", "Usuario dado de baja correctamente")
            self.cargar_desplegables()
            self.var_uid_baja.set("")
            self.actualizar_tabla_registros()
        except ErrorConexionBaseDeDatos:
            self._manejar_desconexion()
        except Exception as error:
            messagebox.showerror("Error", str(error))

    # =========================
    # TABLA / FILTROS
    # =========================
    def limpiar_filtros(self) -> None:
        self.var_filtro_usuario.set("")
        self.var_filtro_uid.set("")
        self.var_filtro_tipo.set("")
        self.fecha_desde_filtro = None
        self.fecha_hasta_filtro = None
        if self.etiqueta_resumen_fechas is not None:
            self.etiqueta_resumen_fechas.configure(text="Sin intervalo")
        self.actualizar_tabla_registros()

    def actualizar_tabla_registros(self) -> None:
        self._cerrar_editor_tabla_activo()
        if self.tabla_registros is None:
            return
        if not self.servicio_fichajes.repositorio.esta_conectado():
            return

        self._set_estado_tabla("Cargando registros...")
        self.token_carga_tabla += 1
        token_actual = self.token_carga_tabla
        snapshot = self._crear_snapshot_filtros()
        threading.Thread(
            target=self._cargar_tabla_en_segundo_plano,
            args=(token_actual, snapshot),
            daemon=True,
        ).start()

    def _crear_snapshot_filtros(self) -> dict:
        usuario_filtro = self.var_filtro_usuario.get().strip() or None

        if self._es_basic():
            usuario_rfid = None
            if self.sesion is not None:
                usuario_rfid = (getattr(self.sesion, "usuario_rfid", None) or "").strip()

            if not usuario_rfid:
                self.logger.warning("Usuario basic sin usuario_rfid asociado")
                usuario_filtro = "__sin_usuario_rfid__"
            else:
                usuario_filtro = usuario_rfid

        return {
            "usuario": usuario_filtro,
            "uid_tarjeta": self.var_filtro_uid.get().strip() or None,
            "fecha_desde": self.fecha_desde_filtro,
            "fecha_hasta": self.fecha_hasta_filtro,
            "tipo": self.var_filtro_tipo.get().strip() or None,
            "limite": 200,
        }

    def _obtener_datos_pantalla_desde_snapshot(self, snapshot: dict) -> tuple[list[tuple], dict]:
        if snapshot.get("usuario") == "__sin_usuario_rfid__":
            return [], {"uids_sin_asignar": [], "usuarios_asignados": [], "tipos": []}

        filtros = FiltrosRegistros(
            usuario=snapshot.get("usuario"),
            uid_tarjeta=snapshot.get("uid_tarjeta"),
            fecha_desde=snapshot.get("fecha_desde"),
            fecha_hasta=snapshot.get("fecha_hasta"),
            tipo=snapshot.get("tipo"),
            limite=snapshot.get("limite", 200),
        )
        with self.lock_bd:
            filas = self.servicio_fichajes.obtener_registros(filtros)
            datos = self.servicio_fichajes.obtener_datos_desplegables()
        return filas, datos

    def _cargar_tabla_en_segundo_plano(self, token: int, snapshot: dict) -> None:
        try:
            filas, datos = self._obtener_datos_pantalla_desde_snapshot(snapshot)

            def aplicar() -> None:
                if token != self.token_carga_tabla:
                    return
                self._actualizar_interfaz_con_datos(filas, datos)

            self.after(0, aplicar)
        except ErrorConexionBaseDeDatos:
            def aplicar_error_conexion() -> None:
                if token != self.token_carga_tabla:
                    return
                self._set_estado_tabla("Sin conexión")
                self._manejar_desconexion()

            self.after(0, aplicar_error_conexion)
        except Exception:
            self.logger.exception("Error al actualizar la tabla de registros")

            def aplicar_error_generico() -> None:
                if token != self.token_carga_tabla:
                    return
                self._set_estado_tabla("Error al cargar")

            self.after(0, aplicar_error_generico)

    def _programar_actualizacion_periodica(self) -> None:
        if self.id_after_refresco is not None:
            try:
                self.after_cancel(self.id_after_refresco)
            except Exception:
                pass
        threading.Thread(target=self._refrescar_datos_en_segundo_plano, daemon=True).start()

    def _reprogramar_actualizacion_periodica(self) -> None:
        self.id_after_refresco = self.after(self.configuracion.intervalo_refresco_ms, self._programar_actualizacion_periodica)

    def editar_celda_tabla(self, evento) -> None:
        if not self._puede_editar_registros() or self.tabla_registros is None:
            return

        self._cerrar_editor_tabla_activo()

        item = self.tabla_registros.identify_row(evento.y)
        columna = self.tabla_registros.identify_column(evento.x)
        if not item or columna not in ("#3", "#4"):
            return

        bbox = self.tabla_registros.bbox(item, columna)
        if not bbox:
            return

        x, y, ancho, alto = bbox
        valor_actual = self.tabla_registros.set(item, columna)
        id_registro = int(item)

        if columna == "#3":
            self._abrir_editor_fecha(x, y, ancho, alto, valor_actual, id_registro)
            return

        if columna == "#4":
            self._abrir_editor_tipo(x, y, ancho, alto, valor_actual, id_registro)

    def _abrir_editor_fecha(self, x: int, y: int, ancho: int, alto: int, valor_actual: str, id_registro: int) -> None:
        editor = ttk.Entry(self.tabla_registros)
        self.editor_tabla_activo = editor
        editor.place(x=x, y=y, width=ancho, height=alto)
        editor.insert(0, valor_actual)
        editor.select_range(0, "end")
        editor.focus_set()

        def guardar_fecha(_event=None) -> None:
            if self.editor_tabla_activo is not editor:
                return

            nuevo_valor = editor.get().strip()
            self._cerrar_editor_tabla_activo()
            if not nuevo_valor:
                return

            try:
                datetime.strptime(nuevo_valor, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                messagebox.showerror(
                    "Formato inválido",
                    "La fecha y hora debe tener el formato: YYYY-MM-DD HH:MM:SS",
                )
                return

            if nuevo_valor == valor_actual:
                return

            if not messagebox.askyesno(
                "Confirmar cambio",
                f"¿Guardar el cambio de fecha/hora?\n\nAnterior: {valor_actual}\nNuevo: {nuevo_valor}",
            ):
                return

            try:
                with self.lock_bd:
                    self.servicio_fichajes.actualizar_fecha_hora_registro(id_registro, nuevo_valor)
                self.actualizar_tabla_registros()
            except Exception as error:
                messagebox.showerror("Error", str(error))

        editor.bind("<Return>", guardar_fecha)
        editor.bind("<Escape>", lambda _event=None: self._cerrar_editor_tabla_activo())
        editor.bind("<FocusOut>", guardar_fecha)

    def _abrir_editor_tipo(self, x: int, y: int, ancho: int, alto: int, valor_actual: str, id_registro: int) -> None:
        opciones_tipo = ("entrada", "salida")
        valor_inicial = valor_actual if valor_actual in opciones_tipo else "entrada"

        var_tipo = tk.StringVar(value=valor_inicial)
        editor = ttk.Combobox(
            self.tabla_registros,
            textvariable=var_tipo,
            values=opciones_tipo,
            state="readonly",
        )
        self.editor_tabla_activo = editor
        editor.place(x=x, y=y, width=ancho, height=alto)
        editor.focus_set()

        def guardar_tipo(_event=None) -> None:
            if self.editor_tabla_activo is not editor:
                return

            nuevo_valor = var_tipo.get().strip()
            self._cerrar_editor_tabla_activo()
            if nuevo_valor not in opciones_tipo or nuevo_valor == valor_actual:
                return

            if not messagebox.askyesno(
                "Confirmar cambio",
                f"¿Guardar el cambio de tipo?\n\nAnterior: {valor_actual}\nNuevo: {nuevo_valor}",
            ):
                return

            try:
                with self.lock_bd:
                    self.servicio_fichajes.actualizar_tipo_registro(id_registro, nuevo_valor)
                self.actualizar_tabla_registros()
            except Exception as error:
                messagebox.showerror("Error", str(error))

        editor.bind("<<ComboboxSelected>>", guardar_tipo)
        editor.bind("<Return>", guardar_tipo)
        editor.bind("<Escape>", lambda _event=None: self._cerrar_editor_tabla_activo())

    def _cerrar_editor_tabla_activo(self) -> None:
        if self.editor_tabla_activo is not None:
            try:
                self.editor_tabla_activo.destroy()
            except Exception:
                pass
            finally:
                self.editor_tabla_activo = None

    # =========================
    # EXPORTACIONES
    # =========================
    def abrir_ventana_excel(self) -> None:
        if not self._puede_exportar():
            return
        if not self.servicio_fichajes.repositorio.esta_conectado():
            messagebox.showwarning("Sin conexión", "No hay conexión con la base de datos")
            return
        VentanaExportacion(self, self.servicio_fichajes, modo="excel")

    def abrir_ventana_pdf(self) -> None:
        if not self._puede_exportar():
            return
        if not self.servicio_fichajes.repositorio.esta_conectado():
            messagebox.showwarning("Sin conexión", "No hay conexión con la base de datos")
            return
        VentanaExportacion(self, self.servicio_fichajes, modo="pdf")

    def cargar_desplegables(self) -> None:
        if not self.servicio_fichajes.repositorio.esta_conectado():
            return
        try:
            with self.lock_bd:
                datos = self.servicio_fichajes.obtener_datos_desplegables()
            self._aplicar_datos_desplegables(datos)
        except ErrorConexionBaseDeDatos:
            self._manejar_desconexion()
        except Exception:
            self.logger.exception("Error al cargar desplegables")

    # =========================
    # FECHAS
    # =========================
    def abrir_selector_intervalo_fechas(self) -> None:
        ventana = tk.Toplevel(self)
        ventana.title("Seleccionar intervalo de fechas")
        ventana.geometry("580x450")
        ventana.resizable(False, False)
        ventana.transient(self)
        ventana.grab_set()
        ventana.configure(bg=self.colores["fondo"])

        frame = ttk.Frame(ventana, padding=18)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Acota la búsqueda por rango de fecha y hora.", style="Muted.TLabel").pack(anchor="w", pady=(0, 12))
        ttk.Label(frame, text="Fecha desde", style="Card.TLabel").pack(anchor="w")
        calendario_desde = DateEntry(frame, date_pattern="yyyy-mm-dd")
        calendario_desde.pack(fill="x", pady=(4, 0))
        ttk.Label(frame, text="Hora desde (HH:MM:SS)", style="Card.TLabel").pack(anchor="w", pady=(10, 0))
        entrada_hora_desde = ttk.Entry(frame)
        entrada_hora_desde.insert(0, "00:00:00")
        entrada_hora_desde.pack(fill="x", pady=(4, 0))
        ttk.Label(frame, text="Fecha hasta", style="Card.TLabel").pack(anchor="w", pady=(10, 0))
        calendario_hasta = DateEntry(frame, date_pattern="yyyy-mm-dd")
        calendario_hasta.pack(fill="x", pady=(4, 0))
        ttk.Label(frame, text="Hora hasta (HH:MM:SS)", style="Card.TLabel").pack(anchor="w", pady=(10, 0))
        entrada_hora_hasta = ttk.Entry(frame)
        entrada_hora_hasta.insert(0, datetime.now().strftime("%H:%M:%S"))
        entrada_hora_hasta.pack(fill="x", pady=(4, 0))

        def aceptar() -> None:
            try:
                hora_desde = entrada_hora_desde.get().strip() or "00:00:00"
                hora_hasta = entrada_hora_hasta.get().strip() or "23:59:59"
                fecha_desde = datetime.strptime(f"{calendario_desde.get()} {hora_desde}", "%Y-%m-%d %H:%M:%S")
                fecha_hasta = datetime.strptime(f"{calendario_hasta.get()} {hora_hasta}", "%Y-%m-%d %H:%M:%S")
                if fecha_desde > fecha_hasta:
                    messagebox.showwarning(
                        "Rango incorrecto",
                        "La fecha 'desde' no puede ser mayor que la fecha 'hasta'",
                        parent=ventana,
                    )
                    return
                self.fecha_desde_filtro = fecha_desde
                self.fecha_hasta_filtro = fecha_hasta
                if self.etiqueta_resumen_fechas is not None:
                    self.etiqueta_resumen_fechas.configure(
                        text=f"{fecha_desde.strftime('%d/%m %H:%M')} → {fecha_hasta.strftime('%d/%m %H:%M')}"
                    )
                ventana.destroy()
                self.actualizar_tabla_registros()
            except ValueError:
                messagebox.showwarning("Formato no válido", "La hora debe tener formato HH:MM:SS", parent=ventana)

        acciones = ttk.Frame(frame)
        acciones.pack(fill="x", pady=18)
        ttk.Button(acciones, text="Cancelar", command=ventana.destroy, style="Secondary.TButton").pack(side="left")
        ttk.Button(acciones, text="Guardar intervalo", command=aceptar, style="Primary.TButton").pack(side="right")

    # =========================
    # AUTOCOMPLETADO
    # =========================
    def _filtrar_usuario(self, _event=None) -> None:
        texto = self.var_filtro_usuario.get().strip().lower()
        if not self.combo_filtro_usuario:
            return
        filtrados = self.lista_usuarios if not texto else [u for u in self.lista_usuarios if texto in u.lower()]
        self.combo_filtro_usuario["values"] = filtrados
        if len(filtrados) == 1:
            self.var_filtro_usuario.set(filtrados[0])

    def _filtrar_uid(self, _event=None) -> None:
        texto = self.var_filtro_uid.get().strip().lower()
        if not self.combo_filtro_uid:
            return
        filtrados = self.lista_uid if not texto else [u for u in self.lista_uid if texto in u.lower()]
        self.combo_filtro_uid["values"] = filtrados
        if len(filtrados) == 1:
            self.var_filtro_uid.set(filtrados[0])

    # =========================
    # DESCONEXIÓN / CIERRE
    # =========================
    def _manejar_desconexion(self) -> None:
        self.servicio_conexion.desconectar()
        self.estado_conexion.set("Desconectado")
        self.ip_base_datos.set("Sin conexión con la Raspberry / base de datos")
        self._limpiar_estado_desconectado()
        self._actualizar_estado_visual()

    def _gestionar_cierre_ventana(self) -> None:
        respuesta = self._mostrar_dialogo_cierre()
        if respuesta == "cancelar":
            return

        self.resultado_cierre = "cerrar_sesion" if respuesta == "cerrar_sesion" else "salir"

        try:
            if self.id_after_refresco is not None:
                self.after_cancel(self.id_after_refresco)
        except Exception:
            pass

        try:
            if self.servicio_conexion.verificar_conexion_activa():
                self.servicio_conexion.desconectar()
        except Exception:
            self.logger.warning("No se pudo cerrar la conexión al salir de la ventana principal")

        self.destroy()

    def _mostrar_dialogo_cierre(self) -> str:
        dialogo = tk.Toplevel(self)
        dialogo.title("Salir")
        dialogo.resizable(False, False)
        dialogo.transient(self)
        dialogo.grab_set()
        dialogo.configure(bg=self.colores["fondo"])

        try:
            if self.icono_ventana is not None:
                dialogo.iconphoto(True, self.icono_ventana)
        except Exception:
            pass

        resultado = {"valor": "cancelar"}

        frame = ttk.Frame(dialogo, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="¿Qué quieres hacer?", style="HeroTitle.TLabel").pack(anchor="w", pady=(0, 8))
        ttk.Label(
            frame,
            text="Puedes cerrar sesión para volver al login o salir completamente del programa.",
            style="HeroSub.TLabel",
            wraplength=360,
            justify="left",
        ).pack(anchor="w", pady=(0, 18))

        botones = ttk.Frame(frame)
        botones.pack(fill="x")

        def elegir(valor: str) -> None:
            resultado["valor"] = valor
            dialogo.destroy()

        ttk.Button(botones, text="Cancelar", command=lambda: elegir("cancelar"), style="Secondary.TButton").pack(side="right")
        ttk.Button(botones, text="Salir", command=lambda: elegir("salir"), style="Secondary.TButton").pack(side="right", padx=(0, 8))
        ttk.Button(botones, text="Cerrar sesión", command=lambda: elegir("cerrar_sesion"), style="Primary.TButton").pack(side="right", padx=(0, 8))

        dialogo.update_idletasks()
        ancho = dialogo.winfo_width()
        alto = dialogo.winfo_height()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (ancho // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (alto // 2)
        dialogo.geometry(f"{ancho}x{alto}+{x}+{y}")

        dialogo.wait_window()
        return resultado["valor"]
