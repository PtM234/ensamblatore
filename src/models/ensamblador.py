# src/models/ensamblador.py
import re


class ErrorDeEnsamblado(Exception):
    def __init__(self, mensaje, numero_linea=None):
        self.numero_linea = numero_linea
        prefijo = f"Línea {numero_linea}: " if numero_linea else ""
        super().__init__(f"{prefijo}{mensaje}")


class Ensamblador:
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

        # Alias de registros definidos por el usuario (ej. {"sp": "x2", "zero": "x0"})
        # Se normalizan a minúsculas para búsqueda insensible a mayúsculas.
        alias_def = getattr(procesador, "alias_registros", {}) or {}
        self._alias = {k.lower(): v for k, v in alias_def.items()}

        # Configuración de comentarios
        com = getattr(procesador, "comentarios", None) or {}
        self._com_linea  = com.get("linea", [";"]) or [";"]
        self._com_bloque = com.get("bloque", []) or []

    # ─────────────────────────────────────────────
    #  PASO 0: PARSE
    # ─────────────────────────────────────────────

    def _quitar_comentarios_bloque(self, texto: str) -> str:
        """
        Elimina comentarios de bloque (ej. /* ... */) preservando los saltos
        de línea para no desfasar la numeración de líneas.
        """
        for apertura, cierre in self._com_bloque:
            if not apertura or not cierre:
                continue
            patron = re.escape(apertura) + r'.*?' + re.escape(cierre)

            def _reemplazo(m):
                # Conservar los \n internos para no perder el conteo de líneas
                return "\n" * m.group(0).count("\n")

            texto = re.sub(patron, _reemplazo, texto, flags=re.DOTALL)
        return texto

    def _quitar_comentario_linea(self, linea: str) -> str:
        """Corta la línea en el primer marcador de comentario de línea que aparezca."""
        corte = len(linea)
        for marcador in self._com_linea:
            if not marcador:
                continue
            idx = linea.find(marcador)
            if idx != -1 and idx < corte:
                corte = idx
        return linea[:corte]

    def parse(self, codigo_fuente: str):
        self.lineas = []
        # Primero quitar comentarios de bloque de todo el texto
        codigo_fuente = self._quitar_comentarios_bloque(codigo_fuente)

        for n, linea_raw in enumerate(codigo_fuente.splitlines(), start=1):
            linea = self._quitar_comentario_linea(linea_raw).strip()
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
                        reg_resuelto = self._alias.get(reg_part, reg_part)
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
        """
        Construye la palabra binaria a partir de los campos del formato.

        Cada campo declara su 'tipo':
          - opcode / constante → valor fijo definido en la instrucción (campos_def)
          - registro / inmediato → valor variable que viene del código del usuario

        El orden de concatenación depende de fmt["lectura"]:
          - "msb_primero": primer campo de la lista = bits más significativos
          - "lsb_primero": primer campo de la lista = bits menos significativos
        """
        mnem           = inst.get("mnemonico", "?")
        bits_totales   = fmt["total_bits"]
        campos_formato = fmt["campos_operandos"]
        lectura        = fmt.get("lectura", "msb_primero")

        partes = []  # lista de (string binario) en el orden de la lista de campos

        for campo in campos_formato:
            nombre_c = campo["nombre"]
            bits_c   = campo["bits"]
            tipo_c   = campo.get("tipo", "constante")
            orden    = campo.get("orden_bits", {str(i): i for i in range(bits_c)})

            # ── Campos de valor fijo: opcode y constante ──────────────
            if tipo_c in ("opcode", "constante"):
                valor_const = campos_def.get(nombre_c, "")
                if not valor_const:
                    raise ErrorDeEnsamblado(
                        f"'{mnem}': el campo '{nombre_c}' (tipo {tipo_c}) "
                        f"no tiene valor definido en la instrucción.", n_linea)
                if len(valor_const) != bits_c:
                    raise ErrorDeEnsamblado(
                        f"'{mnem}': campo '{nombre_c}' tiene {len(valor_const)} "
                        f"bits, se esperaban {bits_c}", n_linea)
                partes.append(valor_const)
                continue

            # ── Campos variables: registro e inmediato ────────────────
            op_raw = mapa_valores.get(nombre_c)

            # Fallback: campo base quitando sufijos _lo/_hi (inmediatos partidos)
            if op_raw is None:
                nombre_base = re.sub(r'_(lo|hi|hi2|lo2|[0-9]+)$', '', nombre_c)
                op_raw = mapa_valores.get(nombre_base)

            if op_raw is None:
                raise ErrorDeEnsamblado(
                    f"'{mnem}': no se encontró valor para el campo '{nombre_c}'. "
                    f"Revisa el mapeo de operandos.", n_linea)

            # Ancho de resolución: si hay orden_bits personalizado, usar el
            # bit más alto referenciado + 1 (ancho del inmediato completo)
            natural = {str(i): i for i in range(bits_c)}
            if orden != natural and orden:
                bits_resolucion = max(int(k) for k in orden.keys()) + 1
            else:
                bits_resolucion = bits_c

            valor_bin = self._resolver_operando(
                op_raw, nombre_c, tipo_c, bits_resolucion, pc, n_linea, mnem)

            valor_bin = self._aplicar_orden_bits(
                valor_bin, bits_c, orden, nombre_c, n_linea, mnem)

            partes.append(valor_bin)

        # Concatenar según dirección de lectura
        if lectura == "lsb_primero":
            # Primer campo = bits menos significativos → va a la derecha
            palabra = "".join(reversed(partes))
        else:
            # msb_primero: primer campo = bits más significativos → va a la izquierda
            palabra = "".join(partes)

        if len(palabra) != bits_totales:
            raise ErrorDeEnsamblado(
                f"'{mnem}': la instrucción generó {len(palabra)} bits, "
                f"se esperaban {bits_totales}", n_linea)

        return palabra

    # ─────────────────────────────────────────────
    #  RESOLVER OPERANDO
    # ─────────────────────────────────────────────

    def _resolver_operando(self, op_raw, nombre_campo, tipo_campo, bits, pc, n_linea, mnem):
        """
        Convierte un operando textual en su representación binaria.
        El 'tipo_campo' ("registro" | "inmediato") determina qué se acepta:
          - registro: solo registros (con prefijo o alias). Rechaza números/etiquetas.
          - inmediato: solo números o etiquetas. Rechaza registros.
        """
        op = op_raw.strip()

        # Resolver alias de registro (sp→x2, etc.) definidos por el usuario
        es_alias = op.lower() in self._alias

        if tipo_campo == "registro":
            if es_alias:
                op = self._alias[op.lower()]
            match_reg = re.match(
                rf'^{re.escape(self._prefijo)}(\d+)$', op, re.IGNORECASE) \
                if self._prefijo else None
            if match_reg:
                n = int(match_reg.group(1))
                if self._n_regs and n >= self._n_regs:
                    raise ErrorDeEnsamblado(
                        f"'{mnem}': registro '{op}' fuera de rango "
                        f"(máximo {self._n_regs - 1})", n_linea)
                return self._int_a_bin(n, bits, n_linea, mnem, op)
            raise ErrorDeEnsamblado(
                f"'{mnem}': el campo '{nombre_campo}' espera un registro, "
                f"pero se recibió '{op_raw}'", n_linea)

        # tipo_campo == "inmediato"
        # Un registro o alias en un campo inmediato es un error
        if es_alias:
            raise ErrorDeEnsamblado(
                f"'{mnem}': el campo '{nombre_campo}' espera un valor inmediato, "
                f"pero se recibió un registro ('{op_raw}')", n_linea)
        if self._prefijo and re.match(
                rf'^{re.escape(self._prefijo)}\d+$', op, re.IGNORECASE):
            raise ErrorDeEnsamblado(
                f"'{mnem}': el campo '{nombre_campo}' espera un valor inmediato, "
                f"pero se recibió un registro ('{op_raw}')", n_linea)

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
            f"'{mnem}': no se pudo interpretar el operando '{op_raw}' "
            f"para el campo '{nombre_campo}'", n_linea)

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
