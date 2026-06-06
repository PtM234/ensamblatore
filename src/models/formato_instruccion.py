class FormatoDeInstruccion:
    """
    Un formato de instrucción define la estructura de bits de una palabra.

    Modelo de campos:
      Cada campo es un dict:
        {
          "nombre": str,              # ej. "opcode", "rd", "imm"
          "tipo":   str,              # "opcode" | "constante" | "registro" | "inmediato"
          "bits":   int,              # ancho del campo en bits
          "orden_bits": {...}         # (opcional) reordenamiento interno del valor
        }

    Propiedad 'lectura':
      "msb_primero" → el primer campo de la lista ocupa los bits MÁS significativos
                      (se lee de izquierda a derecha, como en los manuales).
      "lsb_primero" → el primer campo de la lista ocupa los bits MENOS significativos
                      (se lee de derecha a izquierda).
    """

    TIPOS_VALIDOS = ("opcode", "constante", "registro", "inmediato")

    def __init__(self, nombre: str, total_bits: int,
                 campos_operandos: list, lectura: str = "msb_primero"):
        self.nombre           = nombre
        self.total_bits       = total_bits
        self.campos_operandos = campos_operandos
        self.lectura          = lectura

    @staticmethod
    def orden_natural(bits: int) -> dict:
        """Genera un orden_bits natural para un campo de N bits."""
        return {str(i): i for i in range(bits)}

    @staticmethod
    def parsear_orden_bits(texto: str, bits: int) -> dict:
        """
        Convierte el texto del usuario a un dict de orden_bits.
        Formato esperado: "1:0, 2:1, 3:2, 4:3, 11:4"
        Si el texto está vacío, devuelve orden natural.
        """
        texto = texto.strip()
        if not texto:
            return FormatoDeInstruccion.orden_natural(bits)

        orden = {}
        texto = texto.replace("->", ":").replace("→", ":")
        partes = [p.strip() for p in texto.split(",") if p.strip()]

        for parte in partes:
            if ":" not in parte:
                raise ValueError(
                    f"Formato inválido en '{parte}'. "
                    f"Usa: bit_origen:posicion_campo  ej: 1:0, 2:1"
                )
            origen, destino = parte.split(":")
            orden[str(int(origen.strip()))] = int(destino.strip())

        destinos = list(orden.values())
        if len(destinos) != len(set(destinos)):
            raise ValueError("Hay posiciones de destino duplicadas en el orden de bits.")
        if any(v >= bits for v in destinos):
            raise ValueError(
                f"Una posición de destino excede el tamaño del campo ({bits} bits).")

        return orden

    def validar(self):
        """
        Verifica que la suma de bits de los campos coincida con total_bits
        y que los tipos sean válidos. Lanza ValueError si algo no cuadra.
        """
        suma = sum(c["bits"] for c in self.campos_operandos)
        if suma != self.total_bits:
            raise ValueError(
                f"Formato '{self.nombre}': los campos suman {suma} bits, "
                f"pero el total declarado es {self.total_bits}.")

        for c in self.campos_operandos:
            tipo = c.get("tipo", "")
            if tipo not in self.TIPOS_VALIDOS:
                raise ValueError(
                    f"Formato '{self.nombre}': campo '{c.get('nombre')}' tiene "
                    f"tipo inválido '{tipo}'. Válidos: {self.TIPOS_VALIDOS}")

        # Debe haber exactamente un campo opcode (a menos que no se use opcode)
        n_opcode = sum(1 for c in self.campos_operandos if c.get("tipo") == "opcode")
        if n_opcode > 1:
            raise ValueError(
                f"Formato '{self.nombre}': hay {n_opcode} campos opcode. "
                f"Solo se permite uno (o ninguno).")

    def toDict(self):
        return {
            "nombre":           self.nombre,
            "total_bits":       self.total_bits,
            "lectura":          self.lectura,
            "campos_operandos": self.campos_operandos
        }

    @classmethod
    def fromDict(cls, d):
        return cls(
            nombre=d["nombre"],
            total_bits=d["total_bits"],
            campos_operandos=d.get("campos_operandos", []),
            lectura=d.get("lectura", "msb_primero")
        )

    def __str__(self):
        campos_str = ", ".join(
            f"{c['nombre']}({c['bits']},{c.get('tipo','?')})"
            for c in self.campos_operandos
        )
        return (
            f"Formato '{self.nombre}': {self.total_bits} bits [{self.lectura}]\n"
            f"Campos: {campos_str}"
        )
