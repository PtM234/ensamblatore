# src/services/VentanaIDE.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
import os
import json

from models.procesador import Procesador
from models.ensamblador import Ensamblador, ErrorDeEnsamblado


# ─────────────────────────────────────────────────────────────────────────────
#  Datos de una pestaña individual
# ─────────────────────────────────────────────────────────────────────────────

class TabData:
    def __init__(self):
        self.procesador  = None
        self.ruta_asm    = None
        self.hay_cambios = False
        self.mnemonicos  = set()

        # Widgets (asignados al construir la pestaña)
        self.editor       = None
        self.numeros      = None
        self.consola      = None
        self.txt_simbolos = None
        self.tree_inst    = None
        self.frame_info   = None
        self.canvas_info  = None
        self.lbl_sin_proc = None

    def titulo(self) -> str:
        proc = self.procesador.nombre if self.procesador else "Sin procesador"
        asm  = os.path.basename(self.ruta_asm) if self.ruta_asm else "Sin guardar"
        cambios = " •" if self.hay_cambios else ""
        return f"{proc}  —  {asm}{cambios}"


# ─────────────────────────────────────────────────────────────────────────────
#  IDE Principal
# ─────────────────────────────────────────────────────────────────────────────

class VentanaIDE:
    def __init__(self, root):
        self.root  = root
        self._tabs = []   # list[TabData]

        self.root.title("Ensamblatore")
        self.root.geometry("1280x760")
        self.root.protocol("WM_DELETE_WINDOW", self._confirmar_cierre)

        self._construir_menubar()
        self._construir_toolbar()
        self._construir_notebook()
        self._construir_statusbar()

        # Primera pestaña vacía
        self._nueva_pestana()

    # ─────────────────────────────────────────────
    #  MENUBAR
    # ─────────────────────────────────────────────

    def _construir_menubar(self):
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)

        # ── Archivo ──────────────────────────────────────────────────
        self._menu_archivo = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Archivo", menu=self._menu_archivo)

        self._menu_archivo.add_command(label="Nuevo procesador",
                                       command=self._nuevo_procesador)
        self._menu_archivo.add_command(label="Cargar procesador",
                                       command=self._cargar_procesador)
        self._menu_archivo.add_separator()
        self._menu_archivo.add_command(label="Nueva pestaña",
                                       command=self._nueva_pestana,
                                       accelerator="Ctrl+T")
        self._menu_archivo.add_command(label="Nuevo código",
                                       command=self.nuevo_codigo,
                                       accelerator="Ctrl+N",
                                       state="disabled")
        self._menu_archivo.add_command(label="Cerrar pestaña",
                                       command=self._cerrar_pestana_actual,
                                       accelerator="Ctrl+W")
        self._menu_archivo.add_separator()
        self._menu_archivo.add_command(label="Guardar .asm",
                                       command=self.guardar,
                                       accelerator="Ctrl+S")
        self._menu_archivo.add_command(label="Guardar .asm como…",
                                       command=self.guardar_como)
        self._menu_archivo.add_separator()
        self._menu_archivo.add_command(label="Ensamblar",
                                       command=self.ensamblar,
                                       accelerator="F5")

        # ── Formato ──────────────────────────────────────────────────
        self.menu_formato = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Formato", menu=self.menu_formato,
                                 state="disabled")

        self.menu_formato.add_command(label="Directivas del procesador",
                                      command=self._editar_arquitectura)
        self.menu_formato.add_command(label="Crear / Editar formatos de instrucción",
                                      command=self._abrir_formatos)
        self.menu_formato.add_command(label="Agregar / Editar instrucciones",
                                      command=self._abrir_instrucciones)

        # Atajos
        self.root.bind("<Control-t>", lambda e: self._nueva_pestana())
        self.root.bind("<Control-n>", lambda e: self.nuevo_codigo())
        self.root.bind("<Control-w>", lambda e: self._cerrar_pestana_actual())
        self.root.bind("<Control-s>", lambda e: self.guardar())
        self.root.bind("<F5>",        lambda e: self.ensamblar())

    # ─────────────────────────────────────────────
    #  TOOLBAR
    # ─────────────────────────────────────────────

    def _construir_toolbar(self):
        toolbar = ttk.Frame(self.root, relief="raised")
        toolbar.pack(side="top", fill="x", padx=2, pady=2)

        ttk.Button(toolbar, text="💾 Guardar",
                   command=self.guardar).pack(side="left", padx=4, pady=2)
        ttk.Button(toolbar, text="📂 Guardar como…",
                   command=self.guardar_como).pack(side="left", padx=4, pady=2)

        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=6)

        ttk.Button(toolbar, text="⚙️ Ensamblar",
                   command=self.ensamblar).pack(side="left", padx=4, pady=2)
        ttk.Button(toolbar, text="📋 Instrucciones",
                   command=self._abrir_instrucciones).pack(side="left", padx=4, pady=2)

        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=6)

        self.lbl_toolbar = ttk.Label(toolbar, text="")
        self.lbl_toolbar.pack(side="left", padx=8)

    # ─────────────────────────────────────────────
    #  NOTEBOOK
    # ─────────────────────────────────────────────

    def _construir_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=4, pady=(2, 0))
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_cambiado)
        self.notebook.bind("<Button-3>", self._menu_contextual_tab)

        # Pestaña especial "+" al final
        self._frame_mas = ttk.Frame(self.notebook)
        self.notebook.add(self._frame_mas, text="  +  ")

    def _construir_statusbar(self):
        self.statusbar = ttk.Label(
            self.root, text="Sin procesador",
            anchor="e", relief="sunken", padding=(4, 2)
        )
        self.statusbar.pack(side="bottom", fill="x")

    # ─────────────────────────────────────────────
    #  GESTIÓN DE PESTAÑAS
    # ─────────────────────────────────────────────

    def _nueva_pestana(self, procesador=None):
        """Crea una nueva pestaña vacía y la selecciona."""
        tab = TabData()
        tab.procesador = procesador

        # Frame raíz de la pestaña
        frame_raiz = ttk.Frame(self.notebook)

        # PanedWindow horizontal: panel info | editor
        paned = ttk.PanedWindow(frame_raiz, orient="horizontal")
        paned.pack(expand=True, fill="both")

        # Panel izquierdo de info
        frame_izq = ttk.Frame(paned, width=270)
        paned.add(frame_izq, weight=0)
        self._construir_panel_info_tab(frame_izq, tab)

        # Panel derecho: editor
        frame_der = ttk.Frame(paned)
        paned.add(frame_der, weight=1)
        self._construir_editor_tab(frame_der, tab)

        # Consola
        self._construir_consola_tab(frame_raiz, tab)

        self._tabs.append(tab)
        titulo = tab.titulo()
        # Insertar antes de la pestaña "+"
        try:
            idx_mas = self.notebook.index(self._frame_mas)
            self.notebook.insert(idx_mas, frame_raiz, text=f"  {titulo}  ")
        except Exception:
            self.notebook.add(frame_raiz, text=f"  {titulo}  ")
        self.notebook.select(frame_raiz)

        if procesador:
            self._aplicar_procesador_a_tab(tab)

        return tab

    def _tab_actual(self) -> TabData | None:
        """Devuelve el TabData de la pestaña activa (nunca la pestaña "+")."""
        try:
            idx     = self.notebook.index("current")
            idx_mas = self.notebook.index(self._frame_mas)
            if idx == idx_mas:
                return None
            return self._tabs[idx]
        except Exception:
            return None

    def _idx_actual(self) -> int:
        try:
            idx     = self.notebook.index("current")
            idx_mas = self.notebook.index(self._frame_mas)
            if idx == idx_mas:
                return max(0, len(self._tabs) - 1)
            return idx
        except Exception:
            return 0

    def _actualizar_titulo_tab(self, tab: TabData):
        try:
            idx = self._tabs.index(tab)
            self.notebook.tab(idx, text=f"  {tab.titulo()}  ")
        except (ValueError, tk.TclError):
            pass

    def _on_tab_cambiado(self, event=None):
        """Actualiza toolbar, menús y statusbar al cambiar de pestaña.
        Si se seleccionó la pestaña "+", crea una nueva pestaña real."""
        try:
            idx_actual = self.notebook.index("current")
            # El índice de la pestaña "+" siempre es el último
            idx_mas = self.notebook.index(self._frame_mas)
        except Exception:
            return

        if idx_actual == idx_mas:
            # Seleccionaron "+": crear nueva pestaña y volver a ella
            self._nueva_pestana()
            return

        tab = self._tab_actual()
        if not tab:
            return
        if tab.procesador:
            self._actualizar_ui_con_procesador(tab)
        else:
            self._actualizar_ui_sin_procesador()
        self._actualizar_statusbar(tab)

    def _cerrar_pestana_actual(self):
        if len(self._tabs) <= 1:
            messagebox.showinfo("Información",
                                "No puedes cerrar la última pestaña.")
            return
        tab = self._tab_actual()
        if tab and tab.hay_cambios:
            r = messagebox.askyesnocancel(
                "Cambios sin guardar",
                "Esta pestaña tiene cambios sin guardar.\n¿Deseas guardar antes de cerrar?"
            )
            if r is True:
                self.guardar()
            elif r is None:
                return
        idx = self._idx_actual()
        self.notebook.forget(idx)
        self._tabs.pop(idx)

    def _menu_contextual_tab(self, event):
        """Menú al hacer clic derecho sobre una pestaña."""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Cerrar pestaña",
                         command=self._cerrar_pestana_actual)
        menu.tk_popup(event.x_root, event.y_root)

    # ─────────────────────────────────────────────
    #  PANEL DE INFO (por pestaña)
    # ─────────────────────────────────────────────

    def _construir_panel_info_tab(self, parent, tab: TabData):
        parent.pack_propagate(False)

        canvas    = tk.Canvas(parent, borderwidth=0, highlightthickness=0, bg="#f7f7f7")
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        tab.frame_info  = ttk.Frame(canvas)
        tab.canvas_info = canvas
        cw = canvas.create_window((0, 0), window=tab.frame_info, anchor="nw")

        tab.frame_info.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw, width=e.width))

        # Mensaje inicial sin procesador
        tab.lbl_sin_proc = ttk.Label(
            tab.frame_info,
            text="Sin procesador.\n\nUsa Archivo → Nuevo procesador\no Archivo → Cargar procesador.",
            foreground="gray", justify="center", wraplength=220
        )
        tab.lbl_sin_proc.pack(pady=30, padx=10)

    def _poblar_panel_info_tab(self, tab: TabData):
        """Reconstruye el panel de info con el procesador de la pestaña."""
        for w in tab.frame_info.winfo_children():
            w.destroy()

        p = tab.procesador

        self._segmento(tab.frame_info, "⚙️ Configuración", [
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
        self._segmento(tab.frame_info, "📐 Formatos", lineas_fmt)

        self._segmento_instrucciones_tab(tab.frame_info, tab)
        self._segmento_simbolos_tab(tab.frame_info, tab)

    def _segmento(self, parent, titulo, lineas):
        ttk.Label(parent, text=titulo, font=("Arial", 9, "bold"),
                  background="#dde3ec").pack(fill="x", padx=4, pady=(6, 0))
        frame = ttk.Frame(parent)
        frame.pack(fill="x", padx=4, pady=(0, 4))
        sb  = ttk.Scrollbar(frame, orient="vertical")
        txt = tk.Text(frame,
                      height=min(len([l for l in lineas if l]) + 1, 10),
                      font=("Courier New", 9), bg="#f7f7f7", fg="#222222",
                      relief="flat", wrap="none", state="normal",
                      yscrollcommand=sb.set)
        sb.config(command=txt.yview)
        sb.pack(side="right", fill="y")
        txt.pack(side="left", fill="x", expand=True)
        for linea in lineas:
            txt.insert(tk.END, linea + "\n")
        txt.config(state="disabled")

    def _segmento_instrucciones_tab(self, parent, tab: TabData):
        ttk.Label(parent, text="📜 Instrucciones",
                  font=("Arial", 9, "bold"),
                  background="#dde3ec").pack(fill="x", padx=4, pady=(6, 0))
        frame = ttk.Frame(parent)
        frame.pack(fill="x", padx=4, pady=(0, 4))

        sb_v = ttk.Scrollbar(frame, orient="vertical")
        sb_h = ttk.Scrollbar(frame, orient="horizontal")

        tab.tree_inst = ttk.Treeview(frame, selectmode="browse",
                                      show="tree headings",
                                      yscrollcommand=sb_v.set,
                                      xscrollcommand=sb_h.set, height=10)
        tab.tree_inst["columns"] = ("opcode", "mapeo")
        tab.tree_inst.heading("#0",     text="Instrucción")
        tab.tree_inst.heading("opcode", text="Opcode")
        tab.tree_inst.heading("mapeo",  text="Sintaxis")
        tab.tree_inst.column("#0",     width=90,  minwidth=70)
        tab.tree_inst.column("opcode", width=80,  minwidth=60)
        tab.tree_inst.column("mapeo",  width=100, minwidth=70)
        tab.tree_inst.tag_configure("grupo", font=("Arial", 9, "bold"),
                                     foreground="#2c5f9e")
        tab.tree_inst.tag_configure("instr", font=("Courier New", 9))

        sb_v.config(command=tab.tree_inst.yview)
        sb_h.config(command=tab.tree_inst.xview)
        sb_v.pack(side="right",  fill="y")
        sb_h.pack(side="bottom", fill="x")
        tab.tree_inst.pack(fill="both", expand=True)
        tab.tree_inst.bind("<Button-1>", lambda e: tab.tree_inst.focus_set())

        self._poblar_tree_instrucciones_tab(tab)

    def _poblar_tree_instrucciones_tab(self, tab: TabData):
        if not tab.tree_inst or not tab.procesador:
            return
        tab.tree_inst.delete(*tab.tree_inst.get_children())
        grupos = {}
        for inst in tab.procesador.set_de_instrucciones:
            fmt = inst.get("formato", "Sin formato")
            grupos.setdefault(fmt, []).append(inst)
        for fmt_nombre, instrucciones in grupos.items():
            gid = tab.tree_inst.insert("", "end",
                                        text=f"  {fmt_nombre}  ({len(instrucciones)})",
                                        tags=("grupo",), open=True)
            for inst in instrucciones:
                tab.tree_inst.insert(gid, "end",
                                      text=f"  {inst.get('mnemonico','?')}",
                                      values=(inst.get("opcode","?"),
                                              inst.get("mapeo_operandos","")),
                                      tags=("instr",))

    def _segmento_simbolos_tab(self, parent, tab: TabData):
        ttk.Label(parent, text="🏷️ Tabla de símbolos",
                  font=("Arial", 9, "bold"),
                  background="#dde3ec").pack(fill="x", padx=4, pady=(6, 0))
        frame = ttk.Frame(parent)
        frame.pack(fill="x", padx=4, pady=(0, 4))
        sb = ttk.Scrollbar(frame, orient="vertical")
        tab.txt_simbolos = tk.Text(frame, height=6, font=("Courier New", 9),
                                    bg="#f7f7f7", fg="#222222", relief="flat",
                                    wrap="none", state="normal",
                                    yscrollcommand=sb.set)
        sb.config(command=tab.txt_simbolos.yview)
        sb.pack(side="right", fill="y")
        tab.txt_simbolos.pack(side="left", fill="x", expand=True)
        tab.txt_simbolos.insert(tk.END, "(vacío — ensambla para ver etiquetas)")
        tab.txt_simbolos.config(state="disabled")

    def _actualizar_tabla_simbolos_tab(self, tab: TabData, tabla: dict):
        if not tab.txt_simbolos:
            return
        tab.txt_simbolos.config(state="normal")
        tab.txt_simbolos.delete("1.0", tk.END)
        if tabla:
            for nombre, dir_ in sorted(tabla.items()):
                tab.txt_simbolos.insert(tk.END, f"{nombre.ljust(12)} 0x{dir_:08X}\n")
        else:
            tab.txt_simbolos.insert(tk.END, "(sin etiquetas)")
        tab.txt_simbolos.config(state="disabled")

    # ─────────────────────────────────────────────
    #  EDITOR (por pestaña)
    # ─────────────────────────────────────────────

    def _construir_editor_tab(self, parent, tab: TabData):
        tab.numeros = tk.Text(parent, width=4, padx=6, state="disabled",
                               bg="#f0f0f0", fg="#888888", font=("Courier New", 11),
                               relief="flat", cursor="arrow",
                               selectbackground="#f0f0f0")
        tab.numeros.pack(side="left", fill="y")

        scroll_v = ttk.Scrollbar(parent, orient="vertical")
        scroll_v.pack(side="right", fill="y")

        tab.editor = tk.Text(parent, undo=True, wrap="none",
                              font=("Courier New", 11), bg="#ffffff", fg="#000000",
                              insertbackground="#000000", selectbackground="#cce5ff",
                              relief="flat", state="disabled",
                              yscrollcommand=lambda *a: self._scroll_sincronizado(tab, *a))
        tab.editor.pack(expand=True, fill="both")
        scroll_v.config(command=lambda *a: self._scroll_ambos(tab, *a))

        tab.editor.tag_configure("mnemonico", foreground="#0000cc",
                                  font=("Courier New", 11, "bold"))

        tab.editor.bind("<KeyRelease>",
                         lambda e, t=tab: self._on_key_release(t))
        tab.editor.bind("<ButtonRelease>",
                         lambda e, t=tab: self._actualizar_statusbar(t))

    def _construir_consola_tab(self, parent, tab: TabData):
        frame = ttk.LabelFrame(parent, text="Consola")
        frame.pack(fill="x", padx=4, pady=(2, 4))
        tab.consola = tk.Text(frame, height=4, font=("Courier New", 10),
                               bg="#1e1e1e", fg="#d4d4d4", state="disabled",
                               relief="flat", wrap="word")
        tab.consola.pack(fill="x", padx=4, pady=4)
        tab.consola.tag_configure("error", foreground="#f44747")
        tab.consola.tag_configure("ok",    foreground="#6a9955")
        tab.consola.tag_configure("info",  foreground="#9cdcfe")

    # ─────────────────────────────────────────────
    #  SCROLL (por pestaña)
    # ─────────────────────────────────────────────

    def _scroll_sincronizado(self, tab: TabData, *args):
        if tab.numeros:
            tab.numeros.yview_moveto(args[0])

    def _scroll_ambos(self, tab: TabData, *args):
        if tab.editor:
            tab.editor.yview(*args)
        if tab.numeros:
            tab.numeros.yview(*args)

    # ─────────────────────────────────────────────
    #  EVENTOS DE EDITOR
    # ─────────────────────────────────────────────

    def _on_key_release(self, tab: TabData):
        tab.hay_cambios = True
        self._actualizar_numeros(tab)
        self._resaltar_sintaxis(tab)
        self._actualizar_statusbar(tab)
        self._actualizar_titulo_tab(tab)

    def _actualizar_numeros(self, tab: TabData):
        if not tab.numeros or not tab.editor:
            return
        tab.numeros.config(state="normal")
        tab.numeros.delete("1.0", tk.END)
        total = int(tab.editor.index(tk.END).split(".")[0])
        tab.numeros.insert("1.0", "\n".join(str(i) for i in range(1, total)))
        tab.numeros.config(state="disabled")

    def _resaltar_sintaxis(self, tab: TabData):
        if not tab.editor:
            return
        tab.editor.tag_remove("mnemonico", "1.0", tk.END)
        contenido = tab.editor.get("1.0", tk.END)
        for n_linea, linea in enumerate(contenido.split("\n"), start=1):
            parte = linea.split(";")[0]
            for m in re.finditer(r"\b([A-Za-z_]\w*)\b", parte):
                if m.group(1).upper() in tab.mnemonicos:
                    tab.editor.tag_add("mnemonico",
                                        f"{n_linea}.{m.start()}",
                                        f"{n_linea}.{m.end()}")

    def _actualizar_statusbar(self, tab: TabData = None):
        if tab is None:
            tab = self._tab_actual()
        if not tab or not tab.editor:
            return
        try:
            pos   = tab.editor.index(tk.INSERT)
            linea, col = pos.split(".")
            proc  = tab.procesador.nombre if tab.procesador else "Sin procesador"
            self.statusbar.config(text=f"{proc}  |  Lín {linea}, Col {int(col)+1}")
        except Exception:
            pass

    # ─────────────────────────────────────────────
    #  CONSOLA (por pestaña)
    # ─────────────────────────────────────────────

    def _log(self, tab: TabData, texto: str, tag: str = "info"):
        if not tab.consola:
            return
        tab.consola.config(state="normal")
        tab.consola.insert(tk.END, texto + "\n", tag)
        tab.consola.see(tk.END)
        tab.consola.config(state="disabled")

    def _limpiar_consola(self, tab: TabData):
        if not tab.consola:
            return
        tab.consola.config(state="normal")
        tab.consola.delete("1.0", tk.END)
        tab.consola.config(state="disabled")

    # ─────────────────────────────────────────────
    #  ESTADO CON / SIN PROCESADOR
    # ─────────────────────────────────────────────

    def _aplicar_procesador_a_tab(self, tab: TabData):
        """Habilita el editor, puebla el panel info y actualiza menús."""
        tab.mnemonicos = {
            inst.get("mnemonico", "").upper()
            for inst in tab.procesador.set_de_instrucciones
            if inst.get("mnemonico")
        }
        if tab.editor:
            tab.editor.config(state="normal")
        self._poblar_panel_info_tab(tab)
        self._actualizar_titulo_tab(tab)
        self._actualizar_ui_con_procesador(tab)

    def _actualizar_ui_con_procesador(self, tab: TabData):
        self.menubar.entryconfig("Formato", state="normal")
        self._menu_archivo.entryconfig("Nuevo código", state="normal")
        proc = tab.procesador.nombre if tab.procesador else ""
        n    = len(tab.procesador.set_de_instrucciones) if tab.procesador else 0
        self.lbl_toolbar.config(
            text=f"Procesador: {proc}  |  Instrucciones: {n}")

    def _actualizar_ui_sin_procesador(self):
        self.menubar.entryconfig("Formato", state="disabled")
        self._menu_archivo.entryconfig("Nuevo código", state="disabled")
        self.lbl_toolbar.config(text="")

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
            procesador = Procesador.fromDict(data)
            procesador.ruta_archivo = archivo

            tab = self._tab_actual()
            if tab and tab.procesador is None and (
                    not tab.editor or not tab.editor.get("1.0", tk.END).strip()):
                # Pestaña vacía — reutilizarla
                tab.procesador = procesador
                self._aplicar_procesador_a_tab(tab)
            else:
                # Crear nueva pestaña
                self._nueva_pestana(procesador=procesador)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{e}")

    def nuevo_codigo(self):
        """Limpia el editor de la pestaña actual."""
        tab = self._tab_actual()
        if not tab:
            return
        if tab.hay_cambios:
            r = messagebox.askyesnocancel(
                "Cambios sin guardar",
                "Tienes cambios sin guardar.\n¿Deseas guardar antes?"
            )
            if r is True:
                self.guardar()
            elif r is None:
                return
        if tab.editor:
            tab.editor.delete("1.0", tk.END)
        tab.ruta_asm    = None
        tab.hay_cambios = False
        self._actualizar_titulo_tab(tab)
        self._limpiar_consola(tab)

    # Callbacks para CrearArquitectura / CrearFormatos
    def abrir_crear_formatos(self, procesador):
        tab = self._tab_actual()
        if tab:
            tab.procesador = procesador
            self._aplicar_procesador_a_tab(tab)
        from services.CrearFormatos import VentanaCrearFormatos
        v = VentanaCrearFormatos(self.root, controlador=self,
                                  procesador=procesador, mostrar_siguiente=True)
        self.root.wait_window(v.ventana)
        if tab:
            self._poblar_panel_info_tab(tab)

    def abrir_set_instrucciones(self, procesador):
        tab = self._tab_actual()
        if tab:
            tab.procesador = procesador
            self._aplicar_procesador_a_tab(tab)
        from services.CrearSetInstrucciones import VentanaCrearSetInstrucciones
        v = VentanaCrearSetInstrucciones(self.root, controlador=self,
                                          procesador=procesador)
        self.root.wait_window(v.ventana)
        if tab:
            self._poblar_panel_info_tab(tab)

    def abrir_ide(self, procesador=None):
        tab = self._tab_actual()
        if procesador and tab:
            tab.procesador = procesador
            self._aplicar_procesador_a_tab(tab)

    # ─────────────────────────────────────────────
    #  ACCIONES DE FORMATO
    # ─────────────────────────────────────────────

    def _editar_arquitectura(self):
        tab = self._tab_actual()
        if not tab or not tab.procesador:
            return
        from services.CrearArquitectura import VentanaCrearArquitectura
        VentanaCrearArquitectura(self.root, controlador=self,
                                  procesador_existente=tab.procesador)

    def _abrir_formatos(self):
        tab = self._tab_actual()
        if not tab or not tab.procesador:
            return
        from services.CrearFormatos import VentanaCrearFormatos
        v = VentanaCrearFormatos(self.root, controlador=self,
                                  procesador=tab.procesador,
                                  mostrar_siguiente=False)
        self.root.wait_window(v.ventana)
        self._poblar_panel_info_tab(tab)

    def _abrir_instrucciones(self):
        tab = self._tab_actual()
        if not tab or not tab.procesador:
            return
        from services.CrearSetInstrucciones import VentanaCrearSetInstrucciones
        v = VentanaCrearSetInstrucciones(self.root, controlador=self,
                                          procesador=tab.procesador)
        self.root.wait_window(v.ventana)
        tab.mnemonicos = {
            inst.get("mnemonico", "").upper()
            for inst in tab.procesador.set_de_instrucciones
            if inst.get("mnemonico")
        }
        self._resaltar_sintaxis(tab)
        self._poblar_panel_info_tab(tab)

    # ─────────────────────────────────────────────
    #  ENSAMBLAR
    # ─────────────────────────────────────────────

    def ensamblar(self):
        tab = self._tab_actual()
        if not tab:
            return
        if not tab.procesador:
            messagebox.showwarning("Sin procesador",
                                   "Carga un procesador antes de ensamblar.")
            return
        self._limpiar_consola(tab)
        codigo = tab.editor.get("1.0", tk.END).strip() if tab.editor else ""
        if not codigo:
            self._log(tab, "⚠  El editor está vacío.", "error")
            return

        ensamblador = Ensamblador(tab.procesador)
        try:
            binarios = ensamblador.ensamblar(codigo)
        except ErrorDeEnsamblado as e:
            self._log(tab, f"✗  Error: {e}", "error")
            return
        except Exception as e:
            self._log(tab, f"✗  Error inesperado: {e}", "error")
            return

        self._log(tab, f"✔  Ensamblado exitoso — {len(binarios)} instrucción(es).", "ok")
        self._actualizar_tabla_simbolos_tab(tab, ensamblador.tabla_simbolos)

        direccion = tab.procesador.mapeo_memoria
        paso      = tab.procesador.aumento_pc
        for b in binarios:
            self._log(tab, f"   0x{direccion:08X}  {b}  ({int(b,2):08X})", "info")
            direccion += paso

        self._guardar_salida(tab, ensamblador)

    def _guardar_salida(self, tab: TabData, ensamblador: Ensamblador):
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
            self._exportar(tab, ensamblador, fmt)

        ttk.Button(dialogo, text="Guardar…", command=confirmar).pack(pady=15)

    def _exportar(self, tab: TabData, ensamblador: Ensamblador, fmt: str):
        nombre_base = (os.path.splitext(os.path.basename(tab.ruta_asm))[0]
                       if tab.ruta_asm else tab.procesador.nombre)
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
            self._log(tab, f"✔  Guardado en: {ruta}", "ok")
        except Exception as e:
            self._log(tab, f"✗  Error al guardar: {e}", "error")

    # ─────────────────────────────────────────────
    #  GUARDAR .ASM
    # ─────────────────────────────────────────────

    def guardar(self):
        tab = self._tab_actual()
        if not tab:
            return
        if tab.ruta_asm:
            self._escribir_archivo(tab, tab.ruta_asm)
        else:
            self.guardar_como()

    def guardar_como(self):
        tab = self._tab_actual()
        if not tab:
            return
        nombre = tab.procesador.nombre if tab.procesador else "codigo"
        ruta = filedialog.asksaveasfilename(
            title="Guardar código ensamblador",
            defaultextension=".asm",
            initialfile=f"{nombre}.asm",
            filetypes=[("Archivos ensamblador", "*.asm"),
                       ("Archivos de texto", "*.txt"), ("Todos", "*.*")]
        )
        if ruta:
            tab.ruta_asm = ruta
            self._escribir_archivo(tab, ruta)

    def _escribir_archivo(self, tab: TabData, ruta: str):
        try:
            contenido = tab.editor.get("1.0", tk.END) if tab.editor else ""
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(contenido)
            tab.hay_cambios = False
            self._actualizar_titulo_tab(tab)
        except Exception as e:
            messagebox.showerror("Error al guardar", f"No se pudo guardar:\n{e}")

    # ─────────────────────────────────────────────
    #  CIERRE SEGURO
    # ─────────────────────────────────────────────

    def _confirmar_cierre(self):
        pestanas_con_cambios = [t for t in self._tabs if t.hay_cambios]
        if pestanas_con_cambios:
            r = messagebox.askyesnocancel(
                "Cambios sin guardar",
                f"Hay {len(pestanas_con_cambios)} pestaña(s) con cambios sin guardar.\n"
                "¿Deseas guardar todo antes de cerrar?"
            )
            if r is True:
                for tab in pestanas_con_cambios:
                    if tab.ruta_asm:
                        self._escribir_archivo(tab, tab.ruta_asm)
                    else:
                        self.guardar_como()
            elif r is None:
                return
        self.root.destroy()