class FormatoDeInstruccion:
    def __init__(self, nombre: str, total_bits: int, bits_opcode: int,
                 campos_operandos: list):
        self.nombre = nombre
        self.total_bits = total_bits
        self.bits_opcode = bits_opcode
        # campos_operandos: lista de dicts
        # { "nombre": str, "bits": int, "orden_bits": { "bit_origen": pos_campo } }
        self.campos_operandos = campos_operandos

    @staticmethod
    def orden_natural(bits: int) -> dict:
        """Genera un orden_bits natural para un campo de N bits."""
        return {str(i): i for i in range(bits)}

    @staticmethod
    def parsear_orden_bits(texto: str, bits: int) -> dict:
        """
        Convierte el texto del usuario a un dict de orden_bits.
        Formato esperado: "1→0, 2→1, 3→2, 4→3, 11→4"
        Si el texto está vacío, devuelve orden natural.
        """
        texto = texto.strip()
        if not texto:
            return FormatoDeInstruccion.orden_natural(bits)

        orden = {}
        # Aceptar tanto → como -> como separador
        texto = texto.replace("->", ":")
        partes = [p.strip() for p in texto.split(",") if p.strip()]

        for parte in partes:
            if ":" not in parte:
                raise ValueError(
                    f"Formato inválido en '{parte}'. "
                    f"Usa: bit_origen:posicion_campo  ej: 1:0, 2:1"
                )
            origen, destino = parte.split(":")
            orden[str(int(origen.strip()))] = int(destino.strip())

        # Validar que las posiciones de destino no se repitan
        destinos = list(orden.values())
        if len(destinos) != len(set(destinos)):
            raise ValueError("Hay posiciones de destino duplicadas en el orden de bits.")

        # Validar que no exceda el número de bits del campo
        if any(v >= bits for v in destinos):
            raise ValueError(
                f"Una posición de destino excede el tamaño del campo ({bits} bits).")

        return orden

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
