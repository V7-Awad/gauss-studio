"""Exact, step-by-step Gauss and Gauss-Jordan elimination."""

from __future__ import annotations

from enum import Enum, auto
from fractions import Fraction

from gauss_visualizer.core.analyzer import SolutionAnalyzer
from gauss_visualizer.core.models import (
    Matrix,
    OpType,
    Phase,
    RowOperation,
    SolutionResult,
    SolutionStep,
    StepHighlight,
)


class PivotStrategy(Enum):
    FIRST_NONZERO = auto()
    LARGEST_ABSOLUTE = auto()


class GaussSolver:
    """Solve an augmented matrix while recording every elementary operation."""

    def __init__(self, strategy: PivotStrategy = PivotStrategy.FIRST_NONZERO) -> None:
        self.strategy = strategy

    def solve(self, augmented: list[list[Fraction | int]]) -> SolutionResult:
        """Return all exact steps and classify the system.

        The input is copied. It must be a non-empty rectangular augmented matrix
        with at least one variable column and one constants column.
        """
        if not augmented or not augmented[0] or len(augmented[0]) < 2:
            raise ValueError("An augmented matrix needs at least one row and one variable column.")
        width = len(augmented[0])
        if any(len(row) != width for row in augmented):
            raise ValueError("All augmented matrix rows must have the same length.")
        matrix = [[Fraction(value) for value in row] for row in augmented]
        row_count, col_count = len(matrix), width - 1
        steps: list[SolutionStep] = []
        pivots: list[tuple[int, int]] = []

        def freeze() -> Matrix:
            return tuple(tuple(value for value in row) for row in matrix)

        def record(
            phase: Phase,
            operation: RowOperation,
            title: str,
            explanation: str,
            label: str,
            highlight: StepHighlight,
        ) -> None:
            steps.append(SolutionStep(len(steps), phase, operation, title, explanation,
                                      label, freeze(), highlight))

        record(Phase.INITIAL, RowOperation(OpType.NONE, 0), "Initial augmented matrix",
               "Begin with the system written as an augmented matrix.", "Initial matrix",
               StepHighlight())
        pivot_row = 0
        for col in range(col_count):
            candidates = [r for r in range(pivot_row, row_count) if matrix[r][col] != 0]
            if not candidates:
                continue
            selected = candidates[0] if self.strategy is PivotStrategy.FIRST_NONZERO else max(
                candidates, key=lambda r: abs(matrix[r][col])
            )
            if selected != pivot_row:
                matrix[pivot_row], matrix[selected] = matrix[selected], matrix[pivot_row]
                changed = tuple((r, c) for r in (pivot_row, selected) for c in range(width))
                record(Phase.FORWARD, RowOperation(OpType.SWAP, pivot_row, selected),
                       "Swap rows to obtain a pivot", f"Exchange row {pivot_row + 1} with row {selected + 1}.",
                       f"R{pivot_row + 1} ↔ R{selected + 1}",
                       StepHighlight(pivot_row, col, (pivot_row, selected), (selected, pivot_row),
                                     True, changed))
            pivot = matrix[pivot_row][col]
            if pivot != 1:
                factor = 1 / pivot
                matrix[pivot_row] = [factor * value for value in matrix[pivot_row]]
                changed = tuple((pivot_row, c) for c in range(width))
                record(Phase.FORWARD, RowOperation(OpType.SCALE, pivot_row, factor=factor),
                       "Normalize the pivot row", f"Multiply row {pivot_row + 1} by {factor} so the pivot is 1.",
                       f"R{pivot_row + 1} ← {factor}·R{pivot_row + 1}",
                       StepHighlight(pivot_row, col, (pivot_row,), (), True, changed))
            pivots.append((pivot_row, col))
            for target in range(pivot_row + 1, row_count):
                coefficient = matrix[target][col]
                if coefficient == 0:
                    continue
                factor = -coefficient
                before = matrix[target][:]
                matrix[target] = [a + factor * b for a, b in zip(matrix[target], matrix[pivot_row])]
                changed = tuple((target, c) for c, (old, new) in enumerate(zip(before, matrix[target]))
                                if old != new)
                record(Phase.FORWARD, RowOperation(OpType.ADD_MULTIPLE, target, pivot_row, factor),
                       "Eliminate below the pivot", f"Add {factor} times row {pivot_row + 1} to row {target + 1}.",
                       f"R{target + 1} ← R{target + 1} + ({factor})·R{pivot_row + 1}",
                       StepHighlight(pivot_row, col, (target,), (pivot_row,), True, changed))
            pivot_row += 1
            if pivot_row == row_count:
                break

        record(Phase.FORWARD, RowOperation(OpType.NONE, 0), "Row Echelon Form reached",
               "Forward elimination is complete; the matrix is in REF.", "REF",
               StepHighlight(contradiction_row=next((r for r, values in enumerate(matrix)
                                                     if all(value == 0 for value in values[:-1])
                                                     and values[-1] != 0), None)))
        for row, col in reversed(pivots):
            for target in range(row):
                coefficient = matrix[target][col]
                if coefficient == 0:
                    continue
                factor = -coefficient
                before = matrix[target][:]
                matrix[target] = [a + factor * b for a, b in zip(matrix[target], matrix[row])]
                changed = tuple((target, c) for c, (old, new) in enumerate(zip(before, matrix[target]))
                                if old != new)
                record(Phase.BACKWARD, RowOperation(OpType.ADD_MULTIPLE, target, row, factor),
                       "Eliminate above the pivot", f"Clear column {col + 1} above its pivot.",
                       f"R{target + 1} ← R{target + 1} + ({factor})·R{row + 1}",
                       StepHighlight(row, col, (target,), (row,), True, changed))
        record(Phase.DONE, RowOperation(OpType.NONE, 0), "Reduced Row Echelon Form reached",
               "Backward elimination is complete; the matrix is in RREF.", "RREF",
               StepHighlight(contradiction_row=next((r for r, values in enumerate(matrix)
                                                     if all(value == 0 for value in values[:-1])
                                                     and values[-1] != 0), None)))
        final = freeze()
        homogeneous = all(row[-1] == 0 for row in augmented)
        return SolutionAnalyzer.analyze(final, tuple(col for _, col in pivots), tuple(steps), homogeneous)
