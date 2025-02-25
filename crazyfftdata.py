import numpy as np
import scipy.io.wavfile as wav
from scipy.fftpack import fft
import sys

# Read WAV file
rate, data = wav.read('mekurume.wav')

# Perform FFT
fft_data = np.abs(fft(data))
frequencies = np.fft.fftfreq(len(fft_data), 1/rate)

# Print amplitude-frequency pairs
for f, a in zip(frequencies, fft_data):
    print(f"{f} {a}")