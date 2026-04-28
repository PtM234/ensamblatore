# src/services/CrearFormatos.py
import tkinter as tk
from tkinter import ttk, messagebox
from models.formato_instruccion import FormatoDeInstruccion


class VentanaCrearFormatos:
    def __init__(self, parent, controlador, procesador):
        self.controlador = controlador
        self.procesador = procesador

        self.ventana = tk.Toplevel(parent)
        self.ventana.title(f"Formatos de Instrucción - {procesador.nombre}")
        self.ventana.geometry("800x600")
        self.ventana.transient(parent)
        self.ventana.grab_set()

        # Lista temporal de campos del formato que se está creando
        self.lista_operandos_temporal = []

        self._construir_interfaz()
        self._cargar_formatos_existentes()

    def _construir_interfaz(self):
        ttk.Label(self.ventana, text=f"Definir Formatos para: {self.procesador.nombre}",
                  font=("Arial", 14, "bold")).pack(pady=10)

        panel_principal = ttk.Frame(self.ventana)
        panel_principal.pack(expand=True, fill="both", padx=10)
        panel_principal.columnconfigure(0, weight=1)
        panel_principal.columnconfigure(1, weight=1)

        # === IZQUIERDA: LISTA DE FORMATOS CREADOS ===
        frame_izq = ttk.LabelFrame(panel_principal, text="Formatos Existentes")
        frame_izq.grid(row=0, column=0, sticky="nsew", padx=5)

        self.lista_formatos = tk.Listbox(frame_izq)
        self.lista_formatos.pack(expand=True, fill="both", padx=5, pady=5)

        # === DERECHA: CREAR NUEVO FORMATO ===
        frame_der = ttk.LabelFrame(panel_principal, text="Nuevo Formato")
        frame_der.grid(row=0, column=1, sticky="nsew", padx=5)

        form_top = ttk.Frame(frame_der)
        form_top.pack(fill="x", padx=5, pady=5)

        ttk.Label(form_top, text="Nombre (ej. Tipo-R):").grid(row=0, column=0, sticky="w")
        self.nombre_fmt_entry = ttk.Entry(form_top, width=15)
        self.nombre_fmt_entry.grid(row=0, column=1, padx=5)

        ttk.Label(form_top, text="Bits Opcode:").grid(row=1, column=0, sticky="w")
        self.bits_opcode_entry = ttk.Entry(form_top, width=5)
        self.bits_opcode_entry.grid(row=1, column=1, padx=5)

        ttk.Separator(frame_der, orient="horizontal").pack(fill="x", pady=10)
        ttk.Label(frame_der, text="Agregar Campos (Operandos)", font=("Arial", 10, "bold")).pack()

        form_campos = ttk.Frame(frame_der)
        form_campos.pack(fill="x", padx=5)

        ttk.Label(form_campos, text="Nombre Campo:").pack(side="left")
        self.nombre_campo_entry = ttk.Entry(form_campos, width=10)
        self.nombre_campo_entry.pack(side="left", padx=2)

        ttk.Label(form_campos, text="Bits:").pack(side="left")
        self.bits_campo_entry = ttk.Entry(form_campos, width=5)
        self.bits_campo_entry.pack(side="left", padx=2)

        ttk.Button(form_campos, text="+", width=3, command=self.agregar_campo_a_lista).pack(side="left", padx=5)

        self.lista_campos_view = tk.Listbox(frame_der, height=6)
        self.lista_campos_view.pack(fill="x", padx=5, pady=5)
        ttk.Button(frame_der, text="Limpiar Campos", command=self.limpiar_campos).pack()

        ttk.Button(frame_der, text="GUARDAR FORMATO", command=self.guardar_formato).pack(pady=15, fill="x", padx=20)

        # --- BOTONES INFERIORES ---
        btn_frame = ttk.Frame(self.ventana)
        btn_frame.pack(fill="x", pady=10)

        ttk.Button(btn_frame, text="Siguiente: Crear Instrucciones >>",
                   command=self.ir_a_instrucciones).pack(side="right", padx=20)

    def _cargar_formatos_existentes(self):
        """Muestra en la lista los formatos que ya tenía el procesador al abrir la ventana."""
        for fmt in self.procesador.formato_de_sintaxis:
            nombre = fmt.get("nombre", "?")
            total_bits = fmt.get("total_bits", "?")
            self.lista_formatos.insert(tk.END, f"{nombre} ({total_bits} bits)")

    def agregar_campo_a_lista(self):
        nombre = self.nombre_campo_entry.get().strip()
        bits = self.bits_campo_entry.get().strip()

        if nombre and bits.isdigit():
            # CORREGIDO: se guarda como lista en lugar de tupla para
            # mantener consistencia con lo que devuelve JSON al cargar el archivo.
            self.lista_operandos_temporal.append([nombre, int(bits)])
            self.lista_campos_view.insert(tk.END, f"{nombre} ({bits} bits)")
            self.nombre_campo_entry.delete(0, tk.END)
            self.bits_campo_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "Revisa el nombre y los bits del campo.")

    def limpiar_campos(self):
        self.lista_operandos_temporal = []
        self.lista_campos_view.delete(0, tk.END)

    def guardar_formato(self):
        try:
            nombre = self.nombre_fmt_entry.get().strip()
            if not nombre:
                raise ValueError("El nombre del formato no puede estar vacío.")

            bits_op = int(self.bits_opcode_entry.get())
            total_bits = bits_op + sum(c[1] for c in self.lista_operandos_temporal)

            if total_bits > self.procesador.tamano_palabra:
                messagebox.showwarning(
                    "Advertencia de bits",
                    f"Este formato usa {total_bits} bits, pero el procesador es de "
                    f"{self.procesador.tamano_palabra} bits."
                )

            nuevo_formato = FormatoDeInstruccion(
                nombre=nombre,
                total_bits=total_bits,
                bits_opcode=bits_op,
                campos_operandos=self.lista_operandos_temporal
            )

            self.procesador.formato_de_sintaxis.append(nuevo_formato.toDict())

            self.lista_formatos.insert(tk.END, f"{nombre} ({total_bits} bits)")
            self.limpiar_campos()
            self.nombre_fmt_entry.delete(0, tk.END)
            self.bits_opcode_entry.delete(0, tk.END)

            messagebox.showinfo("Éxito", f"Formato '{nombre}' agregado.")

        except ValueError as ve:
            messagebox.showerror("Error", f"Dato inválido: {ve}")

    def ir_a_instrucciones(self):
        """
        Guarda el JSON en la misma ruta donde el usuario lo guardó originalmente
        y avanza al paso de instrucciones.
        """
        # CORREGIDO: se usa ruta_archivo en lugar de construir un nombre relativo,
        # evitando crear un archivo duplicado en el directorio de trabajo.
        if self.procesador.ruta_archivo:
            self.procesador.guardarEnJSON(self.procesador.ruta_archivo)
        else:
            messagebox.showwarning(
                "Ruta no encontrada",
                "No se pudo determinar la ruta del archivo. "
                "Guarda el archivo manualmente antes de continuar."
            )
            return

        self.ventana.destroy()
        self.controlador.abrir_set_instrucciones(self.procesador)
