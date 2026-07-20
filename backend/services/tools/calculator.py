import ast
import math
import operator
import time

from .base import Tool, ToolResult


class CalculatorTool(Tool):
    name = "calculator"
    description = "Safely evaluate mathematical expressions including basic math, trigonometry, and logarithms."
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematical expression to evaluate",
            },
        },
        "required": ["expression"],
    }

    SAFE_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    SAFE_FUNCTIONS = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "atan2": math.atan2,
        "log": math.log,
        "log2": math.log2,
        "log10": math.log10,
        "exp": math.exp,
        "pow": math.pow,
        "ceil": math.ceil,
        "floor": math.floor,
        "factorial": math.factorial,
        "gcd": math.gcd,
        "radians": math.radians,
        "degrees": math.degrees,
        "pi": math.pi,
        "e": math.e,
        "tau": math.tau,
        "inf": math.inf,
    }

    async def execute(self, expression: str, **kwargs) -> ToolResult:
        start = time.monotonic()
        try:
            if not expression.strip():
                return ToolResult(
                    success=False,
                    output=None,
                    error="Expression cannot be empty",
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

            if len(expression) > 1000:
                return ToolResult(
                    success=False,
                    output=None,
                    error="Expression too long (max 1000 characters)",
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

            try:
                tree = ast.parse(expression, mode="eval")
            except SyntaxError:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Invalid expression syntax: {expression}",
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

            result = self._eval_node(tree.body)

            duration = int((time.monotonic() - start) * 1000)

            if isinstance(result, float):
                if result == int(result) and not math.isinf(result):
                    result = int(result)

            return ToolResult(
                success=True,
                output={"result": result, "expression": expression},
                duration_ms=duration,
                metadata={"type": type(result).__name__},
            )
        except ZeroDivisionError:
            return ToolResult(
                success=False,
                output=None,
                error="Division by zero",
                duration_ms=int((time.monotonic() - start) * 1000),
            )
        except ValueError as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"Math error: {e}",
                duration_ms=int((time.monotonic() - start) * 1000),
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
                duration_ms=int((time.monotonic() - start) * 1000),
            )

    def _eval_node(self, node: ast.AST):
        if isinstance(node, ast.Expression):
            return self._eval_node(node.body)
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float, complex)):
                return node.value
            raise ValueError(f"Unsupported constant type: {type(node.value).__name__}")
        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in self.SAFE_OPERATORS:
                raise ValueError(f"Unsupported operator: {op_type.__name__}")
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            if op_type == ast.Pow and (isinstance(right, float) and right > 1000):
                raise ValueError("Exponent too large")
            if op_type in (ast.Div, ast.FloorDiv) and right == 0:
                raise ZeroDivisionError("Division by zero")
            return self.SAFE_OPERATORS[op_type](left, right)
        elif isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in self.SAFE_OPERATORS:
                raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
            operand = self._eval_node(node.operand)
            return self.SAFE_OPERATORS[op_type](operand)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in self.SAFE_FUNCTIONS:
                    func = self.SAFE_FUNCTIONS[func_name]
                    args = [self._eval_node(arg) for arg in node.args]
                    kwargs = {kw.arg: self._eval_node(kw.value) for kw in node.keywords}
                    return func(*args, **kwargs)
                raise ValueError(f"Unknown function: {func_name}")
            raise ValueError("Unsupported function call")
        elif isinstance(node, ast.Name):
            if node.id in self.SAFE_FUNCTIONS:
                val = self.SAFE_FUNCTIONS[node.id]
                if isinstance(val, (int, float)):
                    return val
                raise ValueError(f"'{node.id}' is a function, not a constant")
            raise ValueError(f"Unknown variable: {node.id}")
        else:
            raise ValueError(f"Unsupported expression type: {type(node).__name__}")


calculator_tool = CalculatorTool()
