
def get_initial_peep(pao2_fio2):

    if pao2_fio2 < 100:
        return 24
    elif pao2_fio2 <= 200:
        return 21
    elif pao2_fio2 <= 300:
        return 18
    else:
        raise ValueError("The protocol does not specify an initial PEEP for PaO2/FiO2 above 300 mmHg.")


def get_peep_sequence(initial_peep):

    return list(range(initial_peep, 5, -3))


def get_next_peep(sequence, current_index):

    next_index = current_index + 1

    if next_index >= len(sequence):
        return None

    return sequence[next_index]


def run_peep_trial():
    initial_peep = get_initial_peep(85)
    sequence = get_peep_sequence(initial_peep)

    print("Initial recruitment PEEP:", initial_peep, "cmH2O")
    print("PEEP trial sequence:", sequence)

    current_index = 0

    while True:
        current_peep = sequence[current_index]

        print(f"\nSet PEEP to {current_peep} cmH2O.")
        print("Maintain this level for 2 minutes.")
        input("After the step is completed, press Enter to continue.")

        next_peep = get_next_peep(sequence, current_index)

        if next_peep is None:
            print("PEEP trial sequence completed.")
            break

        current_index += 1
        print(f"Next recommended PEEP: {next_peep} cmH2O")

