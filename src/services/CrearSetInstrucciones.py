# src/services/CrearSetInstrucciones.py
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox


class VentanaCrearSetInstrucciones:
    def __init__(self, parent, controlador, procesador):
        self.controlador = controlador
        self.procesador = procesador  # ¡Importante! Aquí tenemos la CPU que estamos editando

        # Configuración de la ventana
        self.ventana = tk.Toplevel(parent)
        self.ventana.title(f"Set de Instrucciones - {self.procesador.nombre}")
        self.ventana.geometry("700x500")
        self.ventana.transient(parent)
        self.ventana.grab_set()

        self._construir_interfaz()

    def _construir_interfaz(self):
        # Título
        ttk.Label(self.ventana, text=f"Instrucciones para: {self.procesador.nombre}", font=("Arial", 14, "bold")).pack(
            pady=10)

        # Frame principal dividido en dos: Izquierda (Lista), Derecha (Formulario)
        panel_principal = ttk.Frame(self.ventana)
        panel_principal.pack(expand=True, fill="both", padx=10, pady=10)

        # --- PANEL IZQUIERDO: LISTA DE INSTRUCCIONES ---
        panel_lista = ttk.LabelFrame(panel_principal, text="Instrucciones Agregadas")
        panel_lista.pack(side="left", fill="both", expand=True, padx=5)

        # Listbox para ver las instrucciones
        self.lista_instrucciones = tk.Listbox(panel_lista)
        self.lista_instrucciones.pack(fill="both", expand=True, padx=5, pady=5)

        # --- PANEL DERECHO: FORMULARIO ---
        panel_form = ttk.LabelFrame(panel_principal, text="Nueva Instrucción")
        panel_form.pack(side="right", fill="both", expand=True, padx=5)

        # Mnemónico
        ttk.Label(panel_form, text="Mnemónico (ej. ADD):").pack(anchor="w", padx=5)
        self.mnemonico_entry = ttk.Entry(panel_form)
        self.mnemonico_entry.pack(fill="x", padx=5, pady=2)

        # Opcode (Binario/Hex)
        ttk.Label(panel_form, text="Opcode (ej. 0010):").pack(anchor="w", padx=5)
        self.opcode_entry = ttk.Entry(panel_form)
        self.opcode_entry.pack(fill="x", padx=5, pady=2)

        # Descripción
        ttk.Label(panel_form, text="Descripción:").pack(anchor="w", padx=5)
        self.desc_entry = ttk.Entry(panel_form)
        self.desc_entry.pack(fill="x", padx=5, pady=2)

        # Botón Agregar
        ttk.Button(panel_form, text="Agregar Instrucción", command=self.agregar_instruccion).pack(pady=10)

        # --- BOTONES INFERIORES ---
        btn_frame = ttk.Frame(self.ventana)
        btn_frame.pack(fill="x", pady=10)

        ttk.Button(btn_frame, text="Finalizar", command=self.finalizar).pack(side="right", padx=20)

    def agregar_instruccion(self):
        # Lógica temporal para probar la UI
        mnem = self.mnemonico_entry.get()
        if mnem:
            self.lista_instrucciones.insert(tk.END, mnem)
            self.mnemonico_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Atención", "Escribe al menos un mnemónico.")

    def finalizar(self):
        self.ventana.destroy()
        messagebox.showinfo("Listo", "Definición de instrucciones terminada (Simulado)")