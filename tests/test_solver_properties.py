from fractions import Fraction as F

from hypothesis import given, settings, strategies as st

from gauss_visualizer.core.models import SolutionKind
from gauss_visualizer.core.solver import GaussSolver


@settings(max_examples=40, deadline=None)
@given(
    size=st.integers(min_value=1, max_value=5),
    data=st.data(),
)
def test_random_diagonally_dominant_systems_recover_exact_solution(size: int, data: st.DataObject) -> None:
    solution = data.draw(st.lists(st.integers(-5, 5), min_size=size, max_size=size))
    matrix: list[list[int]] = []
    for row in range(size):
        off_diagonal = data.draw(
            st.lists(st.integers(-3, 3), min_size=size - 1, max_size=size - 1)
        )
        values: list[int] = []
        source = iter(off_diagonal)
        for col in range(size):
            values.append(sum(abs(value) for value in off_diagonal) + 1 if col == row else next(source))
        matrix.append(values)
    augmented = [
        row + [sum(F(value) * F(x) for value, x in zip(row, solution))]
        for row in matrix
    ]
    result = GaussSolver().solve(augmented)
    assert result.kind is SolutionKind.UNIQUE
    assert result.values == tuple(F(value) for value in solution)
    for row in augmented:
        assert sum(F(value) * result.values[col] for col, value in enumerate(row[:-1])) == row[-1]
