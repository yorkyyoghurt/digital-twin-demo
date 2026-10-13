import numpy as np
import matplotlib.pyplot as plt

def calculate_optimal_peep(peep, collapse, overdistension):
    peep = np.asarray(peep, dtype=float)
    collapse = np.asarray(collapse, dtype=float)
    overdistension = np.asarray(overdistension, dtype=float)

    if not (len(peep) == len(collapse) == len(overdistension)):
        raise ValueError("All arrays must have the same length.")
    
    if len(peep) < 2:
        raise ValueError("At least two PEEP values are required.")
    
    difference = collapse - overdistension
    
    crossings = np.where(np.diff(np.sign(difference)) != 0)[0] # Find intervals where the difference changes sign

    if len(crossings) == 0:
        raise ValueError("The curves do not cross.")

    idx = crossings[0]
    
    # Values around the intersection
    x1, x2 = peep[idx], peep[idx + 1]
    y1, y2 = difference[idx], difference[idx + 1]
    
    # Linear interpolation to find the exact PEEP
    optimal_peep = x1 - y1 * (x2 - x1) / (y2 - y1)

    return optimal_peep


def plot():
    peep = np.array([5, 8, 10, 12, 15])
    collapse = np.array([30, 18, 10, 5, 2])
    overdistension = np.array([2, 4, 8, 15, 25])

    optimal_peep = calculate_optimal_peep(peep, collapse, overdistension)

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


if __name__ == "__plot__":
    plot()
