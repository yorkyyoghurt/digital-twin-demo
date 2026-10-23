import subprocess
import os
from scipy.io import loadmat


project_folder = os.path.dirname(os.path.abspath(__file__))

def get_data_path():
    return os.path.join(project_folder, "data", "human-ventilation-2014.eit")

def get_mat_file_path():
    return os.path.join(project_folder,"EIT_reconstructed.mat")

def run_matlab(data_path):
    subprocess.run(["matlab","-batch",f"cd('{project_folder}'); test_EIT('{data_path}')"], check=True)

def load_eit_data(mat_file):
    data = loadmat(mat_file)

    imgs = data["imgs"]
    time = data["time"].flatten()

    return imgs, time


def main():
    # Step 1: Select the EIT data
    data_path = get_data_path()

    # Step 2: Run MATLAB
    run_matlab(data_path)

    # Step 3: Load the reconstructed images
    mat_file = get_mat_file_path()

    imgs, time = load_eit_data(mat_file)

    return imgs, time
