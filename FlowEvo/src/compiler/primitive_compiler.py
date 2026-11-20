"""Conservative executable primitive compilation from successful traces."""

from __future__ import annotations

import ast
import hashlib
import re
from dataclasses import dataclass

from compiler.compiler import Compiler
from core.schemas import ExecutionTrace, PrimitiveCard


@dataclass(frozen=True)
class PrimitiveCandidate:
    card: PrimitiveCard
    code: str


class PrimitiveCompiler:
    """Extract replayable helper-level primitives from successful artifacts."""

    def __init__(self) -> None:
        self._skill_compiler = Compiler()

    def _safe_task_id(self, task_id: str) -> str:
        return re.sub(r"[^A-Za-z0-9_]+", "_", task_id)

    def _select_skill_source(self, trace: ExecutionTrace) -> str:
        attempt = self._skill_compiler._select_passing_attempt(trace)
        return self._skill_compiler._build_skill_source(trace, attempt.candidate_code)

    def _extract_entry_point(self, source: str) -> str:
        return self._skill_compiler._extract_entry_point(source)

    def _extract_literal_replay_cases(self, executed_code: str, entry_point: str) -> list[tuple[list[object], object]]:
        return self._skill_compiler._extract_literal_replay_cases(executed_code, entry_point)

    def _infer_target_entry_point(self, trace: ExecutionTrace, source: str) -> str:
        if trace.validated_entry_point:
            return trace.validated_entry_point
        executed_code = ""
        if trace.verifier_feedback:
            executed_code = trace.verifier_feedback[-1].executed_code or ""
        match = re.search(r"assert\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", executed_code)
        if match:
            return match.group(1)
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return self._extract_entry_point(source)
        functions = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
        if functions:
            return functions[-1]
        return self._extract_entry_point(source)

    def _called_names(self, function_node: ast.FunctionDef) -> set[str]:
        names: set[str] = set()
        for node in ast.walk(function_node):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                names.add(node.func.id)
        return names

    def _reachable_helpers(self, tree: ast.Module, entry_point: str) -> list[ast.FunctionDef]:
        functions = {
            node.name: node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
        }
        root = functions.get(entry_point)
        if root is None:
            return []
        direct_helpers = sorted(name for name in self._called_names(root) if name in functions and name != entry_point)
        selected: list[ast.FunctionDef] = []
        seen: set[str] = set()
        for helper_name in direct_helpers:
            stack = [helper_name]
            while stack:
                current_name = stack.pop()
                if current_name in seen or current_name == entry_point:
                    continue
                helper = functions.get(current_name)
                if helper is None:
                    continue
                seen.add(current_name)
                selected.append(helper)
                for called_name in self._called_names(helper):
                    if called_name in functions and called_name not in seen:
                        stack.append(called_name)
        selected.sort(key=lambda node: node.name)
        return selected

    def _primitive_id(self, trace: ExecutionTrace, helper_name: str, code: str) -> str:
        digest = hashlib.sha256(code.encode("utf-8")).hexdigest()[:10]
        task_pattern = self._safe_task_id(trace.task_pattern or "unknown")
        return f"primitive_{trace.benchmark}_{task_pattern}_{helper_name}_{digest}"

    def compile_success_primitives(self, trace: ExecutionTrace) -> list[PrimitiveCandidate]:
        if not trace.success:
            return []
        try:
            source = self._select_skill_source(trace)
            tree = ast.parse(source)
        except Exception:  # noqa: BLE001
            return []

        entry_point = self._infer_target_entry_point(trace, source)
        if trace.validated_entry_point:
            from failure_evo.skill_runtime import check_source
            try:
                check_source(source)
            except (ValueError, SyntaxError):
                return []
        helper_nodes = self._reachable_helpers(tree, entry_point)
        # A declared top-level parameterized operation is not required to be a
        # helper. Preserve the complete original module/SHA for this path.
        explicit = trace.operation_contracts.get(entry_point, {})
        entry_node = next((n for n in reversed(tree.body) if isinstance(n, ast.FunctionDef) and n.name == entry_point), None)
        if trace.validated_entry_point and explicit and entry_node is not None:
            exact = trace.attempts[-1].candidate_code if trace.attempts else trace.code_history[-1]
            check_source(exact)
            card = PrimitiveCard(
                executable_dependencies=trace.executable_dependencies,
                independent_source_ids=trace.independent_source_ids or [trace.task_id],
                operation_contracts=trace.operation_contracts,
                validation_status='source_verified_dependency_checked',
                source_sha256=hashlib.sha256(exact.encode()).hexdigest(),
                primitive_id=self._primitive_id(trace, entry_point, exact),
                name=entry_point+'_operation', description=str(explicit.get('purpose', entry_point)),
                benchmark=trace.benchmark, task_pattern=trace.task_pattern,
                helper_name=entry_point,target_entry_point=entry_point,
                signature={'helper_name':entry_point,'target_entry_point':entry_point,
                           'args':[a.arg for a in entry_node.args.args]},
                source_trace_ids=[trace.trace_id],source_skill_ids=[],support_count=1,utility=0.5,status='draft')
            return [PrimitiveCandidate(card=card, code=exact)]
        if not helper_nodes:
            return []

        imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
        candidates: list[PrimitiveCandidate] = []
        for helper in helper_nodes[:2]:
            helper_closure = [node for node in helper_nodes if node.name == helper.name or node.name in self._called_names(helper)]
            # New explicit-entry path preserves the complete dependency closure,
            # including constants and transitive helpers. Legacy extraction is unchanged.
            if trace.validated_entry_point:
                functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
                names, todo = set(), [helper.name]
                while todo:
                    name = todo.pop()
                    if name in names:
                        continue
                    names.add(name)
                    todo.extend(n.id for n in ast.walk(functions[name]) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id in functions)
                if entry_point in names:
                    continue  # A reusable helper may not depend on the task entry.
                constants = [n for n in tree.body if isinstance(n, (ast.Assign, ast.AnnAssign))]
                module = ast.Module(body=[*imports, *constants, *[functions[n] for n in sorted(names)]], type_ignores=[])
            else:
                module = ast.Module(body=[*imports, *helper_closure], type_ignores=[])
            ast.fix_missing_locations(module)
            try:
                code = ast.unparse(module).rstrip() + "\n"
                if trace.validated_entry_point:check_source(code)
            except Exception:  # noqa: BLE001
                continue
            replay_cases = self._extract_literal_replay_cases(
                trace.verifier_feedback[-1].executed_code if trace.verifier_feedback else "",
                entry_point,
            )
            task_pattern = trace.task_pattern or self._skill_compiler._infer_task_pattern(
                trace,
                entry_point=entry_point,
                replay_cases=replay_cases,
            )
            primitive_id = self._primitive_id(trace, helper.name, code)
            card = PrimitiveCard(
                executable_dependencies=trace.executable_dependencies,
                independent_source_ids=trace.independent_source_ids or [trace.task_id],
                operation_contracts=trace.operation_contracts,
                validation_status="source_verified_dependency_checked" if trace.validated_entry_point else "legacy",
                source_sha256=hashlib.sha256(code.encode()).hexdigest(),
                primitive_id=primitive_id,
                name=f"{helper.name}_primitive",
                description=f"Compiled helper primitive {helper.name} for {trace.benchmark}/{trace.task_pattern}.",
                benchmark=trace.benchmark,
                task_pattern=task_pattern,
                helper_name=helper.name,
                target_entry_point=entry_point,
                signature={
                    "helper_name": helper.name,
                    "target_entry_point": entry_point,
                    "args": [arg.arg for arg in helper.args.args],
                },
                source_trace_ids=[trace.trace_id],
                source_skill_ids=[trace.selected_skill_id] if trace.selected_skill_id else [],
                support_count=1,
                utility=0.5,
                status="draft",
            )
            candidates.append(PrimitiveCandidate(card=card, code=code))
        return candidates
