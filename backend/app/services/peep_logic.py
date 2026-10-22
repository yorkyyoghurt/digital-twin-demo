# peep_logic.py

def get_initial_peep(pao2_fio2: float) -> int:
    """Bepaalt de initiële recruitment PEEP op basis van de PaO2/FiO2 ratio."""
    if pao2_fio2 < 100:
        return 24
    elif pao2_fio2 <= 200:
        return 21
    elif pao2_fio2 <= 300:
        return 18
    else:
        raise ValueError("Het protocol voorziet geen initiële PEEP voor een PaO2/FiO2-ratio boven 300 mmHg.")

def get_peep_sequence(initial_peep: int) -> list[int]:
    """Genereert de decrementale PEEP-reeks in stappen van 3 cmH2O tot 6 cmH2O."""
    return list(range(initial_peep, 5, -3))

def get_next_peep(sequence: list[int], current_index: int):
    """Geeft de volgende PEEP-waarde in de reeks terug, of None als het protocol afgerond is."""
    next_index = current_index + 1
    if next_index >= len(sequence):
        return None
    return sequence[next_index]