import matplotlib as plt
import numpy as np
from eit_analysis import calculate_optimal_peep
from temporary_dictionary import trial_data_value

def plot(peep, collapse, overdistension):
   peep = np.array(peep)
   collapse = np.array(collapse)
   overdistension = np.array(overdistension)


   optimal_peep = calculate_optimal_peep(peep, collapse, overdistension)
   trial_data_value["optimal_peep"] = optimal_peep


   print(f"Optimal PEEP = {optimal_peep:.2f} cmH₂O")


   plt.figure()
   plt.plot(peep, collapse, marker="o", label="Collapse")
   plt.plot(peep, overdistension, marker="o", label="Overdistension")


   plt.axvline(optimal_peep, linestyle="--", label=f"Optimal PEEP = {optimal_peep:.1f} cmH₂O")


   plt.xlabel("PEEP (cmH₂O)")
   plt.ylabel("Percentage (%)")
   plt.title("Collapse and Overdistension vs PEEP")
   plt.legend()
   plt.grid(True)
   plt.show()


# running optimal peep calculation and plotting
plot(trial_data_value["PEEP"], trial_data_value["collapse"], trial_data_value["overdistension"])
print(f"the optimal PEEP is: {trial_data_value['optimal_peep']} cmH2O")
