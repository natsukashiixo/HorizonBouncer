import numpy as np
import scipy.io.wavfile as wav
from pathlib import Path
from wav_validator import validate_wav_format

WAV_PATH = Path("mekurume.wav")

def calculate_bass_thresholds(audio_file, bpm=160, beat_division=4):
    """
    Analyzes audio file for bass energy at specified beat division granularity.
    
    Args:
        audio_file: Path to WAV file
        bpm: Beats per minute
        beat_division: Number of segments per beat (4=16th notes, 8=32nd notes, etc.)
    
    Returns:
        tuple: (thresholds, bass_energies, timestamps)
    """
    # Load and process audio file
    rate, data = wav.read(audio_file)
    is_valid, warnings = validate_wav_format(rate, data)
    
    # Handle stereo
    if len(data.shape) > 1:
        data = np.mean(data, axis=1)
    
    # Calculate granularity
    beat_duration = 60 / bpm  # Duration of a beat in seconds
    segment_duration = beat_duration / beat_division  # Duration of each segment
    samples_per_segment = int(rate * segment_duration)
    
    bass_energies = []
    timestamps = []
    
    # Calculate bass energy for each segment
    for i in range(0, len(data), samples_per_segment):
        segment_frame = data[i:i + samples_per_segment]
        if len(segment_frame) < samples_per_segment * 0.5:  # Skip very short segments
            break
            
        fft_data = np.abs(np.fft.rfft(segment_frame))
        frequencies = np.fft.rfftfreq(len(segment_frame), d=1/rate)
        
        # Calculate bass energy
        indices = (frequencies >= 20) & (frequencies <= 250)
        bass_amplitudes = fft_data[indices]
        if len(bass_amplitudes) > 0:
            bass_energy = np.sum(bass_amplitudes)
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
    
    # Calculate thresholds
    bass_energies = np.array(bass_energies)
    thresholds = {
        'min': np.percentile(bass_energies, 5),
        'low': np.percentile(bass_energies, 25),
        'mid': np.percentile(bass_energies, 50),
        'high': np.percentile(bass_energies, 75),
        'max': np.percentile(bass_energies, 95)
    }
    
    return thresholds, bass_energies, timestamps

def smooth_bass_response(bass_energies, window_size=5):
    kernel = np.ones(window_size) / window_size
    return np.convolve(bass_energies, kernel, mode='same')

def normalize_to_float(val: np.ndarray, min_val: np.float64, max_val: np.float64) -> np.ndarray:
    clipped_val = np.clip(val, min_val, max_val)
    return (clipped_val - min_val) / (max_val - min_val)

def generate_bass_data(wav_path, bpm=160, beat_division=4, smoothing_window=5):
    """
    Generates bass analysis data with the specified granularity
    
    Args:
        wav_path: Path to the WAV file
        bpm: Beats per minute
        beat_division: Number of segments per beat
        smoothing_window: Window size for smoothing algorithm
    
    Returns:
        dict: Bass analysis data with timestamps and normalized values
        {
        'thresholds': thresholds,
        'segments': [{}, {}, ...]
        }
    """
    thresholds, bass_energies, timestamps = calculate_bass_thresholds(
        wav_path, bpm=bpm, beat_division=beat_division
    )
    
    # Apply smoothing
    smoothed_energies = smooth_bass_response(
        bass_energies, window_size=smoothing_window
    )
    
    # Normalize between low and high thresholds
    normalized_values = normalize_to_float(
        smoothed_energies, thresholds['low'], thresholds['high']
    )
    
    # Combine everything into a clean data structure
    result = {
        'thresholds': thresholds,
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