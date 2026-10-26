"""A small exact recursive-descent parser for linear equations."""

from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction

from gauss_visualizer.core.fraction_utils import parse_fraction
from gauss_visualizer.core.normalizer import TextNormalizer


@dataclass(frozen=True)
class ParseResult:
    success: bool
    coefficients: tuple[Fraction, ...]
    constant: Fraction
    error: str | None = None
    error_pos: int | None = None
    variables: tuple[str, ...] = ()


class _ExpressionParser:
    token_pattern = re.compile(r"\s*(?:(\d+(?:\.\d*)?(?:/\d+(?:\.\d*)?)?)|([A-Za-z_]\w*)|([()+\-*/]))")

    def __init__(self, text: str) -> None:
        self.text = text
        self.tokens: list[tuple[str, int]] = []
        pos = 0
        while pos < len(text):
            match = self.token_pattern.match(text, pos)
            if not match:
                if text[pos:].strip() == "":
                    break
                raise ValueError(f"Unexpected character {text[pos]!r} at position {pos + 1}.")
            token = next(group for group in match.groups() if group is not None)
            self.tokens.append((token, match.start()))
            pos = match.end()
        self.index = 0

    def peek(self) -> str | None:
        return self.tokens[self.index][0] if self.index < len(self.tokens) else None

    def take(self) -> str:
        value = self.peek()
        if value is None:
            raise ValueError("Unexpected end of expression.")
        self.index += 1
        return value

    @staticmethod
    def add(left: dict[str, Fraction], right: dict[str, Fraction], scale: Fraction = Fraction(1)) -> dict[str, Fraction]:
        result = left.copy()
        for name, value in right.items():
            result[name] = result.get(name, Fraction(0)) + scale * value
        return {name: value for name, value in result.items() if value}

    def expression(self) -> dict[str, Fraction]:
        result = self.term()
        while self.peek() in ("+", "-"):
            op = self.take()
            result = self.add(result, self.term(), Fraction(1) if op == "+" else Fraction(-1))
        return result

    def term(self) -> dict[str, Fraction]:
        result = self.unary()
        while self.peek() in ("*", "/") or (
            self.peek() is not None and (
                self.peek() == "(" or re.fullmatch(r"\d+(?:\.\d*)?(?:/\d+(?:/\d+)?)?", self.peek())
                or re.fullmatch(r"[A-Za-z_]\w*", self.peek())
            )
        ):
            explicit = self.peek() in ("*", "/")
            op = self.take() if explicit else "*"
            right = self.unary()
            left_vars = any(key != "" and value for key, value in result.items())
            right_vars = any(key != "" and value for key, value in right.items())
            if not explicit and not left_vars and not right_vars:
                raise ValueError("Ambiguous adjacent numbers; write multiplication with '*'.")
            if op == "*":
                if left_vars and right_vars:
                    raise ValueError("Multiplying two variable expressions is not linear.")
                if left_vars:
                    scalar = right.get("", Fraction(0))
                    result = {key: value * scalar for key, value in result.items()}
                else:
                    scalar = result.get("", Fraction(0))
                    result = {key: value * scalar for key, value in right.items()}
            else:
                if right_vars:
                    raise ValueError("Division by a variable expression is not linear.")
                scalar = right.get("", Fraction(0))
                if scalar == 0:
                    raise ValueError("Division by zero.")
                result = {key: value / scalar for key, value in result.items()}
        return result

    def unary(self) -> dict[str, Fraction]:
        sign = Fraction(1)
        while self.peek() in ("+", "-"):
            if self.take() == "-":
                sign *= -1
        value = self.atom()
        return {key: sign * coefficient for key, coefficient in value.items()}

    def atom(self) -> dict[str, Fraction]:
        token = self.peek()
        if token == "(":
            self.take()
            value = self.expression()
            if self.take() != ")":
                raise ValueError("Missing closing parenthesis.")
            return value
        if token is None:
            raise ValueError("Expected a number or variable.")
        if re.fullmatch(r"\d+(?:\.\d*)?(?:/\d+(?:\.\d*)?)?", token):
            self.take()
            return {"": parse_fraction(token)}
        if re.fullmatch(r"[A-Za-z_]\w*", token):
            self.take()
            return {token: Fraction(1)}
        raise ValueError(f"Unexpected token {token!r}.")


class EquationParser:
    """Parse equations into coefficients ordered by supplied or inferred variables."""

    def parse(self, text: str, variable_count: int | None = None,
              variable_names: tuple[str, ...] | None = None) -> ParseResult:
        normalized = TextNormalizer.normalize(text)
        if normalized.count("=") != 1:
            return ParseResult(False, (), Fraction(0), "Equation must contain exactly one '='.")
        left_text, right_text = normalized.split("=", 1)
        try:
            left_parser = _ExpressionParser(left_text)
            right_parser = _ExpressionParser(right_text)
            left = left_parser.expression()
            right = right_parser.expression()
            if left_parser.peek() is not None or right_parser.peek() is not None:
                raise ValueError("Unexpected trailing input.")
            expression = _ExpressionParser.add(left, right, Fraction(-1))
            variables = variable_names or tuple(key for key in expression if key)
            if variable_count is not None:
                variables = variables or tuple(f"x{i + 1}" for i in range(variable_count))
                unknown = [name for name in expression if name and name not in variables]
                if unknown:
                    raise ValueError(f"Unknown variable '{unknown[0]}'; increase the variable count or correct it.")
                if len(variables) != variable_count:
                    raise ValueError("Variable names must match the variable count.")
            else:
                variable_count = len(variables)
            coeffs = tuple(expression.get(name, Fraction(0)) for name in variables)
            return ParseResult(True, coeffs, -expression.get("", Fraction(0)), variables=tuple(variables))
        except ValueError as exc:
            return ParseResult(False, (), Fraction(0), str(exc))
