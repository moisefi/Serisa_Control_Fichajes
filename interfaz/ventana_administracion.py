from __future__ import annotations

import os
import tkinter as tk
from tkinter import messagebox, ttk


class VentanaAdministracion(tk.Toplevel):
    ROLES = ("admin", "rrhh", "basic")

    def __init__(self, master, servicio_autenticacion, logger, sesion) -> None:
        super().__init__(master)

        self.servicio_autenticacion = servicio_autenticacion
        self.logger = logger
        self.sesion = sesion

        if getattr(self.sesion, "rol", "").lower() != "admin":
            raise PermissionError("Solo un administrador puede abrir esta ventana")

        self.icono_ventana = None
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.usuario_seleccionado_id: int | None = None

        self.var_username_sel = tk.StringVar()
        self.var_rol_sel = tk.StringVar(value="basic")
        self.var_activo_sel = tk.BooleanVar(value=True)

        self.var_nuevo_username = tk.StringVar()
        self.var_nuevo_rol = tk.StringVar(value="basic")
        self.var_nueva_password = tk.StringVar()

        self.var_eliminar_username = tk.StringVar()

        self.title("Administración · Usuarios SERISA")
        self.geometry("1180x850")
        self.minsize(1180, 850)
        self.configure(bg="#eef3f8")
        self.transient(master)

        self._crear_estilos()
        self._configurar_icono_ventana()
        self._crear_interfaz()
        self._centrar()
        self._cargar_usuarios()

    def _crear_estilos(self) -> None:
        estilo = ttk.Style(self)
        try:
            if "clam" in estilo.theme_names():
                estilo.theme_use("clam")
        except Exception:
            pass

        estilo.configure("App.TFrame", background="#eef3f8")
        estilo.configure("Card.TFrame", background="#ffffff")
        estilo.configure("PanelTitle.TLabel", background="#ffffff", foreground="#132238", font=("TkHeadingFont", 14, "bold"))
        estilo.configure("PanelText.TLabel", background="#ffffff", foreground="#5f6b7a")
        estilo.configure("Field.TLabel", background="#ffffff", foreground="#132238")
        estilo.configure("Primary.TButton", padding=(14, 10))
        estilo.configure("Danger.TButton", padding=(14, 10))

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

    def _crear_interfaz(self) -> None:
        contenedor = ttk.Frame(self, style="App.TFrame", padding=16)
        contenedor.pack(fill="both", expand=True)

        panel_izq = ttk.Frame(contenedor, style="Card.TFrame", padding=16)
        panel_izq.pack(side="left", fill="both", expand=True)

        panel_der = ttk.Frame(contenedor, style="Card.TFrame", padding=16)
        panel_der.pack(side="right", fill="y", padx=(16, 0))

        ttk.Label(panel_izq, text="Usuarios SERISA", style="PanelTitle.TLabel").pack(anchor="w")
        ttk.Label(
            panel_izq,
            text="Gestiona usuarios de acceso a la aplicación.",
            style="PanelText.TLabel",
        ).pack(anchor="w", pady=(4, 14))

        columnas = ("username", "rol", "activo", "creado_en")
        self.tree = ttk.Treeview(panel_izq, columns=columnas, show="headings", height=18)
        self.tree.heading("username", text="Usuario")
        self.tree.heading("rol", text="Rol")
        self.tree.heading("activo", text="Activo")
        self.tree.heading("creado_en", text="Creado")

        self.tree.column("username", width=220, anchor="w")
        self.tree.column("rol", width=120, anchor="center")
        self.tree.column("activo", width=100, anchor="center")
        self.tree.column("creado_en", width=180, anchor="center")

        scroll_y = ttk.Scrollbar(panel_izq, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._al_seleccionar_usuario)

        # Panel derecho
        bloque_edicion = ttk.LabelFrame(panel_der, text="Editar usuario seleccionado", padding=14)
        bloque_edicion.pack(fill="x", pady=(0, 16))

        ttk.Label(bloque_edicion, text="Usuario", style="Field.TLabel").pack(anchor="w")
        ttk.Entry(bloque_edicion, textvariable=self.var_username_sel, state="readonly").pack(fill="x", pady=(4, 10))

        ttk.Label(bloque_edicion, text="Rol", style="Field.TLabel").pack(anchor="w")
        self.combo_rol = ttk.Combobox(
            bloque_edicion,
            textvariable=self.var_rol_sel,
            values=self.ROLES,
            state="readonly",
        )
        self.combo_rol.pack(fill="x", pady=(4, 10))

        ttk.Checkbutton(
            bloque_edicion,
            text="Usuario activo",
            variable=self.var_activo_sel,
        ).pack(anchor="w", pady=(0, 12))

        ttk.Button(
            bloque_edicion,
            text="Guardar cambios",
            style="Primary.TButton",
            command=self._guardar_cambios_usuario,
        ).pack(fill="x")

        bloque_alta = ttk.LabelFrame(panel_der, text="Registrar usuario SERISA", padding=14)
        bloque_alta.pack(fill="x", pady=(0, 16))

        ttk.Label(bloque_alta, text="Nombre", style="Field.TLabel").pack(anchor="w")
        ttk.Entry(bloque_alta, textvariable=self.var_nuevo_username).pack(fill="x", pady=(4, 10))

        ttk.Label(bloque_alta, text="Rol", style="Field.TLabel").pack(anchor="w")
        ttk.Combobox(
            bloque_alta,
            textvariable=self.var_nuevo_rol,
            values=self.ROLES,
            state="readonly",
        ).pack(fill="x", pady=(4, 10))

        ttk.Label(bloque_alta, text="Contraseña", style="Field.TLabel").pack(anchor="w")
        ttk.Entry(
            bloque_alta,
            textvariable=self.var_nueva_password,
            show="*",
        ).pack(fill="x", pady=(4, 12))

        ttk.Button(
            bloque_alta,
            text="Registrar usuario",
            style="Primary.TButton",
            command=self._registrar_usuario,
        ).pack(fill="x")

        bloque_baja = ttk.LabelFrame(panel_der, text="Eliminar usuario SERISA", padding=14)
        bloque_baja.pack(fill="x")

        ttk.Label(bloque_baja, text="Nombre", style="Field.TLabel").pack(anchor="w")
        ttk.Entry(bloque_baja, textvariable=self.var_eliminar_username).pack(fill="x", pady=(4, 12))

        ttk.Button(
            bloque_baja,
            text="Eliminar usuario",
            command=self._eliminar_usuario,
        ).pack(fill="x")

    def _cargar_usuarios(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        usuarios = self.servicio_autenticacion.listar_usuarios()
        for usuario in usuarios:
            creado = usuario["creado_en"].strftime("%Y-%m-%d %H:%M") if usuario["creado_en"] else ""
            activo = "Sí" if usuario["activo"] else "No"
            self.tree.insert(
                "",
                "end",
                iid=str(usuario["id"]),
                values=(usuario["username"], usuario["rol"], activo, creado),
            )

    def _al_seleccionar_usuario(self, _event=None) -> None:
        seleccion = self.tree.selection()
        if not seleccion:
            return

        user_id = int(seleccion[0])
        usuarios = self.servicio_autenticacion.listar_usuarios()
        usuario = next((u for u in usuarios if u["id"] == user_id), None)
        if usuario is None:
            return

        self.usuario_seleccionado_id = usuario["id"]
        self.var_username_sel.set(usuario["username"])
        self.var_rol_sel.set(usuario["rol"])
        self.var_activo_sel.set(bool(usuario["activo"]))

    def _guardar_cambios_usuario(self) -> None:
        if self.usuario_seleccionado_id is None:
            messagebox.showwarning("Selección", "Selecciona un usuario de la tabla.")
            return

        try:
            self.servicio_autenticacion.actualizar_usuario(
                self.usuario_seleccionado_id,
                self.var_rol_sel.get(),
                self.var_activo_sel.get(),
            )
            self._cargar_usuarios()
            messagebox.showinfo("Correcto", "Usuario actualizado correctamente.")
        except Exception as e:
            self.logger.exception("Error actualizando usuario")
            messagebox.showerror("Error", str(e))

    def _registrar_usuario(self) -> None:
        username = self.var_nuevo_username.get().strip()
        rol = self.var_nuevo_rol.get().strip()
        password = self.var_nueva_password.get()

        if not username or not rol or not password:
            messagebox.showwarning("Campos obligatorios", "Debes completar nombre, rol y contraseña.")
            return

        try:
            self.servicio_autenticacion.crear_usuario(username, password, rol, True)
            self.var_nuevo_username.set("")
            self.var_nuevo_rol.set("basic")
            self.var_nueva_password.set("")
            self._cargar_usuarios()
            messagebox.showinfo("Correcto", "Usuario creado correctamente.")
        except Exception as e:
            self.logger.exception("Error creando usuario")
            messagebox.showerror("Error", str(e))

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
            f"¿Seguro que quieres eliminar el usuario '{username}'?"
        )
        if not confirmado:
            return

        try:
            self.servicio_autenticacion.eliminar_usuario(username)
            self.var_eliminar_username.set("")
            self._cargar_usuarios()
            messagebox.showinfo("Correcto", "Usuario eliminado correctamente.")
        except Exception as e:
            self.logger.exception("Error eliminando usuario")
            messagebox.showerror("Error", str(e))