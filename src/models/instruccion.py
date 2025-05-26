class Instruccion:

    
    def __init__(self, mnemonico: str, nombre: str, descripcion: str, regex: str,
                 sintaxis: str, const: list[list[str]], var_rel: list[list[str]]):
        self.mnemonico = mnemonico
        self.nombre = nombre
        self.descripcion = descripcion
        self.regex = regex
        self.sintaxis = sintaxis
        self.const = const  # Lista de listas de Strings
        self.var_rel = var_rel  # Lista de listas de Strings0

    def toDict(self):
        return {
            "Mnemonico": self.mnemonico,
            "Nombre": self.nombre,
            "Descripcion": self.descripcion,
            "regex": self.regex,
            "Sintaxis": self.sintaxis,
            "Constantes": self.const,
            "Variables relacionadas": self.var_rel
        }

    def __str__(self):
        return (f"Instrucción: {self.nombre} ({self.mnemonico})\n"
                f"Descripción: {self.descripcion}\n"
                f"Regex: {self.regex}\n"
                f"Sintaxis: {self.sintaxis}\n"
                f"Constantes: {len(self.const)} listas\n"
                f"Variables Relacionadas: {len(self.var_rel)} listas")