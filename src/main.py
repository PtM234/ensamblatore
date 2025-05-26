from models.procesador import Procesador
from models.instruccion import Instruccion
from models.formatoInstruccion import FormatoDeInstruccion

def main():

    instruccion1 = Instruccion(
        mnemonico="ADD",
        nombre="Suma",
        descripcion="Suma dos registros",
        regex=r"^ADD R[0-9]+, R[0-9]+, R[0-9]+$",
        sintaxis="ADD reg1, reg2, reg3",
        const=[["R1", "R2"]],
        var_rel=[["reg1", "reg2", "reg3"]]
    )

    formato1 = FormatoDeInstruccion(
        nombre="R-Type",
        total_bits=16,
        bits_opcode=4,
        campos_operandos=[("reg1", 4), ("reg2", 4), ("reg3", 4)]
    )

    procesador = Procesador(
        nombre="MiCPU",
        tamano_palabra=16,
        distribucion_memorias="Harvard",
        profundidad=1024,
        ancho=8,
        tamano_minimo_direccionable=1,
        mapeo_memoria=0x1000,
        aumento_pc=2,
        endianess="Little",
        set_de_instrucciones=[instruccion1],
        formato_de_sintaxis=[formato1.toDict()],
        codigo=["ADD R1, R2, R3"]
    )

    print ("Procesador creado:")
    print(procesador.__str__())
    procesador.guardarEnJSON()

if __name__ == "__main__":
    main()