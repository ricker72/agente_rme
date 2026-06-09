from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from .lua_ast import (
    Assignment,
    Block,
    FunctionCall,
    IfStatement,
    ForLoop,
    Variable,
    Literal,
    RawExpression,
    LuaExpression,
)
from .lua_parser import LuaParser, ParseError


@dataclass
class ValidationResult:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    status: str = "success"


class RMECompatibilityChecker:
    WHITELIST = {
        "app.transaction",
        "app.hasMap",
        "map:getOrCreateTile",
        "tile.ground",
        "tile:addItem",
        "tile:borderize",
        "tile:setSpawn",
        "tile:setCreature",
        "noise.simplex",
        "geo.randomScatter",
        "Dialog",
        "math.abs",
        "app.setCameraPosition",
    }

    BLOCKED = {
        "Map.addItem",
        "Map.addCreature",
        "Position",
        "Game.createTile",
    }

    def check(self, call: FunctionCall) -> Tuple[Optional[str], Optional[str]]:
        full_name = f"{self._receiver_name(call.receiver)}{':' if call.is_method else '.'}{call.name}"
        if full_name in self.BLOCKED:
            return (f"Blocked API call detected: {full_name}", None)
        if full_name in self.WHITELIST:
            return (None, None)
        if call.receiver is not None and isinstance(call.receiver, Variable):
            receiver_name = call.receiver.name
            if receiver_name in {"math", "noise", "geo", "Direction", "app", "map", "tile"}:
                return (None, None)
        return (None, f"API call not on whitelist but appears safe: {full_name}")

    def _receiver_name(self, receiver: Optional[LuaExpression]) -> str:
        if receiver is None:
            return ""
        if isinstance(receiver, Variable):
            return receiver.name
        if isinstance(receiver, FunctionCall):
            return f"{self._receiver_name(receiver.receiver)}{':' if receiver.is_method else '.'}{receiver.name}"
        return ""


class AutoFixer:
    REPLACEMENTS = {
        r"\bMap\.addItem\b": "tile:addItem",
        r"\bMap\.addCreature\b": "tile:setCreature",
        r"\bGame\.createTile\b": "map:getOrCreateTile",
    }

    def fix(self, source: str) -> Tuple[str, List[str]]:
        warnings: List[str] = []
        fixed = source
        for pattern, replacement in self.REPLACEMENTS.items():
            if re.search(pattern, fixed):
                fixed = re.sub(pattern, replacement, fixed)
                warnings.append(f"Auto-fixed blocked API call: {pattern} -> {replacement}")
        return fixed, warnings


class LuaValidator:
    def __init__(self):
        self.parser = LuaParser()
        self.compat_checker = RMECompatibilityChecker()

    def validate(self, source: str) -> ValidationResult:
        result = ValidationResult()
        try:
            ast = self.parser.parse(source)
        except ParseError as err:
            result.errors.append(f"Syntax error: {err}")
            result.status = "failure"
            return result

        self._validate_block(ast, result)
        if result.errors:
            result.status = "failure"
        return result

    def _validate_block(self, block: Block, result: ValidationResult, declared: Optional[Set[str]] = None, tile_vars: Optional[Set[str]] = None) -> None:
        if declared is None:
            declared = set()
        if tile_vars is None:
            tile_vars = set()

        for statement in block.statements:
            if isinstance(statement, Assignment):
                self._validate_assignment(statement, result, declared, tile_vars)
            elif isinstance(statement, FunctionCall):
                self._validate_function_call(statement, result, declared, tile_vars)
            elif isinstance(statement, ForLoop):
                self._validate_expression(statement.start, result, declared)
                self._validate_expression(statement.end, result, declared)
                if statement.step is not None:
                    self._validate_expression(statement.step, result, declared)
                self._validate_block(statement.body, result, declared.copy(), tile_vars.copy())
            elif isinstance(statement, IfStatement):
                self._validate_expression(statement.condition, result, declared)
                self._validate_block(statement.then_body, result, declared.copy(), tile_vars.copy())
                if statement.else_body is not None:
                    self._validate_block(statement.else_body, result, declared.copy(), tile_vars.copy())

    def _validate_assignment(self, assignment: Assignment, result: ValidationResult, declared: Set[str], tile_vars: Set[str]) -> None:
        for value in assignment.values:
            self._validate_expression(value, result, declared)
        for target in assignment.targets:
            if isinstance(target, Variable):
                if assignment.is_local:
                    name = target.name
                    declared.add(name)
                    if self._is_tile_factory_assignment(assignment):
                        tile_vars.add(name)
                if target.name.endswith(".ground"):
                    root_name = target.name.split(".", 1)[0]
                    if root_name not in tile_vars and root_name not in declared:
                        result.warnings.append(f"Possible null tile assignment: {target.name}")

    def _validate_function_call(self, call: FunctionCall, result: ValidationResult, declared: Set[str], tile_vars: Set[str]) -> None:
        if call.receiver is not None:
            self._validate_expression(call.receiver, result, declared)
        for arg in call.args:
            self._validate_expression(arg, result, declared)
        error, warning = self.compat_checker.check(call)
        if error:
            result.errors.append(error)
        elif warning:
            result.warnings.append(warning)
        if call.receiver is not None and isinstance(call.receiver, Variable):
            if call.receiver.name not in declared and call.receiver.name not in tile_vars and call.receiver.name not in {"map", "app", "math", "noise", "geo", "Direction"}:
                result.warnings.append(f"Use of undeclared variable or possible null receiver: {call.receiver.name}")

    def _validate_expression(self, expression: LuaExpression, result: ValidationResult, declared: Set[str]) -> None:
        if isinstance(expression, Variable):
            if expression.name not in declared and expression.name not in {"map", "app", "math", "noise", "geo", "Direction", "x", "y", "z", "dx", "dy", "baseX", "baseY", "bossTile", "spawnCenter", "frazz", "cloak"}:
                if "." not in expression.name and not expression.name.isnumeric():
                    result.warnings.append(f"Possible undeclared variable: {expression.name}")
        elif isinstance(expression, FunctionCall):
            self._validate_function_call(expression, result, declared, set())
        elif isinstance(expression, RawExpression):
            if "Position" in expression.source or "Game.createTile" in expression.source:
                result.errors.append(f"Blocked or invalid syntax detected in expression: {expression.source}")
                return
            for token in re.findall(r'\b[A-Za-z_]\w*(?:\.\w+)*\b', expression.source):
                if token in {"function", "then", "else", "end", "local", "return", "do", "not"}:
                    continue
                if token in {"map", "app", "math", "noise", "geo", "Direction", "x", "y", "z", "dx", "dy", "baseX", "baseY", "bossTile", "spawnCenter", "frazz", "cloak"}:
                    continue
                root_name = token.split('.', 1)[0]
                if root_name in {"app", "map", "math", "noise", "geo", "Direction"}:
                    continue
                if token not in declared:
                    result.warnings.append(f"Possible undeclared variable: {token}")

    def _is_tile_factory_assignment(self, assignment: Assignment) -> bool:
        if not assignment.values or not isinstance(assignment.values[0], FunctionCall):
            return False
        call = assignment.values[0]
        receiver_name = self.compat_checker._receiver_name(call.receiver)
        return receiver_name == "map" and call.name == "getOrCreateTile"
