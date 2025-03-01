import numpy as np
import scipy.io.wavfile as wav
from pathlib import Path
from wav_validator import validate_wav_format

WAV_PATH = Path("mekurume.wav")

def calculate_bass_thresholds(audio_file, beat_duration=60/160):
    # Load and process audio file
    rate, data = wav.read(audio_file)
    is_valid, warnings = validate_wav_format(rate, data)
    
    # Handle stereo
    if len(data.shape) > 1:
        data = np.mean(data, axis=1)
    
    samples_per_beat = int(rate * beat_duration)
    bass_energies = []
    
    # Calculate bass energy for each beat
    for i in range(0, len(data), samples_per_beat):
        beat_frame = data[i:i + samples_per_beat]
        if len(beat_frame) == 0:
            break
            
        fft_data = np.abs(np.fft.rfft(beat_frame))
        frequencies = np.fft.rfftfreq(len(beat_frame), d=1/rate)
        
        # Calculate bass energy
        indices = (frequencies >= 20) & (frequencies <= 250)
        bass_amplitudes = fft_data[indices]
        if len(bass_amplitudes) > 0:
            bass_energy = np.sum(bass_amplitudes)
            bass_energies.append(bass_energy)
    
    # Calculate thresholds
    bass_energies = np.array(bass_energies)
    thresholds = {
        'min': np.percentile(bass_energies, 5),  # Lower bound (5th percentile)
        'low': np.percentile(bass_energies, 25),
        'mid': np.percentile(bass_energies, 50),
        'high': np.percentile(bass_energies, 75),
        'max': np.percentile(bass_energies, 95)  # Upper bound (95th percentile)
    }
    
    return thresholds, bass_energies

def smooth_bass_response(bass_energies, window_size=5):
    kernel = np.ones(window_size) / window_size
    return np.convolve(bass_energies, kernel, mode='same')

def compress_dynamic_range(values, threshold=0.7, ratio=0.5):
    """
    Compresses the dynamic range of values
    threshold: normalized threshold (0-1)
    ratio: compression ratio (0-1, where 0 is full compression)
    """
    normalized = (values - np.min(values)) / (np.max(values) - np.min(values))
    compressed = np.zeros_like(normalized)
    
    for i, value in enumerate(normalized):
        if value <= threshold:
            compressed[i] = value
        else:
            compressed[i] = threshold + (value - threshold) * ratio
    
    # Scale back to original range
    result = compressed * (np.max(values) - np.min(values)) + np.min(values)
    return result

def normalize_to_float(val: np.ndarray, min_val: np.float64, max_val: np.float64) -> np.ndarray:
    # Clip values to the min/max range
    clipped_val = np.clip(val, min_val, max_val)
    # Then normalize
    return (clipped_val - min_val) / (max_val - min_val)

if __name__ == "__main__":
    thresholds, bass_energies = calculate_bass_thresholds(WAV_PATH)
    bass_energies = smooth_bass_response(bass_energies)
    #bass_energies = compress_dynamic_range(bass_energies)
    #print(bass_energies)
    normalized = normalize_to_float(bass_energies, thresholds['low'], thresholds['high'])
    print(thresholds)
    print(normalized)