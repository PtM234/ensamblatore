# src/main.py
import tkinter as tk
from services.VentanaIDE import VentanaIDE

if __name__ == "__main__":
    root = tk.Tk()
    app  = VentanaIDE(root)
    root.mainloop()
