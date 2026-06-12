"""
palabra.py
==========
La unidad más básica del sistema: una secuencia de bits de tamaño fijo.

Decisiones de diseño:
  - Los bits se guardan en una lista, con el índice 0 = bit MENOS significativo
    (LSB). Así, el bit en la posición i siempre tiene peso 2^i.
  - Los números negativos se guardan en complemento a dos automáticamente.
  - Para mostrarla como texto, se invierte el orden (MSB a la izquierda),
    que es como leemos los números normalmente.
"""

from __future__ import annotations


class Palabra:
    """Una secuencia inmutable de bits de tamaño fijo."""

    def __init__(self, valor: int, tamano: int):
        if tamano <= 0:
            raise ValueError(f"El tamaño debe ser positivo, se recibió {tamano}")

        # Rango representable en 'tamano' bits, interpretado con signo o sin signo.
        # Sin signo: 0 .. 2^n - 1
        # Con signo (complemento a dos): -2^(n-1) .. 2^(n-1) - 1
        minimo_con_signo = -(1 << (tamano - 1))
        maximo_sin_signo = (1 << tamano) - 1

        if valor < minimo_con_signo or valor > maximo_sin_signo:
            raise ValueError(
                f"El valor {valor} no cabe en {tamano} bits "
                f"(rango permitido: {minimo_con_signo} a {maximo_sin_signo})"
            )

        # Si es negativo, lo convertimos a su representación en complemento a dos.
        if valor < 0:
            valor = (1 << tamano) + valor

        self._tamano = tamano
        # Extraemos cada bit: el bit i es (valor >> i) & 1
        self._bits = [(valor >> i) & 1 for i in range(tamano)]

    # ── Propiedades de solo lectura ───────────────────────────────────────
    @property
    def tamano(self) -> int:
        return self._tamano

    @property
    def bits(self) -> list[int]:
        """Copia de la lista de bits (índice 0 = LSB)."""
        return list(self._bits)

    # ── Constructores alternativos ────────────────────────────────────────
    @classmethod
    def desde_binario(cls, cadena: str) -> "Palabra":
        """
        Crea una Palabra desde una cadena binaria como '1011' o '10 11'.
        El primer carácter es el bit MÁS significativo (como se lee).
        """
        limpia = cadena.replace(" ", "").replace("_", "")
        if not limpia:
            raise ValueError("La cadena binaria está vacía")
        if any(c not in "01" for c in limpia):
            raise ValueError(f"La cadena '{cadena}' tiene caracteres no binarios")
        return cls(int(limpia, 2), len(limpia))

    # ── Conversiones ──────────────────────────────────────────────────────
    def a_entero(self) -> int:
        """Devuelve el valor como entero SIN signo."""
        return sum(bit << i for i, bit in enumerate(self._bits))

    def a_entero_con_signo(self) -> int:
        """Devuelve el valor interpretado como complemento a dos (con signo)."""
        valor = self.a_entero()
        # Si el bit más significativo es 1, es negativo.
        if self._bits[self._tamano - 1] == 1:
            valor -= (1 << self._tamano)
        return valor

    def a_hex(self) -> str:
        """Representación hexadecimal, con ceros a la izquierda según el tamaño."""
        ancho_hex = (self._tamano + 3) // 4
        return format(self.a_entero(), f"0{ancho_hex}X")

    # ── Representación como texto ─────────────────────────────────────────
    def __str__(self) -> str:
        """Cadena binaria con el MSB a la izquierda (como se lee)."""
        return "".join(str(bit) for bit in reversed(self._bits))

    def __repr__(self) -> str:
        return f"Palabra('{self}', tamano={self._tamano})"

    # ── Igualdad (útil para las pruebas) ──────────────────────────────────
    def __eq__(self, otro: object) -> bool:
        if not isinstance(otro, Palabra):
            return NotImplemented
        return self._tamano == otro._tamano and self._bits == otro._bits

    def __len__(self) -> int:
        return self._tamano
