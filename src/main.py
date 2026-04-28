# src/main.py
import tkinter as tk
import json
from tkinter import filedialog, messagebox

from services.PantallaInicio import PantallaInicio
from services.CrearArquitectura import VentanaCrearArquitectura
from services.CrearFormatos import VentanaCrearFormatos
from services.CrearSetInstrucciones import VentanaCrearSetInstrucciones
from services.MenuModificacion import VentanaMenuModificacion
from services.VentanaIDE import VentanaIDE
from models.procesador import Procesador


class Application:
    def __init__(self, root):
        self.root = root
        self.root.title("Ensamblatore")
        self.root.geometry("400x300")

        self.frame_actual = None
        self.mostrar_pantalla_inicio()

    def mostrar_pantalla_inicio(self):
        """Muestra la pantalla de bienvenida."""
        if self.frame_actual:
            self.frame_actual.destroy()
        self.frame_actual = PantallaInicio(self.root, controlador=self)
        self.frame_actual.pack(expand=True, fill="both")

    def abrir_crear_arquitectura(self):
        """Paso 1: Definir la arquitectura base del procesador."""
        VentanaCrearArquitectura(self.root, controlador=self)

    def abrir_crear_formatos(self, procesador_creado):
        """Paso 2: Definir los formatos de instrucción."""
        VentanaCrearFormatos(self.root, controlador=self, procesador=procesador_creado)

    def abrir_set_instrucciones(self, procesador_creado):
        """Paso 3: Definir el set de instrucciones."""
        VentanaCrearSetInstrucciones(self.root, controlador=self, procesador=procesador_creado)

    def cargar_arquitectura(self):
        """Abre un JSON, lo convierte a objeto Procesador y abre el menú de modificación."""
        archivo = filedialog.askopenfilename(
            title="Seleccionar Arquitectura",
            filetypes=[("Archivos JSON", "*.json")]
        )

        if archivo:
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                procesador_cargado = Procesador.fromDict(data)
                procesador_cargado.ruta_archivo = archivo

                VentanaMenuModificacion(self.root, controlador=self, procesador=procesador_cargado)

            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{e}")

    def abrir_ide(self):
        """
        Abre un JSON de arquitectura, lo valida y lanza el IDE.
        La arquitectura debe tener al menos un formato y una instrucción definidos.
        """
        archivo = filedialog.askopenfilename(
            title="Seleccionar Arquitectura para escribir código",
            filetypes=[("Archivos JSON", "*.json")]
        )

        if not archivo:
            return  # El usuario canceló el diálogo

        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # ── Validación del JSON ───────────────────────────────────
            errores = _validar_arquitectura(data)
            if errores:
                messagebox.showerror(
                    "Arquitectura incompleta",
                    "No se puede abrir el IDE porque la arquitectura tiene problemas:\n\n"
                    + "\n".join(f"• {e}" for e in errores)
                )
                return

            # ── Cargar y abrir el IDE ─────────────────────────────────
            procesador = Procesador.fromDict(data)
            procesador.ruta_archivo = archivo

            VentanaIDE(self.root, controlador=self, procesador=procesador)

        except json.JSONDecodeError:
            messagebox.showerror("Error", "El archivo seleccionado no es un JSON válido.")
        except KeyError as ke:
            messagebox.showerror("Error", f"El JSON no tiene el campo esperado: {ke}")
        except Exception as e:
            messagebox.showerror("Error inesperado", f"No se pudo abrir el archivo:\n{e}")


# ─────────────────────────────────────────────────────────────────────────────
#  FUNCIÓN DE VALIDACIÓN
# ─────────────────────────────────────────────────────────────────────────────

def _validar_arquitectura(data: dict) -> list[str]:
    """
    Valida que el JSON de arquitectura tenga lo mínimo necesario para
    poder escribir y ensamblar código.
    Devuelve una lista de errores (vacía si todo está bien).
    """
    errores = []

    campos_requeridos = [
        "nombre", "tamano_palabra", "distribucion_memorias",
        "profundidad", "ancho", "endianess"
    ]
    for campo in campos_requeridos:
        if campo not in data:
            errores.append(f"Falta el campo obligatorio '{campo}'.")

    if not data.get("formato_de_sintaxis"):
        errores.append("No hay formatos de instrucción definidos. Define al menos uno antes de escribir código.")

    instrucciones = data.get("set_de_instrucciones", data.get("set de instrucciones", []))
    if not instrucciones:
        errores.append("No hay instrucciones en el set. Define al menos una antes de escribir código.")

    return errores


if __name__ == "__main__":
    root = tk.Tk()
    app = Application(root)
    root.mainloop()
