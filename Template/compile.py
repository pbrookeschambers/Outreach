#!/usr/bin/env python3

import argparse
from dataclasses import dataclass
from typing import Iterator, List, Tuple
from contextlib import nullcontext

import subprocess
import os
from pathlib import Path
import sys
import re

import rich
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.console import Group

from display import LoggerLayout, Layout


# lazy global variables
logs = None
latex_out_box = None
parser = None
args_list = None
live = None


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
    logs = LoggerLayout(Layout(name="outreach"))
    logs.outreach.title = "Outreach"
    logs.outreach.panel_style = "blue"
    if width < 120:
        logs.outreach.narrow = True


# region args


def add_arg(
    name: Tuple[str, str],
    help: str,
    values: List[str] = None,
    default_value: str | bool = None,
    **kwargs: dict,
):
    global parser, args_list
    if isinstance(name, str):
        name = (name,)
    if isinstance(values, str):
        values = (values,)

    parser.add_argument(*name, help=help, **kwargs)
    args_list.append(
        {
            "name": name,
            "help": help,
            "values": values,
            "default": default_value,
        }
    )


def _log_from_argparse(msg: str, _file=None):
    global logs, args_list
    segments = [s.strip().lower() for s in msg.split(":")]
    if segments[0] == "usage":
        print_help()  # automatic usage from argparse misses some information
        return
    msg_type = (
        "error"
        if "error" in segments
        else "warning"
        if "warning" in segments
        else "info"
    )
    if msg_type == "error":
        logs.outreach.error(msg)
        print_help(msg)
    elif msg_type == "warning":
        logs.outreach.warning(msg)
    else:
        logs.outreach.info(msg)


def print_help(error_msg=None, stop_live = True):
    global logs, parser, args_list, live
    term_width, term_height = os.get_terminal_size()
    compact = term_height * term_width < 5000  # roughly enough to fit a lot on screen
    if not compact:
        table = Table(show_lines=True)
    else:
        table = Table(
            box=rich.box.SIMPLE,
            row_styles=["none", "reverse"],
        )
    table.add_column("Argument")
    table.add_column("Description")
    table.add_column("Values ([bold blue]default[/bold blue])")
    for arg in args_list:
        table.add_row(
            (", " if compact else ",\n").join(arg["name"]),
            arg["help"],
            (", " if compact else ",\n").join(
                [
                    f"[bold blue]{v}[/bold blue]" if v == arg["default"] else f"{v}"
                    for v in arg["values"]
                ]
            ),
        )

    usage = "Usage: compile.py directory [type] [audience] [options...]"
    group = [
        Text(usage + "\n", justify="left", style="bold"),
        table,
        Text()
        .append("\nExample: ", style="bold")
        .append("compile.py -v ./cloud_chambers worksheet all -e"),
    ]
    if error_msg is not None:
        group.append(Text("\n").append("Error: ", style="bold red").append(error_msg))
    group = Group(*group)
    live.stop()
    # OS-appropriate method to clear the console
    os.system("cls" if os.name == "nt" else "clear")
    rich.print(Panel(group, title="Outreach", border_style="blue"))


def parse_args():
    global logs, parser, args_list
    parser = argparse.ArgumentParser(description="Compile outreach activities")
    parser._print_message = (
        _log_from_argparse  # hook into argparse to log to rich instead
    )

    args_list = [
        {
            "name": ("-h", "--help"),
            "help": "Show this help message and exit",
            "values": (),
            "default": None,
        }
    ]
    add_arg(
        ("-v", "--verbose"),
        "Give more verbose output, including live LaTeX logs during compilation",
        default_value=False,
        values=(True, False),
        action="store_true",
    )

    add_arg(
        "directory",
        "[red bold](Required)[/red bold]\nDirectory to compile",
        default_value=None,
        values=("Any valid directory containing activity files"),
        metavar="directory",
        type=str,
        nargs=1,
    )

    add_arg(
        "type",
        "Which activity document to compile",
        default_value="all",
        values=("cover", "instructions", "worksheet", "all"),
        metavar="type",
        type=str,
        nargs="?",
        default=None,
    )

    add_arg(
        "audience",
        "Which version of the documents to compile",
        default_value="all",
        values=("instructor", "student", "all"),
        metavar="audience",
        type=str,
        nargs="?",
        default=None,
    )

    add_arg(
        ("-e", "--extension-only"),
        "Compile the extension activity only. Mutually exclusive with `-E`",
        default_value=False,
        values=(True, False),
        action="store_true",
    )

    add_arg(
        ("-E", "--no-extension"),
        "Do not compile the extension activity. Mutually exclusive with `-e`",
        default_value=False,
        values=(True, False),
        action="store_true",
    )

    add_arg(
        ("-b", "--bibtex"),
        "Compile with BibTeX",
        default_value=False,
        values=(True, False),
        action="store_true",
    )

    add_arg(
        ("-c", "--compiler-options"),
        "Options to pass to pdflatex. Do not overwrite jobname or interactionmode unless you are [bold red]absolutely sure[/bold red] you know what you're doing",
        default_value=None,
        values=("Any valid pdflatex options"),
        metavar="options",
        type=str,
        nargs="?",
        default=None,
    )

    add_arg(
        ("-C", "--clean"),
        "Clean auxiliary files after compilation. This can cause documents to become unaware of their context. If no other options are specified, this will only clean auxiliary files without compilation.",
        default_value=False,
        values=(True, False, "(default True if `type` is `all`)"),
        action="store_true",
    )

    add_arg(
        ("-f", "--force-all"),
        "Force compilation of all variants of the documents, even if no changes are detected.",
        default_value=False,
        values=(True, False),
        action="store_true",
    )

    add_arg(
        ("-r", "--remove-old"),
        "Remove all previously compiled pdf documents before compiling.",
        default_value=False,
        values=(True, False),
        action="store_true",
    )

    args = parser.parse_args()

    args.directory = args.directory[0]

    num_args = len(sys.argv) - 1
    if args.clean and num_args - (1 if args.verbose else 0) == 2:
        # We have a directory and clean is true. so don't compile, *just* clean
        return args, True  # args, clean_only

    if args.type is not None:
        args.type = args.type.lower()
        if args.type not in ("cover", "instructions", "worksheet", "all"):
            logs.outreach.critical(
                f"Invalid type: {args.type}. See `compile.py --help` for valid types"
            )
            raise ValueError(
                f"Invalid type: {args.type}. See `compile.py --help` for valid types"
            )
    else:
        args.type = "all"

    if args.type == "all" and args.clean is None:
        args.clean = True

    if args.audience is not None:
        args.audience = args.audience.lower()
        if args.audience not in ("instructor", "student", "all"):
            logs.outreach.critical(
                f"Invalid audience: {args.audience}. See `compile.py --help` for valid audiences"
            )
            raise ValueError(
                f"Invalid audience: {args.audience}. See `compile.py --help` for valid audiences"
            )
    else:
        args.audience = "all"

    if args.extension_only and args.no_extension:
        logs.outreach.warning(
            "Both `--extension-only` and `--no-extension` were specified. Ignoring `--no-extension`"
        )
        args.no_extension = False

    return args, False  # args, clean_only


# endregion args


def update_output(lines: List[str], layout: Layout, max_size=15):
    height = min(max_size, len(lines))
    layout.update(
        Panel(
            Text("\n".join(lines[-height:])),
            height=height,
            title="LaTeX Output",
            border_style="green",
        )
    )


def report_latex_error(lines: List[str], filename: Path, jobname: str):
    for idx in range(len(lines)):
        if lines[idx].strip().startswith("!"):
            break
    else:
        # no error easily found. It's probably within the last 10 lines
        idx = -10

    latex_error = "\n".join(lines[idx:])
    report = Group(
        Text(
            f"pdflatex encountered an error and was unable to compile the file `{filename}`. This is likely the problem:"
        ),
        Panel(
            latex_error,
            title="LaTeX Error",
            border_style="red",
        ),
        Text(f"See the logs ({filename.parent / jobname}.log) for more information."),
    )
    logs.outreach.error(report)


def clean(directory: Path, jobname: str, verbose: bool = False, tex_only: bool = False):
    to_clean = []
    if tex_only:
        to_clean = [
            Path(f"{jobname}.{ext}")
            for ext in ("aux", "log", "out", "synctex.gz", "toc")
        ]
    else:
        to_clean = list(directory.glob(f"{jobname}.*"))

    if len(to_clean) == 0:
        return

    with (
        logs.outreach.timeit(f"Cleaning {len(to_clean)} files")
        if verbose
        else nullcontext()
    ):
        for file in to_clean:
            file.unlink(missing_ok=tex_only)


def remove_old(directory: Path, verbose: bool = False):
    for ftype in ("cover", "instructions", "worksheet"):
        for audience in ("_instructor", "_student", ""):
            for extension in ("", "_extension"):
                filename = directory / f"{ftype}{audience}{extension}.pdf"
                if filename.exists():
                    if verbose:
                        logs.outreach.info(f"Removing {filename}")
                    filename.unlink()


def compile_file(
    filename: Path,
    jobname: str,
    bibtex: bool,
    compiler_options: List[str],
    verbose: bool = False,
    ntimes: int = 1,
):
    global latex_out_box
    if not filename.exists():
        logs.outreach.critical(f"File {filename} does not exist")
        raise FileNotFoundError(f"File {filename} does not exist")
    if not filename.is_file():
        logs.outreach.critical(f"{filename} is not a file")
        raise FileNotFoundError(f"{filename} is not a file")

    if verbose and latex_out_box is None:
        latex_out_box = Layout(name="latex")
        latex_out_box["latex"].size = 15
        logs.outreach.info(latex_out_box)

    options = [
        "-halt-on-error",
        "-interaction=nonstopmode",
        "-jobname",
        jobname,
    ]
    if compiler_options is not None:
        options += compiler_options

    for i in range(ntimes):
        if verbose:
            outlines = []
            try:
                for outline in run_and_capture(
                    ["pdflatex"] + options + [filename.name],
                    cwd=filename.parent,
                ):
                    outlines.append(outline)
                    update_output(outlines, latex_out_box["latex"])
            except subprocess.CalledProcessError:
                report_latex_error(outlines, filename, jobname)
                raise
        else:
            # no need to capture the output live, so this is faster
            result = subprocess.run(
                ["pdflatex"] + options + [filename.name],
                cwd=filename.parent,
                capture_output=True,
            )
            outlines = result.stdout.decode("utf-8").split("\n")
            if result.returncode != 0:
                report_latex_error(outlines, filename, jobname)
                raise subprocess.CalledProcessError(
                    result.returncode, result.args, outlines
                )

    if bibtex:
        logs.outreach.debug("BiBTeX is not yet implemented")


def prune(directory: Path, verbose: bool = False):
    for ftype in ("instructions", "worksheet"):
        if verbose:
            logs.outreach.info(f"Pruning {ftype} files")
        files = list(directory.glob(f"{ftype}*.pdf"))
        if len(files) == 4 or len(files) == 0:
            continue
        if len(files) == 1:
            files[0].rename(directory / f"{ftype}.pdf")
            continue
        if len(files) == 2:
            file_names = [f.stem[len(ftype) + 1 :] for f in files]
            if file_names[0][0:3] == file_names[1][0:3]:
                # either both student or both instructor.
                for file in files:
                    file.rename(
                        directory
                        / file.name.replace("_student", "").replace("_instructor", "")
                    )
            else:
                # student and instructor, either both with or both without extensions
                for file in files:
                    file.rename(directory / file.name.replace("_extension", ""))


def main():
    args, clean_only = parse_args()

    directory = Path(args.directory)
    if not directory.exists():
        logs.outreach.critical(f"Directory {directory} does not exist")
        raise FileNotFoundError(f"Directory {directory} does not exist")
    if not directory.is_dir():
        logs.outreach.critical(f"{directory} is not a directory")
        raise NotADirectoryError(f"{directory} is not a directory")

    jobname = directory.name
    verbose = args.verbose

    if clean_only:
        if verbose:
            logs.outreach.info(f"Cleaning auxiliary files for {jobname}")
        clean(directory, jobname, verbose, tex_only=False)
        return

    if args.remove_old or args.type == "all":
        remove_old(directory, verbose)

    to_compile = []
    variants_audience = (
        [True]
        if args.audience == "student"
        else [False]
        if args.audience == "instructor"
        else [True, False]
    )
    variants_extension = (
        [False]
        if args.no_extension
        else [True]
        if args.extension_only
        else [False, True]
    )
    variants = [(a, e) for a in variants_audience for e in variants_extension]
    if args.type == "all":
        to_compile.append(
            {
                "file": directory / "cover.tex",
                "student": False,
                "extension": False,
                "ntimes": 1,
                "dest": directory / "cover.pdf",
            }
        )
    if args.type in ("all", "instructions"):
        for a, e in variants:
            to_compile.append(
                {
                    "file": directory / "instructions.tex",
                    "student": a,
                    "extension": e,
                    "ntimes": 3, # 3 because we have tikzpicture overlays *and* lastpage, so we need to compile twice for correct tikzpicture location, then once more for correct pagenumbering
                    "dest": directory
                    / f"instructions_{'student' if a else 'instructor'}{'_extension' if e else ''}.pdf",
                }
            )
    if args.type in ("all", "worksheet"):
        for a, e in variants:
            to_compile.append(
                {
                    "file": directory / "worksheet.tex",
                    "student": a,
                    "extension": e,
                    "ntimes": 3,
                    "dest": directory
                    / f"worksheet_{'student' if a else 'instructor'}{'_extension' if e else ''}.pdf",
                }
            )
    if args.type in ("all", "cover"):
        to_compile.append(
            {
                "file": directory / "cover.tex",
                "student": False,
                "extension": False,
                "ntimes": 2,
                "dest": directory / "cover.pdf",
            }
        )

    last_file = None
    num_to_compile = len(to_compile)

    skip_students = []
    skip_extensions = []
    skip_blank = False
    for progress, tc in logs.outreach.track(
        to_compile, name="Compiling", exits_early=True
    ):
        
        # - check that file exists
        # - if it's the same as the last file:
        #   - check if the file has changed, reading from the {jobname}.track file
        #   - If not, skip
        # - compile the file
        # clean text-generated auxiliary files

        if not tc["file"].exists():
            logs.outreach.critical(f"File {tc['file']} does not exist")
            raise FileNotFoundError(f"File {tc['file']} does not exist")

        if last_file is not None and last_file["file"] == tc["file"]:
            if skip_blank:
                last_file = tc
                continue
            if len(skip_students) == 0 and len(skip_extensions) == 0: # only check if we haven't already
                # We've already compiled this file at least once. Check if it's changed since then
                with open(directory / f"{jobname}.track", "r") as file:
                    lines = [l.strip().lower() for l in file.readlines()]
                student_changes = lines[0].split("=")[1].strip() == "true"
                extension_changes = lines[1].split("=")[1].strip() == "true"
                if not student_changes:
                    # Student/instructor makes no difference, so skip any whichever we've not already done
                    skip_students.append(not last_file["student"])
                if not extension_changes:
                    # Extension/no extension makes no difference, so skip any whichever we've not already done
                    skip_extensions.append(not last_file["extension"])
        else:
            skip_students = []
            skip_extensions = []
            skip_blank = False

        if not args.force_all and (
            tc["student"] in skip_students or tc["extension"] in skip_extensions
        ):
            if verbose:
                logs.outreach.info(
                    f"Skipping `{tc['file']}` for {'student' if tc['student'] else 'instructor'} with{'' if tc['extension'] else 'out'} extension"
                )
            last_file = tc
            continue

        if tc["file"].stem != "cover" and not args.force_all:
            # Cover can actually be empty. Otherwise, if the file is empty we skip it
            with open(tc["file"], "r") as file:
                contents = file.read()
                document_contents = re.search(r"^(?<!%)\s*?\\begin{document}(.*?)^(?<!%)\\end{document}", contents, flags = re.DOTALL | re.MULTILINE).group(1)
                document_contents = "\n".join([l for l in document_contents.split("\n") if not l.strip().startswith("%")])
                if len(document_contents.strip()) == 0:
                    if verbose:
                        logs.outreach.info( f"Skipping `{tc['file']}` as it seems to be blank. Use `--force_all` to force compilation.")
                    skip_blank = True
                    last_file = tc
                    continue
        # set flags
        with open(directory / f"{jobname}.flags", "w+") as file:
            file.write(f"\\student{tc['student']}".lower())
            file.write(f"\\extension{tc['extension']}".lower())
        # compile the file
        compile_file(
            tc["file"],
            jobname,
            bibtex=False,
            compiler_options=args.compiler_options,
            verbose=verbose,
            ntimes=tc["ntimes"],
        )
        # move the output file to the destination
        os.rename(directory / f"{jobname}.pdf", tc["dest"])
        # clean text-generated auxiliary files
        clean(directory, jobname, verbose, tex_only=True)
        # update last file
        last_file = tc

    if args.type == "all":
        clean(directory, jobname, verbose, tex_only=False)
        prune(directory, verbose)


if __name__ == "__main__":
    setup_logging()
    with logs.live(refresh_per_second=20) as _live:
        live = _live
        main()
