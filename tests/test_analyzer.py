from fractions import Fraction

from gauss_visualizer.core.models import SolutionKind
from gauss_visualizer.core.solver import GaussSolver


def test_homogeneous_flag_and_free_variable_expression():
    result = GaussSolver().solve([[1, 2, 0], [2, 4, 0]])
    assert result.homogeneous
    assert result.kind is SolutionKind.INFINITE
    assert result.parametric[0] == (Fraction(0), (Fraction(-2),))
    assert result.parametric[1] == (Fraction(0), (Fraction(1),))
