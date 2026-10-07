import subprocess
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import loadmat


project_folder = os.path.dirname(os.path.abspath(__file__))

#select EIT data
data_path = os.path.join(
    project_folder,
    "data",
    "human-ventilation-2014.eit"
)


# Run MATLAB
print("Starting MATLAB...")

subprocess.run([
    "matlab",
    "-batch",
    f"cd('{project_folder}'); test_EIT('{data_path}')"
], check=True)

print("MATLAB finished!")


# 2. Load the reconstructed EIT data
script_folder = os.path.dirname(os.path.abspath(__file__))
mat_file = os.path.join(script_folder, "EIT_reconstructed.mat")

print("Loading:", mat_file)

data = loadmat(mat_file)

imgs = data["imgs"]
time = data["time"].flatten()

print("Image data shape:", imgs.shape)
print("Time data shape:", time.shape)
print(imgs)
