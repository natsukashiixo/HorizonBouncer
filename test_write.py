from bass_bouncer import generate_bass_data
from beatschema import BeatSchema
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("wav_path", type=str, help="Path to the WAV file")
    parser.add_argument("--bpm", type=int, default=160, help="Beats per minute (default: 160)")
    parser.add_argument("--beat_division", type=int, default=4, help="Number of segments per beat (default: 4)")
    parser.add_argument("--smoothing_window", type=int, default=5, help="Window size for smoothing algorithm (default: 5)")
    args = parser.parse_args()

    beat_schema = BeatSchema()
    bass_data = generate_bass_data(
        args.wav_path, 
        bpm=args.bpm, 
        beat_division=args.beat_division, 
        smoothing_window=args.smoothing_window
    )

    for segment in bass_data['segments']:
        beat_schema.add_shift_event(segment['beat'], segment['normalized_value'])

    beat_schema.validate_unique_shift_events()
    beat_schema.remove_redundant_shift_events()
    beat_schema.write_to_json()

if __name__ == "__main__":
    main()