from fractions import Fraction as F

from gauss_visualizer.core.fraction_utils import format_fraction, parse_fraction
from gauss_visualizer.core.normalizer import TextNormalizer
from gauss_visualizer.core.parser import EquationParser


def test_exact_fraction_parse_and_format():
    assert parse_fraction("-0.5") == F(-1, 2)
    assert parse_fraction("3/4") == F(3, 4)
    assert format_fraction(F(-6, 8)) == "-3/4"


def test_equation_syntax_examples():
    parser = EquationParser()
    cases = {
        "2x + 3y - z = 5": ((F(2), F(3), F(-1)), F(5)),
        "x1 + 2x2 = 7": ((F(1), F(2)), F(7)),
        "-x + y = 0": ((F(-1), F(1)), F(0)),
        "3x = 2x + 4 - y": ((F(1), F(1)), F(4)),
        "1/2 x + 0.25 y = 3/4": ((F(1, 2), F(1, 4)), F(3, 4)),
        "2*x + 3*y = 5": ((F(2), F(3)), F(5)),
        "2(x + y) = 6": ((F(2), F(2)), F(6)),
        "0 = 0": ((), F(0)),
    }
    for line, expected in cases.items():
        parsed = parser.parse(line)
        assert parsed.success, (line, parsed.error)
        assert (parsed.coefficients, parsed.constant) == expected


def test_fixed_variables_missing_variable_and_error():
    parser = EquationParser()
    parsed = parser.parse("2x = 4", 2, ("x", "y"))
    assert parsed.success and parsed.coefficients == (F(2), F(0))
    assert not parser.parse("x + w = 2", 2, ("x", "y")).success
    assert not parser.parse("x = = 2").success
    assert not parser.parse("2 3x = 4").success


def test_unicode_minus_and_arabic_digits():
    assert TextNormalizer.normalize("٢x − ١ = ٣") == "2x - 1 = 3"
    assert EquationParser().parse("٢x − ١ = ٣").constant == F(4)
