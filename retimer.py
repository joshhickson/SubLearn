"""
retimer.py - Subtitle Track Timing Fixer for ASS Files

Usage:
    python retimer.py --ass-file <input.ass> --reference-srt <reference.srt> --target-track <track_name> [--output <output.ass>]

- <input.ass>: The multi-track ASS file to fix.
- <reference.srt>: The SRT file whose timings should be used as reference (e.g., the dub).
- <track_name>: The name of the track in the ASS file to retime (e.g., 'English', 'Orig', etc.).
- <output.ass>: Optional output filename. Defaults to '<input>.retimed.ass'.

This script will align the timing of the specified ASS track to the reference SRT, using index-based matching.
"""
import argparse
import re
import os

ASS_EVENT_RE = re.compile(r"^Dialogue: (\d+),([\d:.]+),([\d:.]+),([^,]+),")
SRT_TIMESTAMP_RE = re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})")

def parse_srt(srt_path):
    timings = []
    with open(srt_path, encoding='utf-8') as f:
        block = []
        for line in f:
            if line.strip() == '':
                if block:
                    # Parse timing
                    match = re.search(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})", ''.join(block))
                    if match:
                        timings.append((match.group(1), match.group(2)))
                    block = []
            else:
                block.append(line)
        # Last block
        if block:
            match = re.search(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})", ''.join(block))
            if match:
                timings.append((match.group(1), match.group(2)))
    return timings

def srt_to_ass_time(srt_time):
    h, m, s, ms = map(int, re.match(SRT_TIMESTAMP_RE, srt_time).groups())
    return f"{h:01}:{m:02}:{s:02}.{ms//10:02}"

def retime_ass_track(ass_path, reference_timings, target_track, output_path):
    with open(ass_path, encoding='utf-8') as f:
        lines = f.readlines()
    events_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith('[Events]'):
            events_start = i
            break
    if events_start is None:
        raise ValueError('No [Events] section found in ASS file.')
    # Find all Dialogue lines for the target track
    new_lines = []
    event_idx = 0
    for line in lines:
        m = ASS_EVENT_RE.match(line)
        if m and m.group(4).strip().lower() == target_track.lower():
            if event_idx < len(reference_timings):
                start, end = reference_timings[event_idx]
                start_ass = srt_to_ass_time(start)
                end_ass = srt_to_ass_time(end)
                # Replace timing in line
                line = re.sub(r"(Dialogue: \d+,)[\d:.]+,[\d:.]+,", f"\\1{start_ass},{end_ass},", line)
            event_idx += 1
        new_lines.append(line)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f"Retimed {event_idx} events in track '{target_track}'. Output: {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Retimes a track in an ASS file using timings from a reference SRT.')
    parser.add_argument('--ass-file', required=True, help='Input ASS file')
    parser.add_argument('--reference-srt', required=True, help='Reference SRT file for timings')
    parser.add_argument('--target-track', required=True, help='Name of the ASS track to retime (case-insensitive)')
    parser.add_argument('--output', help='Output ASS file (default: <input>.retimed.ass)')
    args = parser.parse_args()

    reference_timings = parse_srt(args.reference_srt)
    output_path = args.output or os.path.splitext(args.ass_file)[0] + '.retimed.ass'
    retime_ass_track(args.ass_file, reference_timings, args.target_track, output_path)

if __name__ == '__main__':
    main()
