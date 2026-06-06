# src/services/CrearSetInstrucciones.py
import tkinter as tk
from tkinter import ttk, messagebox


class VentanaCrearSetInstrucciones:
    def __init__(self, parent, controlador, procesador):
        self.controlador = controlador
        self.procesador  = procesador

        self.ventana = tk.Toplevel(parent)
        self.ventana.title(f"Set de Instrucciones - {self.procesador.nombre}")
        self.ventana.resizable(True, True)
        self.ventana.transient(parent)
        self.ventana.grab_set()

        self._indice_editando = None
        self._campos_entries  = {}

        self._construir_interfaz()
        self._cargar_instrucciones_existentes()

        # Ajustar tamaño al contenido
        self.ventana.update_idletasks()
        self.ventana.geometry("")

    # ─────────────────────────────────────────────
    #  CONSTRUCCIÓN
    # ─────────────────────────────────────────────

    def _construir_interfaz(self):
        ttk.Label(
            self.ventana,
            text=f"Instrucciones para: {self.procesador.nombre}",
            font=("Arial", 14, "bold")
        ).pack(pady=10)

        panel_principal = ttk.Frame(self.ventana)
        panel_principal.pack(expand=True, fill="both", padx=10, pady=5)

        # --- PANEL IZQUIERDO ---
        panel_lista = ttk.LabelFrame(panel_principal, text="Instrucciones Agregadas")
        panel_lista.pack(side="left", fill="both", expand=True, padx=5)

        self._construir_treeview(panel_lista)
        self._construir_botones_lista(panel_lista)

        # --- PANEL DERECHO con scroll ---
        panel_der = ttk.LabelFrame(panel_principal, text="Nueva Instrucción")
        panel_der.pack(side="right", fill="both", expand=True, padx=5)
        self.panel_form = panel_der

        self._canvas = tk.Canvas(panel_der, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(panel_der, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self.form_inner     = ttk.Frame(self._canvas)
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self.form_inner, anchor="nw")
        self.form_inner.bind("<Configure>", lambda e: self._canvas.configure(
            scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(
            self._canvas_window, width=e.width))

        self._construir_form_fijo()

    def _construir_treeview(self, parent):
        """Treeview agrupado por formato, colapsable."""
        frame_tree = ttk.Frame(parent)
        frame_tree.pack(fill="both", expand=True, padx=5, pady=5)

        self.tree = ttk.Treeview(frame_tree, selectmode="browse", show="tree headings")
        self.tree["columns"] = ("mapeo",)
        self.tree.heading("#0",      text="Instrucción")
        self.tree.heading("mapeo",   text="Sintaxis")
        self.tree.column("#0",      width=120, minwidth=90)
        self.tree.column("mapeo",   width=160, minwidth=100)

        sb_v = ttk.Scrollbar(frame_tree, orient="vertical",   command=self.tree.yview)
        sb_h = ttk.Scrollbar(frame_tree, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=sb_v.set, xscrollcommand=sb_h.set)

        sb_v.pack(side="right",  fill="y")
        sb_h.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        # Tags visuales para grupos e instrucciones
        self.tree.tag_configure("grupo",  font=("Arial", 10, "bold"), foreground="#2c5f9e")
        self.tree.tag_configure("instr",  font=("Courier New", 10))

    def _construir_botones_lista(self, parent):
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", padx=5, pady=(0, 6))

        ttk.Button(btn_frame, text="Editar",
                   command=self.editar_instruccion).pack(side="left", expand=True,
                                                          fill="x", padx=(0, 2))
        ttk.Button(btn_frame, text="Eliminar",
                   command=self.eliminar_instruccion).pack(side="left", expand=True,
                                                            fill="x", padx=(2, 2))
        ttk.Button(btn_frame, text="",
                   command=self.mover_arriba).pack(side="left", padx=(2, 2))
        ttk.Button(btn_frame, text="",
                   command=self.mover_abajo).pack(side="left", padx=(2, 0))

    def _construir_form_fijo(self):
        f = self.form_inner

        ttk.Label(f, text="Mnemónico (ej. ADD):").grid(
            row=0, column=0, sticky="w", padx=8, pady=(10, 2))
        self.mnemonico_entry = ttk.Entry(f)
        self.mnemonico_entry.grid(row=1, column=0, sticky="ew", padx=8)

        ttk.Label(f, text="Formato de instrucción:").grid(
            row=4, column=0, sticky="w", padx=8, pady=(8, 2))
        self.formato_combo = ttk.Combobox(f, state="readonly")
        self.formato_combo.grid(row=5, column=0, sticky="ew", padx=8)
        self.formato_combo.bind("<<ComboboxSelected>>", self._on_formato_seleccionado)

        ttk.Label(f, text="Sintaxis de operandos:").grid(
            row=6, column=0, sticky="w", padx=8, pady=(8, 2))
        self.mapeo_entry = ttk.Entry(f)
        self.mapeo_entry.grid(row=7, column=0, sticky="ew", padx=8)
        ttk.Label(f,
                  text="Ej: 'rd, rs1, rs2'  |  'rs2, imm(rs1)'  |  'rd, rs1, imm'",
                  foreground="gray").grid(row=8, column=0, sticky="w", padx=8, pady=(0, 4))

        ttk.Label(f, text="Descripción:").grid(
            row=9, column=0, sticky="w", padx=8, pady=(4, 2))
        self.desc_entry = ttk.Entry(f)
        self.desc_entry.grid(row=10, column=0, sticky="ew", padx=8)

        ttk.Separator(f, orient="horizontal").grid(
            row=11, column=0, sticky="ew", padx=8, pady=8)

        ttk.Label(f, text="Valores de los campos del formato",
                  font=("Arial", 10, "bold")).grid(row=12, column=0, sticky="w", padx=8)
        ttk.Label(f, text="opcode/constante = binario fijo   |   registro/inmediato = dejar vacío",
                  foreground="gray").grid(row=13, column=0, sticky="w", padx=8, pady=(2, 6))

        self.frame_campos = ttk.Frame(f)
        self.frame_campos.grid(row=14, column=0, sticky="ew", padx=8)

        ttk.Separator(f, orient="horizontal").grid(
            row=15, column=0, sticky="ew", padx=8, pady=8)

        self.btn_guardar = ttk.Button(f, text="Agregar Instrucción",
                                      command=self.guardar_instruccion)
        self.btn_guardar.grid(row=16, column=0, sticky="ew", padx=8, pady=(0, 4))

        self.btn_cancelar = ttk.Button(f, text="Cancelar edición",
                                       command=self._cancelar_edicion)

        f.columnconfigure(0, weight=1)

        btn_frame = ttk.Frame(self.ventana)
        btn_frame.pack(fill="x", pady=10, padx=10)
        ttk.Button(btn_frame, text="Finalizar y Guardar",
                   command=self.finalizar).pack(side="right", padx=5)

        self._actualizar_combo_formatos()

    # ─────────────────────────────────────────────
    #  TREEVIEW — POBLAR Y REFRESCAR
    # ─────────────────────────────────────────────

    def _cargar_instrucciones_existentes(self):
        """Agrupa las instrucciones por formato y las muestra en el Treeview."""
        # Guardar qué grupos están abiertos
        abiertos = {iid for iid in self.tree.get_children()
                    if self.tree.item(iid, "open")}

        self.tree.delete(*self.tree.get_children())

        # Agrupar por formato
        grupos = {}
        for i, inst in enumerate(self.procesador.set_de_instrucciones):
            fmt = inst.get("formato", "Sin formato")
            grupos.setdefault(fmt, []).append((i, inst))

        for fmt_nombre, instrucciones in grupos.items():
            grupo_id = self.tree.insert(
                "", "end", iid=f"grupo_{fmt_nombre}",
                text=f"  {fmt_nombre}  ({len(instrucciones)})",
                tags=("grupo",),
                open=(f"grupo_{fmt_nombre}" in abiertos or not abiertos)
            )
            for idx_global, inst in instrucciones:
                mnem  = inst.get("mnemonico", "?")
                mapeo = inst.get("mapeo_operandos", "")
                self.tree.insert(
                    grupo_id, "end",
                    iid=f"inst_{idx_global}",
                    text=f"  {mnem}",
                    values=(mapeo,),
                    tags=("instr",)
                )

    def _indice_seleccionado(self):
        """Devuelve el índice global de la instrucción seleccionada, o None."""
        sel = self.tree.selection()
        if not sel:
            return None
        iid = sel[0]
        if not iid.startswith("inst_"):
            return None  # Es un grupo, no una instrucción
        return int(iid.split("_")[1])

    def _seleccionar_por_indice(self, idx):
        """Selecciona y muestra la instrucción con ese índice global."""
        iid = f"inst_{idx}"
        if self.tree.exists(iid):
            self.tree.selection_set(iid)
            self.tree.see(iid)

    # ─────────────────────────────────────────────
    #  MOVER ARRIBA / ABAJO
    # ─────────────────────────────────────────────

    def mover_arriba(self):
        idx = self._indice_seleccionado()
        if idx is None or idx == 0:
            return
        lst = self.procesador.set_de_instrucciones
        lst[idx], lst[idx - 1] = lst[idx - 1], lst[idx]
        self._cargar_instrucciones_existentes()
        self._seleccionar_por_indice(idx - 1)

    def mover_abajo(self):
        idx = self._indice_seleccionado()
        lst = self.procesador.set_de_instrucciones
        if idx is None or idx >= len(lst) - 1:
            return
        lst[idx], lst[idx + 1] = lst[idx + 1], lst[idx]
        self._cargar_instrucciones_existentes()
        self._seleccionar_por_indice(idx + 1)

    # ─────────────────────────────────────────────
    #  COMBO Y CAMPOS DINÁMICOS
    # ─────────────────────────────────────────────

    def _actualizar_combo_formatos(self):
        nombres = [fmt.get("nombre", "?") for fmt in self.procesador.formato_de_sintaxis]
        self.formato_combo["values"] = nombres
        if nombres:
            self.formato_combo.current(0)
            self._construir_campos_dinamicos(nombres[0])

    def _on_formato_seleccionado(self, event=None):
        self._construir_campos_dinamicos(self.formato_combo.get())

    def _construir_campos_dinamicos(self, nombre_formato, valores=None):
        for w in self.frame_campos.winfo_children():
            w.destroy()
        self._campos_entries = {}

        fmt = next(
            (f for f in self.procesador.formato_de_sintaxis
             if f.get("nombre") == nombre_formato), None)
        if not fmt:
            return

        for i, campo in enumerate(fmt.get("campos_operandos", [])):
            # Soportar modelo nuevo (dict con tipo) y viejo (lista)
            if isinstance(campo, list):
                nombre_c = campo[0]
                bits_c   = campo[1]
                tipo_c   = "constante"
            else:
                nombre_c = campo["nombre"]
                bits_c   = campo["bits"]
                tipo_c   = campo.get("tipo", "constante")

            es_fijo = tipo_c in ("opcode", "constante")
            etiqueta = f"{nombre_c}  ({bits_c} bits, {tipo_c}):"

            ttk.Label(self.frame_campos, text=etiqueta).grid(
                row=i, column=0, sticky="w", pady=3)

            entry = ttk.Entry(self.frame_campos, width=22)
            entry.grid(row=i, column=1, sticky="ew", padx=(8, 0), pady=3)

            if es_fijo:
                valor = (valores or {}).get(nombre_c, "")
                if valor:
                    entry.insert(0, valor)
            else:
                # Campos variables (registro/inmediato) no llevan valor fijo
                entry.insert(0, "")
                entry.config(state="disabled")

            self._campos_entries[nombre_c] = entry

        self.frame_campos.columnconfigure(1, weight=1)
        self.form_inner.update_idletasks()
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _leer_campos_dinamicos(self):
        resultado = {}
        for nombre, entry in self._campos_entries.items():
            # Los entries deshabilitados (registro/inmediato) se guardan como ""
            if str(entry.cget("state")) == "disabled":
                resultado[nombre] = ""
            else:
                resultado[nombre] = entry.get().strip()
        return resultado

    # ─────────────────────────────────────────────
    #  GUARDAR
    # ─────────────────────────────────────────────

    def guardar_instruccion(self):
        mnem   = self.mnemonico_entry.get().strip().upper()
        fmt    = self.formato_combo.get()
        mapeo  = self.mapeo_entry.get().strip()
        desc   = self.desc_entry.get().strip()
        campos = self._leer_campos_dinamicos()

        if not mnem:
            messagebox.showwarning("Atención", "El mnemónico no puede estar vacío.")
            return
        if not fmt:
            messagebox.showwarning("Atención", "Selecciona un formato.")
            return
        if not mapeo:
            messagebox.showwarning("Atención",
                                   "Define la sintaxis de operandos.\n"
                                   "Ej: 'rd, rs1, rs2'  o  'rs2, imm(rs1)'")
            return
        for nombre_c, valor in campos.items():
            if valor and not all(b in "01" for b in valor):
                messagebox.showwarning("Campo inválido",
                                       f"El campo '{nombre_c}' debe ser binario o vacío.")
                return
        for i, inst in enumerate(self.procesador.set_de_instrucciones):
            if inst.get("mnemonico") == mnem and i != self._indice_editando:
                messagebox.showwarning("Duplicado", f"Ya existe '{mnem}'.")
                return

        nueva = {
            "mnemonico":       mnem,
            "formato":         fmt,
            "mapeo_operandos": mapeo,
            "descripcion":     desc,
            "campos":          campos
        }

        if self._indice_editando is not None:
            self.procesador.set_de_instrucciones[self._indice_editando] = nueva
            self._cancelar_edicion()
            messagebox.showinfo("Actualizado", f"Instrucción '{mnem}' actualizada.")
        else:
            self.procesador.set_de_instrucciones.append(nueva)

        self._cargar_instrucciones_existentes()
        self._limpiar_formulario()

    # ─────────────────────────────────────────────
    #  EDITAR
    # ─────────────────────────────────────────────

    def editar_instruccion(self):
        idx = self._indice_seleccionado()
        if idx is None:
            messagebox.showinfo("Selección",
                                "Selecciona una instrucción (no un grupo) para editarla.")
            return

        inst = self.procesador.set_de_instrucciones[idx]
        self._indice_editando = idx
        self.panel_form.config(text=f"Editando: {inst.get('mnemonico', '?')}")
        self.btn_guardar.config(text="GUARDAR CAMBIOS")
        self.btn_cancelar.grid(row=17, column=0, sticky="ew", padx=8, pady=(0, 8))

        self.mnemonico_entry.delete(0, tk.END)
        self.mnemonico_entry.insert(0, inst.get("mnemonico", ""))

        fmt_nombre = inst.get("formato", "")
        nombres = list(self.formato_combo["values"])
        if fmt_nombre in nombres:
            self.formato_combo.current(nombres.index(fmt_nombre))

        self.mapeo_entry.delete(0, tk.END)
        self.mapeo_entry.insert(0, inst.get("mapeo_operandos", ""))
        self.desc_entry.delete(0, tk.END)
        self.desc_entry.insert(0, inst.get("descripcion", ""))

        self._construir_campos_dinamicos(fmt_nombre, valores=inst.get("campos", {}))

    def _cancelar_edicion(self):
        self._indice_editando = None
        self.panel_form.config(text="Nueva Instrucción")
        self.btn_guardar.config(text="Agregar Instrucción")
        self.btn_cancelar.grid_remove()
        self._limpiar_formulario()

    # ─────────────────────────────────────────────
    #  ELIMINAR
    # ─────────────────────────────────────────────

    def eliminar_instruccion(self):
        idx = self._indice_seleccionado()
        if idx is None:
            messagebox.showinfo("Selección",
                                "Selecciona una instrucción (no un grupo) para eliminarla.")
            return

        mnem = self.procesador.set_de_instrucciones[idx].get("mnemonico", "?")
        if messagebox.askyesno("Confirmar",
                               f"¿Estás seguro que quieres borrar '{mnem}'?"):
            del self.procesador.set_de_instrucciones[idx]
            if self._indice_editando == idx:
                self._cancelar_edicion()
            self._cargar_instrucciones_existentes()

    # ─────────────────────────────────────────────
    #  UTILIDADES
    # ─────────────────────────────────────────────

    def _limpiar_formulario(self):
        self.mnemonico_entry.delete(0, tk.END)
        self.mapeo_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        if self.formato_combo["values"]:
            self.formato_combo.current(0)
            self._construir_campos_dinamicos(self.formato_combo.get())

    # ─────────────────────────────────────────────
    #  FINALIZAR
    # ─────────────────────────────────────────────

    def finalizar(self):
        if self.procesador.ruta_archivo:
            try:
                self.procesador.guardarEnJSON(self.procesador.ruta_archivo)
                self.ventana.destroy()
                messagebox.showinfo("Guardado",
                    f"Set de instrucciones guardado en:\n{self.procesador.ruta_archivo}")
            except Exception as e:
                messagebox.showerror("Error al guardar", f"No se pudo guardar:\n{e}")
        else:
            messagebox.showwarning("Ruta no encontrada",
                                   "No se encontró la ruta del archivo.")
