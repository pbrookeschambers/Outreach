# Newcastle University Outreach

## Templates

The `Templates/packages` directory contains three LaTeX packages for creating activity documents, two packages for internal use, and some assets. The three packages are:
 - `NUCover.sty` - for generating coversheets for activities
 - `NUInstructions.sty` - for generating instructions for activities
 - `NUWorksheet.sty` - for generating worksheets for activities 

The `Templates` directory also contains the file `compile.py`, which should be used for compiling the activity documents. It's recommended that each activity be given its own directory, containing three latex source files: `cover.tex`, `instructions.tex`, and `worksheet.tex`. The directory structure should look like this, with *relative* package imports:
```
Templates/
├── compile.py
├── packages/
│   ├── NUCover.sty
│   ├── NUInstructions.sty
│   ├── NUIW.sty
│   ├── NUOutreach.sty
│   ├── NUWorksheet.sty
│   ├── ncl_crest.pdf
│   ├── ncl_logo.pdf
│   └── themes/
│       └── ncl.tex
└── some_activity/
    ├── cover.tex
    │   └── "\usepackage{../packages/NUCover}"
    ├── instructions.tex
    │   └── "\usepackage{../packages/NUInstructions}"
    └── worksheet.tex
        └── "\usepackage{../packages/NUWorksheet}"
```

### Coversheets

The coversheet should be a mostly empty document. Most information should be specified in the preamble. Use the following once each:
- `\title{<activity name>}` to specify the name of the activity. This is the only required command.
- `\description{<description>}` to specify a short description of the activity.
- `\duration[<extended>]{<normal>}` to specify the duration (in minutes) of the activity. The optional argument is for the extended duration, if applicable.
- `\stage{<stage>}` to specify the appropriate key stage or age range for the activity.
- `\workswith{<other activities>}` to specify any other activities that work particularly well alongside this one.
- `\oncampusonly{}` to specify that the activity can only be run on campus.

The following commands can be used more than once (if applicable):
- `\prerequisite[]{<prerequisite>}` to specify some prerequisite information. Omit the optional argument if the prerequisite is for the core activity, or include a blank optional argument if the prerequisite is for the extended activity.
- `\curriculumlink[<exam board/section>]{<link>}` to specify a link to the curriculum. The optional argument may be used to specify an exam board and section number.

Within the document, an environment `equipment` is provided. Usually this will be the only content of the document. Within the `equipment` environment, the syntax is very similar to that of `tabular`. Pieces of equipment are separated by `\\` (do not terminate the last entry with `\\`). Optionally, a second "cell" can be used to specify the quantity of the equipment needed per group. If it is not provided, the quantity will be assumed to be one. For example:

```latex
\begin{equipment}
    Test tube rack \\ % defaults to 1
    Test tube & 4 \\ % 4 per group
    Sulfuric acid & \siunit{10}{\milli\litre} \\ % 10 mL per group. Quantity does not have to be a number.
    Pipette 
\end{equipment}
```

**Note:** Compile in `draft` mode for hints about missing information.

### Instructions

The instructions document should import the `NUInstructions` package. A title page and other front matter will be generated automatically, taken from the auxiliary files produced when compiling `cover.tex`.

Most of the `instructions` document is left to the author. However, it's expected that there may be some information which should only be available to the instructor, and some content which should only be given for the extended version of an activity. To this end, several environments are provided. These do not affect formatting. Nesting of these environments should be avoided wherever possible.
 - `studnetonly` - Any content within this environment will only be included in the student version of the document.
 - `instructoronly` - Any content within this environment will only be included in the instructor version of the document.
 - `extensiononly` - Any content within this environment will only be included in the extended version of the document.
 - `studentextextensiononly` - An alternative to nesting `studentonly` and `extensiononly` environments. 
 - `instructorextensiononly` - An alternative to nesting `instructoronly` and `extensiononly` environments.

Additionally, the flag `\extension` is available. Anything after this flag will only be included in the extended version of the document. 

The `compile.py` script will attempt to detect changes between the student and instructor versions of the document, and the extended and core versions. If no changes are detected, the script will compile the minimum number of documents possible. However, this is not foolproof. If you wish to ensure changes are detected, you can set `\studenttrue` and `\extensiontrue` at any point in the document.

#### Tasks

You may wish to divide the instructions into tasks. This can be done with `\task{}` or `\task{<task title>}`. Both will produce a new section with a task number (separate from the section numbering). The macro `\subtask{}` can be used in the same way, producing a subsection with a subtask number (e.g., "Task 2.a"). 

Alternatively, you can use the `task` environment, which produces a `tcolorbox` with a task number. An optional argument can be passed for the task title. The `\subtask` macro works identically within this environment. These boxes are infinitely breakable across page breaks, so this can be quite long if you wish.

The `\task` macro and `task` environment use the same counter, so the can be used concurrently, but this is not recommended.

#### Safety

In addition to the environments above, one command is provided for highlighting safety considerations:
 - `\safety[<instructor's summary>]{<description for students>}`
This will add a "Caution!" box to the instructions at the point that this macro is used, and add to the safety summary in the cover sheet. If the optional argument is provided, this is the description used in the cover sheet; otherwise, the full description is used. The full description is always used in the instructions, regardless of whether it is compiled for students or instructors. 

### Worksheets

The `NUWorksheet` package should be imported. The same environments as for the instructions document are available for the worksheet document (except for `task` and `safety`). `\question`, `\subquestion`, and `\subsubquestion` commands are availabel and act identically to `\task` etc.

Like the `instructions` file, most of `worksheet` is left to the author. However, there are several macros available for allowing space for student responses.
 - `\answertext[<height>]{<sample answer>}` - Produces a box with the specified height (default `10em`) for students to write their answer. The `sample answer` will only be shown in the instructor version of the document.
 - `\answertextlong[<height>]{<sampel answer>}` - Identical to `\answertext` but with a default height of `15em`
 - `\answerinline{<sample answer>}` - Produces an inline underlined space for students to write their answer. The `sample answer` will only be shown in the instructor version of the document. The width is automatically determined by the length of the `sample answer`. While anything can be used as the `sample answer`, a `tikzpicture` will often cause problems.
 - `\answertable{<key-value options>}` - Produces a blank table (optionally with headers). See below for a list of the options available.
 - `\answergraph{<key-value options>}` - Produces a blank graph (optionally with axes, scale etc). See below for a list of the options available. 

#### Answer Tables

The tables can take a comma-separated list of key-value pairs. All keys are optional. The list of keys are:
 - `rows` - The number of rows in the table. Default is `5`.
 - `columns` - The number of columns in the table. Default is `2`.
 - `headers` - A comma-separated list of column headers. Default is no headers. If given, this must have the same number of entries as `columns` (though some can be empty), and will **not** count towards the number of rows.
 - `header style` - The styling of the header row. The final macro here can take the header as an argument (e.g., `header style = {\Large\textbf}`). Default is `\color{ForegroundColour}\bfseries`
 - `minimum column width` - The minimum width of each column. Default is `3cm`.
 - `minimum row height` - The minimum height of each row. Default is `2.5em`.

#### Answer Graphs

Like tables, graphs can take a comma-separated list of key-value pairs. They are as follows:
 - `x min` - The minimum value on the $x$-axis. Default is `0`.
 - `x max` - The maximum value on the $x$-axis. Default is `10`.
 - `x step` - The step size on the $x$-axis between major ticks. Default is `1`.
 - `x minor per major` - The number of minor ticks between major ticks on the $x$-axis. Default is `5`.
 - `x label` - The label for the $x$-axis. Default is `x`. Can be empty (`{}`).
 - `x label style` - The styling of the $x$-axis label. Default is `\color{ForegroundColour}`.
 - `y min` - The minimum value on the $y$-axis. Default is `0`.
 - `y max` - The maximum value on the $y$-axis. Default is `10`.
 - `y step` - The step size on the $y$-axis between major ticks. Default is `1`.
 - `y minor per major` - The number of minor ticks between major ticks on the $y$-axis. Default is `5`.
 - `y label` - The label for the $y$-axis. Default is `y`. Can be empty (`{}`).
 - `y label style` - The styling of the $y$-axis label. Default is `\color{ForegroundColour}`.
 - `x grid size` - The size on the page of each major tick on the $x$-axis. This **must** be a valid dimension. Default is `1cm`.
 - `y grid size` - The size on the page of each major tick on the $y$-axis. This **must** be a valid dimension. Default is `1cm`. 
 - `show axes` - Whether to show the axes. Default is `true`. (Note that this must be lower case.)
 - `show ticks` - Whether to show the axis ticks and tick labels. Default is `true`. (Note that this must be lower case.)
 - `axis labels at end` - Whether to place the axis labels at the end of the axes instead of the centre. Default is `false`. (Note that this must be lower case.)
 - `padding` - The amount of padding around the axes, in units of major axis ticks. Default is `1`.

## `compile.py`

*This has only been tested on Ubuntu linux. I see no reason it wouldn't work on Windows and Mac, but I can't guarantee it.*

```
>>> python3 compile.py -h
╭─ Outreach (Most recent first) ───────────────────────────────────────────────────────────────────╮
│ ─────────────────────────────────────────── 01:26:26 ─────────────────────────────────────────── │
│  INFO      Usage: compile.py [-h] [-v] directory [type] [audience] [-e | -E]                     │
│                                                                                                  │
│                                                                                                  │
│            ┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│            ┃ Argument           ┃ Description                  ┃ Values (default)             ┃  │
│            ┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩  │
│            │ -h,                │ Show this help message and   │                              │  │
│            │ --help             │ exit                         │                              │  │
│            ├────────────────────┼──────────────────────────────┼──────────────────────────────┤  │
│            │ -v,                │ Give more verbose output,    │ False                        │  │
│            │ --verbose          │ including live LaTeX logs    │                              │  │
│            │                    │ during compilation           │                              │  │
│            ├────────────────────┼──────────────────────────────┼──────────────────────────────┤  │
│            │ directory          │ (Required)                   │ Any valid directory          │  │
│            │                    │ Directory to compile         │ containing activity files    │  │
│            ├────────────────────┼──────────────────────────────┼──────────────────────────────┤  │
│            │ type               │ Which activity document to   │ cover,                       │  │
│            │                    │ compile                      │ instructions,                │  │
│            │                    │                              │ worksheet,                   │  │
│            │                    │                              │ all                          │  │
│            ├────────────────────┼──────────────────────────────┼──────────────────────────────┤  │
│            │ audience           │ Which version of the         │ student,                     │  │
│            │                    │ documents to compile         │ instructor,                  │  │
│            │                    │                              │ all                          │  │
│            ├────────────────────┼──────────────────────────────┼──────────────────────────────┤  │
│            │ -e,                │ Compile the extension        │ False                        │  │
│            │ --extension-only   │ activity only. Mutually      │                              │  │
│            │                    │ exclusive with `-E`          │                              │  │
│            ├────────────────────┼──────────────────────────────┼──────────────────────────────┤  │
│            │ -E,                │ Compile activity without     │ False                        │  │
│            │ --no-extension     │ extension only. Mutually     │                              │  │
│            │                    │ exclusive with `-e`          │                              │  │
│            ├────────────────────┼──────────────────────────────┼──────────────────────────────┤  │
│            │ -b,                │ Compile with bibtex          │ False                        │  │
│            │ --bibtex           │                              │                              │  │
│            ├────────────────────┼──────────────────────────────┼──────────────────────────────┤  │
│            │ -c,                │ Options to pass to pdflatex. │ None                         │  │
│            │ --compiler-options │ Do not overwrite jobname or  │                              │  │
│            │                    │ interactionmode unless you   │                              │  │
│            │                    │ are absolutely sure you know │                              │  │
│            │                    │ what you're doing            │                              │  │
│            ├────────────────────┼──────────────────────────────┼──────────────────────────────┤  │
│            │ -C,                │ Clean auxiliary files after  │ False                        │  │
│            │ --clean            │ compilation. This can cause  │ True if `type` is `all`      │  │
│            │                    │ documents to become unaware  │                              │  │
│            │                    │ of their context. If no      │                              │  │
│            │                    │ other options are specified, │                              │  │
│            │                    │ this will only clean         │                              │  │
│            │                    │ auxiliary files without      │                              │  │
│            │                    │ compilation.                 │                              │  │
│            ├────────────────────┼──────────────────────────────┼──────────────────────────────┤  │
│            │ -f,                │ Force compilation of all     │ False                        │  │
│            │  --force-all       │ variants of the documents,   │                              │  │
│            │                    │ even if no changes are       │                              │  │
│            │                    │ detected.                    │                              │  │
│            └────────────────────┴──────────────────────────────┴──────────────────────────────┘  │
│                                                                                                  │
│                                                                                                  │
│            Example: compile.py -v ./cloud_chambers worksheet all -e                              │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```