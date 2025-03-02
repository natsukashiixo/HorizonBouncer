import numpy as np
import scipy.io.wavfile as wav
from pathlib import Path
from wav_validator import validate_wav_format

WAV_PATH = Path("mekurume.wav")

def calculate_bass_thresholds(audio_file, bpm=160, beat_division=4):
    """
    Analyzes audio file for bass energy with focus on transients
    """
    # Load and process audio file
    rate, data = wav.read(audio_file)
    is_valid, warnings = validate_wav_format(rate, data)
    
    # Handle stereo
    if len(data.shape) > 1:
        data = np.mean(data, axis=1)
    
    # Calculate granularity
    beat_duration = 60 / bpm  # Duration of a beat in seconds
    segment_duration = beat_duration / beat_division  
    samples_per_segment = int(rate * segment_duration)
    
    bass_energies = []
    transient_energies = []  # New array for storing transient energy
    timestamps = []
    
    # Calculate bass energy for each segment
    for i in range(0, len(data), samples_per_segment):
        segment_frame = data[i:i + samples_per_segment]
        if len(segment_frame) < samples_per_segment * 0.5:
            break
            
        fft_data = np.abs(np.fft.rfft(segment_frame))
        frequencies = np.fft.rfftfreq(len(segment_frame), d=1/rate)
        
        # Calculate bass energy - focusing on key frequency bands
        # Sub-bass (20-60 Hz)
        sub_indices = (frequencies >= 20) & (frequencies <= 60)
        sub_bass = np.sum(fft_data[sub_indices]) if any(sub_indices) else 0
        
        # Punchy bass (60-120 Hz)
        punch_indices = (frequencies >= 60) & (frequencies <= 120)
        punch_bass = np.sum(fft_data[punch_indices]) if any(punch_indices) else 0
        
        # Upper bass (120-250 Hz)
        upper_indices = (frequencies >= 120) & (frequencies <= 250)
        upper_bass = np.sum(fft_data[upper_indices]) if any(upper_indices) else 0
        
        # Calculate bass transients by detecting rapid changes
        if len(bass_energies) > 0:
            # Calculate the rate of change from previous segment
            prev_energy = bass_energies[-1]
            current_energy = punch_bass + 0.5 * sub_bass + 0.3 * upper_bass
            
            # Weight punch frequencies more heavily
            transient = max(0, current_energy - prev_energy)
            transient_energies.append(transient)
        else:
            # First segment has no previous for comparison
            current_energy = punch_bass + 0.5 * sub_bass + 0.3 * upper_bass
            transient_energies.append(0)
        
        # Total bass energy with punch emphasis
        bass_energy = punch_bass + 0.5 * sub_bass + 0.3 * upper_bass
        bass_energies.append(bass_energy)
        
        # Store timestamp for this segment
        timestamp_seconds = i / rate
        beat_number = timestamp_seconds / beat_duration
        timestamps.append({
            'time_seconds': timestamp_seconds,
            'beat': beat_number,
            'beat_fraction': beat_number % 1,
            'segment_index': len(bass_energies) - 1
        })
    
    # Shift transient_energies to align with bass_energies
    transient_energies = np.array([0] + transient_energies[:-1])
    
    # Calculate thresholds for both energy types
    bass_energies = np.array(bass_energies)
    transient_energies = np.array(transient_energies)
    
    bass_thresholds = {
        'min': np.percentile(bass_energies, 5),
        'low': np.percentile(bass_energies, 25),
        'mid': np.percentile(bass_energies, 50),
        'high': np.percentile(bass_energies, 75),
        'max': np.percentile(bass_energies, 95)
    }
    
    transient_thresholds = {
        'min': np.percentile(transient_energies, 5),
        'low': np.percentile(transient_energies, 25),
        'mid': np.percentile(transient_energies, 50),
        'high': np.percentile(transient_energies, 75),
        'max': np.percentile(transient_energies, 95)
    }
    
    return bass_thresholds, bass_energies, transient_energies, timestamps

def convolve(bass_energies, window_size=5):
    """Smooth using convolution (moving average)"""
    kernel = np.ones(window_size) / window_size
    return np.convolve(bass_energies, kernel, mode='same')

def cross_correlate(bass_energies, pattern=None):
    """
    Cross-correlation to find pattern matches in the bass energy
    """
    if pattern is None:
        # If no pattern provided, use the first few beats as a pattern
        pattern_length = min(16, len(bass_energies) // 4)
        pattern = bass_energies[:pattern_length]
    
    return np.correlate(bass_energies, pattern, mode='same')

def auto_correlate(bass_energies, max_lag=None):
    """
    Autocorrelation to find repeating patterns in the bass energy
    Useful for detecting rhythm patterns and periodicity
    """
    if max_lag is None:
        max_lag = len(bass_energies) // 2
        
    result = np.zeros(max_lag)
    mean = np.mean(bass_energies)
    var = np.var(bass_energies)
    
    for lag in range(max_lag):
        cov = np.mean((bass_energies[:(len(bass_energies)-lag)] - mean) * 
                      (bass_energies[lag:] - mean))
        result[lag] = cov / var if var > 0 else 0
        
    return result

def normalize_to_float(val: np.ndarray, min_val: np.float64, max_val: np.float64) -> np.ndarray:
    clipped_val = np.clip(val, min_val, max_val)
    return (clipped_val - min_val) / (max_val - min_val)

def interpolate_array(array: np.ndarray) -> np.ndarray:
    return np.interp(array, (array.min(), array.max()), (0, 1))

def generate_bass_data(wav_path, bpm=160, beat_division=4, smoothing_window=3, 
                      threshold_vals=('low', 'high'), smoothing_algo='convolution',
                      transient_focus=0.7):  # New parameter for balancing transients vs sustained bass
    """
    Generates bass analysis data with emphasis on transients/punch
    
    Args:
        wav_path: Path to the WAV file
        bpm: Beats per minute
        beat_division: Number of segments per beat
        smoothing_window: Window size for smoothing algorithm
        threshold_vals: Tuple of (lower, upper) threshold keys
        smoothing_algo: Algorithm for smoothing
        transient_focus: 0.0-1.0 value where higher values emphasize punchy transients
    """
    bass_thresholds, bass_energies, transient_energies, timestamps = calculate_bass_thresholds(
        wav_path, bpm=bpm, beat_division=beat_division
    )
    
    # Combine bass energy and transients based on transient_focus parameter
    combined_energy = (1 - transient_focus) * bass_energies + transient_focus * transient_energies
    
    # Apply selected smoothing algorithm on the combined energy
    match smoothing_algo:
        case 'convolution':
            smoothed_energies = convolve(combined_energy, window_size=smoothing_window)
        case 'cross_correlation':
            # Use first beat as pattern by default
            pattern_length = int(beat_division)
            pattern = bass_energies[:pattern_length] if len(bass_energies) > pattern_length else bass_energies
            smoothed_energies = cross_correlate(bass_energies, pattern)
        case 'auto_correlation':
            # Auto-correlation output length doesn't match input
            # Use it for analysis but not for direct replacement
            auto_corr = auto_correlate(bass_energies)
            # Just use convolution for smoothing in this case
            smoothed_energies = convolve(bass_energies, window_size=smoothing_window)
            # Store autocorrelation separately
            result_extra = {'autocorrelation': auto_corr.tolist()}
        case 'none':
            smoothed_energies = bass_energies.copy()
        case _:
            raise ValueError(f"Unknown smoothing algorithm: {smoothing_algo}")
    
    # Normalize between selected thresholds
    lower_bound, upper_bound = threshold_vals
    normalized_values = normalize_to_float(
        smoothed_energies, bass_thresholds[lower_bound], bass_thresholds[upper_bound]
    )
    
    # Combine everything into a clean data structure
    result = {
        'thresholds': bass_thresholds,
        'segments': []
    }
    
    for i, timestamp in enumerate(timestamps):
        result['segments'].append({
            'time_seconds': timestamp['time_seconds'],
            'beat': timestamp['beat'],
            'beat_fraction': timestamp['beat_fraction'],
            'raw_energy': float(bass_energies[i]),
            'smoothed_energy': float(smoothed_energies[i]),
            'normalized_value': float(normalized_values[i])
        })
    
    return result

if __name__ == "__main__":
    # Example usage with different granularities
    for division in [4, 8, 16, 32]:
        print(f"\nAnalyzing with {division} segments per beat:")
        result = generate_bass_data(WAV_PATH, bpm=160, beat_division=division)
        print(f"Generated {len(result['segments'])} segments")
        print(f"Thresholds: {result['thresholds']}")
        
        # Print first few segments for inspection
        for i, segment in enumerate(result['segments'][128:128+16]):
            print(f"Segment {i}: Beat {segment['beat']:.6f}, Value: {segment['normalized_value']:.3f}")