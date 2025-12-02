import tkinter as tk
import json
from services.PantallaInicio import PantallaInicio
from services.CrearArquitectura import VentanaCrearArquitectura
# --- AQUÍ FALTABA ESTA IMPORTACIÓN ---
from services.CrearFormatos import VentanaCrearFormatos
from services.CrearSetInstrucciones import VentanaCrearSetInstrucciones
from tkinter import filedialog, messagebox
from models.procesador import Procesador
from services.MenuModificacion import VentanaMenuModificacion

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

    def abrir_crear_formatos(self, procesador_creado):
        """Paso 2: Definir formatos"""
        # Ahora sí funcionará porque ya importamos la clase arriba
        VentanaCrearFormatos(self.root, controlador=self, procesador=procesador_creado)

    def abrir_set_instrucciones(self, procesador_creado):
        """Paso 3: Definir instrucciones"""
        VentanaCrearSetInstrucciones(self.root, controlador=self, procesador=procesador_creado)

    def cargar_arquitectura(self):
        """Abre un JSON, lo convierte a Objeto y abre el menú de modificación"""
        archivo = filedialog.askopenfilename(
            title="Seleccionar Arquitectura",
            filetypes=[("Archivos JSON", "*.json")]
        )

        if archivo:
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Usamos el método que creamos en el Paso 1
                procesador_cargado = Procesador.fromDict(data)

                # Abrimos el menú de modificación (Paso 2)
                VentanaMenuModificacion(self.root, controlador=self, procesador=procesador_cargado)

            except Exception as e:
                tk.messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = Application(root)
    root.mainloop()