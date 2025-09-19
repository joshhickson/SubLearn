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
import Levenshtein

ASS_EVENT_RE = re.compile(r"^Dialogue: (\d+),([\d:.]+),([\d:.]+),([^,]+),")
SRT_TIMESTAMP_RE = re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})")
TAG_RE = re.compile(r'{.*?}')
SOUND_EFFECT_RE = re.compile(r'\[.*?\]')

def clean_text(text):
    text = TAG_RE.sub('', text)
    text = SOUND_EFFECT_RE.sub('', text)
    text = text.replace(r'\N', ' ')
    text = re.sub(r'[^\w\s]', '', text)
    return text.lower().strip()

def parse_srt(srt_path):
    with open(srt_path, encoding='utf-8') as f:
        content = f.read()

    blocks = content.strip().split('\n\n')
    subtitles = []
    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            try:
                match = re.search(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})", lines[1])
                if match:
                    start, end = match.groups()
                    text = ' '.join(lines[2:])
                    subtitles.append({'start': start, 'end': end, 'text': text})
            except IndexError:
                pass # Ignore malformed blocks
    return subtitles

def parse_ass_track(ass_path, target_track):
    with open(ass_path, encoding='utf-8') as f:
        lines = f.readlines()

    events = []
    in_events_section = False
    for line in lines:
        if line.strip() == '[Events]':
            in_events_section = True
            continue
        if in_events_section and line.startswith('Dialogue:'):
            m = ASS_EVENT_RE.match(line)
            if m and m.group(4).strip().lower() == target_track.lower():
                events.append(line)
    return events


def srt_to_ass_time(srt_time):
    h, m, s, ms = map(int, re.match(SRT_TIMESTAMP_RE, srt_time).groups())
    return f"{h:01}:{m:02}:{s:02}.{ms//10:02}"

def retime_ass_track(ass_path, reference_subs, target_track, output_path):
    ass_events = parse_ass_track(ass_path, target_track)

    new_lines = []
    with open(ass_path, encoding='utf-8') as f:
        lines = f.readlines()

    event_idx = 0
    for line in lines:
        if line.startswith('Dialogue:'):
            m = ASS_EVENT_RE.match(line)
            if m and m.group(4).strip().lower() == target_track.lower():
                original_text = line.split(',', 9)[-1]
                cleaned_original_text = clean_text(original_text)

                best_match = None
                min_dist = float('inf')

                for ref_sub in reference_subs:
                    cleaned_ref_text = clean_text(ref_sub['text'])
                    dist = Levenshtein.distance(cleaned_original_text, cleaned_ref_text)
                    if dist < min_dist:
                        min_dist = dist
                        best_match = ref_sub

                if best_match and min_dist < 40: # Threshold for matching
                    start_ass = srt_to_ass_time(best_match['start'])
                    end_ass = srt_to_ass_time(best_match['end'])
                    line = re.sub(r"(Dialogue: \d+,)[\d:.]+,[\d:.]+,", f"\\g<1>{start_ass},{end_ass},", line)
                    event_idx +=1

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

    reference_subs = parse_srt(args.reference_srt)
    output_path = args.output or os.path.splitext(args.ass_file)[0] + '.retimed.ass'
    retime_ass_track(args.ass_file, reference_subs, args.target_track, output_path)

if __name__ == '__main__':
    main()
