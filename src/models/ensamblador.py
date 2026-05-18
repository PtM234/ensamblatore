# src/models/ensamblador.py
import re


class ErrorDeEnsamblado(Exception):
    def __init__(self, mensaje, numero_linea=None):
        self.numero_linea = numero_linea
        prefijo = f"Línea {numero_linea}: " if numero_linea else ""
        super().__init__(f"{prefijo}{mensaje}")


class Ensamblador:
    # Tabla de alias ABI de RISC-V → nombre con prefijo x
    _ALIAS_ABI = {
        "zero": "x0",  "ra": "x1",  "sp": "x2",  "gp": "x3",
        "tp":   "x4",  "t0": "x5",  "t1": "x6",  "t2": "x7",
        "s0":   "x8",  "fp": "x8",  "s1": "x9",  "a0": "x10",
        "a1":   "x11", "a2": "x12", "a3": "x13", "a4": "x14",
        "a5":   "x15", "a6": "x16", "a7": "x17", "s2": "x18",
        "s3":   "x19", "s4": "x20", "s5": "x21", "s6": "x22",
        "s7":   "x23", "s8": "x24", "s9": "x25", "s10": "x26",
        "s11":  "x27", "t3": "x28", "t4": "x29", "t5": "x30",
        "t6":   "x31",
    }

    def __init__(self, procesador):
        self.procesador              = procesador
        self.tabla_simbolos          = {}
        self.lineas                  = []
        self.instrucciones_binarias  = []

        self._indice_instrucciones = {
            inst["mnemonico"].upper(): inst
            for inst in procesador.set_de_instrucciones
        }
        self._indice_formatos = {
            fmt["nombre"]: fmt
            for fmt in procesador.formato_de_sintaxis
        }
        self._prefijo = procesador.prefijo_registro
        self._n_regs  = procesador.num_registros

    # ─────────────────────────────────────────────
    #  PASO 0: PARSE
    # ─────────────────────────────────────────────

    def parse(self, codigo_fuente: str):
        self.lineas = []
        for n, linea_raw in enumerate(codigo_fuente.splitlines(), start=1):
            linea = linea_raw.split(";")[0].strip()
            if not linea:
                continue

            etiqueta = None
            match_etiqueta = re.match(r'^(\w+)\s*:(.*)', linea)
            if match_etiqueta:
                etiqueta = match_etiqueta.group(1).upper()
                linea    = match_etiqueta.group(2).strip()

            if not linea:
                self.lineas.append({"numero": n, "etiqueta": etiqueta,
                                    "mnemonico": None, "operandos": []})
                continue

            partes    = linea.split(None, 1)
            mnemonico = partes[0].upper()
            ops_raw   = partes[1] if len(partes) > 1 else ""

            # Separar operandos respetando paréntesis: "x10, 4(x2)" → ["x10", "4(x2)"]
            operandos = self._separar_operandos(ops_raw)

            self.lineas.append({"numero": n, "etiqueta": etiqueta,
                                 "mnemonico": mnemonico, "operandos": operandos})

    def _separar_operandos(self, ops_raw: str) -> list:
        """
        Separa operandos por coma o espacios sin romper expresiones con paréntesis.
        Acepta tanto "x10, 4(x2), x1" como "x10 4(x2) x1".
        Si hay comas las usa como separador; si no, usa espacios.
        """
        ops_raw = ops_raw.strip()
        if not ops_raw:
            return []

        # Determinar separador: coma si hay alguna fuera de paréntesis, sino espacio
        usa_coma = False
        profundidad = 0
        for c in ops_raw:
            if c == "(":
                profundidad += 1
            elif c == ")":
                profundidad -= 1
            elif c == "," and profundidad == 0:
                usa_coma = True
                break

        operandos   = []
        actual      = ""
        profundidad = 0

        for c in ops_raw:
            if c == "(":
                profundidad += 1
                actual += c
            elif c == ")":
                profundidad -= 1
                actual += c
            elif profundidad == 0 and ((usa_coma and c == ",") or
                                        (not usa_coma and c == " ")):
                if actual.strip():
                    operandos.append(actual.strip())
                actual = ""
            else:
                actual += c

        if actual.strip():
            operandos.append(actual.strip())

        return operandos

    # ─────────────────────────────────────────────
    #  PASO 1: PRIMERA PASADA
    # ─────────────────────────────────────────────

    def primera_pasada(self):
        self.tabla_simbolos = {}
        direccion = self.procesador.mapeo_memoria
        paso      = self.procesador.aumento_pc

        for linea in self.lineas:
            if linea["etiqueta"]:
                if linea["etiqueta"] in self.tabla_simbolos:
                    raise ErrorDeEnsamblado(
                        f"Etiqueta duplicada: '{linea['etiqueta']}'", linea["numero"])
                self.tabla_simbolos[linea["etiqueta"]] = direccion
            if linea["mnemonico"]:
                direccion += paso

    # ─────────────────────────────────────────────
    #  PASO 2: SEGUNDA PASADA
    # ─────────────────────────────────────────────

    def segunda_pasada(self):
        self.instrucciones_binarias = []
        direccion_actual = self.procesador.mapeo_memoria
        paso = self.procesador.aumento_pc

        for linea in self.lineas:
            if not linea["mnemonico"]:
                continue

            mnem = linea["mnemonico"]
            n    = linea["numero"]

            if mnem not in self._indice_instrucciones:
                raise ErrorDeEnsamblado(f"Instrucción desconocida: '{mnem}'", n)

            inst   = self._indice_instrucciones[mnem]
            fmt    = self._indice_formatos.get(inst.get("formato", ""))
            campos = inst.get("campos", {})
            mapeo  = inst.get("mapeo_operandos", "")

            if not fmt:
                raise ErrorDeEnsamblado(
                    f"Formato '{inst.get('formato')}' no encontrado para '{mnem}'", n)

            # Construir dict { nombre_campo_variable: valor_operando_raw }
            mapa_valores = self._mapear_operandos(
                mapeo, linea["operandos"], campos, mnem, n)

            binario = self._ensamblar_instruccion(
                inst, fmt, campos, mapa_valores, direccion_actual, n)

            self.instrucciones_binarias.append(binario)
            direccion_actual += paso

    # ─────────────────────────────────────────────
    #  MAPEO DE OPERANDOS
    # ─────────────────────────────────────────────

    def _mapear_operandos(self, mapeo: str, operandos: list,
                           campos_def: dict, mnem: str, n_linea: int) -> dict:
        """
        Usa el mapeo_operandos de la instrucción para construir un dict
        { nombre_campo: valor_raw } a partir de los operandos del código.

        Ejemplos de mapeo:
          "rd, rs1, rs2"     → token simple por campo
          "rs2, imm(rs1)"    → token compuesto: extrae imm y rs1 de "4(x2)"
          "rd, rs1, imm"     → token simple
        """
        if not mapeo:
            # Sin mapeo definido: asignación posicional simple (compatibilidad)
            campos_var = [k for k, v in campos_def.items() if not v]
            return {c: operandos[i] for i, c in enumerate(campos_var)
                    if i < len(operandos)}

        # Parsear los tokens del mapeo
        tokens_mapeo = self._separar_operandos(mapeo)

        if len(tokens_mapeo) != len(operandos):
            raise ErrorDeEnsamblado(
                f"'{mnem}': se esperaban {len(tokens_mapeo)} operandos "
                f"({mapeo}), se recibieron {len(operandos)}", n_linea)

        resultado = {}

        for token, op_raw in zip(tokens_mapeo, operandos):
            token = token.strip()

            # ── Patrón compuesto: imm(rs1) ──────────────────────────
            match_compuesto = re.match(r'^(\w+)\((\w+)\)$', token)
            if match_compuesto:
                nombre_imm = match_compuesto.group(1)
                nombre_reg = match_compuesto.group(2)

                # El operando real puede ser "4(x2)" o "4(sp)" con alias ABI
                # Primero intentar con prefijo numérico
                match_op = re.match(
                    rf'^(-?\w+)\({re.escape(self._prefijo)}(\d+)\)$',
                    op_raw, re.IGNORECASE)

                if match_op:
                    resultado[nombre_imm] = match_op.group(1)
                    resultado[nombre_reg] = f"{self._prefijo}{match_op.group(2)}"
                else:
                    # Intentar con alias ABI: "4(sp)" → imm=4, reg=x2
                    match_alias = re.match(r'^(-?\w+)\((\w+)\)$', op_raw)
                    if match_alias:
                        imm_part = match_alias.group(1)
                        reg_part = match_alias.group(2).lower()
                        reg_resuelto = self._ALIAS_ABI.get(reg_part, reg_part)
                        resultado[nombre_imm] = imm_part
                        resultado[nombre_reg] = reg_resuelto
                    else:
                        raise ErrorDeEnsamblado(
                            f"'{mnem}': se esperaba '{token}' pero se recibió '{op_raw}'",
                            n_linea)
            else:
                # ── Token simple: nombre de campo ────────────────────
                resultado[token] = op_raw

        return resultado

    # ─────────────────────────────────────────────
    #  ENSAMBLADO DE INSTRUCCIÓN
    # ─────────────────────────────────────────────

    def _ensamblar_instruccion(self, inst, fmt, campos_def,
                                mapa_valores, pc, n_linea):
        opcode         = inst["opcode"]
        bits_totales   = fmt["total_bits"]
        campos_formato = fmt["campos_operandos"]

        if len(opcode) != fmt["bits_opcode"]:
            raise ErrorDeEnsamblado(
                f"'{inst['mnemonico']}': opcode tiene {len(opcode)} bits, "
                f"se esperaban {fmt['bits_opcode']}", n_linea)

        partes = [opcode]

        for campo in campos_formato:
            if isinstance(campo, list):
                nombre_c = campo[0]
                bits_c   = campo[1]
                orden    = {str(i): i for i in range(bits_c)}
            else:
                nombre_c = campo["nombre"]
                bits_c   = campo["bits"]
                orden    = campo.get("orden_bits", {str(i): i for i in range(bits_c)})

            valor_const = campos_def.get(nombre_c, "")

            if valor_const:
                # Campo constante definido en la instrucción
                if len(valor_const) != bits_c:
                    raise ErrorDeEnsamblado(
                        f"'{inst['mnemonico']}': campo '{nombre_c}' tiene "
                        f"{len(valor_const)} bits, se esperaban {bits_c}", n_linea)
                partes.append(valor_const)
            else:
                # Campo variable — obtener del mapa de valores
                op_raw       = mapa_valores.get(nombre_c)
                uso_fallback = False

                # Fallback: buscar campo base quitando sufijos _lo/_hi etc.
                # Permite que 'imm_lo' e 'imm_hi' se resuelvan desde 'imm'
                if op_raw is None:
                    nombre_base = re.sub(r'_(lo|hi|hi2|lo2|[0-9]+)$', '', nombre_c)
                    op_raw = mapa_valores.get(nombre_base)
                    if op_raw is not None:
                        uso_fallback = True

                if op_raw is None:
                    raise ErrorDeEnsamblado(
                        f"'{inst['mnemonico']}': no se encontró valor para "
                        f"el campo '{nombre_c}'. Revisa el mapeo de operandos.",
                        n_linea)

                # Si tiene orden_bits personalizado, resolver con el ancho real
                # = bit índice más alto + 1 (aplica tanto a fallback como a campo directo)
                natural = {str(i): i for i in range(bits_c)}
                if orden != natural and orden:
                    bits_resolucion = max(int(k) for k in orden.keys()) + 1
                else:
                    bits_resolucion = bits_c

                valor_bin = self._resolver_operando(
                    op_raw, nombre_c, bits_resolucion, pc, n_linea, inst["mnemonico"])

                valor_bin = self._aplicar_orden_bits(
                    valor_bin, bits_c, orden, nombre_c, n_linea, inst["mnemonico"])

                partes.append(valor_bin)

        palabra = "".join(reversed(partes))

        if len(palabra) != bits_totales:
            raise ErrorDeEnsamblado(
                f"'{inst['mnemonico']}': la instrucción generó {len(palabra)} bits, "
                f"se esperaban {bits_totales}", n_linea)

        return palabra

    # ─────────────────────────────────────────────
    #  RESOLVER OPERANDO
    # ─────────────────────────────────────────────

    def _resolver_operando(self, op_raw, nombre_campo, bits, pc, n_linea, mnem):
        op = op_raw.strip()

        # Resolver alias ABI (sp→x2, zero→x0, ra→x1, etc.)
        if op.lower() in self._ALIAS_ABI:
            op = self._ALIAS_ABI[op.lower()]

        # Registro
        match_reg = re.match(
            rf'^{re.escape(self._prefijo)}(\d+)$', op, re.IGNORECASE)
        if match_reg:
            n = int(match_reg.group(1))
            if n >= self._n_regs:
                raise ErrorDeEnsamblado(
                    f"'{mnem}': registro '{op}' fuera de rango", n_linea)
            return self._int_a_bin(n, bits, n_linea, mnem, op)

        # Etiqueta
        if op.upper() in self.tabla_simbolos:
            offset = self.tabla_simbolos[op.upper()] - pc
            return self._int_a_bin(offset, bits, n_linea, mnem, op, signed=True)

        # Inmediato numérico
        try:
            if op.lower().startswith("0x"):
                valor = int(op, 16)
            elif op.lower().startswith("0b"):
                valor = int(op, 2)
            else:
                valor = int(op)
            return self._int_a_bin(valor, bits, n_linea, mnem, op, signed=(valor < 0))
        except ValueError:
            pass

        raise ErrorDeEnsamblado(
            f"'{mnem}': no se pudo interpretar el operando '{op_raw}'", n_linea)

    def _int_a_bin(self, valor, bits, n_linea, mnem, op_raw, signed=False):
        if signed or valor < 0:
            minimo = -(2 ** (bits - 1))
            maximo =  (2 ** (bits - 1)) - 1
            if not (minimo <= valor <= maximo):
                raise ErrorDeEnsamblado(
                    f"'{mnem}': valor {valor} ('{op_raw}') no cabe en {bits} bits "
                    f"con signo (rango {minimo}..{maximo})", n_linea)
            if valor < 0:
                valor = valor + (2 ** bits)
        else:
            maximo = (2 ** bits) - 1
            if valor > maximo:
                raise ErrorDeEnsamblado(
                    f"'{mnem}': valor {valor} ('{op_raw}') no cabe en {bits} bits "
                    f"sin signo (máximo {maximo})", n_linea)
        return format(valor, f'0{bits}b')

    # ─────────────────────────────────────────────
    #  ORDEN DE BITS
    # ─────────────────────────────────────────────

    def _aplicar_orden_bits(self, valor_bin, bits, orden, nombre_campo, n_linea, mnem):
        natural = {str(i): i for i in range(bits)}
        if orden == natural:
            return valor_bin

        resultado = ['0'] * bits
        for bit_origen_str, pos_campo in orden.items():
            bit_origen = int(bit_origen_str)
            if bit_origen >= len(valor_bin):
                raise ErrorDeEnsamblado(
                    f"'{mnem}': campo '{nombre_campo}': bit origen {bit_origen} "
                    f"fuera del rango del valor", n_linea)
            bit_valor = valor_bin[-(bit_origen + 1)]
            resultado[bits - 1 - pos_campo] = bit_valor

        return "".join(resultado)

    # ─────────────────────────────────────────────
    #  API PÚBLICA
    # ─────────────────────────────────────────────

    def ensamblar(self, codigo_fuente: str):
        self.parse(codigo_fuente)
        self.primera_pasada()
        self.segunda_pasada()
        return self.instrucciones_binarias

    # ─────────────────────────────────────────────
    #  GENERADORES DE SALIDA
    # ─────────────────────────────────────────────

    def generar_bin(self, ruta: str):
        with open(ruta, "wb") as f:
            for instr_bin in self.instrucciones_binarias:
                valor     = int(instr_bin, 2)
                es_little = "little" in self.procesador.endianess.lower()
                f.write(valor.to_bytes(4, byteorder="little" if es_little else "big"))

    def generar_mem(self, ruta: str):
        with open(ruta, "w", encoding="utf-8") as f:
            for instr_bin in self.instrucciones_binarias:
                f.write(f"{int(instr_bin, 2):08X}\n")

    def generar_coe(self, ruta: str):
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("memory_initialization_radix=16;\n")
            f.write("memory_initialization_vector=\n")
            hex_vals = [f"{int(b, 2):08X}" for b in self.instrucciones_binarias]
            for i, val in enumerate(hex_vals):
                sep = "," if i < len(hex_vals) - 1 else ";"
                f.write(f"{val}{sep}\n")
