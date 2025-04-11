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

class Procesador:
    def __init__(self):
        self.nombre
        self.tamanoPalabra
        self.distMemorias
        self.profundidad
        self.ancho
        self.tamMinDir
        self.mapMem
        self.aumentoPc
        self.endianess
        self.setDeInstrucciones
        self.formatoDeSintaxis
        self.codigo

    @classmethod
    def crearNuevo(cls, nombre, tamano_palabra, distribucion_memoria, profundidad, ancho, tam_min_dir, map_mem, aumento_pc, endianness):
        instancia  = cls()
        instancia.nombre = nombre
        instancia.tamano_palabra = tamano_palabra
        instancia.distribucion_memoria = distribucion_memoria
        instancia.profundidad = profundidad
        instancia.ancho = ancho
        instancia.tam_min_dir = tam_min_dir
        instancia.map_mem = map_mem
        instancia.aumento_pc = aumento_pc
        instancia.endianness = endianness

    @classmethod
    def leer_existente (cls, nombre, tamano_palabra, distribucion_memoria, profundidad, ancho, tam_min_dir, map_mem, aumento_pc, endianness, set_de_instrucciones, formato_de_sintaxis):
        instancia = cls()
        instancia.nombre = nombre
        instancia.tamano_palabra = tamano_palabra
        instancia.distribucion_memoria = distribucion_memoria
        instancia.profundidad = profundidad
        instancia.ancho = ancho
        instancia.tam_min_dir = tam_min_dir
        instancia.map_mem = map_mem
        instancia.aumento_pc = aumento_pc
        instancia.endianness = endianness
        instancia.set_de_instrucciones = set_de_instrucciones
        instancia.formato_de_sintaxis = formato_de_sintaxis

    @classmethod
    def leer_codigo(cls, nombre, tamano_palabra, distribucion_memoria, profundidad, ancho, tam_min_dir, map_mem, aumento_pc, endianness, set_de_instrucciones, formato_de_sintaxis, codigo):
        instancia = cls()
        instancia.nombre = nombre
        instancia.tamano_palabra = tamano_palabra
        instancia.distribucion_memoria = distribucion_memoria
        instancia.profundidad = profundidad
        instancia.ancho = ancho
        instancia.tam_min_dir = tam_min_dir
        instancia.map_mem = map_mem
        instancia.aumento_pc = aumento_pc
        instancia.endianness = endianness
        instancia.set_de_instrucciones = set_de_instrucciones
        instancia.formato_de_sintaxis = formato_de_sintaxis
        instancia.codigo = codigo



    def __str__(self):
        return (f"Procesador: {self.nombre}, Tamaño Palabra: {self.tamano_palabra}, "
                f"Dist. Memorias: {self.dist_memorias}, Profundidad: {self.profundidad}, Ancho: {self.ancho}, "
                f"Tamaño Min. Dir: {self.tam_min_dir}, MapMem: {self.map_mem}, Aumento PC: {self.aumento_pc}, "
                f"Endianess: {self.endianess}, Set de Instrucción: {len(self.set_de_instruccion)}, "
                f"Formato de Sintaxis: {len(self.formato_de_sintaxis)}, Código: {len(self.codigo)} líneas")