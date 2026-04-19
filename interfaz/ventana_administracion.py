from __future__ import annotations

import os
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, ttk


class VentanaAdministracion(tk.Toplevel):
    ROLES = ("admin", "rrhh", "basic")

    def __init__(self, master, servicio_autenticacion, servicio_fichajes, logger, sesion) -> None:
        super().__init__(master)

        self.servicio_autenticacion = servicio_autenticacion
        self.servicio_fichajes = servicio_fichajes
        self.logger = logger
        self.sesion = sesion

        if getattr(self.sesion, "rol", "").lower() != "admin":
            raise PermissionError("Solo un administrador puede abrir esta ventana")

        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.icono_ventana = None

        self.usuario_seleccionado_id: int | None = None
        self.usuarios_cache: list[dict] = []
        self.usuarios_rfid_disponibles: list[str] = []
        self.usuarios_rfid_todos: list[str] = []

        self.var_username_sel = tk.StringVar()
        self.var_rol_sel = tk.StringVar(value="basic")
        self.var_activo_sel = tk.BooleanVar(value=True)
        self.var_usuario_rfid_sel = tk.StringVar()

        self.var_nuevo_username = tk.StringVar()
        self.var_nuevo_rol = tk.StringVar(value="basic")
        self.var_nueva_password = tk.StringVar()
        self.var_nuevo_usuario_rfid = tk.StringVar()

        self.var_eliminar_username = tk.StringVar()
        self.var_estado = tk.StringVar(value="Selecciona un usuario o crea uno nuevo.")

        self.title("Administración · Usuarios SERISA")
        self.geometry("1160x880")
        self.minsize(1040, 880)
        self.configure(bg="#eef3f8")
        self.transient(master)

        self._crear_estilos()
        self._configurar_icono_ventana()
        self._crear_interfaz()
        self._centrar()

        self._cargar_usuarios()
        self._cargar_usuarios_rfid()
        self._actualizar_estado_botones()

        self.protocol("WM_DELETE_WINDOW", self.destroy)

    # =========================
    # ESTILOS
    # =========================
    def _crear_estilos(self) -> None:
        self.fuente_base = tkfont.nametofont("TkDefaultFont").copy()
        self.fuente_base.configure(size=10)

        self.fuente_texto = tkfont.nametofont("TkTextFont").copy()
        self.fuente_texto.configure(size=10)

        self.fuente_titulo = tkfont.nametofont("TkHeadingFont").copy()
        self.fuente_titulo.configure(size=15, weight="bold")

        self.fuente_subtitulo = tkfont.nametofont("TkDefaultFont").copy()
        self.fuente_subtitulo.configure(size=10)

        self.fuente_estado = tkfont.nametofont("TkDefaultFont").copy()
        self.fuente_estado.configure(size=10)

        self.fuente_cabecera_tabla = tkfont.nametofont("TkDefaultFont").copy()
        self.fuente_cabecera_tabla.configure(size=10, weight="bold")

        estilo = ttk.Style(self)
        try:
            if "clam" in estilo.theme_names():
                estilo.theme_use("clam")
        except Exception:
            pass

        fondo = "#eef3f8"
        superficie = "#ffffff"
        primario = "#1f5a92"
        primario_hover = "#174a78"
        secundario = "#f1f5f9"
        secundario_hover = "#e2e8f0"
        borde = "#d9e2ec"
        texto = "#132238"
        texto_suave = "#5f6b7a"
        estado = "#49637a"

        self.colores = {
            "fondo": fondo,
            "superficie": superficie,
            "primario": primario,
            "primario_hover": primario_hover,
            "secundario": secundario,
            "secundario_hover": secundario_hover,
            "borde": borde,
            "texto": texto,
            "texto_suave": texto_suave,
            "estado": estado,
        }

        estilo.configure("App.TFrame", background=fondo)
        estilo.configure("Card.TFrame", background=superficie)

        estilo.configure(
            "PanelTitle.TLabel",
            background=superficie,
            foreground=texto,
            font=self.fuente_titulo,
        )
        estilo.configure(
            "PanelText.TLabel",
            background=superficie,
            foreground=texto_suave,
            font=self.fuente_subtitulo,
        )
        estilo.configure(
            "Field.TLabel",
            background=superficie,
            foreground=texto,
            font=self.fuente_base,
        )
        estilo.configure(
            "Status.TLabel",
            background=superficie,
            foreground=estado,
            font=self.fuente_estado,
        )
        estilo.configure(
            "Section.TLabelframe",
            background=superficie,
            borderwidth=1,
            relief="solid",
        )
        estilo.configure(
            "Section.TLabelframe.Label",
            background=superficie,
            foreground=texto,
            font=self.fuente_base,
        )

        estilo.configure(
            "Primary.TButton",
            background=primario,
            foreground="white",
            borderwidth=0,
            focusthickness=0,
            padding=(12, 8),
            font=self.fuente_base,
        )
        estilo.map(
            "Primary.TButton",
            background=[("active", primario_hover), ("disabled", "#bfcad6")],
            foreground=[("disabled", "#ffffff")],
        )

        estilo.configure(
            "Secondary.TButton",
            background=secundario,
            foreground="#1f2937",
            borderwidth=1,
            padding=(10, 7),
            font=self.fuente_base,
        )
        estilo.map(
            "Secondary.TButton",
            background=[("active", secundario_hover)],
        )

        estilo.configure(
            "TEntry",
            fieldbackground=superficie,
            bordercolor=borde,
            lightcolor=borde,
            padding=6,
        )
        estilo.configure(
            "TCombobox",
            fieldbackground=superficie,
            background=superficie,
            padding=5,
        )

        estilo.configure(
            "Treeview",
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground="#1f2937",
            rowheight=34,
            borderwidth=1,
        )
        estilo.configure(
            "Treeview.Heading",
            background="#e8f1fb",
            foreground="#1f2937",
            font=self.fuente_cabecera_tabla,
            relief="flat",
            padding=(8, 8),
        )
        estilo.map(
            "Treeview.Heading",
            background=[("active", "#dceaf8")],
        )

    # =========================
    # VENTANA
    # =========================
    def _configurar_icono_ventana(self) -> None:
        try:
            ruta_logo = os.path.join(self.base_dir, "imagenes", "logo_serisa.png")
            if os.path.exists(ruta_logo):
                self.icono_ventana = tk.PhotoImage(file=ruta_logo)
                self.iconphoto(True, self.icono_ventana)
        except Exception as e:
            self.logger.warning(f"No se pudo cargar el icono de la ventana: {e}")

    def _centrar(self) -> None:
        self.update_idletasks()
        ancho = self.winfo_width()
        alto = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.winfo_screenheight() // 2) - (alto // 2)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    # =========================
    # INTERFAZ
    # =========================
    def _crear_interfaz(self) -> None:
        contenedor = ttk.Frame(self, style="App.TFrame", padding=16)
        contenedor.pack(fill="both", expand=True)

        contenedor.columnconfigure(0, weight=1)
        contenedor.columnconfigure(1, weight=0)
        contenedor.rowconfigure(0, weight=1)

        panel_izq = ttk.Frame(contenedor, style="Card.TFrame", padding=16)
        panel_izq.grid(row=0, column=0, sticky="nsew")

        panel_der = ttk.Frame(contenedor, style="Card.TFrame", padding=12)
        panel_der.grid(row=0, column=1, sticky="ns", padx=(16, 0))

        cabecera_izq = ttk.Frame(panel_izq, style="Card.TFrame")
        cabecera_izq.pack(fill="x", pady=(0, 12))

        ttk.Label(
            cabecera_izq,
            text="Usuarios SERISA",
            style="PanelTitle.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            cabecera_izq,
            text="Gestiona usuarios de acceso a la aplicación.",
            style="PanelText.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        ttk.Label(
            panel_izq,
            textvariable=self.var_estado,
            style="Status.TLabel",
        ).pack(anchor="w", pady=(0, 12))

        columnas = ("username", "rol", "activo", "usuario_rfid", "creado_en")
        marco_tabla = ttk.Frame(panel_izq, style="Card.TFrame")
        marco_tabla.pack(fill="both", expand=True)

        marco_tabla.columnconfigure(0, weight=1)
        marco_tabla.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            marco_tabla,
            columns=columnas,
            show="headings",
        )
        self.tree.heading("username", text="Usuario")
        self.tree.heading("rol", text="Rol")
        self.tree.heading("activo", text="Activo")
        self.tree.heading("usuario_rfid", text="Usuario RFID")
        self.tree.heading("creado_en", text="Creado")

        self.tree.column("username", width=190, anchor="w")
        self.tree.column("rol", width=90, anchor="center")
        self.tree.column("activo", width=80, anchor="center")
        self.tree.column("usuario_rfid", width=220, anchor="w")
        self.tree.column("creado_en", width=150, anchor="center")

        self.tree.tag_configure("par", background="#ffffff")
        self.tree.tag_configure("impar", background="#f3f8ff")

        scroll_y = ttk.Scrollbar(marco_tabla, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<<TreeviewSelect>>", self._al_seleccionar_usuario)

        # Panel derecho
        self.bloque_edicion = ttk.LabelFrame(
            panel_der,
            text="Editar usuario seleccionado",
            style="Section.TLabelframe",
            padding=10,
        )
        self.bloque_edicion.pack(fill="x", pady=(0, 10))

        ttk.Label(self.bloque_edicion, text="Usuario", style="Field.TLabel").pack(anchor="w")
        self.entry_username_sel = ttk.Entry(
            self.bloque_edicion,
            textvariable=self.var_username_sel,
            state="readonly",
        )
        self.entry_username_sel.pack(fill="x", pady=(4, 8))

        ttk.Label(self.bloque_edicion, text="Rol", style="Field.TLabel").pack(anchor="w")
        self.combo_rol = ttk.Combobox(
            self.bloque_edicion,
            textvariable=self.var_rol_sel,
            values=self.ROLES,
            state="readonly",
        )
        self.combo_rol.pack(fill="x", pady=(4, 8))

        self.check_activo = ttk.Checkbutton(
            self.bloque_edicion,
            text="Usuario activo",
            variable=self.var_activo_sel,
        )
        self.check_activo.pack(anchor="w", pady=(0, 8))

        ttk.Label(self.bloque_edicion, text="Usuario RFID", style="Field.TLabel").pack(anchor="w")
        self.combo_usuario_rfid_sel = ttk.Combobox(
            self.bloque_edicion,
            textvariable=self.var_usuario_rfid_sel,
            state="normal",
        )
        self.combo_usuario_rfid_sel.pack(fill="x", pady=(4, 10))

        self.boton_guardar = ttk.Button(
            self.bloque_edicion,
            text="Guardar cambios",
            style="Primary.TButton",
            command=self._guardar_cambios_usuario,
        )
        self.boton_guardar.pack(fill="x")

        self.bloque_alta = ttk.LabelFrame(
            panel_der,
            text="Registrar usuario SERISA",
            style="Section.TLabelframe",
            padding=10,
        )
        self.bloque_alta.pack(fill="x", pady=(0, 10))

        ttk.Label(self.bloque_alta, text="Nombre", style="Field.TLabel").pack(anchor="w")
        self.entry_nuevo_username = ttk.Entry(
            self.bloque_alta,
            textvariable=self.var_nuevo_username,
        )
        self.entry_nuevo_username.pack(fill="x", pady=(4, 8))

        ttk.Label(self.bloque_alta, text="Rol", style="Field.TLabel").pack(anchor="w")
        self.combo_nuevo_rol = ttk.Combobox(
            self.bloque_alta,
            textvariable=self.var_nuevo_rol,
            values=self.ROLES,
            state="readonly",
        )
        self.combo_nuevo_rol.pack(fill="x", pady=(4, 8))

        ttk.Label(self.bloque_alta, text="Contraseña", style="Field.TLabel").pack(anchor="w")
        self.entry_nueva_password = ttk.Entry(
            self.bloque_alta,
            textvariable=self.var_nueva_password,
            show="*",
        )
        self.entry_nueva_password.pack(fill="x", pady=(4, 8))

        ttk.Label(self.bloque_alta, text="Usuario RFID (opcional)", style="Field.TLabel").pack(anchor="w")
        self.combo_nuevo_usuario_rfid = ttk.Combobox(
            self.bloque_alta,
            textvariable=self.var_nuevo_usuario_rfid,
            state="normal",
        )
        self.combo_nuevo_usuario_rfid.pack(fill="x", pady=(4, 10))

        self.boton_crear = ttk.Button(
            self.bloque_alta,
            text="Registrar usuario",
            style="Primary.TButton",
            command=self._registrar_usuario,
        )
        self.boton_crear.pack(fill="x")

        self.bloque_baja = ttk.LabelFrame(
            panel_der,
            text="Eliminar usuario SERISA",
            style="Section.TLabelframe",
            padding=10,
        )
        self.bloque_baja.pack(fill="x")

        ttk.Label(self.bloque_baja, text="Nombre", style="Field.TLabel").pack(anchor="w")
        self.entry_eliminar = ttk.Entry(
            self.bloque_baja,
            textvariable=self.var_eliminar_username,
        )
        self.entry_eliminar.pack(fill="x", pady=(4, 10))

        self.boton_eliminar = ttk.Button(
            self.bloque_baja,
            text="Eliminar usuario",
            style="Secondary.TButton",
            command=self._eliminar_usuario,
        )
        self.boton_eliminar.pack(fill="x")

    # =========================
    # DATOS
    # =========================
    def _cargar_usuarios_rfid(self) -> None:
        try:
            datos = self.servicio_fichajes.obtener_datos_desplegables()
            usuarios_asignados = datos.get("usuarios_asignados", [])

            # Todos los usuarios RFID existentes en fichajes
            todos_rfid = sorted({nombre for nombre, _uid in usuarios_asignados})

            # RFID ya usados en usuarios SERISA
            rfid_en_uso = {
                u["usuario_rfid"]
                for u in self.usuarios_cache
                if u.get("usuario_rfid")
            }

            # Solo disponibles para ALTA
            self.usuarios_rfid_disponibles = [r for r in todos_rfid if r not in rfid_en_uso]

            # Guardamos también todos para EDICIÓN
            self.usuarios_rfid_todos = todos_rfid

        except Exception:
            self.logger.exception("No se pudieron cargar los usuarios RFID")
            self.usuarios_rfid_disponibles = []
            self.usuarios_rfid_todos = []

        # Alta: solo disponibles
        self.combo_nuevo_usuario_rfid["values"] = [""] + self.usuarios_rfid_disponibles

        # Edición: todos
        self.combo_usuario_rfid_sel["values"] = [""] + self.usuarios_rfid_todos

    def _cargar_usuarios(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.usuarios_cache = self.servicio_autenticacion.listar_usuarios()

        for indice, usuario in enumerate(self.usuarios_cache):
            creado = usuario["creado_en"].strftime("%Y-%m-%d %H:%M") if usuario["creado_en"] else ""
            activo = "Sí" if usuario["activo"] else "No"
            usuario_rfid = usuario["usuario_rfid"] or ""
            tag = "par" if indice % 2 == 0 else "impar"

            self.tree.insert(
                "",
                "end",
                iid=str(usuario["id"]),
                values=(usuario["username"], usuario["rol"], activo, usuario_rfid, creado),
                tags=(tag,),
            )

    def _obtener_usuario_cache_por_id(self, user_id: int) -> dict | None:
        return next((u for u in self.usuarios_cache if u["id"] == user_id), None)

    # =========================
    # ESTADO
    # =========================
    def _actualizar_estado_botones(self) -> None:
        hay_seleccion = self.usuario_seleccionado_id is not None

        estado = "normal" if hay_seleccion else "disabled"
        self.combo_rol.configure(state="readonly" if hay_seleccion else "disabled")
        self.check_activo.configure(state=estado)
        self.combo_usuario_rfid_sel.configure(state="normal" if hay_seleccion else "disabled")
        self.boton_guardar.configure(state=estado)
        self.boton_eliminar.configure(state=estado if self.var_eliminar_username.get().strip() else "disabled")

    def _limpiar_panel_edicion(self) -> None:
        self.usuario_seleccionado_id = None
        self.var_username_sel.set("")
        self.var_rol_sel.set("basic")
        self.var_activo_sel.set(True)
        self.var_usuario_rfid_sel.set("")
        self.var_eliminar_username.set("")
        self._actualizar_estado_botones()

    def _set_estado(self, texto: str) -> None:
        self.var_estado.set(texto)

    # =========================
    # EVENTOS
    # =========================
    def _al_seleccionar_usuario(self, _event=None) -> None:
        seleccion = self.tree.selection()
        if not seleccion:
            self._limpiar_panel_edicion()
            self._set_estado("Selecciona un usuario o crea uno nuevo.")
            return

        user_id = int(seleccion[0])
        usuario = self._obtener_usuario_cache_por_id(user_id)
        if usuario is None:
            self._limpiar_panel_edicion()
            return

        self.usuario_seleccionado_id = usuario["id"]
        self.var_username_sel.set(usuario["username"])
        self.var_rol_sel.set(usuario["rol"])
        self.var_activo_sel.set(bool(usuario["activo"]))
        self.var_usuario_rfid_sel.set(usuario["usuario_rfid"] or "")
        self.var_eliminar_username.set(usuario["username"])

        self._actualizar_estado_botones()
        self._set_estado(f"Editando usuario: {usuario['username']}")

    # =========================
    # ACCIONES
    # =========================
    def _guardar_cambios_usuario(self) -> None:
        if self.usuario_seleccionado_id is None:
            messagebox.showwarning("Selección", "Selecciona un usuario de la tabla.")
            return

        usuario_rfid = self.var_usuario_rfid_sel.get().strip()
        rol = self.var_rol_sel.get().strip()
        activo = self.var_activo_sel.get()

        if self._usuario_rfid_ya_asignado(usuario_rfid, self.usuario_seleccionado_id):
            messagebox.showwarning(
                "RFID en uso",
                f"El usuario RFID '{usuario_rfid}' ya está asignado a otro usuario.",
            )
            return

        username = self.var_username_sel.get().strip()
        activo_texto = "Sí" if activo else "No"
        usuario_rfid_texto = usuario_rfid if usuario_rfid else "Sin asignar"

        confirmado = messagebox.askyesno(
            "Confirmar cambios",
            (
                f"¿Quieres guardar los cambios del usuario '{username}'?\n\n"
                f"Rol: {rol}\n"
                f"Activo: {activo_texto}\n"
                f"Usuario RFID: {usuario_rfid_texto}"
            ),
            parent=self,
        )
        if not confirmado:
            return

        try:
            self.servicio_autenticacion.actualizar_usuario(
                user_id=self.usuario_seleccionado_id,
                rol=rol,
                activo=activo,
                usuario_rfid=usuario_rfid,
            )
            self._cargar_usuarios()
            self._cargar_usuarios_rfid()
            self._set_estado("Usuario actualizado correctamente.")
            messagebox.showinfo("Correcto", "Usuario actualizado correctamente.", parent=self)
        except Exception as e:
            self.logger.exception("Error actualizando usuario")
            messagebox.showerror("Error", str(e), parent=self)

    def _registrar_usuario(self) -> None:
        username = self.var_nuevo_username.get().strip()
        rol = self.var_nuevo_rol.get().strip()
        password = self.var_nueva_password.get()
        usuario_rfid = self.var_nuevo_usuario_rfid.get().strip()

        if not username or not rol or not password:
            messagebox.showwarning(
                "Campos obligatorios",
                "Debes completar nombre, rol y contraseña.",
                parent=self,
            )
            return

        if self._usuario_rfid_ya_asignado(usuario_rfid):
            messagebox.showwarning(
                "RFID en uso",
                f"El usuario RFID '{usuario_rfid}' ya está asignado a otro usuario.",
                parent=self,
            )
            return

        usuario_rfid_texto = usuario_rfid if usuario_rfid else "Sin asignar"

        confirmado = messagebox.askyesno(
            "Confirmar registro",
            (
                f"¿Quieres registrar este usuario?\n\n"
                f"Nombre: {username}\n"
                f"Rol: {rol}\n"
                f"Usuario RFID: {usuario_rfid_texto}"
            ),
            parent=self,
        )
        if not confirmado:
            return

        try:
            self.servicio_autenticacion.crear_usuario(
                username=username,
                password_plano=password,
                rol=rol,
                activo=True,
                usuario_rfid=usuario_rfid,
            )
            self.var_nuevo_username.set("")
            self.var_nuevo_rol.set("basic")
            self.var_nueva_password.set("")
            self.var_nuevo_usuario_rfid.set("")
            self._cargar_usuarios()
            self._cargar_usuarios_rfid()
            self._set_estado("Usuario creado correctamente.")
            messagebox.showinfo("Correcto", "Usuario creado correctamente.", parent=self)
        except Exception as e:
            self.logger.exception("Error creando usuario")
            messagebox.showerror("Error", str(e), parent=self)

    def _eliminar_usuario(self) -> None:
        username = self.var_eliminar_username.get().strip()
        if not username:
            messagebox.showwarning("Campo obligatorio", "Debes indicar el nombre del usuario.")
            return

        if username == getattr(self.sesion, "username", ""):
            messagebox.showwarning("Operación no permitida", "No puedes eliminar tu propio usuario.")
            return

        confirmado = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Seguro que quieres eliminar el usuario '{username}'?",
        )
        if not confirmado:
            return

        try:
            self.servicio_autenticacion.eliminar_usuario(username)
            self._limpiar_panel_edicion()
            self._cargar_usuarios()
            self._set_estado("Usuario eliminado correctamente.")
            messagebox.showinfo("Correcto", "Usuario eliminado correctamente.")
        except Exception as e:
            self.logger.exception("Error eliminando usuario")
            messagebox.showerror("Error", str(e))

    def _usuario_rfid_ya_asignado(self, usuario_rfid: str, user_id_actual: int | None = None) -> bool:
        if not usuario_rfid:
            return False

        for usuario in self.usuarios_cache:
            if usuario["usuario_rfid"] == usuario_rfid:
                # Permitir si es el mismo usuario que estamos editando
                if user_id_actual is not None and usuario["id"] == user_id_actual:
                    continue
                return True
        return False