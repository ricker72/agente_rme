from __future__ import annotations

import re
from typing import List, Optional

from .lua_ast import (
    Assignment,
    Block,
    FunctionCall,
    IfStatement,
    ForLoop,
    Literal,
    RawExpression,
    Variable,
)


class ParseError(Exception):
    pass


class LuaParser:
    ASSIGNMENT_RE = re.compile(r"^(local\s+)?(.+?)=(.+)$")
    IF_RE = re.compile(r"^if\s+(.+?)\s+then$")
    FOR_RE = re.compile(r"^for\s+(\w+)\s*=\s*(.+?)\s*,\s*(.+?)(?:\s*,\s*(.+?))?\s*do$")
    FUNCTION_CALL_RE = re.compile(
        r"^(?P<receiver>[\w\.]+)(?P<op>[:\.])(?P<name>\w+)\s*\((?P<args>.*)\)$"
    )

    def parse(self, source: str) -> Block:
        root = Block()
        stack: List[Block] = [root]

        for raw_line in source.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("--"):
                continue
            if line.startswith("end"):
                if len(stack) > 1:
                    stack.pop()
                    continue
                raise ParseError("Unmatched end")
            if line == "else":
                if len(stack) < 2:
                    raise ParseError("Unexpected else without matching if")
                parent_block = stack[-2]
                last_stmt = (
                    parent_block.statements[-1] if parent_block.statements else None
                )
                if not isinstance(last_stmt, IfStatement):
                    raise ParseError("Else without matching if statement")
                last_stmt.else_body = Block()
                stack.pop()
                stack.append(last_stmt.else_body)
                continue
            if (if_match := self.IF_RE.match(line)) is not None:
                condition = self.parse_expression(if_match.group(1).strip())
                if_node = IfStatement(condition=condition)
                stack[-1].statements.append(if_node)
                stack.append(if_node.then_body)
                continue
            if (for_match := self.FOR_RE.match(line)) is not None:
                variable = for_match.group(1)
                start = self.parse_expression(for_match.group(2).strip())
                end = self.parse_expression(for_match.group(3).strip())
                step_text = for_match.group(4)
                step = self.parse_expression(step_text.strip()) if step_text else None
                for_node = ForLoop(variable=variable, start=start, end=end, step=step)
                stack[-1].statements.append(for_node)
                stack.append(for_node.body)
                continue
            if "function(" in line:
                statement = self.parse_statement(line)
                if isinstance(statement, FunctionCall):
                    statement.body = Block()
                    stack[-1].statements.append(statement)
                    stack.append(statement.body)
                else:
                    stack[-1].statements.append(statement)
                continue
            if (assign_match := self.ASSIGNMENT_RE.match(line)) is not None:
                is_local = bool(assign_match.group(1))
                targets = [
                    self.parse_expression(t.strip())
                    for t in self.split_comma_aware(assign_match.group(2).strip())
                ]
                values = [
                    self.parse_expression(v.strip())
                    for v in self.split_comma_aware(assign_match.group(3).strip())
                ]
                assignment = Assignment(
                    targets=targets, values=values, is_local=is_local
                )
                stack[-1].statements.append(assignment)
                continue
            statement = self.parse_statement(line)
            stack[-1].statements.append(statement)

        if len(stack) != 1:
            raise ParseError("Unclosed block detected")
        return root

    def parse_statement(self, text: str):
        expression = self.parse_expression(text)
        if isinstance(expression, FunctionCall):
            return expression
        return RawExpression(text)

    def parse_expression(self, text: str):
        text = text.strip()
        if not text:
            return RawExpression(text)
        if text[0] in ('"', "'") and text[-1] == text[0]:
            return Literal(text[1:-1])
        if self.is_integer(text):
            return Literal(int(text))
        if self.is_float(text):
            return Literal(float(text))
        if (func_match := self.FUNCTION_CALL_RE.match(text)) is not None:
            receiver = Variable(func_match.group("receiver"))
            name = func_match.group("name")
            op = func_match.group("op")
            args = [
                self.parse_expression(arg.strip())
                for arg in self.split_comma_aware(func_match.group("args").strip())
                if arg.strip()
            ]
            return FunctionCall(
                receiver=receiver, name=name, args=args, is_method=op == ":"
            )
        if any(ch in text for ch in " +-*/%<>=!()") or " " in text:
            return RawExpression(text)
        return Variable(text)

    @staticmethod
    def is_integer(text: str) -> bool:
        return text.isdigit() or (text.startswith("-") and text[1:].isdigit())

    @staticmethod
    def is_float(text: str) -> bool:
        try:
            float(text)
            return "." in text or "e" in text.lower()
        except ValueError:
            return False

    @staticmethod
    def split_comma_aware(text: str) -> List[str]:
        parts: List[str] = []
        current = []
        depth = 0
        quote: Optional[str] = None
        escape = False

        for char in text:
            if escape:
                current.append(char)
                escape = False
                continue
            if quote:
                current.append(char)
                if char == quote:
                    quote = None
                elif char == "\\":
                    escape = True
                continue
            if char in ('"', "'"):
                quote = char
                current.append(char)
                continue
            if char == "(":
                depth += 1
            elif char == ")":
                depth = max(depth - 1, 0)
            if char == "," and depth == 0:
                parts.append("".join(current).strip())
                current = []
                continue
            current.append(char)

        final = "".join(current).strip()
        if final:
            parts.append(final)
        return parts
