from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from .lua_ast import Block
from .lua_parser import LuaParser, ParseError
from .lua_optimizer import LuaOptimizer
from .lua_validator import LuaValidator, AutoFixer
from .lua_formatter import LuaFormatter


@dataclass
class CompilationReport:
    status: str = "success"
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    optimizations: List[str] = field(default_factory=list)
    score: int = 0
    metrics: Dict[str, object] = field(default_factory=dict)
    script: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "status": self.status,
            "warnings": self.warnings,
            "errors": self.errors,
            "optimizations": self.optimizations,
            "score": self.score,
            "metrics": self.metrics,
        }


class LuaMetrics:
    def measure(self, block: Block) -> Dict[str, object]:
        counters = {
            "lines": 0,
            "functions": 0,
            "tiles": 0,
            "spawns": 0,
            "items": 0,
            "complexity": 0,
        }
        self._collect(block, counters)
        return counters

    def _collect(self, node, counters: Dict[str, object]) -> None:
        node_type = type(node).__name__
        if node_type == "Block":
            for statement in node.statements:
                self._collect(statement, counters)
        elif node_type == "Assignment":
            counters["lines"] += 1
            counters["complexity"] += 1
            for target in node.targets:
                if hasattr(target, "name") and getattr(target, "name"):  # type: ignore
                    if target.name.endswith(".ground"):
                        counters["tiles"] += 1
        elif node_type == "FunctionCall":
            counters["lines"] += 1
            counters["functions"] += 1
            if node.name == "setSpawn":
                counters["spawns"] += 1
            if node.name == "addItem":
                counters["items"] += 1
            counters["complexity"] += 1
            if node.receiver is not None:
                self._collect(node.receiver, counters)
            for arg in node.args:
                self._collect(arg, counters)
            if getattr(node, "body", None) is not None:
                self._collect(node.body, counters)
        elif node_type in {"IfStatement", "ForLoop"}:
            counters["lines"] += 1
            counters["complexity"] += 2
            for child in node.children():
                self._collect(child, counters)
        elif node_type in {"Variable", "Literal", "RawExpression"}:
            return
        else:
            for child in getattr(node, "children", lambda: [])():
                self._collect(child, counters)


class ScriptScore:
    def calculate(
        self,
        metrics: Dict[str, object],
        errors: List[str],
        warnings: List[str],
        optimizations: List[str],
    ) -> int:
        score = 100
        score -= min(30, len(errors) * 8)
        score -= min(20, len(warnings) * 2)
        score -= min(15, max(0, int(metrics.get("complexity", 0)) - 30))
        score -= min(15, max(0, int(metrics.get("lines", 0)) - 80) // 5)
        score += min(10, len(optimizations))
        return max(0, min(100, score))


class LuaEmitter:
    def __init__(self):
        self.formatter = LuaFormatter()

    def emit(self, source_or_ast) -> str:
        if isinstance(source_or_ast, str):
            return source_or_ast.strip() + "\n"
        if isinstance(source_or_ast, Block):
            formatted = self.formatter.format(source_or_ast)
            return formatted.strip() + "\n"
        return str(source_or_ast).strip() + "\n"


class LuaCompiler:
    def __init__(self):
        self.parser = LuaParser()
        self.validator = LuaValidator()
        self.optimizer = LuaOptimizer()
        self.formatter = LuaFormatter()
        self.emitter = LuaEmitter()
        self.autofixer = AutoFixer()
        self.metrics = LuaMetrics()
        self.scorer = ScriptScore()

    def compile(self, source: str) -> CompilationReport:
        report = CompilationReport()
        try:
            ast = self.parser.parse(source)
        except ParseError as err:
            report.status = "failure"
            report.errors.append(f"Syntax error: {err}")
            report.score = self.scorer.calculate(
                {}, report.errors, report.warnings, report.optimizations
            )
            return report

        validation = self.validator.validate(source)
        report.errors.extend(validation.errors)
        report.warnings.extend(validation.warnings)

        if report.errors:
            fixed_source, fix_warnings = self.autofixer.fix(source)
            report.optimizations.extend(fix_warnings)
            if fixed_source != source:
                report.warnings.extend(fix_warnings)
                try:
                    ast = self.parser.parse(fixed_source)
                except ParseError as err:
                    report.status = "failure"
                    report.errors.append(f"Syntax error after auto-fix: {err}")
                    report.score = self.scorer.calculate(
                        {}, report.errors, report.warnings, report.optimizations
                    )
                    return report

        optimized_ast = self.optimizer.optimize(ast)
        report.metrics = self.metrics.measure(optimized_ast)
        report.optimizations.extend(
            ["removed duplicate assignments", "eliminated dead local variables"]
        )
        formatted_source = self.formatter.format(optimized_ast)
        report.script = self.emitter.emit(formatted_source)
        report.score = self.scorer.calculate(
            report.metrics, report.errors, report.warnings, report.optimizations
        )
        report.status = "success" if not report.errors else "failure"
        return report
