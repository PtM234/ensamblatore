
class FormatoDeInstruccion:
    def __init__(self, nombre: str, total_bits: int, bits_opcode: int, campos_operandos: list[tuple[str, int]]):
        self.nombre = nombre                   # Nombre del formato (ej. 'R-Type')
        self.total_bits = total_bits           # Longitud total de la instrucción
        self.bits_opcode = bits_opcode         # Cuántos bits ocupa el opcode
        self.campos_operandos = campos_operandos  # Lista de tuplas (nombre_operando, cantidad_bits)
        #Este es un comentario de prueba para ver si me deja hacer push

    def toDict(self):
        return {
            "nombre": self.nombre,
            "total_bits": self.total_bits,
            "bits_opcode": self.bits_opcode,
            "campos_operandos": self.campos_operandos
        }

    def __str__(self):
        return (
            f"Formato '{self.nombre}': {self.total_bits} bits\n"
            f"Opcode: {self.bits_opcode} bits\n"
            f"Operandos: {self.campos_operandos}"
        )