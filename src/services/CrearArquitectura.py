# src/services/CrearArquitectura.py
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog  # <--- IMPORTANTE: Para abrir el explorador de archivos
from models.procesador import Procesador


class VentanaCrearArquitectura:
    def __init__(self, parent, controlador):
        self.controlador = controlador

        # --- Configuración de la Ventana ---
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Nueva Arquitectura - Ensamblatore")
        self.ventana.geometry("550x650")
        self.ventana.transient(parent)
        self.ventana.grab_set()

        self._construir_interfaz()

    def _construir_interfaz(self):
        # Frame principal
        main_frame = ttk.Frame(self.ventana, padding="20")
        main_frame.pack(expand=True, fill="both")

        # Configurar columnas
        main_frame.columnconfigure(1, weight=1)

        # --- 1. Nombre ---
        ttk.Label(main_frame, text="Nombre del procesador:").grid(row=0, column=0, sticky="w", pady=5)
        self.nombre_entry = ttk.Entry(main_frame)
        self.nombre_entry.insert(0, "MiCPU_v1")
        self.nombre_entry.grid(row=0, column=1, sticky="ew", padx=5)

        # --- 2. Tamaño de Palabra ---
        ttk.Label(main_frame, text="Tamaño de palabra (bits):").grid(row=1, column=0, sticky="w", pady=5)
        self.palabra_entry = ttk.Entry(main_frame)
        self.palabra_entry.insert(0, "16")
        self.palabra_entry.grid(row=1, column=1, sticky="ew", padx=5)

        # --- 3. Distribución ---
        ttk.Label(main_frame, text="Distribución de memorias:").grid(row=2, column=0, sticky="w", pady=5)
        self.distribucion_combo = ttk.Combobox(main_frame, values=["Harvard", "Von Neumann"], state="readonly")
        self.distribucion_combo.set("Harvard")
        self.distribucion_combo.grid(row=2, column=1, sticky="ew", padx=5)

        # --- 4. Profundidad ---
        ttk.Label(main_frame, text="Profundidad (direcciones):").grid(row=3, column=0, sticky="w", pady=5)
        self.profundidad_entry = ttk.Entry(main_frame)
        self.profundidad_entry.insert(0, "1024")
        self.profundidad_entry.grid(row=3, column=1, sticky="ew", padx=5)

        # --- 5. Ancho ---
        ttk.Label(main_frame, text="Ancho de memoria (bits):").grid(row=4, column=0, sticky="w", pady=5)
        self.ancho_entry = ttk.Entry(main_frame)
        self.ancho_entry.insert(0, "8")
        self.ancho_entry.grid(row=4, column=1, sticky="ew", padx=5)

        # --- 6. Mínimo Direccionable ---
        ttk.Label(main_frame, text="Mínimo direccionable (bits):").grid(row=5, column=0, sticky="w", pady=5)
        self.min_dir_entry = ttk.Entry(main_frame)
        self.min_dir_entry.insert(0, "1")
        self.min_dir_entry.grid(row=5, column=1, sticky="ew", padx=5)

        # --- 7. Mapeo ---
        ttk.Label(main_frame, text="Mapeo de memoria (Inicio Hex):").grid(row=6, column=0, sticky="w", pady=5)
        self.mapeo_entry = ttk.Entry(main_frame)
        self.mapeo_entry.insert(0, "0x0000")
        self.mapeo_entry.grid(row=6, column=1, sticky="ew", padx=5)

        # --- 8. Aumento PC ---
        ttk.Label(main_frame, text="Aumento del PC (pasos):").grid(row=7, column=0, sticky="w", pady=5)
        self.aumento_pc_spin = ttk.Spinbox(main_frame, from_=1, to=8, increment=1)
        self.aumento_pc_spin.set(1)
        self.aumento_pc_spin.grid(row=7, column=1, sticky="ew", padx=5)

        # --- 9. Endianness ---
        ttk.Label(main_frame, text="Endianness:").grid(row=8, column=0, sticky="w", pady=5)
        self.endianness_combo = ttk.Combobox(main_frame, values=["Little Endian", "Big Endian"], state="readonly")
        self.endianness_combo.set("Little Endian")
        self.endianness_combo.grid(row=8, column=1, sticky="ew", padx=5)

        # --- BOTONES ---
        ttk.Separator(main_frame, orient='horizontal').grid(row=9, column=0, columnspan=2, sticky="ew", pady=20)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=10, column=0, columnspan=2)

        ttk.Button(btn_frame, text="Cancelar", command=self.ventana.destroy).pack(side="left", padx=10)
        # Cambiamos el texto del botón para que sea claro que se abrirá un diálogo
        ttk.Button(btn_frame, text="Guardar en...", command=self.guardar_datos).pack(side="right", padx=10)

    def guardar_datos(self):
        """
        Valida los datos, crea el objeto y abre el diálogo 'Guardar como'.
        """
        try:
            # 1. Validación y Conversión (Igual que antes)
            nombre = self.nombre_entry.get()
            if not nombre:
                raise ValueError("El nombre no puede estar vacío.")

            tamano_palabra = int(self.palabra_entry.get())
            distribucion = self.distribucion_combo.get()
            profundidad = int(self.profundidad_entry.get())
            ancho = int(self.ancho_entry.get())
            min_dir = int(self.min_dir_entry.get())

            mapeo_raw = self.mapeo_entry.get()
            if "0x" in mapeo_raw.lower():
                mapeo_memoria = int(mapeo_raw, 16)
            else:
                mapeo_memoria = int(mapeo_raw)

            aumento_pc = int(self.aumento_pc_spin.get())
            endianness = self.endianness_combo.get()

            # 2. Creación del Objeto Procesador
            nuevo_procesador = Procesador(
                nombre=nombre,
                tamano_palabra=tamano_palabra,
                distribucion_memorias=distribucion,
                profundidad=profundidad,
                ancho=ancho,
                tamano_minimo_direccionable=min_dir,
                mapeo_memoria=mapeo_memoria,
                aumento_pc=aumento_pc,
                endianess=endianness
            )

            # ... (código anterior de validación y creación del objeto) ...

            # 3. ABRIR EL DIÁLOGO DE GUARDADO
            archivo_guardado = filedialog.asksaveasfilename(
                title="Guardar Arquitectura",
                defaultextension=".json",
                initialfile=f"{nombre}.json",
                filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
            )

            if archivo_guardado:
                nuevo_procesador.guardarEnJSON(archivo_guardado)

                # --- CAMBIO IMPORTANTE AQUÍ ---
                # Preguntamos si quiere continuar a definir instrucciones
                respuesta = messagebox.askyesno(
                    "Arquitectura Guardada",
                    f"Se guardó '{nombre}'.\n¿Deseas definir el Set de Instrucciones ahora?"
                )

                self.ventana.destroy()  # Cerramos la ventana actual

                if respuesta:
                    # ANTES: self.controlador.abrir_set_instrucciones(nuevo_procesador)
                    # AHORA: Vamos primero a crear formatos
                    self.controlador.abrir_crear_formatos(nuevo_procesador)

            # Si cancela, simplemente no hacemos nada y la ventana sigue abierta

        except ValueError as ve:
            messagebox.showerror("Error de validación", f"Por favor verifica los datos numéricos.\nDetalle: {ve}")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error inesperado: {e}")