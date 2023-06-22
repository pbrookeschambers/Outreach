#!/usr/bin/env python3

from pathlib import Path
import sys
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
    
    for template_name, template in templates.items():
        rprint(f"Creating {directory / f'{template_name}.tex'}")
        template_path = directory / f"{template_name}.tex"
        text = template.format(package_dir=Path(__file__).parent / "packages", title=template_name)
        with open(template_path, "w+") as f:
            f.write(text)

if __name__ == "__main__":
    main()