import tkinter as tk
from tkinter import ttk
from . import CrearArquitectura


def pantalla_principal():
    root = tk.Tk()
    ttk.Label(root, text= "Ensamblatore").pack()
    buttonCrear = ttk.Button(root, text = "Crear nueva arquitectura", command = CrearArquitectura.crear_arquitectura())
    root.mainloop()