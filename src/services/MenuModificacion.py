# src/services/MenuModificacion.py
import tkinter as tk
from tkinter import ttk


class VentanaMenuModificacion:
    def __init__(self, parent, controlador, procesador):
        self.controlador = controlador
        self.procesador = procesador

        self.ventana = tk.Toplevel(parent)
        self.ventana.title(f"Modificar: {procesador.nombre}")
        self.ventana.geometry("400x350")
        self.ventana.transient(parent)
        self.ventana.grab_set()

        self._construir_interfaz()

    def _construir_interfaz(self):
        ttk.Label(self.ventana, text=f"Editando: {self.procesador.nombre}", font=("Arial", 14, "bold")).pack(pady=20)

        ttk.Label(self.ventana, text="¿Qué deseas modificar?").pack(pady=5)

        # Botón 1: Formatos
        # Reutilizamos la ventana de crear formatos, pasándole el procesador cargado
        btn_fmt = ttk.Button(
            self.ventana,
            text="Editar Formatos de Instrucción",
            command=lambda: self.controlador.abrir_crear_formatos(self.procesador)
        )
        btn_fmt.pack(pady=10, fill="x", padx=40)

        # Botón 2: Instrucciones
        # Reutilizamos la ventana de instrucciones
        btn_inst = ttk.Button(
            self.ventana,
            text="Editar Set de Instrucciones",
            command=lambda: self.controlador.abrir_set_instrucciones(self.procesador)
        )
        btn_inst.pack(pady=10, fill="x", padx=40)

        # Botón Cerrar
        ttk.Separator(self.ventana, orient="horizontal").pack(fill="x", pady=20)
        ttk.Button(self.ventana, text="Cerrar Editor", command=self.ventana.destroy).pack()