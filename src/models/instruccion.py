# src/models/instruccion.py

class Instruccion:
    def __init__(self, mnemonico: str, nombre: str, descripcion: str, regex: str,
                 sintaxis: str, const: list[list[str]], var_rel: list[list[str]]):
        self.mnemonico = mnemonico
        self.nombre = nombre
        self.descripcion = descripcion
        self.regex = regex
        self.sintaxis = sintaxis
        # Estas son listas de listas, útiles para validaciones complejas
        self.const = const
        self.var_rel = var_rel

    def toDict(self):
        """Convierte el objeto en un diccionario para guardarlo en JSON"""
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
                f"Sintaxis: {self.sintaxis}")