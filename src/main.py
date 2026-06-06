# src/main.py
import sys
import os

if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    sys.path.insert(0, base_path)
    sys.path.insert(0, os.path.join(base_path, 'services'))
    sys.path.insert(0, os.path.join(base_path, 'models'))
else:
    base_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, base_path)

import tkinter as tk

try:
    from services.VentanaIDE import VentanaIDE
except ModuleNotFoundError:
    from VentanaIDE import VentanaIDE

if __name__ == "__main__":
    root = tk.Tk()
    app  = VentanaIDE(root)
    root.mainloop()