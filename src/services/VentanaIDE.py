# src/services/VentanaIDE.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
import os
import json

from models.procesador import Procesador
from models.ensamblador import Ensamblador, ErrorDeEnsamblado


class VentanaIDE:
    """
    Ventana principal de Ensamblatore.
    El editor y el menú Formato se habilitan solo cuando
    hay un procesador cargado.
    """

    def __init__(self, root):
        self.root       = root
        self.procesador = None
        self.ruta_asm   = None
        self._hay_cambios = False
        self.mnemonicos   = set()

        self.root.title("Ensamblatore")
        self.root.geometry("1280x760")
        self.root.protocol("WM_DELETE_WINDOW", self._confirmar_cierre)

        self._construir_menubar()
        self._construir_cuerpo()
        self._construir_consola()
        self._construir_statusbar()

        # Estado inicial: sin procesador
        self._set_estado_sin_procesador()

    # ─────────────────────────────────────────────
    #  MENUBAR
    # ─────────────────────────────────────────────

    def _construir_menubar(self):
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)

        # ── Menú Archivo ─────────────────────────────────────────────
        menu_archivo = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Archivo", menu=menu_archivo)

        menu_archivo.add_command(label="Nuevo procesador",
                                 command=self._nuevo_procesador)
        menu_archivo.add_command(label="Cargar procesador",
                                 command=self._cargar_procesador)

        menu_archivo.add_separator()

        menu_archivo.add_command(label="Guardar .asm",
                                 command=self.guardar,
                                 accelerator="Ctrl+S")
        menu_archivo.add_command(label="Guardar .asm como…",
                                 command=self.guardar_como)

        menu_archivo.add_separator()

        menu_archivo.add_command(label="Ensamblar",
                                 command=self.ensamblar,
                                 accelerator="F5")

        # Atajos de teclado
        self.root.bind("<Control-s>", lambda e: self.guardar())
        self.root.bind("<F5>",        lambda e: self.ensamblar())

        # ── Menú Formato ──────────────────────────────────────────────
        self.menu_formato = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Formato", menu=self.menu_formato)

        self.menu_formato.add_command(
            label="Directivas del procesador",
            command=self._editar_arquitectura)
        self.menu_formato.add_command(
            label="Crear / Editar formatos de instrucción",
            command=self._abrir_formatos)
        self.menu_formato.add_command(
            label="Agregar / Editar instrucciones",
            command=self._abrir_instrucciones)

    # ─────────────────────────────────────────────
    #  CUERPO PRINCIPAL
    # ─────────────────────────────────────────────

    def _construir_cuerpo(self):
        # PanedWindow horizontal permite al usuario redimensionar el panel lateral
        self._paned = ttk.PanedWindow(self.root, orient="horizontal")
        self._paned.pack(expand=True, fill="both", padx=4, pady=(4, 0))

        # Panel izquierdo de información (redimensionable)
        self._frame_panel_izq = ttk.Frame(self._paned, width=280)
        self._paned.add(self._frame_panel_izq, weight=0)

        # Panel derecho: editor
        self._frame_panel_der = ttk.Frame(self._paned)
        self._paned.add(self._frame_panel_der, weight=1)

        self._construir_panel_info(self._frame_panel_izq)
        self._construir_editor(self._frame_panel_der)

    # ─────────────────────────────────────────────
    #  PANEL INFO
    # ─────────────────────────────────────────────

    def _construir_panel_info(self, parent):
        panel = parent
        panel.pack_propagate(False)

        canvas    = tk.Canvas(panel, borderwidth=0, highlightthickness=0, bg="#f7f7f7")
        scrollbar = ttk.Scrollbar(panel, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._frame_info  = ttk.Frame(canvas)
        self._canvas_info = canvas
        cw = canvas.create_window((0, 0), window=self._frame_info, anchor="nw")

        self._frame_info.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw, width=e.width))

        # Mensaje inicial
        self._lbl_sin_procesador = ttk.Label(
            self._frame_info,
            text="Sin procesador cargado.\n\nUsa Archivo → Nuevo procesador\no Archivo → Cargar procesador.",
            foreground="gray", justify="center", wraplength=220
        )
        self._lbl_sin_procesador.pack(pady=30, padx=10)

    def _poblar_panel_info(self):
        """Destruye el contenido actual y reconstruye con el procesador cargado."""
        for w in self._frame_info.winfo_children():
            w.destroy()

        p = self.procesador

        self._segmento(self._frame_info, "⚙️ Configuración", [
            f"Nombre:          {p.nombre}",
            f"Palabra:         {p.tamano_palabra} bits",
            f"Distribución:    {p.distribucion_memorias}",
            f"Profundidad:     {p.profundidad}",
            f"Ancho memoria:   {p.ancho} bits",
            f"Mín. direc.:     {p.tamano_minimo_direccionable} bits",
            f"Mapeo memoria:   0x{p.mapeo_memoria:08X}",
            f"Aumento PC:      {p.aumento_pc}",
            f"Endianness:      {p.endianess}",
            f"Prefijo reg.:    {p.prefijo_registro}",
            f"Num. registros:  {p.num_registros}",
        ])

        lineas_fmt = []
        for fmt in p.formato_de_sintaxis:
            lineas_fmt.append(f"▸ {fmt.get('nombre','?')}  ({fmt.get('total_bits','?')} bits)")
            lineas_fmt.append(f"  Opcode: {fmt.get('bits_opcode','?')} bits")
            for campo in fmt.get("campos_operandos", []):
                if isinstance(campo, list):
                    lineas_fmt.append(f"  • {campo[0]} ({campo[1]} bits)")
                else:
                    natural = {str(i): i for i in range(campo["bits"])}
                    sufijo  = "  ⇄" if campo.get("orden_bits", natural) != natural else ""
                    lineas_fmt.append(f"  • {campo['nombre']} ({campo['bits']} bits){sufijo}")
            lineas_fmt.append("")
        self._segmento(self._frame_info, "📐 Formatos", lineas_fmt)

        self._segmento_instrucciones(self._frame_info)

        self._segmento_simbolos(self._frame_info)

    def _segmento(self, parent, titulo, lineas):
        ttk.Label(parent, text=titulo, font=("Arial", 9, "bold"),
                  background="#dde3ec").pack(fill="x", padx=4, pady=(6, 0))

        frame = ttk.Frame(parent)
        frame.pack(fill="x", padx=4, pady=(0, 4))

        sb  = ttk.Scrollbar(frame, orient="vertical")
        txt = tk.Text(
            frame,
            height=min(len([l for l in lineas if l]) + 1, 10),
            font=("Courier New", 9), bg="#f7f7f7", fg="#222222",
            relief="flat", wrap="none", state="normal",
            yscrollcommand=sb.set,
        )
        sb.config(command=txt.yview)
        sb.pack(side="right", fill="y")
        txt.pack(side="left", fill="x", expand=True)

        for linea in lineas:
            txt.insert(tk.END, linea + "\n")
        txt.config(state="disabled")

    def _segmento_instrucciones(self, parent):
        """Segmento de instrucciones agrupadas por formato, colapsable."""
        ttk.Label(parent, text="📜 Instrucciones",
                  font=("Arial", 9, "bold"),
                  background="#dde3ec").pack(fill="x", padx=4, pady=(6, 0))

        frame = ttk.Frame(parent)
        frame.pack(fill="x", padx=4, pady=(0, 4))

        sb_v = ttk.Scrollbar(frame, orient="vertical")
        sb_h = ttk.Scrollbar(frame, orient="horizontal")

        self._tree_inst = ttk.Treeview(
            frame,
            selectmode="browse",
            show="tree headings",
            yscrollcommand=sb_v.set,
            xscrollcommand=sb_h.set,
            height=12
        )
        self._tree_inst["columns"] = ("opcode", "mapeo")
        self._tree_inst.heading("#0",     text="Instrucción")
        self._tree_inst.heading("opcode", text="Opcode")
        self._tree_inst.heading("mapeo",  text="Sintaxis")
        self._tree_inst.column("#0",     width=90,  minwidth=70)
        self._tree_inst.column("opcode", width=80,  minwidth=60)
        self._tree_inst.column("mapeo",  width=100, minwidth=70)

        self._tree_inst.tag_configure("grupo", font=("Arial", 9, "bold"),
                                       foreground="#2c5f9e")
        self._tree_inst.tag_configure("instr", font=("Courier New", 9))

        sb_v.config(command=self._tree_inst.yview)
        sb_h.config(command=self._tree_inst.xview)

        sb_v.pack(side="right",  fill="y")
        sb_h.pack(side="bottom", fill="x")
        self._tree_inst.pack(fill="both", expand=True)

        # Al hacer click el treeview toma foco y responde a las flechas
        self._tree_inst.bind("<Button-1>", lambda e: self._tree_inst.focus_set())

        self._poblar_tree_instrucciones()

    def _poblar_tree_instrucciones(self):
        """Puebla el Treeview de instrucciones agrupadas por formato."""
        if not hasattr(self, "_tree_inst"):
            return

        self._tree_inst.delete(*self._tree_inst.get_children())

        if not self.procesador:
            return

        grupos = {}
        for inst in self.procesador.set_de_instrucciones:
            fmt = inst.get("formato", "Sin formato")
            grupos.setdefault(fmt, []).append(inst)

        for fmt_nombre, instrucciones in grupos.items():
            grupo_id = self._tree_inst.insert(
                "", "end",
                text=f"  {fmt_nombre}  ({len(instrucciones)})",
                tags=("grupo",), open=True
            )
            for inst in instrucciones:
                self._tree_inst.insert(
                    grupo_id, "end",
                    text=f"  {inst.get('mnemonico','?')}",
                    values=(inst.get("opcode","?"), inst.get("mapeo_operandos","")),
                    tags=("instr",)
                )

    def _segmento_simbolos(self, parent):
        ttk.Label(parent, text="🏷️ Tabla de símbolos",
                  font=("Arial", 9, "bold"),
                  background="#dde3ec").pack(fill="x", padx=4, pady=(6, 0))

        frame = ttk.Frame(parent)
        frame.pack(fill="x", padx=4, pady=(0, 4))

        sb = ttk.Scrollbar(frame, orient="vertical")
        self._txt_simbolos = tk.Text(
            frame, height=6, font=("Courier New", 9),
            bg="#f7f7f7", fg="#222222", relief="flat",
            wrap="none", state="normal", yscrollcommand=sb.set,
        )
        sb.config(command=self._txt_simbolos.yview)
        sb.pack(side="right", fill="y")
        self._txt_simbolos.pack(side="left", fill="x", expand=True)
        self._txt_simbolos.insert(tk.END, "(vacío — ensambla para ver etiquetas)")
        self._txt_simbolos.config(state="disabled")

    def _actualizar_tabla_simbolos(self, tabla: dict):
        self._txt_simbolos.config(state="normal")
        self._txt_simbolos.delete("1.0", tk.END)
        if tabla:
            for nombre, dir_ in sorted(tabla.items()):
                self._txt_simbolos.insert(tk.END, f"{nombre.ljust(12)} 0x{dir_:08X}\n")
        else:
            self._txt_simbolos.insert(tk.END, "(sin etiquetas)")
        self._txt_simbolos.config(state="disabled")

    # ─────────────────────────────────────────────
    #  EDITOR
    # ─────────────────────────────────────────────

    def _construir_editor(self, parent):
        frame_editor = ttk.Frame(parent)
        frame_editor.pack(expand=True, fill="both")

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
            state="disabled"  # deshabilitado hasta cargar procesador
        )
        self.editor.pack(expand=True, fill="both")
        scroll_v.config(command=self._scroll_ambos)

        scroll_h = ttk.Scrollbar(parent, orient="horizontal",
                                  command=self.editor.xview)
        scroll_h.pack(side="bottom", fill="x")
        self.editor.config(xscrollcommand=scroll_h.set)

        # Tags
        self.editor.tag_configure(
            "mnemonico", foreground="#0000cc",
            font=("Courier New", 11, "bold"))

        self.editor.bind("<KeyRelease>",    self._on_key_release)
        self.editor.bind("<ButtonRelease>", self._actualizar_statusbar)

    def _construir_consola(self):
        frame = ttk.LabelFrame(self.root, text="Consola")
        frame.pack(fill="x", padx=4, pady=(2, 4))

        self.consola = tk.Text(
            frame, height=5, font=("Courier New", 10),
            bg="#1e1e1e", fg="#d4d4d4", state="disabled",
            relief="flat", wrap="word"
        )
        self.consola.pack(fill="x", padx=4, pady=4)
        self.consola.tag_configure("error", foreground="#f44747")
        self.consola.tag_configure("ok",    foreground="#6a9955")
        self.consola.tag_configure("info",  foreground="#9cdcfe")

    def _construir_statusbar(self):
        self.statusbar = ttk.Label(
            self.root, text="Sin procesador",
            anchor="e", relief="sunken", padding=(4, 2)
        )
        self.statusbar.pack(side="bottom", fill="x")

    # ─────────────────────────────────────────────
    #  ESTADO: CON / SIN PROCESADOR
    # ─────────────────────────────────────────────

    def _set_estado_sin_procesador(self):
        """Deshabilita editor y menú Formato."""
        self.editor.config(state="disabled")
        self.menubar.entryconfig("Formato", state="disabled")
        self.statusbar.config(text="Sin procesador cargado")
        self.root.title("Ensamblatore")

    def _set_estado_con_procesador(self):
        """Habilita editor y menú Formato, puebla el panel info."""
        self.editor.config(state="normal")
        self.menubar.entryconfig("Formato", state="normal")
        self._poblar_panel_info()
        self._refrescar_mnemonicos()
        self._actualizar_titulo()
        self.statusbar.config(text=f"Procesador: {self.procesador.nombre}")
        self._log(f"✔  Procesador '{self.procesador.nombre}' cargado.", "ok")

    # ─────────────────────────────────────────────
    #  ACCIONES DE ARCHIVO
    # ─────────────────────────────────────────────

    def _nuevo_procesador(self):
        from services.CrearArquitectura import VentanaCrearArquitectura
        VentanaCrearArquitectura(self.root, controlador=self)

    def _cargar_procesador(self):
        archivo = filedialog.askopenfilename(
            title="Cargar procesador",
            filetypes=[("Archivos JSON", "*.json")]
        )
        if not archivo:
            return
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.procesador = Procesador.fromDict(data)
            self.procesador.ruta_archivo = archivo
            self._set_estado_con_procesador()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{e}")

    # ─────────────────────────────────────────────
    #  CALLBACKS DEL CONTROLADOR
    #  (usados por VentanaCrearArquitectura, etc.)
    # ─────────────────────────────────────────────

    def abrir_crear_formatos(self, procesador):
        self.procesador = procesador
        self._set_estado_con_procesador()
        self._abrir_formatos()

    def abrir_set_instrucciones(self, procesador):
        self.procesador = procesador
        self._set_estado_con_procesador()
        self._abrir_instrucciones()

    def abrir_ide(self, procesador=None):
        """Llamado al terminar el flujo de creación."""
        if procesador:
            self.procesador = procesador
        self._set_estado_con_procesador()

    # ─────────────────────────────────────────────
    #  ACCIONES DE FORMATO
    # ─────────────────────────────────────────────

    def _editar_arquitectura(self):
        from services.CrearArquitectura import VentanaCrearArquitectura
        VentanaCrearArquitectura(self.root, controlador=self,
                                 procesador_existente=self.procesador)

    def _abrir_formatos(self):
        from services.CrearFormatos import VentanaCrearFormatos
        v = VentanaCrearFormatos(self.root, controlador=self,
                                 procesador=self.procesador)
        self.root.wait_window(v.ventana)
        self._poblar_panel_info()

    def _abrir_instrucciones(self):
        from services.CrearSetInstrucciones import VentanaCrearSetInstrucciones
        v = VentanaCrearSetInstrucciones(self.root, controlador=self,
                                         procesador=self.procesador)
        self.root.wait_window(v.ventana)
        self._refrescar_mnemonicos()
        self._poblar_panel_info()
        self._poblar_tree_instrucciones()

    # ─────────────────────────────────────────────
    #  RESALTADO Y MNEMONICOS
    # ─────────────────────────────────────────────

    def _refrescar_mnemonicos(self):
        if not self.procesador:
            return
        self.mnemonicos = {
            inst.get("mnemonico", "").upper()
            for inst in self.procesador.set_de_instrucciones
            if inst.get("mnemonico")
        }
        self._resaltar_sintaxis()

    def _resaltar_sintaxis(self):
        self.editor.tag_remove("mnemonico", "1.0", tk.END)
        contenido = self.editor.get("1.0", tk.END)
        for n_linea, linea in enumerate(contenido.split("\n"), start=1):
            parte = linea.split(";")[0]
            for m in re.finditer(r"\b([A-Za-z_]\w*)\b", parte):
                if m.group(1).upper() in self.mnemonicos:
                    self.editor.tag_add("mnemonico",
                                        f"{n_linea}.{m.start()}",
                                        f"{n_linea}.{m.end()}")

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
        nombre = self.procesador.nombre if self.procesador else "Sin procesador"
        self.statusbar.config(text=f"{nombre}  |  Lín {linea}, Col {int(col)+1}")

    def _actualizar_titulo(self):
        nombre  = self.ruta_asm if self.ruta_asm else "Sin guardar"
        cambios = " •" if self._hay_cambios else ""
        proc    = self.procesador.nombre if self.procesador else "Ensamblatore"
        self.root.title(f"Ensamblatore — {proc}  |  {nombre}{cambios}")

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
        if not self.procesador:
            messagebox.showwarning("Sin procesador",
                                   "Carga un procesador antes de ensamblar.")
            return

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

        self._log(f"✔  Ensamblado exitoso — {len(binarios)} instrucción(es).", "ok")
        self._actualizar_tabla_simbolos(ensamblador.tabla_simbolos)

        direccion = self.procesador.mapeo_memoria
        paso      = self.procesador.aumento_pc
        for b in binarios:
            self._log(f"   0x{direccion:08X}  {b}  ({int(b,2):08X})", "info")
            direccion += paso

        self._guardar_salida(ensamblador)

    def _guardar_salida(self, ensamblador):
        dialogo = tk.Toplevel(self.root)
        dialogo.title("Guardar salida")
        dialogo.geometry("300x200")
        dialogo.transient(self.root)
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

    def _exportar(self, ensamblador, fmt):
        nombre_base = (os.path.splitext(os.path.basename(self.ruta_asm))[0]
                       if self.ruta_asm else self.procesador.nombre)
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
        nombre = self.procesador.nombre if self.procesador else "codigo"
        ruta = filedialog.asksaveasfilename(
            title="Guardar código ensamblador",
            defaultextension=".asm",
            initialfile=f"{nombre}.asm",
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
                self.root.destroy()
            elif r is False:
                self.root.destroy()
        else:
            self.root.destroy()
