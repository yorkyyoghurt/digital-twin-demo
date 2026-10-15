def get_initial_peep(pao2_fio2): # returns the initial PEEP in cmH2O for a given PaO2/FiO2 ratio
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


if __name__ == "__main__": # om de functies te testen, kun je dit script uitvoeren. Het zal de initial PEEP berekenen voor verschillende PaO2/FiO2 ratios en de bijbehorende PEEP sequences tonen.
   for ratio in (85, 150, 250):
       initial = get_initial_peep(ratio)
       print(ratio, "->", get_peep_sequence(initial))
