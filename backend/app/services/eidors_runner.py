import os
import subprocess
from scipy.io import loadmat

def run_eidors(data_path):
    """Start MATLAB op de achtergrond en leest EIT_reconstructed.mat in."""
    project_folder = os.path.dirname(os.path.abspath(__file__))
    
    # Start MATLAB batch mode
    subprocess.run([
        "matlab",
        "-batch",
        f"cd('{project_folder}'); test_EIT('{data_path}')"
    ], check=True)
    
    # Laad de gegenereerde .mat file in via SciPy
    mat_file = os.path.join(project_folder, "EIT_reconstructed.mat")
    data = loadmat(mat_file)
    
    imgs = data["imgs"]
    time_data = data["time"].flatten()
    
    return imgs, time_data