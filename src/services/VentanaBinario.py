# src/services/VentanaBinario.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


class VentanaBinario:
    """
    Ventana de visualización del resultado del ensamblado.
    Pestaña 1: Tabla  — Dirección | Binario | Hex | Instrucción fuente
    Pestaña 2: Hex    — Vista estilo editor hexadecimal
    """

    def __init__(self, parent, procesador, binarios: list, fuentes: list):
        """
        binarios : list[str]  — lista de cadenas de 32 bits
        fuentes  : list[str]  — lista de instrucciones originales (mismo orden)
        """
        self.procesador = procesador
        self.binarios   = binarios
        self.fuentes    = fuentes

        self.ventana = tk.Toplevel(parent)
        self.ventana.title(f"Resultado — {procesador.nombre}")
        self.ventana.geometry("860x520")
        self.ventana.transient(parent)

        self._construir_interfaz()

    # ─────────────────────────────────────────────
    #  CONSTRUCCIÓN
    # ─────────────────────────────────────────────

    def _construir_interfaz(self):
        # Toolbar superior
        toolbar = ttk.Frame(self.ventana)
        toolbar.pack(fill="x", padx=6, pady=(6, 0))

        ttk.Label(toolbar,
                  text=f"{len(self.binarios)} instrucción(es)  |  "
                       f"{len(self.binarios) * 4} bytes",
                  font=("Arial", 10)).pack(side="left")

        ttk.Button(toolbar, text="Exportar...",
                   command=self._exportar).pack(side="right", padx=4)
        ttk.Button(toolbar, text="Copiar hex",
                   command=self._copiar_hex).pack(side="right", padx=4)
        ttk.Button(toolbar, text="Copiar tabla",
                   command=self._copiar_tabla).pack(side="right", padx=4)

        # Notebook con dos vistas
        nb = ttk.Notebook(self.ventana)
        nb.pack(expand=True, fill="both", padx=6, pady=6)

        frame_tabla = ttk.Frame(nb)
        frame_hex   = ttk.Frame(nb)

        nb.add(frame_tabla, text="  Tabla  ")
        nb.add(frame_hex,   text="  Hexadecimal  ")

        self._construir_tabla(frame_tabla)
        self._construir_hex(frame_hex)

    # ─────────────────────────────────────────────
    #  PESTAÑA 1 — TABLA
    # ─────────────────────────────────────────────

    def _construir_tabla(self, parent):
        cols = ("dir", "binario", "hex", "fuente")
        tree = ttk.Treeview(parent, columns=cols, show="headings",
                             selectmode="browse")

        tree.heading("dir",     text="Dirección")
        tree.heading("binario", text="Binario (32 bits)")
        tree.heading("hex",     text="Hex")
        tree.heading("fuente",  text="Instrucción fuente")

        tree.column("dir",     width=100, anchor="center", minwidth=80)
        tree.column("binario", width=260, anchor="center", minwidth=220)
        tree.column("hex",     width=90,  anchor="center", minwidth=70)
        tree.column("fuente",  width=260, anchor="w",      minwidth=150)

        # Scrollbars
        sb_v = ttk.Scrollbar(parent, orient="vertical",   command=tree.yview)
        sb_h = ttk.Scrollbar(parent, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=sb_v.set, xscrollcommand=sb_h.set)

        sb_v.pack(side="right",  fill="y")
        sb_h.pack(side="bottom", fill="x")
        tree.pack(expand=True, fill="both")

        tree.tag_configure("par",   background="#f7f7f7")
        tree.tag_configure("impar", background="#ffffff")

        direccion = self.procesador.mapeo_memoria
        paso      = self.procesador.aumento_pc
        es_little = "little" in self.procesador.endianess.lower()

        for i, (b, fuente) in enumerate(zip(self.binarios, self.fuentes)):
            val = int(b, 2)
            hex_val  = f"{val:08X}"
            # Binario con espacios cada 4 bits para legibilidad
            bin_fmt  = " ".join(b[j:j+4] for j in range(0, 32, 4))
            dir_str  = f"0x{direccion:08X}"
            tag      = "par" if i % 2 == 0 else "impar"
            tree.insert("", "end",
                        values=(dir_str, bin_fmt, hex_val, fuente.strip()),
                        tags=(tag,))
            direccion += paso

    # ─────────────────────────────────────────────
    #  PESTAÑA 2 — HEX
    # ─────────────────────────────────────────────

    def _construir_hex(self, parent):
        """
        Vista estilo editor hexadecimal.
        Columnas: Offset | 00 01 02 03 ... 0F | ASCII
        Agrupa los bytes de todas las instrucciones de 4 en 4 por fila (16 bytes/fila).
        """
        # Construir array de bytes en el orden de endianness
        es_little = "little" in self.procesador.endianess.lower()
        todos_bytes = []
        for b in self.binarios:
            val = int(b, 2)
            todos_bytes += list(val.to_bytes(4, byteorder="little" if es_little else "big"))

        # Text widget con fuente monoespaciada
        frame = ttk.Frame(parent)
        frame.pack(expand=True, fill="both")

        sb_v = ttk.Scrollbar(frame, orient="vertical")
        sb_h = ttk.Scrollbar(frame, orient="horizontal")

        txt = tk.Text(frame, font=("Courier New", 11),
                      bg="#1e1e1e", fg="#d4d4d4",
                      state="normal", wrap="none",
                      yscrollcommand=sb_v.set,
                      xscrollcommand=sb_h.set)

        sb_v.config(command=txt.yview)
        sb_h.config(command=txt.xview)
        sb_v.pack(side="right",  fill="y")
        sb_h.pack(side="bottom", fill="x")
        txt.pack(expand=True, fill="both")

        # Tags de color
        txt.tag_configure("offset", foreground="#569cd6")
        txt.tag_configure("hex",    foreground="#9cdcfe")
        txt.tag_configure("sep",    foreground="#555555")
        txt.tag_configure("ascii",  foreground="#ce9178")
        txt.tag_configure("header", foreground="#6a9955")

        # Cabecera
        header_offset = "Offset   "
        header_hex    = " ".join(f"{i:02X}" for i in range(16))
        header_ascii  = "  ASCII"
        txt.insert(tk.END, header_offset, "header")
        txt.insert(tk.END, header_hex,    "header")
        txt.insert(tk.END, header_ascii + "\n", "header")
        txt.insert(tk.END, "─" * 70 + "\n", "sep")

        # Filas de 16 bytes
        bytes_por_fila = 16
        base = self.procesador.mapeo_memoria

        for row in range(0, len(todos_bytes), bytes_por_fila):
            chunk = todos_bytes[row:row + bytes_por_fila]
            offset_str = f"{base + row:08X}  "
            hex_str    = " ".join(f"{b:02X}" for b in chunk)
            # Rellenar si la fila está incompleta
            hex_str   += "   " * (bytes_por_fila - len(chunk))
            ascii_str  = "  " + "".join(
                chr(b) if 32 <= b < 127 else "." for b in chunk
            )

            txt.insert(tk.END, offset_str, "offset")
            txt.insert(tk.END, hex_str,    "hex")
            txt.insert(tk.END, ascii_str + "\n", "ascii")

        txt.config(state="disabled")

    # ─────────────────────────────────────────────
    #  EXPORTAR
    # ─────────────────────────────────────────────

    def _exportar(self):
        """Exporta el contenido visible (tabla) a un archivo .txt."""
        ruta = filedialog.asksaveasfilename(
            title="Exportar resultado",
            defaultextension=".txt",
            initialfile=f"{self.procesador.nombre}_resultado.txt",
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")]
        )
        if not ruta:
            return
        direccion = self.procesador.mapeo_memoria
        paso      = self.procesador.aumento_pc
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(f"{'Dirección':<14} {'Binario':<35} {'Hex':<10} Instrucción\n")
            f.write("─" * 80 + "\n")
            for b, fuente in zip(self.binarios, self.fuentes):
                val     = int(b, 2)
                bin_fmt = " ".join(b[j:j+4] for j in range(0, 32, 4))
                f.write(f"0x{direccion:08X}    {bin_fmt}  {val:08X}  {fuente.strip()}\n")
                direccion += paso
    # ─────────────────────────────────────────────
    #  COPIAR
    # ─────────────────────────────────────────────

    def _copiar_al_portapapeles(self, texto):
        self.ventana.clipboard_clear()
        self.ventana.clipboard_append(texto)
        self.ventana.update()  # mantiene el portapapeles tras cerrar

    def _copiar_tabla(self):
        """Copia la tabla completa (dirección, binario, hex, fuente) como texto."""
        direccion = self.procesador.mapeo_memoria
        paso      = self.procesador.aumento_pc
        lineas = [f"{'Direccion':<12}\t{'Binario':<35}\t{'Hex':<8}\tInstruccion"]
        for b, fuente in zip(self.binarios, self.fuentes):
            val     = int(b, 2)
            bin_fmt = " ".join(b[j:j+4] for j in range(0, 32, 4))
            lineas.append(f"0x{direccion:08X}\t{bin_fmt}\t{val:08X}\t{fuente.strip()}")
            direccion += paso
        self._copiar_al_portapapeles("\n".join(lineas))
        messagebox.showinfo("Copiado", "Tabla copiada al portapapeles.")

    def _copiar_hex(self):
        """Copia solo los valores hexadecimales, uno por línea."""
        hex_vals = [f"{int(b, 2):08X}" for b in self.binarios]
        self._copiar_al_portapapeles("\n".join(hex_vals))
        messagebox.showinfo("Copiado", "Valores hex copiados al portapapeles.")
