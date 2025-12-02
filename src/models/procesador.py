# src/models/procesador.py
import json


class Procesador:
    def __init__(self, nombre, tamano_palabra, distribucion_memorias, profundidad, ancho,
                 tamano_minimo_direccionable, mapeo_memoria, aumento_pc, endianess,
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

        # Validación para evitar listas compartidas (Buenas prácticas)
        self.formato_de_sintaxis = formato_de_sintaxis if formato_de_sintaxis is not None else []
        self.set_de_instrucciones = set_de_instrucciones if set_de_instrucciones is not None else []
        self.codigo = codigo if codigo is not None else []

    def agregarFormatoDeSintaxis(self, formato_de_sintaxis):
        self.formato_de_sintaxis = formato_de_sintaxis

    def agregarSetDeInstrucciones(self, set_de_instrucciones):
        self.set_de_instrucciones = set_de_instrucciones

    def agregarCodigo(self, codigo):
        self.codigo = codigo

    def toDict(self):
        return {
            "nombre": self.nombre,
            "tamano_palabra": self.tamano_palabra,
            "distribucion_memorias": self.distribucion_memorias,
            "profundidad": self.profundidad,
            "ancho": self.ancho,
            "tamano_minimo_direccionable": self.tamano_minimo_direccionable,
            "mapeo_memoria": self.mapeo_memoria,
            "aumento_pc": self.aumento_pc,
            "endianess": self.endianess,
            "formato_de_sintaxis": self.formato_de_sintaxis,
            # Verificamos si los objetos tienen método toDict antes de llamarlo
            "set de instrucciones": [i.toDict() if hasattr(i, 'toDict') else i for i in self.set_de_instrucciones],
            "codigo": self.codigo
        }

    def guardarEnJSON(self, ruta="procesador.json"):
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(self.toDict(), f, indent=4)

    @classmethod
    def fromDict(cls, d):
        """Crea una instancia de Procesador a partir de un diccionario (JSON loaded)"""
        nuevo_proc = cls(
            nombre=d["nombre"],
            tamano_palabra=d["tamano_palabra"],
            distribucion_memorias=d["distribucion_memorias"],
            profundidad=d["profundidad"],
            ancho=d["ancho"],
            tamano_minimo_direccionable=d["tamano_minimo_direccionable"],
            mapeo_memoria=d["mapeo_memoria"],
            aumento_pc=d["aumento_pc"],
            endianess=d["endianess"],
            formato_de_sintaxis=d["formato_de_sintaxis"],
            set_de_instrucciones=d.get("set de instrucciones", []),  # Usamos .get por seguridad
            codigo=d.get("codigo", [])
        )
        return nuevo_proc

    def __str__(self):
        return (f"Procesador: {self.nombre}, Palabra: {self.tamano_palabra} bits")