# HorizonBouncer

A Python utility for generating beat-synchronized data from audio files, with a focus on bass frequencies. For use with the Sonolus Horizon editor. https://horizon-editor.sonolus.com/

## Requirements

- Python 3.12.2+
- Virtual environment (venv)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/natsukashiixo/HorizonBouncer.git
   cd HorizonBouncer
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Unix or MacOS:
   source venv/bin/activate
   ```

3. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Basic usage:
```
python main.py your_audio_file.wav 120
```

Where `120` is the BPM (beats per minute) of your audio file.

### Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `wav_path` | str | (required) | Path to the WAV file |
| `bpm` | int | (required) | Beats per minute of the audio file |
| `--beat_division` | int | 4 | Number of segments per beat |
| `--smoothing_window` | int | 5 | Window size for smoothing algorithm |
| `--output` | str | output.json | Output file name |
| `--min-max` | str | min,max | Comma separated string of 2 values to decide bounds. Valid values: min, low, mid, high, max |
| `--no-round` | flag | True | Disable rounding of minmaxed values |
| `--as-leveldata` | flag | False | Output as LevelData format |

### Examples

Generate beat data with a higher beat division:
```
python main.py drum_loop.wav 128 --beat_division 8
```

Use custom min-max thresholds:
```
python main.py bass_heavy.wav 140 --min-max low,high
```

Output as level data for game integration:
```
python main.py song.wav 95 --as-leveldata --output "nameitwhatever"
```

## How It Works

1. `generate_bass_data()` analyzes the WAV file to extract bass frequency information
2. The data is segmented according to the BPM and beat division
3. Optional smoothing is applied to reduce noise
4. Values are normalized based on min-max thresholds
5. Beat events are added to a `BeatSchema`
6. Redundant events are removed, and the data is scaled
7. The result is saved as JSON or LevelData format

## Project Structure

- `main.py`: Entry point script
- `bass_bouncer.py`: Audio analysis and bass data extraction
- `beatschema.py`: Schema definition for beat data structures

## License

MIT