
import pytest

from app.models.optimal_PEEP import calculate_optimal_peep


def test_optimal_peep_intersection():
    peep = [5, 8, 10, 12, 15]
    collapse = [30, 18, 10, 5, 2]
    overdistension = [2, 4, 8, 15, 25]

    result = calculate_optimal_peep(peep, collapse, overdistension)

    assert result == pytest.approx(10.3333333)


def test_no_intersection():
    peep = [5, 8, 10]
    collapse = [10, 8, 6]
    overdistension = [2, 3, 4]

    with pytest.raises(ValueError, match="curves do not cross"):
        calculate_optimal_peep(peep, collapse, overdistension)


def test_arrays_must_have_same_length():
    with pytest.raises(ValueError, match="same length"):
        calculate_optimal_peep([5, 8, 10], [10, 8], [2, 3, 4])


def test_at_least_two_peep_values_required():
    with pytest.raises(ValueError, match="At least two"):
        calculate_optimal_peep([5], [10], [2])
