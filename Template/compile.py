#!/usr/bin/env python3

import argparse
from typing import Iterator, List
from display import LoggerLayout, Layout
import subprocess
from pathlib import Path
# Yes this is overkill. No, I don't care.
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.console import Group
import rich
import time
import os

from contextlib import nullcontext

# This is messy. It works, I'll tidy it up later if I have time.



logs = None
latex_out = None

def run_and_capture(command: List[str], *args, **kwargs) -> Iterator[str]:
    popen = subprocess.Popen(command, stdout=subprocess.PIPE, *args, **kwargs)
    for line in iter(popen.stdout.readline, b""):
        yield line.decode("utf-8").rstrip()
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, command)

def setup_logging():
    global logs
    # get terminal width
    width = os.get_terminal_size().columns
    logs = LoggerLayout(Layout(name = "outreach"))
    logs.outreach.title = "Outreach"
    logs.outreach.panel_style = "blue"
    if width < 120:
        logs.outreach.narrow = True

def _print_usage():
    usage = """Usage: compile.py [-h] [-v] directory [type] [audience] [-e | -E]"""

    table = Table(show_lines=True)
    table.add_column("Argument")
    table.add_column("Description")
    table.add_column("Values [bold blue](default)[/bold blue]")
    table.add_row("-h,\n--help", "Show this help message and exit", "")
    table.add_row("-v,\n--verbose", "Give more verbose output, including live LaTeX logs during compilation", "[bold blue]False[/bold blue]")
    table.add_row("directory", "[red bold](Required)[/red bold]\nDirectory to compile", "Any valid directory containing activity files")
    table.add_row("type", "Which activity document to compile", "cover,\ninstructions,\nworksheet,\n[bold blue]all[/bold blue]")
    table.add_row("audience", "Which version of the documents to compile", "student,\ninstructor,\n[bold blue]all[/bold blue]")
    table.add_row("-e,\n--extension-only", "Compile the extension activity only. Mutually exclusive with `-E`", "[bold blue]False[/bold blue]")
    table.add_row("-E,\n--no-extension", "Compile activity without extension only. Mutually exclusive with `-e`", "[bold blue]False[/bold blue]")
    table.add_row("-b,\n--bibtex", "Compile with bibtex", "[bold blue]False[/bold blue]")
    table.add_row("-c,\n--compiler-options", "Options to pass to pdflatex. Do not overwrite jobname or interactionmode unless you are [bold red]absolutely sure[/bold red] you know what you're doing", "[bold blue]None[/bold blue]")
    table.add_row("-C,\n--clean", "Clean auxiliary files after compilation. This can cause documents to become unaware of their context. If no other options are specified, this will only clean auxiliary files without compilation.", "[bold blue]False[/bold blue]\n[bold blue]True[/bold blue] if `type` is `all`")
    table.add_row("-f,\n --force-all", "Force compilation of all variants of the documents, even if no changes are detected.", "[bold blue]False[/bold blue]")
    group = Group(
        Text(usage + "\n\n", justify="left", style="bold"),
        table,
        Text().append("\n\nExample: ", style = "bold").append("compile.py -v ./cloud_chambers worksheet all -e")
    )
    logs.outreach.info(group)

def _log_from_argparse(msg: str, _file = None):
    global logs
    segments = [s.strip().lower() for s in msg.split(":")]
    if segments[0] == "usage":
        _print_usage() # automatic usage from argparse misses some information
        return
    msg_type = "error" if "error" in segments else "warning" if "warning" in segments else "info"
    if msg_type == "error":
        logs.outreach.error(msg)
    elif msg_type == "warning":
        logs.outreach.warning(msg)
    else:
        logs.outreach.info(msg)

def parse_args():
    global logs
    # compile.py -v directory [cover, instructions, worksheet, all] [student, instructor, all] -e
    parser = argparse.ArgumentParser(description='Compile outreach activities')
    parser._print_message = _log_from_argparse # hook into argparse to log to rich instead
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='verbose output')
    parser.add_argument('directory', metavar='directory', type=str, nargs=1,
                        help='directory to compile')
    parser.add_argument('type', metavar='type', type=str, nargs='?', default = None, # could default all, but I might want to act differently
                        help='Which document to compile. Options are cover, instructions, worksheet, all')
    parser.add_argument('audience', metavar='audience', type=str, nargs='?', default = None, # could default all, but I might want to act differently
                        help='Which audience to compile for. Options are student, instructor, all')
    parser.add_argument('-e', '--extension-only', action='store_true',
                        help='compile activity with extension only')
    parser.add_argument('-E', '--no-extension', action='store_true',
                        help='compile activity without extension - also use this when the activity has no extension to avoid unnecessary compilations')
    parser.add_argument('-b', '--bibtex', action='store_true',
                        help='compile with bibtex')
    parser.add_argument('-c', '--compiler-options', metavar='options', type=str, nargs='?', default = None,
                        help='options to pass to pdflatex')
    parser.add_argument('-C', '--clean', action='store_true',
                        help='clean auxiliary files')
    parser.add_argument('-f', '--force-all', action='store_true',
                        help='force compilation of all variants of the documents, even if no changes are detected')
    args = parser.parse_args()
    no_args = True
    if args.type is not None:
        if args.type not in ['cover', 'instructions', 'worksheet', 'all']:
            logs.outreach.critical(f"Invalid type: `{args.type}`. See compile.py --help for more information")
            raise ValueError(f"Invalid type: `{args.type}`. See compile.py --help for more information")
        no_args = False
    else:
        args.type = 'all'
    if args.audience is not None:
        if args.audience not in ['student', 'instructor', 'all']:
            logs.outreach.critical(f"Invalid audience: `{args.audience}`. See compile.py --help for more information")
            raise ValueError(f"Invalid audience: `{args.audience}`. See compile.py --help for more information")
        no_args = False
    else:
        args.audience = 'all'
    args.directory = args.directory[0]
    if args.extension_only and args.no_extension:
        logs.outreach.warning("Both --extension and --no-extension were specified. Assuming --extension")
        args.no_extension = False
    no_args = no_args \
        and not args.extension_only \
        and not args.no_extension \
        and not args.bibtex \
        and not args.compiler_options \
        and not args.force_all
    return args, no_args

def update_output(lines: List[str], layout: Layout, max_size = 15):
    height = min(max_size, len(lines))
    layout.update(Panel(Text("\n".join(lines[-height:])), height = height, title = "LaTeX Output", border_style="green"))

def report_latex_error(outlines: List[str], filename: Path, jobname: str):
    latex_error = "!" + "!".join(outlines.split("!")[1:])
    panel = Panel(latex_error, title="LaTeX Error", border_style="red")
    report =  Group(
        Text(f"pdflatex encountered an error and was unable to compile file `{filename}`. This is likely the problem:"),
        panel,
        Text(f"See the logs ({filename.parent}/{jobname}.log) for more information.")
    )
    logs.outreach.error(report)



def compile_file(filename: str | Path, jobname: str, ntimes: int = 1, verbose: bool = False) -> bool:
    global logs, latex_out
    if verbose and latex_out is None:
        latex_out = Layout(name = "latex")
        latex_out["latex"].size = 15
        logs.outreach.info(latex_out)

    if isinstance(filename, str):
        filename = Path(filename)
    if not filename.exists():
        logs.outreach.error(f"File `{filename}` does not exist")
        return
    if not filename.is_file():
        logs.outreach.error(f"File `{filename}` is not a file")
        return


    options = [
        "-halt-on-error",
        "-interaction=nonstopmode",
    ]

    for i in range(ntimes):
        # compile, capturing the output and error streams
        # Run from the directory of the file
        if verbose:
            outlines = []
            try:
                for outline in run_and_capture(["pdflatex", *options, "-jobname", jobname, filename.name], cwd=filename.parent):
                    outlines.append(outline)
                    update_output(outlines, latex_out["latex"])
            except subprocess.CalledProcessError as e:
                report_latex_error("\n".join(outlines), filename, jobname)
                return False
        else:
            # No need to collect the output as we go, so this is faster
            result = subprocess.run(["pdflatex", *options, "-jobname", jobname, filename.name], cwd=filename.parent, capture_output=True)
            outlines = result.stdout.decode("utf-8")
            if result.returncode != 0:
                report_latex_error(outlines, filename, jobname)
                return False
    return True

def _compile_activity_file(filename: Path, directory: Path, jobname: str, verbose: bool = False, ntimes: int = 1, suffix: str = None) -> bool:
    global logs
    if verbose:
        logs.outreach.info(f"Compiling activity file `{directory}/{filename}`")
    
    result = compile_file(directory / filename , jobname, ntimes = ntimes, verbose = verbose)

    if not result:
        logs.outreach.error(f"Failed to compile activity file `{directory}/{filename}`")
        raise RuntimeError(f"Failed to compile activity file `{directory}/{filename}`")

    os.rename(directory / f"{jobname}.pdf", directory / f"{filename.stem}{f'_{suffix}' if suffix is not None else ''}.pdf")

    return result

def compile_cover(directory: Path, jobname: str, verbose: bool = False, ntimes: int = 1) -> bool:
    return _compile_activity_file(Path("cover.tex"), directory, jobname, verbose = verbose, ntimes = ntimes)

def compile_instructions(directory: Path, jobname: str, for_students: bool, with_extension: bool, verbose: bool = False, ntimes: int = 1) -> bool:
    suffix = "student" if for_students else "instructor"
    if with_extension:
        suffix += "_extension"
    
    with open(directory/f"{jobname}.flags", "w+") as file:
        file.write(f"\\student{for_students}\n\\extension{with_extension}\n".lower())

    return _compile_activity_file(Path("instructions.tex"), directory, jobname, verbose = verbose, ntimes = ntimes, suffix = suffix)

def compile_worksheet(directory: Path, jobname: str, for_students: bool, with_extension: bool, verbose: bool = False, ntimes: int = 1) -> bool:
    suffix = "student" if for_students else "instructor"
    if with_extension:
        suffix += "_extension"
    
    with open(directory/f"{jobname}.flags", "w+") as file:
        file.write(f"\\student{for_students}\n\\extension{with_extension}\n".lower())

    return _compile_activity_file(Path("worksheet.tex"), directory, jobname, verbose = verbose, ntimes = ntimes, suffix = suffix)

def compile_all(directory: Path, jobname: str, for_students: List[bool], with_extension: List[bool], verbose: bool = False) -> bool:
    global logs

    total_compilations = len(for_students)*len(with_extension)*2+2
    with logs.outreach.progress_bar(name = "Compiling", total = total_compilations, done_description = "Compilation") as progress:
        progress.update_name("Compiling cover")
        progress.increment()
        result = compile_cover(directory, jobname, verbose = verbose)
        if not result:
            return False
        clean(directory, jobname, verbose = verbose, tex_only = True)
        student_changes = True
        extension_changes = True
        for si, student in enumerate(for_students):
            if not student_changes:
                for _ in with_extension:
                    progress.increment()
                break
            for ei, extension in enumerate(with_extension):
                if not extension_changes:
                    for _ in range(len(with_extension)-ei):
                        progress.increment()
                    break
                progress.update_name(f"Compiling instructions for {'students' if student else 'instructors'} {'with' if extension else 'without'} extension")
                result = result and compile_instructions(directory, jobname, student, extension, verbose = verbose, ntimes = 2)
                if not result:
                    return False
                clean(directory, jobname, verbose = verbose, tex_only = True)
                with open(directory/f"{jobname}.track", "r") as file:
                    contents = [l.strip() for l in file.readlines()]
                    student_changes = contents[0].split("=")[-1].strip().lower() == "true"
                    if verbose and not student_changes:
                        logs.outreach.debug("No changes detected between student and instructor instructions")
                    extension_changes = contents[1].split("=")[-1].strip().lower() == "true"
                    if verbose and not extension_changes:
                        logs.outreach.debug("No changes detected between extension and non-extension instructions")
                progress.increment()

        
        student_changes = True
        extension_changes = True
        for student in for_students:
            if not student_changes:
                for _ in with_extension:
                    progress.increment()
                break
            for extension in with_extension:
                if not extension_changes:
                    progress.increment()
                    break
                progress.update_name(f"Compiling worksheet for {'students' if student else 'instructors'} {'with' if extension else 'without'} extension")
                progress.increment()
                result = result and compile_worksheet(directory, jobname, student, extension, verbose = verbose, ntimes = 2)
                if not result:
                    return False
                clean(directory, jobname, verbose = verbose, tex_only = True)
                with open(directory/f"{jobname}.track", "r") as file:
                    contents = [l.strip() for l in file.readlines()]
                    student_changes = contents[0].split("=")[-1].strip().lower() == "true"
                    if verbose and not student_changes:
                        logs.outreach.debug("No changes detected between student and instructor worksheet")
                    extension_changes = contents[1].split("=")[-1].strip().lower() == "true"
                    if verbose and not extension_changes:
                        logs.outreach.debug("No changes detected between extension and non-extension worksheet")
        progress.update_name("Compiling cover")
        progress.increment()
        result = result and compile_cover(directory, jobname, verbose = verbose, ntimes = 2)
        if not result:
            return False
    return True

def clean(directory: Path, jobname: str, verbose: bool = False, tex_only: bool = False) -> bool:
    global logs
    if tex_only:
        to_clean = [directory / f"{jobname}.{ext}" for ext in ["aux", "log", "toc"]]
    else:
        to_clean = list(directory.glob(f"{jobname}.*"))
    if len(to_clean) == 0:
        logs.outreach.warning(f"No auxiliary files to clean in `{directory}`")
        return True
    with logs.outreach.timeit(f"Cleaning {len(to_clean)} files") if verbose else nullcontext():    
        for filename in to_clean:
            try:
                filename.unlink()
            except FileNotFoundError:
                if verbose and not tex_only:
                    logs.outreach.warning(f"File `{filename}` not found")
    return True

def main():
    global logs
    args, no_args = parse_args()
    directory = Path(args.directory)
    if not directory.exists():
        logs.outreach.critical(f"Directory `{directory}` does not exist")
        return
    if not directory.is_dir():
        logs.outreach.critical(f"Directory `{directory}` is not a directory")
        return
    jobname = directory.name

    if args.clean and no_args:
        clean(directory, jobname, args.verbose)
        return

    for_students = [True, False] if args.audience == 'all' else [args.audience == 'student']
    with_extension = [True] if args.extension_only else [False] if args.no_extension else [False, True]


    match args.type:
        case 'all':
            compile_all(directory, jobname, for_students, with_extension, args.verbose)
        case 'cover':
            with logs.outreach.timeit("Compiling cover"):
                compile_cover(directory, jobname, args.verbose, ntimes = 2)
        case 'instructions':
            with logs.outreach.timeit("Compiling instructions") as t:
                for student in for_students:
                    for extension in with_extension:
                        t.update_name(f"Compiling instructions for {'students' if student else 'instructors'} {'with' if extension else 'without'} extension")
                        compile_instructions(directory, jobname, student, extension, args.verbose, ntimes = 2)
        case 'worksheet':
            with logs.outreach.timeit("Compiling worksheet") as t:
                for student in for_students:
                    for extension in with_extension:
                        t.update_name(f"Compiling worksheet for {'students' if student else 'instructors'} {'with' if extension else 'without'} extension")
                        compile_worksheet(directory, jobname, student, extension, args.verbose, ntimes = 2)
    
    if args.type == 'all' or args.clean:
        clean(directory, jobname, args.verbose)

if __name__ == '__main__':
    setup_logging()
    with logs.live(refresh_per_second = 20):
        main()