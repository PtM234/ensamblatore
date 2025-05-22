from models.procesador import Procesador

def main():
    procesador = Procesador(
        nombre = "prueba",
        tamano_palabra = 3,
        distribucion_memorias = "Harvard",
        profundidad = 1024,
        ancho = 16,
        tamano_minimo_direccionable = 2,
        mapeo_memoria = 0,
        aumento_pc = 3,
        endianess = "Little Endian"
    )

    print ("Procesador creado:")
    print(procesador.__str__())

if __name__ == "__main__":
    main()