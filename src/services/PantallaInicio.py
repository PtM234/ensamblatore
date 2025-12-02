import tkinter as tk
from tkinter import ttk

class PantallaInicio(ttk.Frame):
    def __init__(self, parent, controlador):
        super().__init__(parent)
        self.controlador = controlador # Guardamos referencia al "Jefe"
        self._construir_interfaz()

    def _construir_interfaz(self):
        # Título
        ttk.Label(self, text="Ensamblatore", font=("Arial", 20, "bold")).pack(pady=30)

        # Contenedor de botones
        botones_frame = ttk.Frame(self)
        botones_frame.pack(fill="x", padx=50)

        # Botón Crear: Llama a la función del controlador
        btn_crear = ttk.Button(
            botones_frame,
            text="Crear nueva arquitectura",
            command=self.controlador.abrir_crear_arquitectura
        )
        btn_crear.pack(pady=10, fill="x")

        btn_modificar = ttk.Button(
            botones_frame,
            text="Modificar una arquitectura",
            # AQUI CONECTAMOS LA FUNCIÓN
            command=self.controlador.cargar_arquitectura
        )
        btn_modificar.pack(pady=10, fill="x")

        # Otros botones (sin función por ahora)
        ttk.Button(botones_frame, text="Abrir archivo y escribir código").pack(pady=10, fill="x")
