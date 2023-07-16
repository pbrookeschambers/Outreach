from io import StringIO
import re
import sys
import os
import subprocess
from pathlib import Path
from typing import List, Tuple

import argparse

def parse_args():
    # process.py path [-n -C -o]
    # -n, --no-labels: don't add labels to the notes
    # -C, --no-compile: don't compile the file
    # -s, --suffix: suffix to the file name, default `_temp`
    # -S, --no-suffix: don't add a suffix to the file name
    # -d, --directory: output directory, default same as input
    # -p, --pdf: compile to pdf instead of svg
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Path to the file to process")
    parser.add_argument("-n", "--no-labels", help="Don't add labels to the notes", action="store_true")
    parser.add_argument("-C", "--no-compile", help="Don't compile the file", action="store_true")
    parser.add_argument("-s", "--suffix", help="Suffix to the file name, default `_temp`", default="_temp")
    parser.add_argument("-S", "--no-suffix", help="Don't add a suffix to the file name", action="store_true")
    parser.add_argument("-d", "--directory", help="Output directory, default same as input")
    parser.add_argument("-p", "--pdf", help="Compile to pdf instead of svg", action="store_true")
    return parser.parse_args()

key = 0
active_accidentals = [None] * 7
ignore_next_label = False
base_note_length = 8
key_map = {
    # 0b[#/b]CDEFGAB. E.g., 0b10001000 is G major: 0b[sharp][C = natural][D = natural][E = natural][F = sharp][G = natural][A = natural][B = natural]
    0: 0b10000000,
    1: 0b10001000,
    2: 0b11001000,
    3: 0b11001100,
    4: 0b11101100,
    5: 0b11101110,
    6: 0b11111110,
    7: 0b11111111,
    -1: 0b00000001,
    -2: 0b00010001,
    -3: 0b00010011,
    -4: 0b00110011,
    -5: 0b00110111,
    -6: 0b01110111,
    -7: 0b01111111
}

all_notes_used = None

def main():
    # get the path of the file
    args = parse_args()
    path = Path(args.path)
    add_labels = not(args.no_labels)
    compile_file = not(args.no_compile)
    # check the file exists
    if args.no_suffix:
        args.suffix = ""
    if args.directory:
        args.directory = Path(args.directory)
        if not args.directory.exists():
            # create it
            args.directory.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        raise Exception("File does not exist")
    if path.is_dir():
        for file in path.glob("*.tex"):
            process_file(file, add_labels=add_labels, compile = compile_file, suffix = args.suffix, output_dir = args.directory, pdf_only = args.pdf)
    else:
        process_file(path, add_labels=add_labels, compile = compile_file, suffix = args.suffix, output_dir = args.directory, pdf_only = args.pdf)

def should_add_labels(block):
    # look for `\add_labels`, `\add_labels{true}`, or `\add_labels{false}`
    # if `\add_labels` is found, return True
    # if `\add_labels{true}` is found, return True
    # if `\add_labels{false}` is found, return False
    # if none of the above are found, return None
    lines = block.splitlines()
    lines = [l.split("%")[0] for l in lines]
    lines = [l for l in lines if l.strip()]
    for line in lines:
        if "\\add_labels{true}" in line.lower():
            return True
        elif "\\add_labels{false}" in line.lower():
            return False
        elif "\\add_labels" in line.lower():
            return True
    return None

def process_file(path, add_labels = False, compile = True, suffix = "", output_dir = None, pdf_only = False):
    global key, all_notes_used
    with path.open("r") as f:
        contents = f.read()
    # find anything within `\begin{music}` and `\end{music}`
    music_blocks = re.findall(r"(?P<begin>\\begin{music})(?P<block>.*?)(?P<end>\\end{music})", contents, re.DOTALL)
    if len(music_blocks) == 0:
        raise Exception("No music blocks found")
    for i, block in enumerate(music_blocks):
        new_block = block[1]
        add_labels_local = should_add_labels(new_block)
        new_block = re.sub(r"\\add_labels{.*?}", "", new_block)
        all_notes_used = set()
        key = get_key(new_block)
        new_block = new_block.splitlines()
        new_block = [line for line in new_block if not line.strip().startswith("%")]
        new_block = [line.split("%")[0] for line in new_block]
        new_block = "".join(new_block)
        new_block = new_block.replace("\n", "").replace(" ", "")
        new_block = parse_py(new_block, add_labels=add_labels if add_labels_local is None else add_labels_local)
        contents = contents.replace(block[1], new_block)
        print(f"For block {i+1}, {len(all_notes_used)} notes used: {', '.join(all_notes_used)}")
    outfile = path.parent / (path.stem + suffix + ".tex")
    if output_dir:
        outfile = Path(output_dir) / (path.stem + suffix + ".tex")
    outfile.write_text(contents)
    # using subprocess instead of os.system to suppress output. Capture anyway in case of errors. Run from the output directory.
    if compile:
        result = subprocess.run(["pdflatex", "-jobname", path.stem, outfile.name], capture_output=True, cwd=output_dir)
        if result.returncode != 0:
            print(result.stderr.decode("utf-8"))
            raise Exception("pdflatex failed")
        result = subprocess.run(["pdflatex", "-jobname", path.stem, outfile.name], capture_output=True, cwd=output_dir)
        if result.returncode != 0:
            print(result.stderr.decode("utf-8"))
            raise Exception("pdflatex failed")
        outfile.unlink()
        # os.system(f"pdf2svg {path.stem}.pdf {path.stem}.svg")
        if not pdf_only:
            result = subprocess.run(["pdf2svg", f"{path.stem}.pdf", f"{path.stem}.svg"], capture_output=True, cwd=output_dir)
            if result.returncode != 0:
                print(result.stderr.decode("utf-8"))
                raise Exception("pdf2svg failed")
            svg_file = Path(f"{path.stem}.svg")
            with svg_file.open("r") as f:
                svg_contents = f.read()
                # replace anything black with rgb(87, 82, 121)
                svg_contents = svg_contents.replace("rgb(0%,0%,0%)", "rgb(87, 82, 121)")
            with svg_file.open("w") as f:
                f.write(svg_contents)
        # remove all the auxiliary files (.aux, .log, .mx1, .pdf)
        for file in output_dir.glob(f"{path.stem}.*"):
            if file.suffix in [".aux", ".log", ".mx1"] + ([".pdf"] if not pdf_only else []):
                file.unlink()
    

def note_to_label(note):
    global key, key_map
    n_note_num, n_local_num, n_note, n_octave, n_accidental = note
    octave = n_octave + 4
    note_name = "CDEFGAB"[n_local_num]
    accidental = None
    if n_accidental is not None:
        accidental = "_=^"[n_accidental + 1]
    if accidental is None:
        # check if the note is changed by the key
        if key_map[key] & (0b01000000 >> n_local_num) > 0:
            accidental = "_" if key_map[key] >> 7 == 0 else "^"
        if active_accidentals[n_local_num] is not None:
            accidental = "_=^"[active_accidentals[n_local_num] + 1]
    if accidental is None or accidental == "=":
        return f"\\notelabel{{\\notename{{{note_name}}}{{{octave}}}}}"
    else:
        return f"\\notelabel{{\\notename[{accidental}]{{{note_name}}}{{{octave}}}}}"
    # return ""

def parse_py(contents, add_labels = False):
    global active_accidentals, base_note_length
    out = StringIO()
    pattern = re.compile(r"\\py(\[(?P<direction>.*?)\])?{(?P<length>.*?)}{(?P<notes>.*?)}(?P<tie>{tie})?")
    note_length_match = re.search(r"\\py_set_base_note{(?P<length>.*?)}", contents)
    if note_length_match is not None:
        base_note_length = int(note_length_match.group("length"))
        contents = contents.replace(note_length_match.group(0), "")
    else:
        base_note_length = 8 # default to quaver
    while len(contents) > 0:
        if contents.startswith("\\bar"):
            out.write("\\bar")
            contents = contents[4:]
            active_accidentals =  [None] * 7
            continue
        matched = pattern.match(contents)
        if matched is None:
            out.write(contents[0])
            contents = contents[1:]
            continue
        length = matched.group("length").strip()
        if length.endswith("."):
            length = length[:-1]
            dotted = True
        else:
            dotted = False
        length = int(length)
        tie = matched.group("tie") is not None and len(matched.group("tie").strip()) > 0
        notes = parse_notes(matched.group("notes"))
        if len(notes) == 0:
            print(f"Warning: no notes found in {matched.group(0)}")
        direction = None
        if matched.group("direction") is not None and len(matched.group("direction").strip()) > 0:
            direction = matched.group("direction").strip()
        if length < 8:
            out.write(_non_beamed(length, notes, dotted, tie_last = tie, add_labels = add_labels, direction = direction))
        else:
            out.write(_beamed(length, notes, dotted, tie_last = tie, add_labels = add_labels, direction = direction))
        contents = contents[len(matched.group(0)):]
    # swap tie termination and bar lines
    pattern = re.compile(r"\\ttie{(?P<tie_num>[0-9]{1,2})}\s*\\en\s*\\bar\s*\\(?P<notes_var>[Nn][Oo][Tt][Ee][Ss])")
    out = out.getvalue()
    out = pattern.sub(r"\\en\\bar\\\g<notes_var>\\ttie{\g<tie_num>}", out)
    return out
        
def _non_beamed(length, notes, dotted, tie_last = False, add_labels = False, direction = None) -> str:
    global ignore_next_label, base_note_length
    out = StringIO()
    for i, note in enumerate(notes):
        if direction is None:
            up = note[0] < 5
        else:
            up = direction.lower() == "up"
        if length == 1:
            macro = "\\wh"
            post = r"\sk" * int(base_note_length * (1.5 if dotted else 1) - 1)
        elif length == 2:
            macro = f"\\h{'u' if up else 'l'}" 
            post = r"\sk" * int(base_note_length / 2 * (1.5 if dotted else 1) - 1)
        elif length == 4:
            macro = f"\\q{'u' if up else 'l'}"
            post = r"\sk" * int(base_note_length / 4 * (1.5 if dotted else 1) - 1)
        else:
            raise Exception(f"Invalid length: {length}")
        if dotted:
            macro += "p"
        if i == len(notes) - 1 and tie_last:
            out.write(f"\\itie{'u' if not up else 'd'}{{0}}{note[0]}")
        if not ignore_next_label and add_labels:
            out.write(note_to_label(note))
        ignore_next_label = False
        out.write(f"{macro}{{{note_to_musixtex(note)}}}{post}")
        if i == len(notes) - 1 and tie_last:
            out.write("\\ttie{0}")
            ignore_next_label = True
    return out.getvalue()

def note_to_musixtex(note):    
    n_note_num, n_local_num, n_note, n_octave, n_accidental = note
    return f"{'_=^'[n_accidental+1] if n_accidental is not None else ''}{n_note_num}"

def _beamed(length, notes, dotted, tie_last = False, add_labels = False, direction = None) -> str:
    global ignore_next_label
    out = StringIO()
    num_beams = 1 if length == 8 else 2 if length == 16 else 3 # don't care after that. Yes this is a dumb way to do this.
    if len(notes) == 0:
        raise Exception("No notes")
    if len(notes) == 1:
        note = notes[0]
        if direction is None:
            up = note[0] < 5
        else:
            up = direction.lower() == "up"
        if tie_last:
            out.write(f"\\itie{'u' if not up else 'd'}{{0}}{note[0]}")
        if not ignore_next_label and add_labels:
            out.write(note_to_label(note))
        ignore_next_label = False
        out.write(f"\\{'c' * num_beams}{'u' if up else 'l'}{{{note[0]}}}")
        if length < base_note_length:
            out.write(r"\sk" * int(base_note_length / length - 1))
        if tie_last:
            out.write("\\ttie{0}")
            ignore_next_label = True
        return out.getvalue()
    if notes[0][0] < notes[1][0]:
        start = min(notes[:2], key=lambda x: x[0])[0]
        end = max(notes[-2:], key=lambda x: x[0])[0]
    else:
        start = max(notes[:2], key=lambda x: x[0])[0]
        end = min(notes[-2:], key=lambda x: x[0])[0]
    if direction is None:
        up = max(notes, key=lambda x: x[0])[0] < 5
    else:
        up = direction.lower() == "up"
    pre = f"\\I{'b' * num_beams}{'u' if up else 'l'}{{0}}{{{start}}}{{{end}}}{{{len(notes)}}}"
    macro = f"\qb{'p' if dotted else ''}{{0}}"
    out.write(pre)
    for note in notes[:-1]:
        if not ignore_next_label and add_labels:
            out.write(note_to_label(note))
        ignore_next_label = False
        out.write(f"{macro}{{{note_to_musixtex(note)}}}")
        if length < base_note_length:
            out.write(r"\sk" * int(base_note_length / length - 1))
    out.write(f"\\tb{'u' if up else 'l'}{{0}}")
    if tie_last:
        out.write(f"\\itie{'d' if up else 'u'}{{0}}{notes[-1][0]}")
    if not ignore_next_label and add_labels:
        out.write(note_to_label(notes[-1]))
    out.write(f"{macro}{{{note_to_musixtex(notes[-1])}}}")
    if length < base_note_length:
        out.write(r"\sk" * int(base_note_length / length - 1))
    if tie_last:
        ignore_next_label = True
        out.write("\\ttie{0}")
    return out.getvalue()

def note_to_num(note, octave):
    # note is in range [A-Na-z]
    # relative to "e = 0" if lowercase, "N = -5" if uppercase
    if note.islower():
        return ord(note) - ord("e") + octave * 7
    else:
        return ord(note) - ord("N") - 5 + octave * 7

def parse_notes(notes_list: str) -> List[Tuple[int, int]]:
    global active_accidentals, all_notes_used
    pattern = re.compile(r"(?P<accidental>[\^=_]?)(?P<octave>[`']*?)(?P<note>[A-Na-z])")
    notes = []
    accidental_map = {"^": 1, "_": -1, "=": 0}
    while len(notes_list) > 0:
        matched = pattern.match(notes_list)
        if matched is None:
            raise Exception(f"Invalid next note: {notes_list}")
        accidental = matched.group("accidental")
        if len(accidental) == 0:
            accidental = None
        octave = matched.group("octave")
        if len(octave) == 0:
            octave = None
        note = matched.group("note")
        if accidental is not None:
            accidental = accidental_map[accidental]
        if octave is not None:
            if len(set(list(octave))) > 1:
                raise Exception(f"Invalid octave: {octave}")
            if octave[0] == "`" or octave[0] == ",":
                octave = -1 * len(octave)
            elif octave[0] == "'":
                octave = len(octave)
            else:
                raise Exception(f"Invalid octave: {octave}")
        else:
            octave = 0
        note_num = note_to_num(note, octave)
        local_num = (note_num + 2) % 7
        if accidental is not None:
            active_accidentals[local_num] = accidental
        notes.append((note_num, local_num, note, octave, accidental))
        used_note(notes[-1])
        notes_list = notes_list[len(matched.group(0)):]
    return notes

def used_note(note):
    global key, key_map, all_notes_used
    n_note_num, n_local_num, n_note, n_octave, n_accidental = note
    octave = n_octave + 4
    note_name = "CDEFGAB"[n_local_num]
    accidental = None
    sharp = "\u266F"
    flat = "\u266D"
    natural = "\u266E"
    if n_accidental is not None:
        accidental = (flat, natural, sharp)[n_accidental + 1]
    if accidental is None:
        # check if the note is changed by the key
        if key_map[key] & (0b01000000 >> n_local_num) > 0:
            accidental = flat if key_map[key] >> 7 == 0 else sharp
        if active_accidentals[n_local_num] is not None:
            accidental = (flat, natural, sharp)[active_accidentals[n_local_num] + 1]
    if accidental is None:
        accidental = natural
    all_notes_used.add(f"{note_name}{accidental}{octave}")
    


def get_key(block) -> int:
    pattern = re.compile(r"\\generalsignature{(?P<key>[0-9-]+)}")
    matched = pattern.search(block)
    if matched is None or matched.group("key") is None:
        return 0
    return int(matched.group("key"))

if __name__ == "__main__":
    main()