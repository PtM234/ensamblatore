# src/services/PantallaInicio.py
import tkinter as tk
from tkinter import ttk


class PantallaInicio(ttk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent)
        self.controlador = controlador
        self._construir_interfaz()

    def _construir_interfaz(self):
        ttk.Label(self, text="Ensamblatore", font=("Arial", 20, "bold")).pack(pady=30)

        botones_frame = ttk.Frame(self)
        botones_frame.pack(fill="x", padx=50)

        ttk.Button(
            botones_frame,
            text="Crear nueva arquitectura",
            command=self.controlador.abrir_crear_arquitectura
        ).pack(pady=10, fill="x")

        ttk.Button(
            botones_frame,
            text="Modificar una arquitectura",
            command=self.controlador.cargar_arquitectura
        ).pack(pady=10, fill="x")

        # CORREGIDO: ahora tiene comando conectado al controlador
        ttk.Button(
            botones_frame,
            text="Abrir archivo y escribir código",
            command=self.controlador.abrir_ide
        ).pack(pady=10, fill="x")
