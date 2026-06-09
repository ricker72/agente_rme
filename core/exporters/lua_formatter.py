"""
Lua Formatter — normaliza indentación, saltos de línea y espacios en
código Lua generado.

Asegura que todo script Lua generado siga el estilo consistente del
proyecto OpenTibiaBR RME.
"""

from __future__ import annotations

import re
from typing import List


class LuaFormatter:
    """
    Normaliza código Lua generado.

    Reglas:
        1. Indentación consistente (4 espacios por nivel)
        2. Sin espacios al final de línea
        3. Saltos de línea UNIX (\\n)
        4. Línea final en blanco
        5. Espacios alrededor de operadores binarios (=, +, etc.)

    Usage:
        formatter = LuaFormatter()
        clean_code = formatter.format(raw_code)
    """

    def format(self, lua_code: str) -> str:
        """
        Normaliza código Lua.

        Args:
            lua_code: Código Lua sin formatear.

        Returns:
            Código formateado.
        """
        if not lua_code:
            return ""

        # Normalizar saltos de línea a UNIX
        lua_code = lua_code.replace("\r\n", "\n").replace("\r", "\n")

        # Eliminar espacios al final de cada línea
        lines = [line.rstrip() for line in lua_code.split("\n")]

        # Reconstruir con indentación estándar
        formatted = self._reindent(lines)

        # Asegurar línea final
        formatted = formatted.rstrip("\n") + "\n"

        return formatted

    def _reindent(self, lines: List[str]) -> str:
        """
        Re-indenta líneas de código basado en palabras clave.

        Incrementa indentación después de:
            - for ... do, while ... do, repeat
            - function(...), if ... then, else
            - app.transaction(function(map)
            - then

        Decrementa indentación antes de:
            - end, end), until
            - else, elseif
        """
        result: List[str] = []
        indent_level = 0

        for line in lines:
            stripped = line.strip()

            if not stripped:
                result.append("")
                continue

            # Comentarios se mantienen sin cambios de indentación
            if stripped.startswith("--"):
                result.append("    " * indent_level + stripped)
                continue

            # Palabras clave que decrementan indentación
            if any(stripped.startswith(kw) for kw in ["end", "until", "else", "elseif"]):
                indent_level = max(0, indent_level - 1)

            # Aplicar indentación actual
            result.append("    " * indent_level + stripped)

            # Palabras clave que incrementan indentación
            if any(kw in stripped for kw in ["do$", "then$", "function("]):
                indent_level += 1
            elif stripped.startswith("for ") and stripped.endswith(" do"):
                indent_level += 1
            elif stripped.startswith("if ") and stripped.endswith(" then"):
                indent_level += 1
            elif stripped.startswith("while ") and stripped.endswith(" do"):
                indent_level += 1
            elif stripped == "repeat":
                indent_level += 1
            elif stripped.startswith("app.transaction("):
                indent_level += 1

        return "\n".join(result)