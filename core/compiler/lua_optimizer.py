from __future__ import annotations

from typing import Set

from .lua_ast import (
    Assignment,
    Block,
    FunctionCall,
    IfStatement,
    ForLoop,
    Variable,
    Literal,
    RawExpression,
    LuaStatement,
    LuaExpression,
)


class LuaOptimizer:
    def optimize(self, block: Block) -> Block:
        block = self._optimize_block(block)
        self._eliminate_dead_locals(block)
        return block

    def _optimize_block(self, block: Block) -> Block:
        optimized = Block()
        last_assignment = {}
        seen_calls = set()

        for statement in block.statements:
            if isinstance(statement, Assignment):
                target_key = self._assignment_key(statement)
                if (
                    target_key
                    and target_key in last_assignment
                    and self._assignment_key(statement) == last_assignment[target_key]
                ):
                    continue
                if isinstance(statement, Assignment) and self._is_tile_ground_duplicate(
                    statement, optimized
                ):
                    continue
                last_assignment[target_key] = self._assignment_key(statement)
                optimized.statements.append(statement)
                continue
            if isinstance(statement, FunctionCall):
                if self._is_duplicate_add_item(statement, seen_calls):
                    continue
                seen_calls.add(self._call_key(statement))
                optimized.statements.append(statement)
                continue
            if isinstance(statement, ForLoop):
                statement.body = self._optimize_block(statement.body)
                if isinstance(statement.step, Literal) and statement.step.value == 1:
                    statement.step = None
                optimized.statements.append(statement)
                continue
            if isinstance(statement, IfStatement):
                statement.then_body = self._optimize_block(statement.then_body)
                if statement.else_body is not None:
                    statement.else_body = self._optimize_block(statement.else_body)
                optimized.statements.append(statement)
                continue
            optimized.statements.append(statement)

        return optimized

    def _assignment_key(self, assignment: Assignment) -> str:
        if len(assignment.targets) != 1 or len(assignment.values) != 1:
            return ""
        target = assignment.targets[0]
        value = assignment.values[0]
        return f"{self._expression_key(target)}={self._expression_key(value)}"

    def _expression_key(self, expression: LuaExpression) -> str:
        if isinstance(expression, Variable):
            return expression.name
        if isinstance(expression, Literal):
            return str(expression.value)
        if isinstance(expression, RawExpression):
            return expression.source
        if isinstance(expression, FunctionCall):
            args = ",".join(self._expression_key(arg) for arg in expression.args)
            receiver = (
                self._expression_key(expression.receiver) if expression.receiver else ""
            )
            return f"{receiver}{':' if expression.is_method else '.'}{expression.name}({args})"
        return repr(expression)

    def _is_tile_ground_duplicate(
        self, assignment: Assignment, optimized: Block
    ) -> bool:
        if len(assignment.targets) != 1 or len(assignment.values) != 1:
            return False
        target = assignment.targets[0]
        if not isinstance(target, Variable) or not target.name.endswith(".ground"):
            return False
        if not optimized.statements:
            return False
        last = optimized.statements[-1]
        if (
            isinstance(last, Assignment)
            and len(last.targets) == 1
            and isinstance(last.targets[0], Variable)
        ):
            return target.name == last.targets[0].name and self._expression_key(
                last.values[0]
            ) == self._expression_key(assignment.values[0])
        return False

    def _call_key(self, call: FunctionCall) -> str:
        receiver = self._expression_key(call.receiver) if call.receiver else ""
        args = ",".join(self._expression_key(arg) for arg in call.args)
        return f"{receiver}{':' if call.is_method else '.'}{call.name}({args})"

    def _is_duplicate_add_item(self, call: FunctionCall, seen_calls: Set[str]) -> bool:
        if call.name != "addItem" or not call.is_method:
            return False
        return self._call_key(call) in seen_calls

    def _eliminate_dead_locals(self, block: Block) -> None:
        used_names = self._collect_used_names(block)
        block.statements = [
            stmt
            for stmt in block.statements
            if not self._is_dead_local_assignment(stmt, used_names)
        ]
        for statement in block.statements:
            if isinstance(statement, ForLoop):
                self._eliminate_dead_locals(statement.body)
            elif isinstance(statement, IfStatement):
                self._eliminate_dead_locals(statement.then_body)
                if statement.else_body is not None:
                    self._eliminate_dead_locals(statement.else_body)

    def _collect_used_names(self, block: Block) -> Set[str]:
        used: Set[str] = set()
        for statement in block.statements:
            self._collect_names_from_statement(statement, used)
        return used

    def _collect_names_from_statement(
        self, statement: LuaStatement, used: Set[str]
    ) -> None:
        if isinstance(statement, Assignment):
            for value in statement.values:
                self._collect_names_from_expression(value, used)
        elif isinstance(statement, FunctionCall):
            if statement.receiver is not None:
                self._collect_names_from_expression(statement.receiver, used)
            for arg in statement.args:
                self._collect_names_from_expression(arg, used)
        elif isinstance(statement, ForLoop):
            self._collect_names_from_expression(statement.start, used)
            self._collect_names_from_expression(statement.end, used)
            if statement.step is not None:
                self._collect_names_from_expression(statement.step, used)
            self._collect_used_names(statement.body)
        elif isinstance(statement, IfStatement):
            self._collect_names_from_expression(statement.condition, used)
            self._collect_used_names(statement.then_body)
            if statement.else_body is not None:
                self._collect_used_names(statement.else_body)

    def _collect_names_from_expression(
        self, expression: LuaExpression, used: Set[str]
    ) -> None:
        if isinstance(expression, Variable):
            used.add(expression.name)
        elif isinstance(expression, FunctionCall):
            if expression.receiver is not None:
                self._collect_names_from_expression(expression.receiver, used)
            for arg in expression.args:
                self._collect_names_from_expression(arg, used)
        elif isinstance(expression, RawExpression):
            tokens = [
                token.strip()
                for token in expression.source.replace("(", " ")
                .replace(")", " ")
                .split()
                if token.strip()
            ]
            for token in tokens:
                if token.isidentifier():
                    used.add(token)

    def _is_dead_local_assignment(
        self, statement: LuaStatement, used_names: Set[str]
    ) -> bool:
        if not isinstance(statement, Assignment) or not statement.is_local:
            return False
        if len(statement.targets) != 1 or not isinstance(
            statement.targets[0], Variable
        ):
            return False
        if statement.targets[0].name not in used_names:
            if any(isinstance(value, FunctionCall) for value in statement.values):
                return False
            if any(
                isinstance(value, RawExpression) and "(" in value.source
                for value in statement.values
            ):
                return False
            return True
        return False
