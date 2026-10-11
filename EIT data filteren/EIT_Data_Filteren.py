import numpy as np
from scipy.signal import butter, filtfilt, find_peaks

def extract_minmax_breath_frames(eit_data, sampling_freq=20.0, lowpass_cutoff=0.6, num_breaths_to_average=3): # Deze functie haalt de EIT-beelden aan het einde van de ademhaling uit de input

   num_frames = eit_data.shape[0]
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

   chosen_inspiration_peaks = np.array(paired_inspiration[-num_breaths_to_average:]) # De code selecteert de laatste num_breaths_to_average complete ademhalingen
   chosen_expiration_peaks = np.array(paired_expiration[-num_breaths_to_average:])
      
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
