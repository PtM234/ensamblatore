import tkinter as tk
from services.PantallaInicio import PantallaInicio
from services.CrearArquitectura import VentanaCrearArquitectura
# 1. IMPORTANTE: Importamos la nueva ventana aquí abajo
from services.CrearSetInstrucciones import VentanaCrearSetInstrucciones


class Application:
    def __init__(self, root):
        self.root = root
        self.root.title("Ensamblatore")
        self.root.geometry("400x300")

        self.frame_actual = None
        self.mostrar_pantalla_inicio()

    def mostrar_pantalla_inicio(self):
        """Muestra la pantalla de bienvenida"""
        if self.frame_actual:
            self.frame_actual.destroy()
        self.frame_actual = PantallaInicio(self.root, controlador=self)
        self.frame_actual.pack(expand=True, fill="both")

    def abrir_crear_arquitectura(self):
        """Abre la ventana para crear el procesador"""
        VentanaCrearArquitectura(self.root, controlador=self)

    # 2. IMPORTANTE: Esta es la función que te faltaba
    def abrir_set_instrucciones(self, procesador_creado):
        """Abre la ventana para definir instrucciones, pasando el objeto procesador"""
        VentanaCrearSetInstrucciones(self.root, controlador=self, procesador=procesador_creado)


if __name__ == "__main__":
    root = tk.Tk()
    app = Application(root)
    root.mainloop()