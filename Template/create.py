#!/usr/bin/env python3

from pathlib import Path
import sys
import os
from types import SimpleNamespace
from rich import print as rprint
from rich.prompt import Confirm

templates = {
    "cover": r"""\documentclass[draft]{{article}}

\usepackage{{{package_dir}/NUCover}}

\title{{{title}}}
%\description{{}}
%\duration[]{{}} % [extension]{{core}}, in minutes, or like 1h25
%\stage{{...}}
%\workswith{{...}}

%\prerequisite{{...}} % for the core activity
%\prerequisite[]{{...}} % for the extension activity

%\curriculumlink[...]{{...}}
%\curriculumlink[...]{{...}}

\begin{{document}}

\begin{{equipment}}
    ... \\
    ... & ...
\end{{equipment}}    

\end{{document}}
""",

"instructions": r"""\documentclass{{article}}

\usepackage{{{package_dir}/NUInstructions}}

\begin{{document}}

\end{{document}}""",

"worksheet": r"""\documentclass{{article}}

\usepackage{{{package_dir}/NUWorksheet}}

\begin{{document}}

\end{{document}}""",
}


def parse_args():
    if len(sys.argv) < 2:
        rprint("Usage: create.py <directory>")
        sys.exit(1)
    directory = sys.argv[1]
    directory = Path(directory)
    return directory


def main():
    directory = parse_args()
    if directory.exists():
        if not directory.is_dir():
            rprint(f"{directory} already exists, but is not a directory. Delete it or use another name")
            sys.exit(1)
        else:
            response = Confirm.ask(f"{directory} already exists. Continue anyway? This may overwrite existing files in the directory.", default=False)
            if not response:
                sys.exit(0)
    else:
        directory.mkdir(parents=True)

    #directory = directory.absolute()
    
    for template_name, template in templates.items():
        rprint(f"Creating {directory / f'{template_name}.tex'}")
        template_path = directory / f"{template_name}.tex"
        # package_dir relative to the template file
        package_dir = Path(__file__).parent / "packages"
        package_dir = os.path.relpath(package_dir, directory)
        package_dir = str(package_dir).replace("\\", "/") # if we're on Windows, we need to sort out the path separator
        text = template.format(package_dir=package_dir, title=template_name)
        with open(template_path, "w+") as f:
            f.write(text)

if __name__ == "__main__":
    main()