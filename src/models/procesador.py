# src/models/procesador.py
import json


class Procesador:
    def __init__(self, nombre, tamano_palabra, distribucion_memorias, profundidad, ancho,
                 tamano_minimo_direccionable, mapeo_memoria, aumento_pc, endianess,
                 prefijo_registro="x", num_registros=32, alias_registros=None,
                 comentarios=None,
                 formato_de_sintaxis=None, set_de_instrucciones=None, codigo=None):
        self.nombre = nombre
        self.tamano_palabra = tamano_palabra
        self.distribucion_memorias = distribucion_memorias
        self.profundidad = profundidad
        self.ancho = ancho
        self.tamano_minimo_direccionable = tamano_minimo_direccionable
        self.mapeo_memoria = mapeo_memoria
        self.aumento_pc = aumento_pc
        self.endianess = endianess
        self.prefijo_registro = prefijo_registro   # ej. "x", "r", "reg"
        self.num_registros = num_registros         # ej. 32

        # Alias de registros definidos por el usuario: { "sp": "x2", "zero": "x0", ... }
        self.alias_registros = alias_registros if alias_registros is not None else {}

        # Configuración de comentarios:
        #   "linea":  lista de marcadores de comentario de línea (ej. [";", "//", "#"])
        #   "bloque": lista de pares [apertura, cierre]  (ej. [["/*", "*/"], ["(*", "*)"]])
        if comentarios is not None:
            self.comentarios = comentarios
        else:
            self.comentarios = {"linea": [";"], "bloque": []}

        self.formato_de_sintaxis    = formato_de_sintaxis    if formato_de_sintaxis    is not None else []
        self.set_de_instrucciones   = set_de_instrucciones   if set_de_instrucciones   is not None else []
        self.codigo                 = codigo                 if codigo                 is not None else []

        # Ruta donde se guardó el archivo (no se serializa al JSON)
        self.ruta_archivo = None

    def agregarFormatoDeSintaxis(self, formato_de_sintaxis):
        self.formato_de_sintaxis = formato_de_sintaxis

    def agregarSetDeInstrucciones(self, set_de_instrucciones):
        self.set_de_instrucciones = set_de_instrucciones

    def agregarCodigo(self, codigo):
        self.codigo = codigo

    def toDict(self):
        return {
            "nombre":                       self.nombre,
            "tamano_palabra":               self.tamano_palabra,
            "distribucion_memorias":        self.distribucion_memorias,
            "profundidad":                  self.profundidad,
            "ancho":                        self.ancho,
            "tamano_minimo_direccionable":  self.tamano_minimo_direccionable,
            "mapeo_memoria":                self.mapeo_memoria,
            "aumento_pc":                   self.aumento_pc,
            "endianess":                    self.endianess,
            "prefijo_registro":             self.prefijo_registro,
            "num_registros":                self.num_registros,
            "alias_registros":              self.alias_registros,
            "comentarios":                  self.comentarios,
            "formato_de_sintaxis":          self.formato_de_sintaxis,
            "set_de_instrucciones": [
                i.toDict() if hasattr(i, 'toDict') else i
                for i in self.set_de_instrucciones
            ],
            "codigo": self.codigo
        }

    def guardarEnJSON(self, ruta="procesador.json"):
        self.ruta_archivo = ruta
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(self.toDict(), f, indent=4, ensure_ascii=False)

    @classmethod
    def fromDict(cls, d):
        """
        Crea una instancia de Procesador a partir de un diccionario.
        Compatible con JSONs antiguos sin prefijo_registro ni num_registros.
        """
        set_instrucciones = d.get("set_de_instrucciones", d.get("set de instrucciones", []))

        return cls(
            nombre=d["nombre"],
            tamano_palabra=d["tamano_palabra"],
            distribucion_memorias=d["distribucion_memorias"],
            profundidad=d["profundidad"],
            ancho=d["ancho"],
            tamano_minimo_direccionable=d["tamano_minimo_direccionable"],
            mapeo_memoria=d["mapeo_memoria"],
            aumento_pc=d["aumento_pc"],
            endianess=d["endianess"],
            prefijo_registro=d.get("prefijo_registro", "x"),   # default "x" para JSONs viejos
            num_registros=d.get("num_registros", 32),           # default 32 para JSONs viejos
            alias_registros=d.get("alias_registros", {}),
            comentarios=d.get("comentarios", {"linea": [";"], "bloque": []}),
            formato_de_sintaxis=d.get("formato_de_sintaxis", []),
            set_de_instrucciones=set_instrucciones,
            codigo=d.get("codigo", [])
        )

    def __str__(self):
        return f"Procesador: {self.nombre}, Palabra: {self.tamano_palabra} bits"
