"""
Lua Validator — valida código Lua generado contra reglas RME.

Antes de guardar, ejecuta:
    1. RMEValidator (forbidden APIs: Map.addItem, Position(, etc.)
    2. Reglas locales (header, transaction, brackets, spawns)

Si encuentra:
    Map.addItem
    Position(
    etc.

→ Export abortado
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from validators.rme_validator import validate as rme_validate, RMEValidationError


class LuaValidationResult:
    """Resultado de la validación de código Lua."""

    def __init__(self):
        self.passed: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.passed = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def __bool__(self) -> bool:
        return self.passed

    def summary(self) -> str:
        status = "PASSED" if self.passed else "FAILED"
        lines = [f"Lua validation: {status}"]
        if self.warnings:
            lines.append(f"  Warnings ({len(self.warnings)}):")
            for w in self.warnings:
                lines.append(f"    - {w}")
        if self.errors:
            lines.append(f"  Errors ({len(self.errors)}):")
            for e in self.errors:
                lines.append(f"    - {e}")
        return "\n".join(lines)


class LuaValidator:
    """
    Valida código Lua generado para compatibilidad con RME.

    Usage:
        validator = LuaValidator()
        result = validator.validate(lua_code)
        if result.passed:
            print("Lua code is valid")
    """

    def validate(self, lua_code: str) -> LuaValidationResult:
        """
        Valida código Lua contra reglas RME.

        Args:
            lua_code: Código Lua generado.

        Returns:
            LuaValidationResult con errores/warnings.
        """
        result = LuaValidationResult()

        if not lua_code or not lua_code.strip():
            result.add_error("Lua code is empty")
            return result

        # 1. Ejecutar RMEValidator (forbidden APIs)
        try:
            rme_validate(lua_code)
        except RMEValidationError as e:
            result.add_error(f"RME validation failed: {str(e)}")
            # No continuar si hay APIs prohibidas
            return result

        # 2. Reglas locales
        self._check_header(result, lua_code)
        self._check_transaction(result, lua_code)
        self._check_local_map(result, lua_code)
        self._check_forbidden_apis(result, lua_code)
        self._check_bracket_balance(result, lua_code)
        self._check_spawn_intervals(result, lua_code)
        self._check_creature_calls(result, lua_code)

        return result

    # ------------------------------------------------------------------
    # Validaciones locales
    # ------------------------------------------------------------------

    def _check_header(self, result: LuaValidationResult, lua_code: str) -> None:
        """Verifica que el script tenga el guard app.hasMap()."""
        if "app.hasMap()" not in lua_code:
            result.add_error("Script missing app.hasMap() guard")

    def _check_transaction(self, result: LuaValidationResult, lua_code: str) -> None:
        """Verifica app.transaction() presente."""
        if "app.transaction(" not in lua_code:
            result.add_error("Script missing app.transaction() call")

    def _check_local_map(self, result: LuaValidationResult, lua_code: str) -> None:
        """Verifica 'local map = app.map' presente."""
        if "local map = app.map" not in lua_code:
            result.add_warning("Script missing 'local map = app.map'")

    def _check_forbidden_apis(self, result: LuaValidationResult, lua_code: str) -> None:
        """Verifica APIs prohibidas adicionales."""
        forbidden_local = [
            (r"tile:addGround\b", "tile:addGround — use tile.ground = <id>"),
            (r"tile:setGround\b", "tile:setGround — use tile.ground = <id>"),
            (r"setGround\(", "setGround() — use tile.ground = <id>"),
            (r"addGround\(", "addGround() — use tile.ground = <id>"),
            (r"map\.setTile\b", "map:setTile — use map:getOrCreateTile"),
            (r"removeMap\b", "removeMap — forbidden"),
            (r"app\.createMap\b", "app:createMap — forbidden"),
        ]

        for pattern, message in forbidden_local:
            if re.search(pattern, lua_code, re.IGNORECASE):
                result.add_error(f"Forbidden API: {message}")

        # Verificar createTile suelto (no getOrCreateTile)
        for match in re.finditer(r'createTile', lua_code, re.IGNORECASE):
            start = match.start()
            preceding = lua_code[max(0, start - 5):start].lower()
            if 'getor' not in preceding and not preceding.endswith('or'):
                result.add_error(
                    "Forbidden API: bare 'createTile' — use map:getOrCreateTile()"
                )
                break

    def _check_bracket_balance(self, result: LuaValidationResult, lua_code: str) -> None:
        """Verifica paréntesis balanceados."""
        for name, open_c, close_c in [
            ("parentheses", "(", ")"),
            ("brackets", "[", "]"),
            ("braces", "{", "}"),
        ]:
            opens = lua_code.count(open_c)
            closes = lua_code.count(close_c)
            if opens != closes:
                result.add_error(
                    f"Unbalanced {name}: {opens} opening vs {closes} closing"
                )

    def _check_spawn_intervals(self, result: LuaValidationResult, lua_code: str) -> None:
        """Verifica intervalos de spawn positivos."""
        for match in re.finditer(r"setSpawn\((\d+)\)", lua_code):
            interval = int(match.group(1))
            if interval <= 0:
                result.add_warning(
                    f"Non-positive spawn interval: {interval}"
                )

    def _check_creature_calls(self, result: LuaValidationResult, lua_code: str) -> None:
        """Verifica nombres de criatura no vacíos."""
        for match in re.finditer(r"setCreature\('([^']*)'", lua_code):
            name = match.group(1)
            if not name.strip():
                result.add_warning(
                    f"Empty creature name at position {match.start()}"
                )


# Conveniencia
def validate_lua(lua_code: str) -> LuaValidationResult:
    validator = LuaValidator()
    return validator.validate(lua_code)