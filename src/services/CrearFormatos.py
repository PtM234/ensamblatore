# src/services/CrearFormatos.py
import tkinter as tk
from tkinter import ttk, messagebox
from models.formato_instruccion import FormatoDeInstruccion


class VentanaCrearFormatos:
    TIPOS = ("opcode", "constante", "registro", "inmediato")

    def __init__(self, parent, controlador, procesador, mostrar_siguiente=False):
        self.controlador = controlador
        self.procesador = procesador
        self.mostrar_siguiente = mostrar_siguiente

        self.ventana = tk.Toplevel(parent)
        self.ventana.title(f"Formatos de Instrucción - {procesador.nombre}")
        self.ventana.resizable(True, True)
        self.ventana.transient(parent)
        self.ventana.grab_set()

        self.lista_operandos_temporal = []
        self._indice_editando = None

        self._construir_interfaz()
        self._cargar_formatos_existentes()

        self.ventana.update_idletasks()
        self.ventana.geometry("")

    # ─────────────────────────────────────────────
    #  CONSTRUCCIÓN
    # ─────────────────────────────────────────────

    def _construir_interfaz(self):
        ttk.Label(self.ventana, text=f"Definir Formatos para: {self.procesador.nombre}",
                  font=("Arial", 14, "bold")).pack(pady=10)

        panel_principal = ttk.Frame(self.ventana)
        panel_principal.pack(expand=True, fill="both", padx=10)
        panel_principal.columnconfigure(0, weight=1)
        panel_principal.columnconfigure(1, weight=2)

        # === IZQUIERDA: LISTA DE FORMATOS ===
        frame_izq = ttk.LabelFrame(panel_principal, text="Formatos Existentes")
        frame_izq.grid(row=0, column=0, sticky="nsew", padx=5)

        self.lista_formatos = tk.Listbox(frame_izq, selectmode="single")
        self.lista_formatos.pack(expand=True, fill="both", padx=5, pady=5)

        btn_fmt_frame = ttk.Frame(frame_izq)
        btn_fmt_frame.pack(fill="x", padx=5, pady=(0, 8))

        ttk.Button(btn_fmt_frame, text="Editar",
                   command=self.editar_formato).pack(side="left", expand=True, fill="x", padx=(0, 2))
        ttk.Button(btn_fmt_frame, text="Eliminar",
                   command=self.eliminar_formato).pack(side="left", expand=True, fill="x", padx=(2, 2))
        ttk.Button(btn_fmt_frame, text="",
                   command=self.mover_formato_arriba).pack(side="left", padx=(2, 2))
        ttk.Button(btn_fmt_frame, text="",
                   command=self.mover_formato_abajo).pack(side="left", padx=(2, 0))

        # === DERECHA: CREAR / EDITAR FORMATO ===
        self.frame_der = ttk.LabelFrame(panel_principal, text="Nuevo Formato")
        self.frame_der.grid(row=0, column=1, sticky="nsew", padx=5)

        # ── Nombre y dirección de lectura ─────────────────────────────
        form_top = ttk.Frame(self.frame_der)
        form_top.pack(fill="x", padx=5, pady=5)

        ttk.Label(form_top, text="Nombre (ej. Tipo-R):").grid(row=0, column=0, sticky="w")
        self.nombre_fmt_entry = ttk.Entry(form_top, width=15)
        self.nombre_fmt_entry.grid(row=0, column=1, padx=5)

        ttk.Label(form_top, text="Lectura:").grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.lectura_combo = ttk.Combobox(
            form_top, state="readonly", width=24,
            values=["MSB primero (izq → der)", "LSB primero (der → izq)"])
        self.lectura_combo.current(0)
        self.lectura_combo.grid(row=1, column=1, padx=5, pady=(4, 0), sticky="w")
        ttk.Label(form_top,
                  text="MSB primero: el primer campo ocupa los bits más significativos.",
                  foreground="gray").grid(row=2, column=0, columnspan=2, sticky="w", pady=(2, 0))

        ttk.Separator(self.frame_der, orient="horizontal").pack(fill="x", pady=8)
        ttk.Label(self.frame_der, text="Agregar Campos",
                  font=("Arial", 10, "bold")).pack()

        # ── Fila de entrada de campo ──────────────────────────────────
        form_campos = ttk.Frame(self.frame_der)
        form_campos.pack(fill="x", padx=8, pady=4)

        ttk.Label(form_campos, text="Nombre:").grid(row=0, column=0, sticky="w")
        self.nombre_campo_entry = ttk.Entry(form_campos, width=10)
        self.nombre_campo_entry.grid(row=0, column=1, padx=4)

        ttk.Label(form_campos, text="Bits:").grid(row=0, column=2, sticky="w")
        self.bits_campo_entry = ttk.Entry(form_campos, width=5)
        self.bits_campo_entry.grid(row=0, column=3, padx=4)

        ttk.Label(form_campos, text="Tipo:").grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.tipo_campo_combo = ttk.Combobox(
            form_campos, state="readonly", width=12, values=list(self.TIPOS))
        self.tipo_campo_combo.current(2)  # "registro" por defecto
        self.tipo_campo_combo.grid(row=1, column=1, columnspan=2, padx=4,
                                   pady=(4, 0), sticky="w")

        ttk.Button(form_campos, text="Agregar campo", width=14,
                   command=self.agregar_campo_a_lista).grid(
            row=1, column=3, padx=4, pady=(4, 0))

        # Ayuda de tipos
        ttk.Label(
            form_campos,
            text="opcode/constante = valor fijo en la instrucción   |   "
                 "registro/inmediato = lo escribe el usuario",
            foreground="gray", wraplength=380, justify="left"
        ).grid(row=2, column=0, columnspan=4, sticky="w", pady=(4, 0))

        # ── Orden de bits ─────────────────────────────────────────────
        ttk.Label(form_campos,
                  text="Orden bits (ej: 1:0, 2:1, 11:4) — vacío = orden natural",
                  foreground="gray").grid(row=3, column=0, columnspan=4, sticky="w", pady=(6, 0))
        self.orden_bits_entry = ttk.Entry(form_campos, width=40)
        self.orden_bits_entry.grid(row=4, column=0, columnspan=4, sticky="ew", pady=2)

        # ── Lista de campos + botones por campo ───────────────────────
        self.lista_campos_view = tk.Listbox(self.frame_der, height=7,
                                            font=("Courier New", 10))
        self.lista_campos_view.pack(fill="x", padx=5, pady=5)

        btn_campos_frame = ttk.Frame(self.frame_der)
        btn_campos_frame.pack(fill="x", padx=5, pady=(0, 4))

        ttk.Button(btn_campos_frame, text="Editar",
                   command=self.editar_campo_seleccionado).pack(side="left", padx=(0, 4))
        ttk.Button(btn_campos_frame, text="Eliminar",
                   command=self.eliminar_campo_seleccionado).pack(side="left", padx=(0, 4))
        ttk.Button(btn_campos_frame, text="",
                   command=self.mover_campo_arriba).pack(side="left", padx=(0, 2))
        ttk.Button(btn_campos_frame, text="",
                   command=self.mover_campo_abajo).pack(side="left", padx=(0, 8))
        ttk.Button(btn_campos_frame, text="Limpiar todos",
                   command=self.limpiar_campos).pack(side="left")

        ttk.Separator(self.frame_der, orient="horizontal").pack(fill="x", padx=5, pady=6)

        # ── Botón guardar (único) ─────────────────────────────────────
        self.btn_guardar = ttk.Button(self.frame_der, text="GUARDAR FORMATO",
                                      command=self.guardar_formato)
        self.btn_guardar.pack(pady=4, fill="x", padx=20)

        self.btn_cancelar_edicion = ttk.Button(self.frame_der, text="Cancelar edición",
                                               command=self._cancelar_edicion)

        # --- BOTONES INFERIORES ---
        btn_frame = ttk.Frame(self.ventana)
        btn_frame.pack(fill="x", pady=10)

        if self.mostrar_siguiente:
            ttk.Button(btn_frame, text="Siguiente: Crear Instrucciones >>",
                       command=self.ir_a_instrucciones).pack(side="right", padx=20)

    # ─────────────────────────────────────────────
    #  CARGA INICIAL
    # ─────────────────────────────────────────────

    def _cargar_formatos_existentes(self):
        self.lista_formatos.delete(0, tk.END)
        for fmt in self.procesador.formato_de_sintaxis:
            nombre     = fmt.get("nombre", "?")
            total_bits = fmt.get("total_bits", "?")
            self.lista_formatos.insert(tk.END, f"{nombre} ({total_bits} bits)")

    # ─────────────────────────────────────────────
    #  AGREGAR / ELIMINAR CAMPO
    # ─────────────────────────────────────────────

    def _lectura_valor(self):
        """Devuelve 'msb_primero' o 'lsb_primero' según el combo."""
        return "lsb_primero" if self.lectura_combo.current() == 1 else "msb_primero"

    def agregar_campo_a_lista(self):
        nombre    = self.nombre_campo_entry.get().strip()
        bits_str  = self.bits_campo_entry.get().strip()
        tipo      = self.tipo_campo_combo.get()
        orden_str = self.orden_bits_entry.get().strip()

        if not nombre or not bits_str.isdigit():
            messagebox.showerror("Error", "Revisa el nombre y los bits del campo.")
            return
        if tipo not in self.TIPOS:
            messagebox.showerror("Error", "Selecciona un tipo de campo válido.")
            return

        # Solo puede haber un campo opcode por formato
        if tipo == "opcode":
            ya_hay = any(c.get("tipo") == "opcode" for c in self.lista_operandos_temporal)
            if ya_hay:
                messagebox.showerror(
                    "Error", "Ya existe un campo de tipo opcode en este formato.")
                return

        bits = int(bits_str)

        try:
            orden_bits = FormatoDeInstruccion.parsear_orden_bits(orden_str, bits)
        except ValueError as e:
            messagebox.showerror("Error en orden de bits", str(e))
            return

        campo = {"nombre": nombre, "bits": bits, "tipo": tipo, "orden_bits": orden_bits}
        self.lista_operandos_temporal.append(campo)
        self._refrescar_lista_campos()

        self.nombre_campo_entry.delete(0, tk.END)
        self.bits_campo_entry.delete(0, tk.END)
        self.orden_bits_entry.delete(0, tk.END)

    def eliminar_campo_seleccionado(self):
        seleccion = self.lista_campos_view.curselection()
        if not seleccion:
            messagebox.showinfo("Selección", "Selecciona un campo de la lista para eliminarlo.")
            return
        indice = seleccion[0]
        nombre_campo = self.lista_operandos_temporal[indice]["nombre"]
        if messagebox.askyesno("Confirmar", f"¿Eliminar el campo '{nombre_campo}'?"):
            del self.lista_operandos_temporal[indice]
            self._refrescar_lista_campos()

    def editar_campo_seleccionado(self):
        seleccion = self.lista_campos_view.curselection()
        if not seleccion:
            messagebox.showinfo("Selección", "Selecciona un campo para editarlo.")
            return
        indice = seleccion[0]
        campo  = self.lista_operandos_temporal[indice]

        self.nombre_campo_entry.delete(0, tk.END)
        self.nombre_campo_entry.insert(0, campo["nombre"])

        self.bits_campo_entry.delete(0, tk.END)
        self.bits_campo_entry.insert(0, str(campo["bits"]))

        tipo = campo.get("tipo", "registro")
        if tipo in self.TIPOS:
            self.tipo_campo_combo.current(self.TIPOS.index(tipo))

        self.orden_bits_entry.delete(0, tk.END)
        natural = FormatoDeInstruccion.orden_natural(campo["bits"])
        if campo.get("orden_bits", natural) != natural:
            orden_str = ", ".join(
                f"{k}:{v}" for k, v in sorted(campo["orden_bits"].items(), key=lambda x: int(x[0]))
            )
            self.orden_bits_entry.insert(0, orden_str)

        del self.lista_operandos_temporal[indice]
        self._refrescar_lista_campos()

    def mover_campo_arriba(self):
        seleccion = self.lista_campos_view.curselection()
        if not seleccion or seleccion[0] == 0:
            return
        i = seleccion[0]
        self.lista_operandos_temporal[i], self.lista_operandos_temporal[i-1] = \
            self.lista_operandos_temporal[i-1], self.lista_operandos_temporal[i]
        self._refrescar_lista_campos()
        self.lista_campos_view.selection_set(i - 1)

    def mover_campo_abajo(self):
        seleccion = self.lista_campos_view.curselection()
        if not seleccion or seleccion[0] >= len(self.lista_operandos_temporal) - 1:
            return
        i = seleccion[0]
        self.lista_operandos_temporal[i], self.lista_operandos_temporal[i+1] = \
            self.lista_operandos_temporal[i+1], self.lista_operandos_temporal[i]
        self._refrescar_lista_campos()
        self.lista_campos_view.selection_set(i + 1)

    def _refrescar_lista_campos(self):
        """Redibuja el Listbox de campos desde lista_operandos_temporal."""
        self.lista_campos_view.delete(0, tk.END)
        for campo in self.lista_operandos_temporal:
            natural = FormatoDeInstruccion.orden_natural(campo["bits"])
            tipo    = campo.get("tipo", "?")
            if campo.get("orden_bits", natural) != natural:
                orden_str = ", ".join(
                    f"{k}:{v}" for k, v in sorted(
                        campo["orden_bits"].items(), key=lambda x: int(x[0])))
                display = f"{campo['nombre']:<8} {campo['bits']:>2}b  {tipo:<9} [{orden_str}]"
            else:
                display = f"{campo['nombre']:<8} {campo['bits']:>2}b  {tipo:<9}"
            self.lista_campos_view.insert(tk.END, display)

    def limpiar_campos(self):
        self.lista_operandos_temporal = []
        self.lista_campos_view.delete(0, tk.END)

    # ─────────────────────────────────────────────
    #  GUARDAR FORMATO
    # ─────────────────────────────────────────────

    def guardar_formato(self):
        try:
            nombre = self.nombre_fmt_entry.get().strip()
            if not nombre:
                raise ValueError("El nombre del formato no puede estar vacío.")
            if not self.lista_operandos_temporal:
                raise ValueError("El formato debe tener al menos un campo.")

            total_bits = sum(c["bits"] for c in self.lista_operandos_temporal)

            if total_bits != self.procesador.tamano_palabra:
                continuar = messagebox.askyesno(
                    "Advertencia de bits",
                    f"Este formato usa {total_bits} bits, pero el procesador es de "
                    f"{self.procesador.tamano_palabra} bits.\n¿Deseas guardarlo de todas formas?"
                )
                if not continuar:
                    return

            # Confirmar reordenamientos personalizados
            campos_con_orden = [
                c for c in self.lista_operandos_temporal
                if c["orden_bits"] != FormatoDeInstruccion.orden_natural(c["bits"])
            ]
            if campos_con_orden:
                resumen = "\n".join(
                    f"  • {c['nombre']} ({c['bits']} bits): {c['orden_bits']}"
                    for c in campos_con_orden
                )
                if not messagebox.askyesno(
                    "Confirmar reordenamiento",
                    f"Campos con reordenamiento personalizado:\n\n{resumen}\n\n¿Es correcto?"
                ):
                    return

            nuevo_formato = FormatoDeInstruccion(
                nombre=nombre,
                total_bits=total_bits,
                campos_operandos=list(self.lista_operandos_temporal),
                lectura=self._lectura_valor()
            ).toDict()

            if self._indice_editando is not None:
                self.procesador.formato_de_sintaxis[self._indice_editando] = nuevo_formato
                self._cancelar_edicion()
                messagebox.showinfo("Actualizado", f"Formato '{nombre}' actualizado.")
            else:
                self.procesador.formato_de_sintaxis.append(nuevo_formato)
                messagebox.showinfo("Éxito", f"Formato '{nombre}' agregado.")

            self._cargar_formatos_existentes()
            self.limpiar_campos()
            self.nombre_fmt_entry.delete(0, tk.END)

        except ValueError as ve:
            messagebox.showerror("Error", f"Dato inválido: {ve}")

    # ─────────────────────────────────────────────
    #  EDITAR FORMATO
    # ─────────────────────────────────────────────

    def editar_formato(self):
        seleccion = self.lista_formatos.curselection()
        if not seleccion:
            messagebox.showinfo("Selección", "Selecciona un formato para editarlo.")
            return

        indice = seleccion[0]
        fmt    = self.procesador.formato_de_sintaxis[indice]

        self._indice_editando = indice
        self.frame_der.config(text=f"Editando: {fmt.get('nombre', '?')}")
        self.btn_guardar.config(text="GUARDAR CAMBIOS")
        self.btn_cancelar_edicion.pack(pady=(0, 8), fill="x", padx=20)

        self.nombre_fmt_entry.delete(0, tk.END)
        self.nombre_fmt_entry.insert(0, fmt.get("nombre", ""))

        # Dirección de lectura
        lectura = fmt.get("lectura", "msb_primero")
        self.lectura_combo.current(1 if lectura == "lsb_primero" else 0)

        self.limpiar_campos()
        for campo in fmt.get("campos_operandos", []):
            # Compatibilidad con formato viejo (lista) y nuevo (dict)
            if isinstance(campo, list):
                c = {"nombre": campo[0], "bits": campo[1], "tipo": "constante",
                     "orden_bits": FormatoDeInstruccion.orden_natural(campo[1])}
            else:
                c = campo.copy()
                if "orden_bits" not in c:
                    c["orden_bits"] = FormatoDeInstruccion.orden_natural(c["bits"])
                if "tipo" not in c:
                    c["tipo"] = "constante"
            self.lista_operandos_temporal.append(c)

        self._refrescar_lista_campos()

    def _cancelar_edicion(self):
        self._indice_editando = None
        self.frame_der.config(text="Nuevo Formato")
        self.btn_guardar.config(text="GUARDAR FORMATO")
        self.btn_cancelar_edicion.pack_forget()
        self.limpiar_campos()
        self.nombre_fmt_entry.delete(0, tk.END)
        self.lectura_combo.current(0)

    # ─────────────────────────────────────────────
    #  MOVER / ELIMINAR FORMATO
    # ─────────────────────────────────────────────

    def mover_formato_arriba(self):
        seleccion = self.lista_formatos.curselection()
        if not seleccion or seleccion[0] == 0:
            return
        i = seleccion[0]
        lst = self.procesador.formato_de_sintaxis
        lst[i], lst[i-1] = lst[i-1], lst[i]
        self._cargar_formatos_existentes()
        self.lista_formatos.selection_set(i - 1)

    def mover_formato_abajo(self):
        seleccion = self.lista_formatos.curselection()
        lst = self.procesador.formato_de_sintaxis
        if not seleccion or seleccion[0] >= len(lst) - 1:
            return
        i = seleccion[0]
        lst[i], lst[i+1] = lst[i+1], lst[i]
        self._cargar_formatos_existentes()
        self.lista_formatos.selection_set(i + 1)

    def eliminar_formato(self):
        seleccion = self.lista_formatos.curselection()
        if not seleccion:
            messagebox.showinfo("Selección", "Selecciona un formato para eliminarlo.")
            return

        indice = seleccion[0]
        nombre = self.procesador.formato_de_sintaxis[indice].get("nombre", "?")

        if messagebox.askyesno("Confirmar", f"¿Estás seguro que quieres borrar '{nombre}'?"):
            del self.procesador.formato_de_sintaxis[indice]
            if self._indice_editando == indice:
                self._cancelar_edicion()
            self._cargar_formatos_existentes()

    # ─────────────────────────────────────────────
    #  SIGUIENTE PASO
    # ─────────────────────────────────────────────

    def ir_a_instrucciones(self):
        if self.procesador.ruta_archivo:
            self.procesador.guardarEnJSON(self.procesador.ruta_archivo)
        else:
            messagebox.showwarning("Ruta no encontrada",
                                   "No se pudo determinar la ruta del archivo.")
            return
        self.ventana.destroy()
        self.controlador.abrir_set_instrucciones(self.procesador)
