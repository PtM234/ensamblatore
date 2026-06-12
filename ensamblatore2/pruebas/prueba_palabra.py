"""
prueba_palabra.py
==================
Pruebas de la clase Palabra. Se ejecuta con: python3 prueba_palabra.py
No usa librerías externas: cada prueba imprime OK o FALLA.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from nucleo.palabra import Palabra


# Pequeño marco de pruebas casero (sin dependencias)
_total = 0
_ok = 0

def revisar(descripcion, condicion):
    global _total, _ok
    _total += 1
    if condicion:
        _ok += 1
        print(f"  OK   | {descripcion}")
    else:
        print(f"  FALLA| {descripcion}")

def revisar_error(descripcion, funcion):
    """Verifica que 'funcion' lance una excepción (caso inválido)."""
    global _total, _ok
    _total += 1
    try:
        funcion()
        print(f"  FALLA| {descripcion} (se esperaba un error y no ocurrió)")
    except (ValueError, Exception):
        _ok += 1
        print(f"  OK   | {descripcion}")


print("=" * 60)
print("PRUEBAS DE Palabra")
print("=" * 60)

# ── Creación básica desde entero ──────────────────────────────────────────
print("\n[Creación desde entero]")
p = Palabra(5, 8)
revisar("5 en 8 bits -> '00000101'", str(p) == "00000101")
revisar("5 en 8 bits -> entero 5", p.a_entero() == 5)
revisar("5 en 8 bits -> hex '05'", p.a_hex() == "05")
revisar("tamaño es 8", p.tamano == 8)

# ── Creación desde binario ────────────────────────────────────────────────
print("\n[Creación desde binario]")
p = Palabra.desde_binario("1011")
revisar("'1011' -> entero 11", p.a_entero() == 11)
revisar("'1011' -> tamaño 4", p.tamano == 4)
p = Palabra.desde_binario("0001 0101 1010")  # con espacios
revisar("'0001 0101 1010' ignora espacios -> 12 bits", p.tamano == 12)
revisar("'0001 0101 1010' -> hex '15A'", p.a_hex() == "15A")

# ── El bit 0 es el menos significativo ────────────────────────────────────
print("\n[Orden de bits: índice 0 = LSB]")
p = Palabra.desde_binario("1000")  # = 8
revisar("'1000' bit[0] (LSB) = 0", p.bits[0] == 0)
revisar("'1000' bit[3] (MSB) = 1", p.bits[3] == 1)
revisar("'1000' -> entero 8", p.a_entero() == 8)

# ── Números negativos (complemento a dos) ─────────────────────────────────
print("\n[Complemento a dos]")
p = Palabra(-4, 8)
revisar("-4 en 8 bits -> '11111100'", str(p) == "11111100")
revisar("-4 en 8 bits -> sin signo 252", p.a_entero() == 252)
revisar("-4 en 8 bits -> con signo -4", p.a_entero_con_signo() == -4)

p = Palabra(-1, 8)
revisar("-1 en 8 bits -> '11111111'", str(p) == "11111111")
revisar("-1 -> con signo -1", p.a_entero_con_signo() == -1)

p = Palabra(127, 8)
revisar("127 en 8 bits -> con signo 127 (máximo positivo)", p.a_entero_con_signo() == 127)
p = Palabra(-128, 8)
revisar("-128 en 8 bits -> con signo -128 (mínimo)", p.a_entero_con_signo() == -128)

# ── RISC-V: una instrucción real de 32 bits ───────────────────────────────
print("\n[Caso real: add x6,x5,x1 = 0x00128333]")
p = Palabra(0x00128333, 32)
revisar("0x00128333 -> hex '00128333'", p.a_hex() == "00128333")
revisar("0x00128333 -> 32 bits", p.tamano == 32)

# ── Igualdad ──────────────────────────────────────────────────────────────
print("\n[Igualdad]")
revisar("dos palabras iguales son ==", Palabra(5, 8) == Palabra(5, 8))
revisar("distinto valor -> !=", Palabra(5, 8) != Palabra(6, 8))
revisar("mismo valor distinto tamaño -> !=", Palabra(5, 8) != Palabra(5, 16))

# ── Casos inválidos (deben dar error) ─────────────────────────────────────
print("\n[Casos inválidos: deben lanzar error]")
revisar_error("valor que no cabe (256 en 8 bits)", lambda: Palabra(256, 8))
revisar_error("negativo fuera de rango (-129 en 8 bits)", lambda: Palabra(-129, 8))
revisar_error("tamaño cero", lambda: Palabra(0, 0))
revisar_error("binario con caracteres inválidos", lambda: Palabra.desde_binario("10X1"))
revisar_error("binario vacío", lambda: Palabra.desde_binario("   "))

# ── Resumen ───────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"RESULTADO: {_ok}/{_total} pruebas pasaron")
print("=" * 60)
sys.exit(0 if _ok == _total else 1)
