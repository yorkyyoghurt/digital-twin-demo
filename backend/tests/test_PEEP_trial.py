
import pytest

from app.models.PEEP_trial import (get_initial_peep, get_peep_sequence, get_next_peep)


def test_initial_peep_below_100():
    assert get_initial_peep(85) == 24


def test_initial_peep_between_100_and_200():
    assert get_initial_peep(150) == 21


def test_initial_peep_between_200_and_300():
    assert get_initial_peep(250) == 18


def test_initial_peep_above_300_is_undefined():
    with pytest.raises(ValueError):
        get_initial_peep(350)


def test_sequence_starts_at_initial_peep():
    assert get_peep_sequence(24) == [24, 21, 18, 15, 12, 9, 6]


def test_sequence_for_initial_peep_21():
    assert get_peep_sequence(21) == [21, 18, 15, 12, 9, 6]


def test_sequence_for_initial_peep_18():
    assert get_peep_sequence(18) == [18, 15, 12, 9, 6]


def test_next_peep():
    sequence = [24, 21, 18, 15, 12, 9, 6]

    assert get_next_peep(sequence, 0) == 21
    assert get_next_peep(sequence, 1) == 18
    assert get_next_peep(sequence, 5) == 6


def test_no_next_peep_at_end():
    sequence = [24, 21, 18, 15, 12, 9, 6]

    assert get_next_peep(sequence, 6) is None
