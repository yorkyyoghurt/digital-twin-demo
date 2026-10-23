# durfte ff niet aan de api shit te zitten ##############################################################
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.bmi import router as bmi_router
##########################################################################################################

#all imports
import subprocess
import os
from time import time
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import loadmat
from scipy.signal import butter, filtfilt, find_peaks

# 0. dictionaries

constant_dictionary = {"voltage_meting":0 , "mesh":0, "lowpass_cutoff":0.6, "num_breaths_to_average":3}
patient_data = { "pao2_fio2":0 , "patient_id":0}

trial_data_value = {"PEEP":[] , "p_plateau":[] ,  "compliance":[] , "collapse":[], "overdistention":[], "optimal_peep":0}
trial_data_frames = {"compliance_matrix":[] , "collapse_matrix":[] , "overdistention_matrix":[]}


# 1. first questions to fill in patient_data
patient_data["pao2_fio2"] = float(input("Enter the patient's PaO2/FiO2 ratio (mmHg): "))
patient_data["patient_id"] = input("Enter the patient's ID: ")

# 2. peep trial
# functions to run peep trial:
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

def extract_minmax_breath_frames(eit_data, time, lowpass_cutoff, num_breaths_to_average):

   num_frames = eit_data.shape[0]
   sampling_freq = 1 / np.mean(np.diff(time)) # berekent de sampling frequency van de EIT-data
   global_impedance = np.zeros(num_frames) # maakt een lege array waarin voor elk EIT-frame één globale impedantiewaarde wordt opgeslagen

   for g in range(num_frames):
       global_impedance[g] = np.sum(eit_data[g]) # telt alle pixels van het 2D EIT-beeld op tot één globale impedantiewaarde

   nyquist_freq = 0.5 * sampling_freq
   normal_cutoff = lowpass_cutoff / nyquist_freq
   b, a = butter(
       N=2,
       Wn=normal_cutoff,
       btype='low',
       analog=False
       ) 
   filtered_impedance = filtfilt(b, a, global_impedance, axis=0) # filtert ruis uit de glabale impedantie door middel van een lowpass filter
   min_distance_samples = int(sampling_freq * 1.5) # minimale afstand tussen pieken in samples

   inspiration_peaks, _ = find_peaks(filtered_impedance, distance=min_distance_samples)
   expiration_peaks, _ = find_peaks(-filtered_impedance, distance=min_distance_samples) # vindt de maxima en minima in de gefilterde globale impedantie

   paired_inspiration = []
   paired_expiration = [] 

   expiration_index = 0 # houdt bij welke expiratiepiek als volgende bekeken moet worden

   for i in inspiration_peaks:
    while (
       expiration_index < len(expiration_peaks)
       and expiration_peaks[expiration_index] <= i # Controleert of de huidige expiratiepiek vóór of op dezelfde positie als de inspiratiepiek ligt
    ):
        expiration_index += 1 

    if expiration_index < len(expiration_peaks): # als er nog een expiratiepiek beschikbaar is, wordt deze gekoppeld aan de huidige inspiratiepiek
        paired_inspiration.append(i)
        paired_expiration.append(expiration_peaks[expiration_index])

        expiration_index += 1 

   if len(paired_inspiration) < num_breaths_to_average:
       raise ValueError("Not enough complete breaths found.")

   chosen_inspiration_peaks = np.array(
       paired_inspiration[-num_breaths_to_average:] # De code selecteert de laatste num_breaths_to_average complete ademhalingen
   )

   chosen_expiration_peaks = np.array(
       paired_expiration[-num_breaths_to_average:]
   )
      
   frame_shape = eit_data[0].shape # Bepaalt eerst de afmetingen van één EIT-beeld en maakt vervolgens twee lege beelden aan waarin de inspiratie- en expiratiebeelden kunnen worden opgeteld
   sum_inspiration_frames = np.zeros(frame_shape, dtype=float)
   sum_expiration_frames = np.zeros(frame_shape, dtype=float)

   for h in range(num_breaths_to_average): # Voor iedere geselecteerde ademhaling worden het originele EIT-beeld op het einde van de inspiratie en het originele EIT-beeld op het einde van de expiratie bij hun respectievelijke som opgeteld
       i_index = chosen_inspiration_peaks[h]
       e_index = chosen_expiration_peaks[h]
      
       sum_inspiration_frames += eit_data[i_index]
       sum_expiration_frames += eit_data[e_index]

   mean_inspiration_frame = sum_inspiration_frames / num_breaths_to_average # gemiddelde van de inspiratiebeelden en het gemiddelde van de expiratiebeelden worden berekend door de som te delen door het aantal ademhalingen dat wordt meegenomen in het gemiddelde
   mean_expiration_frame = sum_expiration_frames / num_breaths_to_average

   indices = {
   'insp_indices' : chosen_inspiration_peaks,
   'exp_indices' : chosen_expiration_peaks,
   'global_impedance_raw' : global_impedance,
   'filtered_impedance' : filtered_impedance
      
   }
   return mean_inspiration_frame, mean_expiration_frame, indices

def compliance_matrix(matrix1, matrix2, Pplat, PEEP):
    # functie om compliance matrix te maken
    
    delz = matrix1-matrix2
    delp = Pplat-PEEP
    c = delz / delp
    return c #c is je compliance matrix

# function peep trial
def run_peep_trial(pao2_fio2):
    #get initial PEEP and sequence
    initial_peep = get_initial_peep(pao2_fio2)
    sequence = get_peep_sequence(initial_peep)
    trial_data_value["PEEP"] = sequence

    print("Initial recruitment PEEP:", initial_peep, "cmH2O")
    print("PEEP trial sequence:", sequence)

    # initiate decremental peep trial (loop per peep step)
    current_index = 0

    while True:
        # set the PEEP value (add in manual override if needed)
        current_peep = sequence[current_index]
        print(f"\nSet PEEP to {current_peep} cmH2O.")
        
        # enter p_plateau value and store it in trial_data_value["p_plateau"]
        P_plateau = float(input("Enter the measured Pplateau value (cmH2O): "))
        trial_data_value["p_plateau"].append(P_plateau)

        # doctor instruction (add in EIT data collection)
        print("Maintain this level for 2 minutes.")
        input("After the step is completed, press Enter to continue.")

        ###### somehow new data ##########################################################################
        # temporary EIT data collection (add in actual EIT data collection code here)
        EIT_data = os.path.dirname(os.path.abspath(__file__))

        data_path = os.path.join(
            EIT_data,
            "data",
            "human-ventilation-2014.eit"
            )

        ###################################################################################################

        # Run MATLAB

        #silenced prints
        # print("Starting MATLAB...")

        subprocess.run([
           "matlab",
           "-batch",
           f"cd('{EIT_data}'); test_EIT('{data_path}')"
        ], check=True)

        #silenced prints
        # print("MATLAB finished!")

        # Load the reconstructed EIT data
        script_folder = os.path.dirname(os.path.abspath(__file__))
        mat_file = os.path.join(script_folder, "EIT_reconstructed.mat")

        # silenced prints
        # print("Loading:", mat_file)

        data = loadmat(mat_file)

        # EIT data (check units and consistancy, correct and name in limitations)
        imgs = data["imgs"]
        time = data["time"].flatten()

        #silenced prints
        #print("Image data shape:", imgs.shape)
        #print("Time data shape:", time.shape)
        #print(imgs)

        # Extract the mean inspiration and expiration frames (indices are also returned, currently not used, but could be useful for further analysis or output)
        mean_inspiration_frame, mean_expiration_frame, indices = extract_minmax_breath_frames(imgs, time, constant_dictionary['lowpass_cutoff'], constant_dictionary['num_breaths_to_average'])

        # Calculate compliance matrix and store it in trial_data_frames["compliance_matrix"]
        Compliance_matrix = compliance_matrix(mean_inspiration_frame, mean_expiration_frame, P_plateau, current_peep)
        trial_data_frames["compliance_matrix"].append(Compliance_matrix)

        # initiate next step in the PEEP trial
        next_peep = get_next_peep(sequence, current_index)

        if next_peep is None:
            print("PEEP trial sequence completed.")
            break

        current_index += 1
        print(f"Next recommended PEEP: {next_peep} cmH2O")
    
# running peep trial 
run_peep_trial(patient_data["pao2_fio2"])


# 3. collapse and overdistention function
def collapse_berekenen(compliance_array):
    result = [
        [max(values) for values in zip(*rows)]
        for rows in zip(*compliance_array)
    ] # bereken de maximale compliance voor elke PEEP

    collapse_array = []
    collapse_percentage = []
    overdistention_array = []
    overdistention_percentage = []
    
    current_result_index = 0
    current_result_row = 0

    list_best_compliance = []

    

    for list in compliance_array:
        current_compliance = 0
        collapse_percent_matrix = []
        overdistention_percent_matrix = []
        for row in list: # bepaal de collapse van een rij van de matrix
            row_collapse = []
            row_overdistention = []
            for element in row:
                current_compliance = element

                best_compliance = result[current_result_row][current_result_index]
                current_result_index += 1
        
                collapse_percent = ((best_compliance-current_compliance)*100)/best_compliance
                overdistention_percent = collapse_percent

                if current_compliance == best_compliance: #bepaal of de beste compliance al is geweest
                    list_best_compliance.append((current_result_row,current_result_index))

                if (current_result_row,current_result_index) in list_best_compliance: # als de beste compliance al is geweest is de overdistention sws 0
                    overdistention_percent = 0

                if (current_result_row,current_result_index) not in list_best_compliance: # anders is de collapse sws 0
                                    collapse_percent = 0
                
                row_collapse.append(collapse_percent)
                row_overdistention.append(overdistention_percent)
                            
            collapse_percent_matrix.append(row_collapse)
            overdistention_percent_matrix.append(row_overdistention)
            current_result_index = 0
            current_result_row += 1
        current_result_row = 0

        overdistention_array.append(overdistention_percent_matrix)
        collapse_array.append(collapse_percent_matrix)
        collapse_percentage.append(np.mean(collapse_percent_matrix))
        overdistention_percentage.append(np.mean(overdistention_percent_matrix))
    
    return(collapse_array,overdistention_array, collapse_percentage, overdistention_percentage)

#running collapse and overdistention calculation
collapse_matrix, overdistention_matrix, collapse_percentage, overdistention_percentage = collapse_berekenen(trial_data_frames["compliance_matrix"])

# storing restults in dictionaries
trial_data_frames["collapse_matrix"] = collapse_matrix
trial_data_frames["overdistention_matrix"] = overdistention_matrix
trial_data_value["overdistention"] = overdistention_percentage
trial_data_value["collapse"] = collapse_percentage

# 4. optimal peep 
# functions
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