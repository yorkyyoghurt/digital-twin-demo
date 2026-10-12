import numpy as np
import matplotlib.pyplot as plt

peep = np.array([5, 8, 10, 12, 15])

collapse = np.array([30, 18, 10, 5, 2])
overdistension = np.array([2, 4, 8, 15, 25])

# Difference between the two curves
difference = collapse - overdistension

# Find where the curves cross
idx = np.where(np.diff(np.sign(difference)) != 0)[0][0]

# Values around the intersection
x1, x2 = peep[idx], peep[idx + 1]
y1, y2 = difference[idx], difference[idx + 1]

# Linear interpolation to find the exact PEEP
optimal_peep = x1 - y1 * (x2 - x1) / (y2 - y1)

# Plot
plt.figure()

plt.plot(peep, collapse, marker="o", label="Collapse")
plt.plot(peep, overdistension, marker="o", label="Overdistension")

# Mark optimal PEEP
plt.axvline(
    optimal_peep,
    linestyle="--",
    label=f"Optimal PEEP = {optimal_peep:.1f} cmH₂O"
)

plt.xlabel("PEEP (cmH₂O)")
plt.ylabel("Percentage (%)")
plt.title("Collapse and Overdistension vs PEEP")

plt.legend()
plt.grid()

plt.show()

print(f"Optimal PEEP = {optimal_peep:.2f} cmH₂O")
