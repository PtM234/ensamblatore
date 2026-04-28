# src/services/VentanaIDE.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re


class VentanaIDE:
    def __init__(self, parent, controlador, procesador):
        self.controlador = controlador
        self.procesador = procesador
        self.ruta_asm = None  # Ruta del archivo .asm activo (None = sin guardar)

        # Extraemos los mnemónicos del procesador para el resaltado
        self.mnemonicos = {
            inst.get("mnemonico", "").upper()
            for inst in procesador.set_de_instrucciones
            if inst.get("mnemonico")
        }

        self.ventana = tk.Toplevel(parent)
        self.ventana.title(f"IDE — {procesador.nombre}")
        self.ventana.geometry("900x650")
        self.ventana.transient(parent)

        # Confirmar cierre si hay cambios sin guardar
        self.ventana.protocol("WM_DELETE_WINDOW", self._confirmar_cierre)

        self._hay_cambios = False  # Flag para detectar cambios sin guardar

        self._construir_interfaz()
        self._actualizar_titulo()

    # ─────────────────────────────────────────────
    #  CONSTRUCCIÓN DE LA INTERFAZ
    # ─────────────────────────────────────────────

    def _construir_interfaz(self):
        self._construir_toolbar()
        self._construir_editor()
        self._construir_statusbar()

    def _construir_toolbar(self):
        toolbar = ttk.Frame(self.ventana, relief="raised")
        toolbar.pack(side="top", fill="x", padx=2, pady=2)

        ttk.Button(toolbar, text="💾 Guardar",       command=self.guardar).pack(side="left", padx=4, pady=2)
        ttk.Button(toolbar, text="📂 Guardar como…", command=self.guardar_como).pack(side="left", padx=4, pady=2)

        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=6)

        ttk.Label(
            toolbar,
            text=f"Procesador: {self.procesador.nombre}  |  "
                 f"Instrucciones: {len(self.procesador.set_de_instrucciones)}  |  "
                 f"Formatos: {len(self.procesador.formato_de_sintaxis)}"
        ).pack(side="left", padx=4)

    def _construir_editor(self):
        """Área principal: números de línea + editor de texto."""
        frame_editor = ttk.Frame(self.ventana)
        frame_editor.pack(expand=True, fill="both", padx=4, pady=4)

        # ── Números de línea ──────────────────────────────────────────
        self.numeros = tk.Text(
            frame_editor,
            width=4,
            padx=6,
            state="disabled",
            bg="#2b2b2b",
            fg="#858585",
            font=("Courier New", 11),
            relief="flat",
            cursor="arrow",
            selectbackground="#2b2b2b",  # Sin selección visual
        )
        self.numeros.pack(side="left", fill="y")

        # ── Scrollbar vertical compartida ────────────────────────────
        scroll_v = ttk.Scrollbar(frame_editor, orient="vertical")
        scroll_v.pack(side="right", fill="y")

        # ── Editor principal ─────────────────────────────────────────
        self.editor = tk.Text(
            frame_editor,
            undo=True,
            wrap="none",
            font=("Courier New", 11),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="#ffffff",
            selectbackground="#264f78",
            relief="flat",
            yscrollcommand=self._scroll_sincronizado,
        )
        self.editor.pack(expand=True, fill="both")

        # Conectar scrollbar con ambos widgets
        scroll_v.config(command=self._scroll_ambos)

        # ── Scrollbar horizontal solo para el editor ─────────────────
        scroll_h = ttk.Scrollbar(self.ventana, orient="horizontal", command=self.editor.xview)
        scroll_h.pack(side="bottom", fill="x")
        self.editor.config(xscrollcommand=scroll_h.set)

        # ── Configurar tags de color ─────────────────────────────────
        self._configurar_tags()

        # ── Eventos ──────────────────────────────────────────────────
        self.editor.bind("<KeyRelease>",    self._on_key_release)
        self.editor.bind("<ButtonRelease>", self._actualizar_statusbar)

    def _construir_statusbar(self):
        self.statusbar = ttk.Label(
            self.ventana,
            text="Lín 1, Col 1",
            anchor="e",
            relief="sunken",
            padding=(4, 2)
        )
        self.statusbar.pack(side="bottom", fill="x")

    # ─────────────────────────────────────────────
    #  TAGS DE COLOR (resaltado de sintaxis)
    # ─────────────────────────────────────────────

    def _configurar_tags(self):
        # Mnemónicos de instrucción → azul claro
        self.editor.tag_configure("mnemonico",  foreground="#569cd6", font=("Courier New", 11, "bold"))
        # Comentarios (;…) → verde
        self.editor.tag_configure("comentario", foreground="#6a9955", font=("Courier New", 11, "italic"))
        # Números (dec, 0x hex, 0b bin) → naranja claro
        self.editor.tag_configure("numero",     foreground="#ce9178")
        # Registros (r0..r31 / R0..R31) → verde azulado
        self.editor.tag_configure("registro",   foreground="#4ec9b0")
        # Etiquetas (palabra seguida de :) → amarillo
        self.editor.tag_configure("etiqueta",   foreground="#dcdcaa")

    # ─────────────────────────────────────────────
    #  RESALTADO DE SINTAXIS
    # ─────────────────────────────────────────────

    def _resaltar_sintaxis(self):
        """Elimina todos los tags y vuelve a aplicar el resaltado en todo el documento."""
        for tag in ("mnemonico", "comentario", "numero", "registro", "etiqueta"):
            self.editor.tag_remove(tag, "1.0", tk.END)

        contenido = self.editor.get("1.0", tk.END)
        lineas = contenido.split("\n")

        for n_linea, linea in enumerate(lineas, start=1):
            inicio_linea = f"{n_linea}.0"

            # 1. Comentarios — todo lo que va desde ; hasta el final de línea
            m = re.search(r";.*$", linea)
            if m:
                self.editor.tag_add("comentario",
                                    f"{n_linea}.{m.start()}",
                                    f"{n_linea}.{m.end()}")
                # Solo resaltamos antes del comentario
                linea = linea[:m.start()]

            # 2. Etiquetas (palabras que terminan en :)
            for m in re.finditer(r"\b(\w+)\s*:", linea):
                self.editor.tag_add("etiqueta",
                                    f"{n_linea}.{m.start()}",
                                    f"{n_linea}.{m.end()}")

            # 3. Mnemónicos (primera palabra de la instrucción, ignorando etiquetas)
            #    Busca palabras que estén en el set de instrucciones del procesador
            for m in re.finditer(r"\b([A-Za-z_]\w*)\b", linea):
                if m.group(1).upper() in self.mnemonicos:
                    self.editor.tag_add("mnemonico",
                                        f"{n_linea}.{m.start()}",
                                        f"{n_linea}.{m.end()}")

            # 4. Registros (r0–r31, R0–R31)
            for m in re.finditer(r"\b[Rr]\d{1,2}\b", linea):
                self.editor.tag_add("registro",
                                    f"{n_linea}.{m.start()}",
                                    f"{n_linea}.{m.end()}")

            # 5. Números (0x…, 0b…, decimales)
            for m in re.finditer(r"\b(0x[0-9A-Fa-f]+|0b[01]+|\d+)\b", linea):
                self.editor.tag_add("numero",
                                    f"{n_linea}.{m.start()}",
                                    f"{n_linea}.{m.end()}")

    # ─────────────────────────────────────────────
    #  NUMERACIÓN DE LÍNEAS
    # ─────────────────────────────────────────────

    def _actualizar_numeros(self):
        """Redibuja el panel de números de línea."""
        self.numeros.config(state="normal")
        self.numeros.delete("1.0", tk.END)

        total_lineas = int(self.editor.index(tk.END).split(".")[0])
        numeracion = "\n".join(str(i) for i in range(1, total_lineas))
        self.numeros.insert("1.0", numeracion)

        self.numeros.config(state="disabled")

    # ─────────────────────────────────────────────
    #  SCROLL SINCRONIZADO
    # ─────────────────────────────────────────────

    def _scroll_sincronizado(self, *args):
        """Mueve la scrollbar y sincroniza los números de línea."""
        self.numeros.yview_moveto(args[0])

    def _scroll_ambos(self, *args):
        """Desplaza editor y números al mismo tiempo."""
        self.editor.yview(*args)
        self.numeros.yview(*args)

    # ─────────────────────────────────────────────
    #  EVENTOS
    # ─────────────────────────────────────────────

    def _on_key_release(self, event=None):
        self._hay_cambios = True
        self._actualizar_numeros()
        self._resaltar_sintaxis()
        self._actualizar_statusbar()
        self._actualizar_titulo()

    def _actualizar_statusbar(self, event=None):
        pos = self.editor.index(tk.INSERT)
        linea, col = pos.split(".")
        self.statusbar.config(text=f"Lín {linea}, Col {int(col) + 1}")

    def _actualizar_titulo(self):
        nombre_archivo = self.ruta_asm if self.ruta_asm else "Sin guardar"
        cambios = " •" if self._hay_cambios else ""
        self.ventana.title(f"IDE — {self.procesador.nombre}  |  {nombre_archivo}{cambios}")

    # ─────────────────────────────────────────────
    #  GUARDAR
    # ─────────────────────────────────────────────

    def guardar(self):
        """Guarda en la ruta actual; si no hay ruta, abre el diálogo."""
        if self.ruta_asm:
            self._escribir_archivo(self.ruta_asm)
        else:
            self.guardar_como()

    def guardar_como(self):
        """Abre el diálogo 'Guardar como' para elegir ruta y nombre."""
        ruta = filedialog.asksaveasfilename(
            title="Guardar código ensamblador",
            defaultextension=".asm",
            initialfile=f"{self.procesador.nombre}.asm",
            filetypes=[("Archivos ensamblador", "*.asm"), ("Archivos de texto", "*.txt"), ("Todos", "*.*")]
        )
        if ruta:
            self.ruta_asm = ruta
            self._escribir_archivo(ruta)

    def _escribir_archivo(self, ruta):
        try:
            contenido = self.editor.get("1.0", tk.END)
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(contenido)
            self._hay_cambios = False
            self._actualizar_titulo()
        except Exception as e:
            messagebox.showerror("Error al guardar", f"No se pudo guardar el archivo:\n{e}")

    # ─────────────────────────────────────────────
    #  CIERRE SEGURO
    # ─────────────────────────────────────────────

    def _confirmar_cierre(self):
        if self._hay_cambios:
            respuesta = messagebox.askyesnocancel(
                "Cambios sin guardar",
                "Tienes cambios sin guardar.\n¿Deseas guardar antes de cerrar?"
            )
            if respuesta is True:
                self.guardar()
                self.ventana.destroy()
            elif respuesta is False:
                self.ventana.destroy()
            # Si es None (Cancel), no hacemos nada
        else:
            self.ventana.destroy()
