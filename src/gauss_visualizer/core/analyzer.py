"""Classify an RREF matrix and derive exact solution expressions."""

from __future__ import annotations

from fractions import Fraction

from gauss_visualizer.core.models import Matrix, SolutionKind, SolutionResult, SolutionStep


class SolutionAnalyzer:
    """Analyze the final augmented matrix produced by :class:`GaussSolver`."""

    @staticmethod
    def analyze(
        matrix: Matrix,
        pivot_cols: tuple[int, ...],
        steps: tuple[SolutionStep, ...],
        homogeneous: bool,
    ) -> SolutionResult:
        variable_count = len(matrix[0]) - 1
        inconsistent = any(
            all(value == 0 for value in row[:variable_count]) and row[-1] != 0
            for row in matrix
        )
        free_vars = tuple(col for col in range(variable_count) if col not in pivot_cols)
        if inconsistent:
            kind = SolutionKind.INCONSISTENT
            values: tuple[Fraction | None, ...] = tuple(None for _ in range(variable_count))
            parametric = ()
        else:
            kind = SolutionKind.UNIQUE if len(pivot_cols) == variable_count else SolutionKind.INFINITE
            value_list: list[Fraction | None] = [None] * variable_count
            expressions: list[tuple[Fraction, tuple[Fraction, ...]] | None] = [None] * variable_count
            for free_col in free_vars:
                coeffs = tuple(Fraction(int(col == free_col)) for col in free_vars)
                expressions[free_col] = (Fraction(0), coeffs)
            for row_index, col in enumerate(pivot_cols):
                constant = matrix[row_index][-1]
                coeffs = tuple(-matrix[row_index][free_col] for free_col in free_vars)
                if free_vars:
                    expressions[col] = (constant, coeffs)
                else:
                    value_list[col] = constant
            values = tuple(value_list)
            parametric = tuple(
                expression if expression is not None else (Fraction(0), ())
                for expression in expressions
            ) if free_vars else ()
        return SolutionResult(
            steps=steps,
            kind=kind,
            rank=len(pivot_cols),
            pivot_cols=pivot_cols,
            free_vars=free_vars,
            values=values,
            parametric=parametric,
            homogeneous=homogeneous,
        )
