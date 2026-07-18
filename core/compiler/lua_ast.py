from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


class LuaNode:
    def children(self) -> List[LuaNode]:
        return []


class LuaExpression(LuaNode):
    pass


class LuaStatement(LuaNode):
    pass


@dataclass
class Variable(LuaExpression):
    name: str

    def children(self) -> List[LuaNode]:
        return []


@dataclass
class Literal(LuaExpression):
    value: object

    def children(self) -> List[LuaNode]:
        return []


@dataclass
class RawExpression(LuaExpression):
    source: str

    def children(self) -> List[LuaNode]:
        return []


@dataclass
class FunctionCall(LuaExpression, LuaStatement):
    receiver: Optional[LuaExpression]
    name: str
    args: List[LuaExpression] = field(default_factory=list)
    is_method: bool = False
    body: Optional[Block] = None

    def children(self) -> List[LuaNode]:
        children: List[LuaNode] = []
        if self.receiver is not None:
            children.append(self.receiver)
        children.extend(self.args)
        if self.body is not None:
            children.append(self.body)
        return children


@dataclass
class Assignment(LuaStatement):
    targets: List[LuaExpression] = field(default_factory=list)
    values: List[LuaExpression] = field(default_factory=list)
    is_local: bool = False

    def children(self) -> List[LuaNode]:
        return self.targets + self.values


@dataclass
class ForLoop(LuaStatement):
    variable: str
    start: LuaExpression
    end: LuaExpression
    step: Optional[LuaExpression]
    body: Block = field(default_factory=lambda: Block())

    def children(self) -> List[LuaNode]:
        children: List[LuaNode] = [self.start, self.end]
        if self.step is not None:
            children.append(self.step)
        children.append(self.body)
        return children


@dataclass
class IfStatement(LuaStatement):
    condition: LuaExpression
    then_body: Block = field(default_factory=lambda: Block())
    else_body: Optional[Block] = None

    def children(self) -> List[LuaNode]:
        children: List[LuaNode] = [self.condition, self.then_body]
        if self.else_body is not None:
            children.append(self.else_body)
        return children


@dataclass
class Block(LuaNode):
    statements: List[LuaStatement] = field(default_factory=list)

    def children(self) -> List[LuaNode]:
        return list(self.statements)
