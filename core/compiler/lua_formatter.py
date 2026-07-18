from __future__ import annotations

from typing import List

from .lua_ast import (
    Assignment,
    Block,
    FunctionCall,
    IfStatement,
    ForLoop,
    Literal,
    RawExpression,
    Variable,
    LuaStatement,
    LuaExpression,
)


class LuaFormatter:
    INDENT = "    "

    def format(self, block: Block) -> str:
        lines: List[str] = []
        self._format_block(block, lines, 0)
        return "\n".join(lines)

    def _format_block(self, block: Block, lines: List[str], indent_level: int) -> None:
        for statement in block.statements:
            self._format_statement(statement, lines, indent_level)

    def _format_statement(
        self, statement: LuaStatement, lines: List[str], indent_level: int
    ) -> None:
        prefix = self.INDENT * indent_level
        if isinstance(statement, Assignment):
            targets = ", ".join(self._format_expression(t) for t in statement.targets)
            values = ", ".join(self._format_expression(v) for v in statement.values)
            keyword = "local " if statement.is_local else ""
            lines.append(f"{prefix}{keyword}{targets} = {values}")
        elif isinstance(statement, FunctionCall):
            lines.append(f"{prefix}{self._format_expression(statement)}")
            if statement.body is not None:
                self._format_block(statement.body, lines, indent_level + 1)
                lines.append(f"{prefix}end)")
        elif isinstance(statement, IfStatement):
            lines.append(
                f"{prefix}if {self._format_expression(statement.condition)} then"
            )
            self._format_block(statement.then_body, lines, indent_level + 1)
            if statement.else_body is not None:
                lines.append(f"{prefix}else")
                self._format_block(statement.else_body, lines, indent_level + 1)
            lines.append(f"{prefix}end")
        elif isinstance(statement, ForLoop):
            step = (
                f", {self._format_expression(statement.step)}"
                if statement.step is not None
                else ""
            )
            fmt_start = self._format_expression(statement.start)
            fmt_end = self._format_expression(statement.end)
            lines.append(
                f"{prefix}for {statement.variable} = {fmt_start}, {fmt_end}{step} do"
            )
            self._format_block(statement.body, lines, indent_level + 1)
            lines.append(f"{prefix}end")
        else:
            lines.append(f"{prefix}{self._format_expression(statement)}")

    def _format_expression(self, expression: LuaExpression) -> str:
        if isinstance(expression, Variable):
            return expression.name
        if isinstance(expression, Literal):
            if isinstance(expression.value, str):
                return f'"{expression.value}"'
            return str(expression.value)
        if isinstance(expression, RawExpression):
            return expression.source
        if isinstance(expression, FunctionCall):
            receiver = (
                self._format_expression(expression.receiver)
                if expression.receiver is not None
                else ""
            )
            operator = ":" if expression.is_method else "."
            args = ", ".join(self._format_expression(arg) for arg in expression.args)
            if receiver:
                return f"{receiver}{operator}{expression.name}({args})"
            return f"{expression.name}({args})"
        return str(expression)
