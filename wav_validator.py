import numpy as np
import scipy.io.wavfile as wav

def load_wav_file(file_path):
    """
    loads a WAV file to check for common errors.
    
    Args:
        file_path: The path to the WAV file to load
    
    Returns:
        tuple: (is_valid, warnings) where is_valid is a boolean and 
               warnings is a list of warning messages
    """
    rate, data = wav.read(file_path)
    return rate, data

def validate_wav_format(rate, data, expected_rate=48000, expected_bit_depth=24):
    """
    Validates the sample rate and bit depth of WAV data.
    
    Args:
        rate: The sample rate of the audio file
        data: The numpy array containing the audio data
        expected_rate: Expected sample rate in Hz (default: 48000)
        expected_bit_depth: Expected bit depth (default: 24)
    
    Returns:
        tuple: (is_valid, warnings) where is_valid is a boolean and 
               warnings is a list of warning messages
    """
    warnings = []
    is_valid = True
    
    # Check sample rate
    if rate != expected_rate:
        warnings.append(f"Expected {expected_rate} Hz sample rate, got {rate} Hz")
        is_valid = False
    
    # Determine bit depth from data type
    if data.dtype == np.int16:
        bit_depth = 16
    elif data.dtype == np.int32:
        bit_depth = 32
    elif data.dtype == np.int24:  # Uncommon, but possible
        bit_depth = 24
    elif data.dtype == np.float32:
        bit_depth = 32  # Float representation
        warnings.append("Data is in float32 format rather than integer format")
    else:
        bit_depth = None
        warnings.append(f"Unexpected data type {data.dtype}")
        is_valid = False
    
    # Check bit depth
    if bit_depth != expected_bit_depth and bit_depth is not None:
        warnings.append(f"Expected {expected_bit_depth}-bit audio, got {bit_depth}-bit")
        is_valid = False
    
    return is_valid, warnings