import numpy as np
from scipy.signal import butter, filtfilt, find_peaks


def extract_minmax_breath_frames(eit_data, sampling_freq=20.0, lowpass_cutoff=0.6, num_breaths_to_average=3):


   num_frames = eit_data.shape[0]
   global_impedance = np.zeros(num_frames)


   for g in range(num_frames):
       global_impedance[g] = np.mean(eit_data[g]) # reduceert de 2d beeld naar 1 getal


   nyquist_freq = 0.5 * sampling_freq
   normal_cutoff = lowpass_cutoff / nyquist_freq
   b, a = butter(
       N=2,
       Wn=normal_cutoff,
       btype='low',
       analog=False
       )


   filtered_data = filtfilt(b, a, global_impedance, axis=0)


   min_distance_samples = int(sampling_freq * 1.5)


   inspiration_peaks, _ = find_peaks(filtered_data, distance=min_distance_samples)
   expiration_peaks, _ = find_peaks(-filtered_data, distance=min_distance_samples)


   paired_inspiration = []
   paired_expiration = []
   expiration_index = 0


   for i in inspiration_peaks:


       while (
       expiration_index < len(expiration_peaks)
       and expiration_peaks[expiration_index] <= i
   ):
        expiration_index += 1


       if expiration_index < len(expiration_peaks):
           paired_inspiration.append(i)
           paired_expiration.append(expiration_peaks[expiration_index])


           expiration_index += 1


   if len(paired_inspiration) < num_breaths_to_average:
       raise ValueError("Not enough complete breaths found.")


   chosen_inspiration_peaks = np.array(
       paired_inspiration[-num_breaths_to_average:]
   )


   chosen_expiration_peaks = np.array(
       paired_expiration[-num_breaths_to_average:]
   )
      
   frame_shape = eit_data[0].shape
   sum_inspiration_frames = np.zeros(frame_shape, dtype=float)
   sum_expiration_frames = np.zeros(frame_shape, dtype=float)


   for h in range(num_breaths_to_average):
       i_index = chosen_inspiration_peaks[h]
       e_index = chosen_expiration_peaks[h]
      
       sum_inspiration_frames += eit_data[i_index]
