from bass_bouncer import generate_bass_data
from beatschema import BeatSchema
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("wav_path", type=str, help="Path to the WAV file")
    parser.add_argument("--bpm", type=int, default=160, help="Beats per minute (default: 160)")
    parser.add_argument("--beat_division", type=int, default=4, help="Number of segments per beat (default: 4)")
    parser.add_argument("--smoothing_window", type=int, default=5, help="Window size for smoothing algorithm (default: 5)")
    parser.add_argument("--output", type=str, default="output.json", help="Output file name (default: output.json)")
    parser.add_argument("--min-max", type=str, default="min,max", help="Comma separated string of 2 values to decide bounds (default: min,max). Valid values: min, low, mid, high, max")
    parser.add_argument("--no-round", action="store_false", default=True, help="Disable rounding of minmaxed values (default: True)")
    args = parser.parse_args()

    beat_schema = BeatSchema()
    min_bound, max_bound = args.min_max.split(',')
    valid_values = "min,low,mid,high,max".split(',')
    assert min_bound in valid_values and max_bound in valid_values

    bass_data = generate_bass_data(
        args.wav_path, 
        bpm=args.bpm, 
        beat_division=args.beat_division, 
        smoothing_window=args.smoothing_window,
        threshold_vals=tuple([min_bound, max_bound]),
        smoothing_algo='none',
        transient_focus=0.9)

    for segment in bass_data['segments']:
        beat_schema.add_shift_event(segment['beat'], segment['normalized_value'])

    beat_schema.validate_unique_shift_events()
    beat_schema.remove_redundant_shift_events()
    beat_schema.scale_minmax(args.no_round)
    beat_schema.add_alignment_event()
    beat_schema.write_to_json(args.output)

if __name__ == "__main__":
    main()