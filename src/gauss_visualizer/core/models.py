"""Immutable models shared by the solver and future visualization layer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from fractions import Fraction

Matrix = tuple[tuple[Fraction, ...], ...]


class Phase(Enum):
    INITIAL = auto()
    FORWARD = auto()
    BACKWARD = auto()
    DONE = auto()


class OpType(Enum):
    NONE = auto()
    SWAP = auto()
    SCALE = auto()
    ADD_MULTIPLE = auto()


class SolutionKind(Enum):
    UNIQUE = auto()
    INFINITE = auto()
    INCONSISTENT = auto()


@dataclass(frozen=True)
class RowOperation:
    type: OpType
    target_row: int
    source_row: int | None = None
    factor: Fraction = Fraction(1)


@dataclass(frozen=True)
class StepHighlight:
    pivot_row: int | None = None
    pivot_col: int | None = None
    affected_rows: tuple[int, ...] = ()
    source_rows: tuple[int, ...] = ()
    highlight_column: bool = False
    changed_cells: tuple[tuple[int, int], ...] = ()
    contradiction_row: int | None = None


@dataclass(frozen=True)
class SolutionStep:
    index: int
    phase: Phase
    operation: RowOperation
    title: str
    explanation: str
    operation_label: str
    snapshot: Matrix
    highlight: StepHighlight


@dataclass(frozen=True)
class SolutionResult:
    steps: tuple[SolutionStep, ...]
    kind: SolutionKind
    rank: int
    pivot_cols: tuple[int, ...]
    free_vars: tuple[int, ...]
    # Each entry is either a Fraction for a fixed value or a sparse expression
    # mapping free-variable column indices to coefficients, plus a constant.
    values: tuple[Fraction | None, ...]
    parametric: tuple[tuple[Fraction, tuple[Fraction, ...]], ...]
    homogeneous: bool
