import formatoInstruccion

"""
Un procesador tiene las siguientes cosas:
- Nombre para identificarlo (String)
- Tamaño de palabra (INT)
- Distribución de memorias (String)
- Profundidad y ancho de memoria (INT)
- Tamaño mínimo direccionable (INT)
- Mapeo de memoria (INT 0 y 1)
- Aumento de contador de programa (INT)
- Endianness (String, big endian y little endian)
- Set de instrucciones, este es un objeto y contiene lo siguiente:
        - Nombre de formato (String)
        - Parametros (Parametros de Formato):
                - Nombre (String)
                - bitsFormato (INT)
                - Constante (boolean)
                - valorEsperado(String)
        - Instrucciones (Instrucción):
                - Mnemónico (String)
                - Nombre (String)
                - Descripción (String)
                - regex (String)
                - sintaxis (String)
                - const (String)
                - varRel (String)

¿Qué sigue?
Ya se tiene la arquitectura de un procesador, sigue añadirle los datos necesarios. Lo siguiente es definir parámetros de la arquitectura

Parámetros de la arquitectura:
        - Nombre del procesador

"""
import json


class Procesador:
    def __init__(self, nombre, tamano_palabra, distribucion_memorias, profundidad, ancho, tamano_minimo_direccionable, mapeo_memoria, aumento_pc, endianess, formato_de_sintaxis = [], set_de_instrucciones = [], codigo = []):
        self.nombre = nombre
        self.tamano_palabra = tamano_palabra
        self.distribucion_memorias = distribucion_memorias
        self.profundidad = profundidad
        self.ancho = ancho
        self.tamano_minimo_direccionable = tamano_minimo_direccionable
        self.mapeo_memoria = mapeo_memoria
        self.aumento_pc = aumento_pc
        self.endianess = endianess
        self.formato_de_sintaxis = formato_de_sintaxis
        self.set_de_instrucciones = set_de_instrucciones
        self.codigo = codigo

    def agregarFormatoDeSintaxis(self, formato_de_sintaxis):
        self.formato_de_sintaxis = formato_de_sintaxis

    def agregarSetDeInstrucciones(self, set_de_instrucciones):
        self.set_de_instrucciones = set_de_instrucciones

    def agregarCodigo(self, codigo):
        self.codigo = codigo

    def toDict(self):
        return (f"Procesador: {self.nombre}, "
                f"Tamaño Palabra: {self.tamano_palabra},"
                f"Dist. Memorias: {self.distribucion_memorias}, "
                f"Profundidad: {self.profundidad}, "
                f"Ancho: {self.ancho}, "
                f"Tamaño Min. Dir: {self.tamano_minimo_direccionable}, "
                f"MapMem: {self.mapeo_memoria}, "
                f"Aumento PC: {self.aumento_pc}, "
                f"Endianess: {self.endianess}, "
                f"Set de Instrucción: {len(self.set_de_instrucciones)}, "
                f"Formato de Sintaxis: {len(self.formato_de_sintaxis)}, "
                f"Código: {len(self.codigo)}")

    def guardarEnJSON(self):
        with open("procesador.json", "w", encoding="utf-8") as f:
            json.dump(Procesador.toDict(), f, indent = 4)

    def __str__(self):
        return (f"Procesador: {self.nombre}, Tamaño Palabra: {self.tamano_palabra}, "
                f"Dist. Memorias: {self.distribucion_memorias}, Profundidad: {self.profundidad}, Ancho: {self.ancho}, "
                f"Tamaño Min. Dir: {self.tamano_minimo_direccionable}, MapMem: {self.mapeo_memoria}, Aumento PC: {self.aumento_pc}, "
                f"Endianess: {self.endianess}, Set de Instrucción: {len(self.set_de_instrucciones)}, "
                f"Formato de Sintaxis: {len(self.formato_de_sintaxis)}, Código: {len(self.codigo)} líneas")