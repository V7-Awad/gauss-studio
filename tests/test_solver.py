from fractions import Fraction as F

from gauss_visualizer.core.models import OpType, SolutionKind
from gauss_visualizer.core.solver import GaussSolver


def test_unique_worked_example_is_exact_and_reaches_rref():
    result = GaussSolver().solve([[2, 1, -1, 8], [-3, -1, 2, -11], [-2, 1, 2, -3]])
    assert result.kind is SolutionKind.UNIQUE
    assert result.values == (F(2), F(3), F(-1))
    assert result.steps[-1].snapshot == ((F(1), F(0), F(0), F(2)),
                                         (F(0), F(1), F(0), F(3)),
                                         (F(0), F(0), F(1), F(-1)))
    assert all(isinstance(value, F) for row in result.steps[-1].snapshot for value in row)


def test_swap_is_recorded_for_zero_first_pivot():
    result = GaussSolver().solve([[0, 1, 2], [1, 1, 3]])
    assert any(step.operation.type is OpType.SWAP for step in result.steps)
    assert result.values == (F(1), F(2))


def test_infinite_and_inconsistent_systems():
    infinite = GaussSolver().solve([[1, 1, 1, 3], [2, 2, 2, 6], [1, -1, 0, 0]])
    assert infinite.kind is SolutionKind.INFINITE
    assert infinite.free_vars == (2,)
    assert infinite.parametric == ((F(3, 2), (F(-1, 2),)),
                                   (F(3, 2), (F(-1, 2),)), (F(0), (F(1),)))
    inconsistent = GaussSolver().solve([[1, 1, 1], [1, 1, 2]])
    assert inconsistent.kind is SolutionKind.INCONSISTENT
    assert any(step.highlight.contradiction_row is not None for step in inconsistent.steps)


def test_underdetermined_and_fractional_inputs():
    result = GaussSolver().solve([[F(1, 2), 1, 2, 3, 4]])
    assert result.kind is SolutionKind.INFINITE
    assert len(result.free_vars) == 3
    assert all(isinstance(value, F) for row in result.steps[-1].snapshot for value in row)


def test_rejects_ragged_matrix():
    try:
        GaussSolver().solve([[1, 2], [1]])
    except ValueError as exc:
        assert "same length" in str(exc)
    else:
        raise AssertionError("Expected invalid matrix to be rejected")


def test_each_snapshot_matches_its_single_recorded_operation():
    result = GaussSolver().solve([[0, 2, 4], [3, 1, 7]])
    previous = None
    for step in result.steps:
        current = [list(row) for row in step.snapshot]
        if previous is not None:
            expected = [row[:] for row in previous]
            operation = step.operation
            if operation.type is OpType.SWAP:
                expected[operation.target_row], expected[operation.source_row] = (
                    expected[operation.source_row], expected[operation.target_row]
                )
            elif operation.type is OpType.SCALE:
                expected[operation.target_row] = [
                    operation.factor * value for value in expected[operation.target_row]
                ]
            elif operation.type is OpType.ADD_MULTIPLE:
                expected[operation.target_row] = [
                    a + operation.factor * b
                    for a, b in zip(expected[operation.target_row], expected[operation.source_row])
                ]
            assert current == expected
        previous = current
