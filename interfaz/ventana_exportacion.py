from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from tkcalendar import DateEntry

from servicios.servicio_exportacion import ExportadorExcel, ExportadorPDF
from servicios.servicio_fichajes import ServicioFichajes


class VentanaExportacion(tk.Toplevel):
    def __init__(self, ventana_padre: tk.Misc, servicio_fichajes: ServicioFichajes, modo: str = "excel") -> None:
        super().__init__(ventana_padre)
        self.ventana_padre = ventana_padre
        self.servicio_fichajes = servicio_fichajes
        self.modo = modo.lower()

        self.title(f"Exportar a {self.modo.upper()}")
        self.geometry("500x420")
        self.resizable(False, False)
        self.transient(ventana_padre)
        self.grab_set()

        self.var_usuario = tk.StringVar()
        self.var_uid = tk.StringVar()
        self.var_fecha_desde = tk.StringVar()
        self.var_fecha_hasta = tk.StringVar()
        self.combo_usuarios: ttk.Combobox | None = None
        self.fecha_desde_activa = False
        self.fecha_hasta_activa = False

        self._crear_interfaz()
        self._cargar_usuarios()

    def _crear_interfaz(self) -> None:
        marco = ttk.Frame(self, padding=18)
        marco.pack(fill="both", expand=True)
        marco.columnconfigure(0, weight=1)

        ttk.Label(marco, text=f"Exportación a {self.modo.upper()}", font=("Segoe UI Semibold", 15, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            marco,
            text="Selecciona filtros opcionales para generar un informe.",
        ).grid(row=1, column=0, sticky="w", pady=(4, 14))

        ttk.Label(marco, text="Usuario").grid(row=2, column=0, sticky="w", pady=(0, 5))
        self.combo_usuarios = ttk.Combobox(marco, textvariable=self.var_usuario, state="normal", width=40)
        self.combo_usuarios.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        self.combo_usuarios.bind("<KeyRelease>", self._filtrar_usuario)

        ttk.Label(marco, text="Tarjeta").grid(row=4, column=0, sticky="w", pady=(0, 5))
        ttk.Entry(marco, textvariable=self.var_uid).grid(row=5, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(marco, text="Fecha desde").grid(row=6, column=0, sticky="w", pady=(0, 5))
        frame_fecha_desde = ttk.Frame(marco)
        frame_fecha_desde.grid(row=7, column=0, sticky="ew", pady=(0, 10))
        frame_fecha_desde.columnconfigure(0, weight=1)

        self.calendario_desde = DateEntry(frame_fecha_desde, date_pattern="yyyy-mm-dd")
        self.calendario_desde.grid(row=0, column=0, sticky="ew")
        self.calendario_desde.delete(0, tk.END)
        self.calendario_desde.bind("<<DateEntrySelected>>", lambda e: self._activar_fecha("desde"))
        self.calendario_desde.bind("<KeyRelease>", lambda e: self._detectar_borrado_fecha("desde"))
        ttk.Button(frame_fecha_desde, text="✕", width=3, command=lambda: self._limpiar_fecha(self.calendario_desde)).grid(
            row=0, column=1, padx=(6, 0)
        )

        ttk.Label(marco, text="Fecha hasta").grid(row=8, column=0, sticky="w", pady=(0, 5))
        frame_fecha_hasta = ttk.Frame(marco)
        frame_fecha_hasta.grid(row=9, column=0, sticky="ew", pady=(0, 16))
        frame_fecha_hasta.columnconfigure(0, weight=1)

        self.calendario_hasta = DateEntry(frame_fecha_hasta, date_pattern="yyyy-mm-dd")
        self.calendario_hasta.grid(row=0, column=0, sticky="ew")
        self.calendario_hasta.delete(0, tk.END)
        self.calendario_hasta.bind("<<DateEntrySelected>>", lambda e: self._activar_fecha("hasta"))
        self.calendario_hasta.bind("<KeyRelease>", lambda e: self._detectar_borrado_fecha("hasta"))
        ttk.Button(frame_fecha_hasta, text="✕", width=3, command=lambda: self._limpiar_fecha(self.calendario_hasta)).grid(
            row=0, column=1, padx=(6, 0)
        )

        acciones = ttk.Frame(marco)
        acciones.grid(row=10, column=0, sticky="ew")
        acciones.columnconfigure(0, weight=1)
        ttk.Button(acciones, text="Cancelar", command=self.destroy).grid(row=0, column=0, sticky="w")
        ttk.Button(acciones, text="Generar archivo", command=self._generar_archivo).grid(row=0, column=1, sticky="e")

    def _cargar_usuarios(self) -> None:
        try:
            usuarios = self.servicio_fichajes.repositorio.obtener_usuarios()
            nombres = [""] + [usuario[1] for usuario in usuarios]
            self.lista_usuarios = nombres
            assert self.combo_usuarios is not None
            self.combo_usuarios["values"] = nombres
            self.combo_usuarios.current(0)
        except Exception as error:
            messagebox.showerror("Error", f"No se pudieron cargar los usuarios:\n{error}", parent=self)

    def _obtener_filtros(self) -> tuple[str | None, str | None, str | None, str | None]:
        usuario = self.var_usuario.get().strip() or None
        uid = self.var_uid.get().strip() or None
        fecha_desde = self.calendario_desde.get().strip() if self.fecha_desde_activa else None
        fecha_hasta = self.calendario_hasta.get().strip() if self.fecha_hasta_activa else None

        if fecha_desde:
            fecha_desde = fecha_desde + " 00:00:00"
        if fecha_hasta:
            fecha_hasta = fecha_hasta + " 23:59:59"

        return usuario, uid, fecha_desde, fecha_hasta

    @staticmethod
    def _texto_filtros(usuario: str | None, uid: str | None, fecha_desde: str | None, fecha_hasta: str | None) -> str:
        partes = []
        if usuario:
            partes.append(f"usuario={usuario}")
        if uid:
            partes.append(f"uid={uid}")
        if fecha_desde:
            partes.append(f"desde={fecha_desde}")
        if fecha_hasta:
            partes.append(f"hasta={fecha_hasta}")
        return ", ".join(partes) if partes else "sin filtros"

    def _generar_archivo(self) -> None:
        try:
            usuario, uid, fecha_desde, fecha_hasta = self._obtener_filtros()
            filas = self.servicio_fichajes.obtener_registros_para_exportacion(
                usuario=usuario,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                uid_tarjeta=uid,
            )
            if not filas:
                messagebox.showinfo("Sin datos", "No hay registros con esos filtros", parent=self)
                return

            if self.modo == "excel":
                ruta = filedialog.asksaveasfilename(
                    parent=self,
                    defaultextension=".xlsx",
                    filetypes=[("Archivo Excel", "*.xlsx")],
                )
                if not ruta:
                    return
                ExportadorExcel.exportar(ruta, filas)
                messagebox.showinfo("Correcto", "Excel generado correctamente", parent=self)
                self.destroy()
                return

            ruta = filedialog.asksaveasfilename(
                parent=self,
                defaultextension=".pdf",
                filetypes=[("Archivo PDF", "*.pdf")],
            )
            if not ruta:
                return
            filtros_texto = self._texto_filtros(usuario, uid, fecha_desde, fecha_hasta)
            ExportadorPDF.exportar(ruta, filas, filtros_texto)
            messagebox.showinfo("Correcto", "PDF generado correctamente", parent=self)
            self.destroy()
        except Exception as error:
            messagebox.showerror("Error", str(error), parent=self)

    def _filtrar_usuario(self, _event=None) -> None:
        texto = self.var_usuario.get().strip().lower()
        if not texto:
            filtrados = self.lista_usuarios
        else:
            filtrados = [u for u in self.lista_usuarios if texto in u.lower()]
        self.combo_usuarios["values"] = filtrados
        if len(filtrados) == 1:
            self.var_usuario.set(filtrados[0])

    def _limpiar_fecha(self, calendario):
        calendario.delete(0, tk.END)
        if calendario == self.calendario_desde:
            self.fecha_desde_activa = False
        else:
            self.fecha_hasta_activa = False

    def _activar_fecha(self, tipo):
        if tipo == "desde":
            self.fecha_desde_activa = True
        else:
            self.fecha_hasta_activa = True

    def _detectar_borrado_fecha(self, tipo):
        if tipo == "desde":
            texto = self.calendario_desde.get().strip()
            self.fecha_desde_activa = bool(texto)
        else:
            texto = self.calendario_hasta.get().strip()
            self.fecha_hasta_activa = bool(texto)
