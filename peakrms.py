import numpy as np
import scipy.io.wavfile as wav
import sys

# Read WAV file
rate, data = wav.read('mekurume.wav')

# Handle stereo: Average both channels if stereo
if len(data.shape) > 1:
    data = np.mean(data, axis=1)  # Merge L & R by averaging

# Define BPM
BPM = 160  # Adjust based on actual BPM

# Calculate samples per beat
beat_duration = 60 / BPM  # Duration of a beat in seconds
samples_per_beat = int(rate * beat_duration)  # Convert to samples

# Frequency band definitions
BASS_RANGE = (20, 250)
MIDRANGE = (250, 4000)
TREBLE = (4000, 20000)

# Function to compute RMS in a frequency range
def compute_band_energy(frequencies, fft_data, freq_range):
    indices = (frequencies >= freq_range[0]) & (frequencies <= freq_range[1])
    band_amplitudes = fft_data[indices]
    rms = np.sqrt(np.mean(band_amplitudes ** 2)) if len(band_amplitudes) > 0 else 0
    return np.sum(band_amplitudes), rms

# Iterate over beats
beat_number = 1
for i in range(0, len(data), samples_per_beat):
    beat_frame = data[i:i + samples_per_beat]  # Extract beat segment
    
    if len(beat_frame) == 0:
        break

    # Compute amplitude metrics
    peak_amplitude = np.max(np.abs(beat_frame))  # Peak amplitude
    rms_amplitude = np.sqrt(np.mean(beat_frame ** 2))  # RMS amplitude

    # Perform FFT
    fft_data = np.abs(np.fft.rfft(beat_frame))  # FFT (real component)
    frequencies = np.fft.rfftfreq(len(beat_frame), d=1/rate)  # Frequency bins

    # Compute amplitude and RMS for each band
    bass_amp, bass_rms = compute_band_energy(frequencies, fft_data, BASS_RANGE)
    mid_amp, mid_rms = compute_band_energy(frequencies, fft_data, MIDRANGE)
    treb_amp, treb_rms = compute_band_energy(frequencies, fft_data, TREBLE)

    # Print beat information
    timestamp_sec = i / rate  # Convert sample index to seconds
    print(f"\nBeat {beat_number} ({timestamp_sec:.2f} sec): Peak={peak_amplitude}, RMS={rms_amplitude}")
    print(f"  Bass    -> Amplitude: {bass_amp:.2f}, RMS: {bass_rms:.2f}")
    print(f"  Midrange-> Amplitude: {mid_amp:.2f}, RMS: {mid_rms:.2f}")
    print(f"  Treble  -> Amplitude: {treb_amp:.2f}, RMS: {treb_rms:.2f}")

    beat_number += 1
