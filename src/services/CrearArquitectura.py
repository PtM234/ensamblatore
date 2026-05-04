# src/services/CrearArquitectura.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from models.procesador import Procesador


class VentanaCrearArquitectura:
    def __init__(self, parent, controlador, procesador_existente=None):
        self.controlador          = controlador
        self.procesador_existente = procesador_existente
        self._modo_edicion        = procesador_existente is not None

        self.ventana = tk.Toplevel(parent)
        self.ventana.title(
            "Editar Arquitectura - Ensamblatore" if self._modo_edicion
            else "Nueva Arquitectura - Ensamblatore"
        )
        self.ventana.resizable(False, False)
        self.ventana.transient(parent)
        self.ventana.grab_set()

        self._construir_interfaz()

        # Si hay procesador existente, poblar los campos
        if self._modo_edicion:
            self._poblar_campos(procesador_existente)

        # Ajustar tamaño al contenido
        self.ventana.update_idletasks()
        self.ventana.geometry("")

    def _construir_interfaz(self):
        main_frame = ttk.Frame(self.ventana, padding="20")
        main_frame.pack(expand=True, fill="both")
        main_frame.columnconfigure(1, weight=1)

        # --- 1. Nombre ---
        ttk.Label(main_frame, text="Nombre del procesador:").grid(
            row=0, column=0, sticky="w", pady=4)
        self.nombre_entry = ttk.Entry(main_frame, width=30)
        self.nombre_entry.insert(0, "MiCPU_v1")
        self.nombre_entry.grid(row=0, column=1, sticky="ew", padx=5)

        # --- 2. Tamaño de Palabra ---
        ttk.Label(main_frame, text="Tamaño de palabra (bits):").grid(
            row=1, column=0, sticky="w", pady=4)
        self.palabra_entry = ttk.Entry(main_frame, width=30)
        self.palabra_entry.insert(0, "16")
        self.palabra_entry.grid(row=1, column=1, sticky="ew", padx=5)

        # --- 3. Distribución ---
        ttk.Label(main_frame, text="Distribución de memorias:").grid(
            row=2, column=0, sticky="w", pady=4)
        self.distribucion_combo = ttk.Combobox(
            main_frame, values=["Harvard", "Von Neumann"],
            state="readonly", width=28)
        self.distribucion_combo.set("Harvard")
        self.distribucion_combo.grid(row=2, column=1, sticky="ew", padx=5)

        # --- 4. Profundidad ---
        ttk.Label(main_frame, text="Profundidad (direcciones):").grid(
            row=3, column=0, sticky="w", pady=4)
        self.profundidad_entry = ttk.Entry(main_frame, width=30)
        self.profundidad_entry.insert(0, "1024")
        self.profundidad_entry.grid(row=3, column=1, sticky="ew", padx=5)

        # --- 5. Ancho ---
        ttk.Label(main_frame, text="Ancho de memoria (bits):").grid(
            row=4, column=0, sticky="w", pady=4)
        self.ancho_entry = ttk.Entry(main_frame, width=30)
        self.ancho_entry.insert(0, "8")
        self.ancho_entry.grid(row=4, column=1, sticky="ew", padx=5)

        # --- 6. Mínimo Direccionable ---
        ttk.Label(main_frame, text="Mínimo direccionable (bits):").grid(
            row=5, column=0, sticky="w", pady=4)
        self.min_dir_entry = ttk.Entry(main_frame, width=30)
        self.min_dir_entry.insert(0, "1")
        self.min_dir_entry.grid(row=5, column=1, sticky="ew", padx=5)

        # --- 7. Mapeo ---
        ttk.Label(main_frame, text="Mapeo de memoria (Inicio Hex):").grid(
            row=6, column=0, sticky="w", pady=4)
        self.mapeo_entry = ttk.Entry(main_frame, width=30)
        self.mapeo_entry.insert(0, "0x0000")
        self.mapeo_entry.grid(row=6, column=1, sticky="ew", padx=5)

        # --- 8. Aumento PC ---
        ttk.Label(main_frame, text="Aumento del PC (pasos):").grid(
            row=7, column=0, sticky="w", pady=4)
        self.aumento_pc_spin = ttk.Spinbox(main_frame, from_=1, to=16, increment=1, width=29)
        self.aumento_pc_spin.set(1)
        self.aumento_pc_spin.grid(row=7, column=1, sticky="ew", padx=5)

        # --- 9. Endianness ---
        ttk.Label(main_frame, text="Endianness:").grid(
            row=8, column=0, sticky="w", pady=4)
        self.endianness_combo = ttk.Combobox(
            main_frame, values=["Little Endian", "Big Endian"],
            state="readonly", width=28)
        self.endianness_combo.set("Little Endian")
        self.endianness_combo.grid(row=8, column=1, sticky="ew", padx=5)

        # --- Sección Registros ---
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=9, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Label(main_frame, text="Registros",
                  font=("Arial", 10, "bold")).grid(
            row=10, column=0, columnspan=2, sticky="w", pady=(0, 4))

        ttk.Label(main_frame, text="Prefijo de registro:").grid(
            row=11, column=0, sticky="w", pady=4)
        self.prefijo_entry = ttk.Entry(main_frame, width=30)
        self.prefijo_entry.insert(0, "x")
        self.prefijo_entry.grid(row=11, column=1, sticky="ew", padx=5)

        ttk.Label(main_frame, text="  ej: x → x0, x1 ... xN",
                  foreground="gray").grid(row=12, column=1, sticky="w", padx=5)

        ttk.Label(main_frame, text="Número de registros:").grid(
            row=13, column=0, sticky="w", pady=4)
        self.num_reg_spin = ttk.Spinbox(main_frame, from_=2, to=256, increment=1, width=29)
        self.num_reg_spin.set(32)
        self.num_reg_spin.grid(row=13, column=1, sticky="ew", padx=5)

        # --- Botones ---
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=14, column=0, columnspan=2, sticky="ew", pady=12)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=15, column=0, columnspan=2)

        ttk.Button(btn_frame, text="Cancelar",
                   command=self.ventana.destroy).pack(side="left", padx=10)

        texto_btn = "Guardar cambios" if self._modo_edicion else "Guardar en..."
        ttk.Button(btn_frame, text=texto_btn,
                   command=self.guardar_datos).pack(side="right", padx=10)

    def _poblar_campos(self, p: Procesador):
        """Rellena todos los campos con los datos del procesador existente."""
        def _set(entry, valor):
            entry.delete(0, tk.END)
            entry.insert(0, str(valor))

        _set(self.nombre_entry,     p.nombre)
        _set(self.palabra_entry,    p.tamano_palabra)
        _set(self.profundidad_entry, p.profundidad)
        _set(self.ancho_entry,      p.ancho)
        _set(self.min_dir_entry,    p.tamano_minimo_direccionable)
        _set(self.mapeo_entry,      f"0x{p.mapeo_memoria:04X}")
        _set(self.prefijo_entry,    p.prefijo_registro)

        self.aumento_pc_spin.set(p.aumento_pc)
        self.num_reg_spin.set(p.num_registros)
        self.distribucion_combo.set(p.distribucion_memorias)
        self.endianness_combo.set(p.endianess)

    def guardar_datos(self):
        try:
            nombre = self.nombre_entry.get().strip()
            if not nombre:
                raise ValueError("El nombre no puede estar vacío.")

            tamano_palabra  = int(self.palabra_entry.get())
            distribucion    = self.distribucion_combo.get()
            profundidad     = int(self.profundidad_entry.get())
            ancho           = int(self.ancho_entry.get())
            min_dir         = int(self.min_dir_entry.get())
            mapeo_raw       = self.mapeo_entry.get()
            mapeo_memoria   = int(mapeo_raw, 16) if "0x" in mapeo_raw.lower() else int(mapeo_raw)
            aumento_pc      = int(self.aumento_pc_spin.get())
            endianness      = self.endianness_combo.get()
            prefijo         = self.prefijo_entry.get().strip()
            if not prefijo:
                raise ValueError("El prefijo de registro no puede estar vacío.")
            num_registros   = int(self.num_reg_spin.get())

            if self._modo_edicion:
                # Actualizar el procesador existente preservando formatos e instrucciones
                p = self.procesador_existente
                p.nombre                      = nombre
                p.tamano_palabra              = tamano_palabra
                p.distribucion_memorias       = distribucion
                p.profundidad                 = profundidad
                p.ancho                       = ancho
                p.tamano_minimo_direccionable = min_dir
                p.mapeo_memoria               = mapeo_memoria
                p.aumento_pc                  = aumento_pc
                p.endianess                   = endianness
                p.prefijo_registro            = prefijo
                p.num_registros               = num_registros

                if p.ruta_archivo:
                    p.guardarEnJSON(p.ruta_archivo)
                    messagebox.showinfo("Guardado",
                                        f"Directivas de '{nombre}' actualizadas.")
                else:
                    # Sin ruta previa — pedir dónde guardar
                    archivo = filedialog.asksaveasfilename(
                        title="Guardar Arquitectura",
                        defaultextension=".json",
                        initialfile=f"{nombre}.json",
                        filetypes=[("Archivos JSON", "*.json")]
                    )
                    if archivo:
                        p.guardarEnJSON(archivo)

                self.ventana.destroy()
                self.controlador.abrir_ide(p)

            else:
                # Modo creación — nuevo procesador
                nuevo_procesador = Procesador(
                    nombre=nombre,
                    tamano_palabra=tamano_palabra,
                    distribucion_memorias=distribucion,
                    profundidad=profundidad,
                    ancho=ancho,
                    tamano_minimo_direccionable=min_dir,
                    mapeo_memoria=mapeo_memoria,
                    aumento_pc=aumento_pc,
                    endianess=endianness,
                    prefijo_registro=prefijo,
                    num_registros=num_registros
                )

                archivo_guardado = filedialog.asksaveasfilename(
                    title="Guardar Arquitectura",
                    defaultextension=".json",
                    initialfile=f"{nombre}.json",
                    filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
                )

                if archivo_guardado:
                    nuevo_procesador.guardarEnJSON(archivo_guardado)

                    respuesta = messagebox.askyesno(
                        "Arquitectura Guardada",
                        f"Se guardó '{nombre}'.\n¿Deseas definir los Formatos de Instrucción ahora?"
                    )

                    self.ventana.destroy()

                    if respuesta:
                        self.controlador.abrir_crear_formatos(nuevo_procesador)
                    else:
                        self.controlador.abrir_ide(nuevo_procesador)

        except ValueError as ve:
            messagebox.showerror("Error de validación",
                                 f"Por favor verifica los datos.\nDetalle: {ve}")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error inesperado: {e}")
