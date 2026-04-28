# src/services/VentanaIDE.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
import os
from models.ensamblador import Ensamblador, ErrorDeEnsamblado


class VentanaIDE:
    def __init__(self, parent, controlador, procesador):
        self.controlador = controlador
        self.procesador = procesador
        self.ruta_asm = None
        self._hay_cambios = False

        self.mnemonicos = {
            inst.get("mnemonico", "").upper()
            for inst in procesador.set_de_instrucciones
            if inst.get("mnemonico")
        }

        self.ventana = tk.Toplevel(parent)
        self.ventana.title(f"IDE — {procesador.nombre}")
        self.ventana.geometry("900x700")
        self.ventana.transient(parent)
        self.ventana.protocol("WM_DELETE_WINDOW", self._confirmar_cierre)

        self._construir_interfaz()
        self._actualizar_titulo()

    # ─────────────────────────────────────────────
    #  CONSTRUCCIÓN
    # ─────────────────────────────────────────────

    def _construir_interfaz(self):
        self._construir_toolbar()
        self._construir_editor()
        self._construir_consola()
        self._construir_statusbar()

    def _construir_toolbar(self):
        toolbar = ttk.Frame(self.ventana, relief="raised")
        toolbar.pack(side="top", fill="x", padx=2, pady=2)

        ttk.Button(toolbar, text="💾 Guardar",       command=self.guardar).pack(side="left", padx=4, pady=2)
        ttk.Button(toolbar, text="📂 Guardar como…", command=self.guardar_como).pack(side="left", padx=4, pady=2)

        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=6)

        ttk.Button(toolbar, text="⚙️ Ensamblar",     command=self.ensamblar).pack(side="left", padx=4, pady=2)
        ttk.Button(toolbar, text="📋 Instrucciones", command=self.abrir_set_instrucciones).pack(side="left", padx=4, pady=2)

        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=6)

        self.lbl_info = ttk.Label(toolbar, text=self._texto_info())
        self.lbl_info.pack(side="left", padx=4)

    def _construir_editor(self):
        frame_editor = ttk.Frame(self.ventana)
        frame_editor.pack(expand=True, fill="both", padx=4, pady=(4, 0))

        self.numeros = tk.Text(
            frame_editor, width=4, padx=6, state="disabled",
            bg="#f0f0f0", fg="#888888", font=("Courier New", 11),
            relief="flat", cursor="arrow", selectbackground="#f0f0f0",
        )
        self.numeros.pack(side="left", fill="y")

        scroll_v = ttk.Scrollbar(frame_editor, orient="vertical")
        scroll_v.pack(side="right", fill="y")

        self.editor = tk.Text(
            frame_editor, undo=True, wrap="none",
            font=("Courier New", 11), bg="#ffffff", fg="#000000",
            insertbackground="#000000", selectbackground="#cce5ff",
            relief="flat", yscrollcommand=self._scroll_sincronizado,
        )
        self.editor.pack(expand=True, fill="both")
        scroll_v.config(command=self._scroll_ambos)

        scroll_h = ttk.Scrollbar(self.ventana, orient="horizontal", command=self.editor.xview)
        scroll_h.pack(side="bottom", fill="x")
        self.editor.config(xscrollcommand=scroll_h.set)

        self._configurar_tags()
        self.editor.bind("<KeyRelease>",    self._on_key_release)
        self.editor.bind("<ButtonRelease>", self._actualizar_statusbar)

    def _construir_consola(self):
        """Panel inferior que muestra errores y resultado del ensamblado."""
        frame_consola = ttk.LabelFrame(self.ventana, text="Consola")
        frame_consola.pack(fill="x", padx=4, pady=(2, 4))

        self.consola = tk.Text(
            frame_consola, height=5, font=("Courier New", 10),
            bg="#1e1e1e", fg="#d4d4d4", state="disabled",
            relief="flat", wrap="word"
        )
        self.consola.pack(fill="x", padx=4, pady=4)

        # Tags de color para la consola
        self.consola.tag_configure("error",   foreground="#f44747")
        self.consola.tag_configure("ok",      foreground="#6a9955")
        self.consola.tag_configure("info",    foreground="#9cdcfe")

    def _construir_statusbar(self):
        self.statusbar = ttk.Label(
            self.ventana, text="Lín 1, Col 1",
            anchor="e", relief="sunken", padding=(4, 2)
        )
        self.statusbar.pack(side="bottom", fill="x")

    # ─────────────────────────────────────────────
    #  SET DE INSTRUCCIONES DESDE EL IDE
    # ─────────────────────────────────────────────

    def _texto_info(self):
        prefijo = self.procesador.prefijo_registro
        n_regs  = self.procesador.num_registros
        return (f"Procesador: {self.procesador.nombre}  |  "
                f"Registros: {prefijo}0–{prefijo}{n_regs - 1}  |  "
                f"Instrucciones: {len(self.procesador.set_de_instrucciones)}")

    def abrir_set_instrucciones(self):
        """
        Abre la ventana de set de instrucciones con el procesador actual.
        Al cerrarla, actualiza el resaltado con los mnemónicos nuevos.
        """
        from services.CrearSetInstrucciones import VentanaCrearSetInstrucciones
        ventana = VentanaCrearSetInstrucciones(
            self.ventana, controlador=self.controlador, procesador=self.procesador
        )
        # Cuando la ventana de instrucciones se cierre, refrescamos
        self.ventana.wait_window(ventana.ventana)
        self._refrescar_mnemonicos()

    def _refrescar_mnemonicos(self):
        """
        Actualiza el set de mnemónicos y el resaltado después de
        modificar instrucciones sin salir del IDE.
        """
        self.mnemonicos = {
            inst.get("mnemonico", "").upper()
            for inst in self.procesador.set_de_instrucciones
            if inst.get("mnemonico")
        }
        self._resaltar_sintaxis()
        # Actualizar contador en el toolbar
        self.lbl_info.config(text=self._texto_info())

    # ─────────────────────────────────────────────
    #  RESALTADO
    # ─────────────────────────────────────────────

    def _configurar_tags(self):
        self.editor.tag_configure(
            "mnemonico", foreground="#0000cc",
            font=("Courier New", 11, "bold")
        )

    def _resaltar_sintaxis(self):
        self.editor.tag_remove("mnemonico", "1.0", tk.END)
        contenido = self.editor.get("1.0", tk.END)
        for n_linea, linea in enumerate(contenido.split("\n"), start=1):
            parte_codigo = linea.split(";")[0]
            for m in re.finditer(r"\b([A-Za-z_]\w*)\b", parte_codigo):
                if m.group(1).upper() in self.mnemonicos:
                    self.editor.tag_add(
                        "mnemonico",
                        f"{n_linea}.{m.start()}",
                        f"{n_linea}.{m.end()}"
                    )

    # ─────────────────────────────────────────────
    #  NUMERACIÓN Y SCROLL
    # ─────────────────────────────────────────────

    def _actualizar_numeros(self):
        self.numeros.config(state="normal")
        self.numeros.delete("1.0", tk.END)
        total = int(self.editor.index(tk.END).split(".")[0])
        self.numeros.insert("1.0", "\n".join(str(i) for i in range(1, total)))
        self.numeros.config(state="disabled")

    def _scroll_sincronizado(self, *args):
        self.numeros.yview_moveto(args[0])

    def _scroll_ambos(self, *args):
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
        nombre  = self.ruta_asm if self.ruta_asm else "Sin guardar"
        cambios = " •" if self._hay_cambios else ""
        self.ventana.title(f"IDE — {self.procesador.nombre}  |  {nombre}{cambios}")

    # ─────────────────────────────────────────────
    #  CONSOLA
    # ─────────────────────────────────────────────

    def _log(self, texto, tag="info"):
        self.consola.config(state="normal")
        self.consola.insert(tk.END, texto + "\n", tag)
        self.consola.see(tk.END)
        self.consola.config(state="disabled")

    def _limpiar_consola(self):
        self.consola.config(state="normal")
        self.consola.delete("1.0", tk.END)
        self.consola.config(state="disabled")

    # ─────────────────────────────────────────────
    #  ENSAMBLAR
    # ─────────────────────────────────────────────

    def ensamblar(self):
        """
        Ensambla el código del editor y ofrece guardar los archivos de salida.
        """
        self._limpiar_consola()
        codigo = self.editor.get("1.0", tk.END).strip()

        if not codigo:
            self._log("⚠  El editor está vacío.", "error")
            return

        ensamblador = Ensamblador(self.procesador)

        try:
            binarios = ensamblador.ensamblar(codigo)
        except ErrorDeEnsamblado as e:
            self._log(f"✗  Error: {e}", "error")
            return
        except Exception as e:
            self._log(f"✗  Error inesperado: {e}", "error")
            return

        n = len(binarios)
        self._log(f"✔  Ensamblado exitoso — {n} instrucción(es).", "ok")

        # Mostrar las instrucciones en la consola
        direccion = self.procesador.mapeo_memoria
        paso = self.procesador.aumento_pc
        for b in binarios:
            hex_val = f"{int(b, 2):08X}"
            self._log(f"   0x{direccion:08X}  {b}  ({hex_val})", "info")
            direccion += paso

        # Preguntar dónde guardar
        self._guardar_salida(ensamblador)

    def _guardar_salida(self, ensamblador: Ensamblador):
        """Abre diálogo para elegir formato y ruta de salida."""
        # Ventana de selección de formato
        dialogo = tk.Toplevel(self.ventana)
        dialogo.title("Guardar salida")
        dialogo.geometry("300x200")
        dialogo.transient(self.ventana)
        dialogo.grab_set()

        ttk.Label(dialogo, text="Selecciona el formato de salida:",
                  font=("Arial", 11)).pack(pady=15)

        var = tk.StringVar(value="bin")
        for texto, valor in [(".bin  — Binario puro", "bin"),
                              (".mem  — Hex para $readmemh", "mem"),
                              (".coe  — Xilinx Block RAM", "coe")]:
            ttk.Radiobutton(dialogo, text=texto, variable=var,
                            value=valor).pack(anchor="w", padx=30)

        def confirmar():
            fmt = var.get()
            dialogo.destroy()
            self._exportar(ensamblador, fmt)

        ttk.Button(dialogo, text="Guardar…", command=confirmar).pack(pady=15)

    def _exportar(self, ensamblador: Ensamblador, fmt: str):
        nombre_base = os.path.splitext(
            os.path.basename(self.ruta_asm)
        )[0] if self.ruta_asm else self.procesador.nombre

        ruta = filedialog.asksaveasfilename(
            title="Guardar archivo ensamblado",
            defaultextension=f".{fmt}",
            initialfile=f"{nombre_base}.{fmt}",
            filetypes=[(f"Archivo .{fmt}", f"*.{fmt}"), ("Todos", "*.*")]
        )

        if not ruta:
            return

        try:
            if fmt == "bin":
                ensamblador.generar_bin(ruta)
            elif fmt == "mem":
                ensamblador.generar_mem(ruta)
            elif fmt == "coe":
                ensamblador.generar_coe(ruta)
            self._log(f"✔  Guardado en: {ruta}", "ok")
        except Exception as e:
            self._log(f"✗  Error al guardar: {e}", "error")

    # ─────────────────────────────────────────────
    #  GUARDAR .ASM
    # ─────────────────────────────────────────────

    def guardar(self):
        if self.ruta_asm:
            self._escribir_archivo(self.ruta_asm)
        else:
            self.guardar_como()

    def guardar_como(self):
        ruta = filedialog.asksaveasfilename(
            title="Guardar código ensamblador",
            defaultextension=".asm",
            initialfile=f"{self.procesador.nombre}.asm",
            filetypes=[("Archivos ensamblador", "*.asm"),
                       ("Archivos de texto", "*.txt"),
                       ("Todos", "*.*")]
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
            messagebox.showerror("Error al guardar", f"No se pudo guardar:\n{e}")

    # ─────────────────────────────────────────────
    #  CIERRE SEGURO
    # ─────────────────────────────────────────────

    def _confirmar_cierre(self):
        if self._hay_cambios:
            r = messagebox.askyesnocancel(
                "Cambios sin guardar",
                "Tienes cambios sin guardar.\n¿Deseas guardar antes de cerrar?"
            )
            if r is True:
                self.guardar()
                self.ventana.destroy()
            elif r is False:
                self.ventana.destroy()
        else:
            self.ventana.destroy()