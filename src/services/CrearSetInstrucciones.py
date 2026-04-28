# src/services/CrearSetInstrucciones.py
import tkinter as tk
from tkinter import ttk, messagebox


class VentanaCrearSetInstrucciones:
    def __init__(self, parent, controlador, procesador):
        self.controlador = controlador
        self.procesador = procesador

        self.ventana = tk.Toplevel(parent)
        self.ventana.title(f"Set de Instrucciones - {self.procesador.nombre}")
        self.ventana.geometry("700x520")
        self.ventana.transient(parent)
        self.ventana.grab_set()

        self._construir_interfaz()
        self._cargar_instrucciones_existentes()

    def _construir_interfaz(self):
        ttk.Label(
            self.ventana,
            text=f"Instrucciones para: {self.procesador.nombre}",
            font=("Arial", 14, "bold")
        ).pack(pady=10)

        panel_principal = ttk.Frame(self.ventana)
        panel_principal.pack(expand=True, fill="both", padx=10, pady=10)

        # --- PANEL IZQUIERDO: LISTA ---
        panel_lista = ttk.LabelFrame(panel_principal, text="Instrucciones Agregadas")
        panel_lista.pack(side="left", fill="both", expand=True, padx=5)

        self.lista_instrucciones = tk.Listbox(panel_lista)
        self.lista_instrucciones.pack(fill="both", expand=True, padx=5, pady=5)

        # Botón para eliminar instrucción seleccionada
        ttk.Button(
            panel_lista,
            text="Eliminar seleccionada",
            command=self.eliminar_instruccion
        ).pack(pady=5)

        # --- PANEL DERECHO: FORMULARIO ---
        panel_form = ttk.LabelFrame(panel_principal, text="Nueva Instrucción")
        panel_form.pack(side="right", fill="both", expand=True, padx=5)

        # Mnemónico
        ttk.Label(panel_form, text="Mnemónico (ej. ADD):").pack(anchor="w", padx=5, pady=(8, 0))
        self.mnemonico_entry = ttk.Entry(panel_form)
        self.mnemonico_entry.pack(fill="x", padx=5, pady=2)

        # Opcode
        ttk.Label(panel_form, text="Opcode (ej. 0010):").pack(anchor="w", padx=5, pady=(8, 0))
        self.opcode_entry = ttk.Entry(panel_form)
        self.opcode_entry.pack(fill="x", padx=5, pady=2)

        # Descripción
        ttk.Label(panel_form, text="Descripción:").pack(anchor="w", padx=5, pady=(8, 0))
        self.desc_entry = ttk.Entry(panel_form)
        self.desc_entry.pack(fill="x", padx=5, pady=2)

        # CORREGIDO: el botón ahora llama a la lógica real
        ttk.Button(
            panel_form,
            text="Agregar Instrucción",
            command=self.agregar_instruccion
        ).pack(pady=15)

        # --- BOTONES INFERIORES ---
        btn_frame = ttk.Frame(self.ventana)
        btn_frame.pack(fill="x", pady=10, padx=10)

        ttk.Button(
            btn_frame,
            text="Finalizar y Guardar",
            command=self.finalizar
        ).pack(side="right", padx=5)

    def _cargar_instrucciones_existentes(self):
        """Muestra en el Listbox las instrucciones que ya tenía el procesador."""
        for inst in self.procesador.set_de_instrucciones:
            mnem = inst.get("mnemonico", "?")
            opcode = inst.get("opcode", "?")
            self.lista_instrucciones.insert(tk.END, f"{mnem}  [{opcode}]")

    def agregar_instruccion(self):
        """
        CORREGIDO: Valida, construye el diccionario de la instrucción,
        lo agrega a procesador.set_de_instrucciones y actualiza el Listbox.
        """
        mnem = self.mnemonico_entry.get().strip().upper()
        opcode = self.opcode_entry.get().strip()
        desc = self.desc_entry.get().strip()

        if not mnem:
            messagebox.showwarning("Atención", "El mnemónico no puede estar vacío.")
            return

        if not opcode:
            messagebox.showwarning("Atención", "El opcode no puede estar vacío.")
            return

        # Verificar que el mnemónico no esté duplicado
        existentes = [i.get("mnemonico", "") for i in self.procesador.set_de_instrucciones]
        if mnem in existentes:
            messagebox.showwarning("Duplicado", f"Ya existe una instrucción con mnemónico '{mnem}'.")
            return

        nueva_instruccion = {
            "mnemonico": mnem,
            "opcode": opcode,
            "descripcion": desc
        }

        # Persistir en el objeto Procesador
        self.procesador.set_de_instrucciones.append(nueva_instruccion)

        # Actualizar la UI
        self.lista_instrucciones.insert(tk.END, f"{mnem}  [{opcode}]")

        # Limpiar campos
        self.mnemonico_entry.delete(0, tk.END)
        self.opcode_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)

    def eliminar_instruccion(self):
        """Elimina la instrucción seleccionada de la lista y del procesador."""
        seleccion = self.lista_instrucciones.curselection()
        if not seleccion:
            messagebox.showinfo("Selección", "Selecciona una instrucción de la lista para eliminarla.")
            return

        indice = seleccion[0]
        mnem = self.procesador.set_de_instrucciones[indice].get("mnemonico", "?")

        confirmar = messagebox.askyesno("Confirmar", f"¿Eliminar la instrucción '{mnem}'?")
        if confirmar:
            del self.procesador.set_de_instrucciones[indice]
            self.lista_instrucciones.delete(indice)

    def finalizar(self):
        """
        CORREGIDO: Guarda el JSON en la ruta original del archivo
        y cierra la ventana con un mensaje real (no 'Simulado').
        """
        if self.procesador.ruta_archivo:
            try:
                self.procesador.guardarEnJSON(self.procesador.ruta_archivo)
                self.ventana.destroy()
                messagebox.showinfo(
                    "Guardado",
                    f"Set de instrucciones guardado correctamente en:\n{self.procesador.ruta_archivo}"
                )
            except Exception as e:
                messagebox.showerror("Error al guardar", f"No se pudo guardar el archivo:\n{e}")
        else:
            messagebox.showwarning(
                "Ruta no encontrada",
                "No se encontró la ruta del archivo. "
                "Asegúrate de haber guardado la arquitectura antes de continuar."
            )
