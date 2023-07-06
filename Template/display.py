from dataclasses import dataclass
from pathlib import Path
import rich
from rich.console import Console
from rich.table import Table, Column
from rich.panel import Panel
from rich.traceback import Traceback
from rich.layout import Layout
from rich.text import Text
from rich.style import Style
from rich.rule import Rule
from rich.console import Group
from rich.live import Live
from rich.progress import Progress, BarColumn, TimeRemainingColumn, TimeElapsedColumn, TextColumn, TaskProgressColumn

from enum import Enum, auto
import time
from munch import Munch
from contextlib import contextmanager



class MessageType(Enum):
    INFO = 0
    TRACE = auto()
    DEBUG = auto()
    SUCCESS = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


@dataclass
class Log:
    time: float
    message: str
    message_type: MessageType


def format_time(t: float):
    # format time as HH:MM:SS
    return time.strftime("%H:%M:%S", time.localtime(t))

def format_elapsed_time(t_ns: float):
    # time is in nanoseconds, format in an appropriate unit to 3 significant figures (NOT 3 decimal places)
    timestring = None
    unit = None
    if t_ns < 1e3:
        # return f"{t_ns:#.3g} ns"
        timestring = f"{t_ns:#.3g}"
        unit = "ns"
    elif t_ns < 1e6:
        # return f"{t_ns / 1e3:#.3g} \xb5s"
        timestring = f"{t_ns / 1e3:#.3g}"
        unit = "\xb5s"
    elif t_ns < 1e9:
        # return f"{t_ns / 1e6:#.3g} ms"
        timestring = f"{t_ns / 1e6:#.3g}"
        unit = "ms"
    elif t_ns < 60e9:
        # return f"{t_ns / 1e9:#.3g} s"
        timestring = f"{t_ns / 1e9:#.3g}"
        unit = "s"
    elif t_ns < 60e9 * 60:
        # return as ##m ##s
        m = int(t_ns / 60e9)
        s = int((t_ns - m * 60e9) / 1e9)
        return f"{m}m {s:0>2d}s"
    else:
        # return as ##h ##m ##s. I really hope we never need this
        h = int(t_ns / 3600e9)
        m = int((t_ns - h * 3600e9) / 60e9)
        s = int((t_ns - h * 3600e9 - m * 60e9) / 1e9)
        return f"{h}h {m:0>2d}m {s:0>2d}s"

    if timestring.endswith("."):
        timestring = timestring[:-1]
    return timestring + " " + unit

class RichLogger:
    def __init__(self, layout: Layout, title=None, panel_style=None):
        self.title = title
        self.layout = layout
        self.logs = []
        self.processes = []
        self.group = None
        self.narrow = False
        self.always_show_processes = False
        if panel_style is None:
            panel_style = "white"
        self.panel_style = panel_style

        self.styles = {
            MessageType.INFO: Style(color="green"),
            MessageType.TRACE: Style(color="blue"),
            MessageType.DEBUG: Style(color="blue"),
            MessageType.SUCCESS: Style(color="green"),
            MessageType.WARNING: Style(color="yellow"),
            MessageType.ERROR: Style(color="red"),
            MessageType.CRITICAL: Style(color="white", bgcolor="red"),
        }

        self.process_persistance = 0.5 # seconds

    # Processes
    # =========
    #
    # We should be able to maintain two types of progress bar, one for defined length processes, and one for indefinite length processes. 
    #
    # Common functionality:
    # ---------------------
    # 
    # - Processes should always show their name, progress bar, and time elapsed.
    # - No auto_update
    # - Processes should be rendered above the logs
    # - When finished, the processes should remain in the layout for 1 second, then be removed
    # - When finished, the process should be added to the logs as a SUCCESS message
    #
    # Defined length processes:
    # -------------------------
    #
    # - Progress bar should also show time remaining
    # - Always defined by an integer number of steps
    # - Should have an increment method to update the total
    # - Should automatically finish when the total is reached
    #
    # Indefinite length processes:
    # ----------------------------
    #
    # - Should have a `finish` method to finish the process
    #
    # When Finsihed:
    # --------------
    #
    # - Should be added to the logs as a SUCCESS message
    # - Set the done_time to the current time
    # - If an indefinite process, we need to give it a total and complete it
    #
    # Rendering:
    # ----------
    #
    # - We maintain a list of tuples, containing:
    #   - process: rich.progress.Progress, which has one task with an index of 0
    #   - indefinite: bool, whether the process is indefinite
    #   - start_time: float, the time the process was started
    #   - done_time: float | None, the time the process was finished, or None if not finished
    # - We will create a rich.console.Group of the processes, and add it to the layout
    # - For each tuple in self.processes:
    #   - If the process is finished, and the finished_time is more than 1 second ago, remove it from the list
    #   - If the process is finished, and the finished_time is less than 1 second ago, render the process
    #   - If the process is not finished, render the process

    def _add_defined_length_process(self, name, total, done_description = None):
        process = Progress(
            TextColumn("[progress.description]{task.description}", table_column = Column(width=20)),
            BarColumn(bar_width=None),
            TaskProgressColumn(table_column = Column(width = 4)),
            TimeRemainingColumn(table_column = Column(width = 7, justify="left")),
            TimeElapsedColumn(table_column = Column(width = 7, justify="right", style = "dim")),
        )
        t = process.add_task(
            name,
            total=total,
            auto_refresh=False,
        )
        start_time = time.perf_counter_ns()
        self.processes.append(
            (
                process,
                False,
                start_time,
                None,
                done_description,
            )
        )
        idx = len(self.processes) - 1
        p = Munch(
            increment = lambda : self.increment_process(t, process, idx),
            finish = lambda : self.finish_process(t, process, idx),
            finished = lambda : process.finished,
            fail = lambda : self.finish_process(t, process, idx, failed = True),
            update_name = lambda name : self.update_process_name(t, process, idx, name),
        )
        self.render()
        return p
    
    def increment_process(self, t, process, idx):
        process.update(t, advance=1)
        if process.finished:
            finished_time = time.perf_counter_ns()
            idx = 0
            for i, p in enumerate(self.processes):
                if p[0] is process:
                    idx = i
                    break
            else:
                raise Exception("Could not find process in self.processes")
            self.processes[idx] = (
                process,
                False,
                self.processes[idx][2],
                finished_time,
                self.processes[idx][4],
            )
            process_time = finished_time - self.processes[idx][2]
            t_string = format_elapsed_time(process_time)
            log_description = process.tasks[0].description if self.processes[idx][4] is None else self.processes[idx][4]
            self.log(f"{log_description} finished in {t_string}", MessageType.SUCCESS)
        self.render()
    
    def update_process_name(self, t, process, idx, name):
        process.tasks[0].description = name
        self.render()

    def _add_indefinite_length_process(self, name, done_description = None):
        process = Progress(
            TextColumn("[progress.description]{task.description}", table_column = Column(width=20)),
            BarColumn(bar_width=None),
            TimeElapsedColumn(table_column = Column(width = 20, justify="right", style = "dim")),
        )
        t = process.add_task(
            name,
            total=None,
            auto_refresh=False,
        )
        start_time = time.perf_counter_ns()
        self.processes.append(
            (
                process,
                True,
                start_time,
                None,
                done_description,
            )
        )
        idx = len(self.processes) - 1
        p = Munch(
            finish = lambda : self.finish_process(t, process, idx),
            finished = lambda : process.finished,
            fail = lambda : self.finish_process(t, process, idx, failed = True),
            update_name = lambda name : self.update_process_name(t, process, idx, name),
        )
        self.render()
        return p
    
    def finish_process(self, t, process, idx, failed = False):
        if process.tasks[t].total is None:
            finished_after = None
            process.update(t, total = 1, completed = 1)# Must be a better way to do this
        else:
            finished_after = process.tasks[t].completed
            process.update(t, completed = process.tasks[t].total)
        finished_time = time.perf_counter_ns()
        idx = 0
        for i, p in enumerate(self.processes):
            if p[0] is process:
                idx = i
                break
        else:
            raise Exception("Could not find process in self.processes")
        self.processes[idx] = (
            process,
            True,
            self.processes[idx][2],
            finished_time,
            self.processes[idx][4],
        )
        process_time = finished_time - self.processes[idx][2]
        t_string = format_elapsed_time(process_time)
        log_description = process.tasks[0].description if self.processes[idx][4] is None else self.processes[idx][4]
        if failed:
            if finished_after is not None and finished_after != process.tasks[t].total:
                self.log(f"{log_description} failed early in {t_string} after {finished_after}/{process.tasks[t].total} steps.", MessageType.ERROR)
            else:
                self.log(f"{log_description} failed in {t_string}", MessageType.ERROR)
            return
        if finished_after is not None and finished_after != process.tasks[t].total:
            self.log(f"{log_description} finished early in {t_string} after {finished_after}/{process.tasks[t].total} steps.", MessageType.SUCCESS)
        else:
            self.log(f"{log_description} finished in {t_string}", MessageType.SUCCESS)

    def render(self):
        processes = self.render_processes()
        if self.narrow:
            logs = self.render_logs_narrow()
        else:
            logs = self.render_logs_wide()

        if processes is False:
            group = Group(
                logs,
            )
        else:
            group = Group(
                processes,
                Text(""), # Spacer
                logs,
            )

        self.layout.update(
            Panel(
                group,
                title=self.title + " [dim](Most recent first)[/dim]",
                title_align="left",
                expand=True,
                border_style=self.panel_style,
            )
        )

    def render_processes(self):
        # render the processes
        if len(self.processes) == 0:
            if self.always_show_processes:
                group = Text("")
            else:
                return False
        else:
            progress_bars = []
            for i, (process, indefinite, start_time, done_time, done_description) in enumerate(self.processes):
                if done_time is not None and done_time < time.perf_counter_ns() - self.process_persistance * 1e9:
                    # remove the process
                    self.processes.pop(i)
                    continue
                progress_bars.append(process)
            group = Group(*progress_bars)
        return Panel(group, border_style = self.panel_style, title = "Processes", title_align = "center", style = self.panel_style)


    def render_logs_wide(self):
        # single table, one colum for time, one for message type, one for message
        table = Table(
            Column(width=8, vertical="top"),
            Column(width=8, vertical="top"),
            "",
            show_header=False,
            box=None,
        )
        last_time = ""
        for log in self.logs[::-1]:
            time_string = format_time(log.time)
            show_time = time_string != last_time
            table.add_row(
                time_string if show_time else "",
                Text(log.message_type.name, style=self.styles[log.message_type]),
                log.message,
            )

            last_time = time_string

        return table

    def render_logs_narrow(self):
        # two column table, message type and message. Timestamps will instead be
        # a Rule between tables. Return a group of the tables.
        if len(self.logs) == 0:
            return Text("")
        tables = []
        last_time = ""
        table = None
        for log in self.logs[::-1]:
            time_string = format_time(log.time)
            show_time = time_string != last_time
            if show_time:
                if table is not None:
                    tables.append(table)
                table = Table(
                    Column(width=8, vertical="top"), "", show_header=False, box=None
                )
                tables.append(Rule(time_string, style="dim"))
            table.add_row(
                Text(log.message_type.name, style=self.styles[log.message_type]),
                log.message,
            )
            last_time = time_string
        tables.append(table)
        return Group(*tables)

    def log(self, message, message_type=MessageType.INFO):
        self._check_can_write()
        if isinstance(message_type, str):
            message_type = MessageType[message_type.upper()]
        elif isinstance(message_type, int):
            message_type = MessageType(message_type)
        self.logs.append(
            Log(
                time=time.time(),
                message=message,
                message_type=message_type,
            )
        )
        self.render()
        return len(self.logs) - 1

    def update_log(self, idx: int, message: str, message_type: MessageType = None, mode: str = "append") -> int:
        """Update a pre-existing log entry. This does not change the time of the log entry.

        Parameters
        ----------
        idx : int
            index of the log entry to update. This is the value returned by the first call to log (or info, debug etc.)
        message : str
            The updated message, or updated part of the message if mode is "append" or "prepend"
        message_type : MessageType, optional
            The message type, by default None. If None, the message type will not be updated.
        mode : str, optional
            The mode in which the log should be updated. Valid options are "replace", "append", and "prepend", by default "append"

        Returns
        -------
        int
            index of the log. This is the same as the index passed to the function.
        """        
        self._check_can_write()
        if isinstance(message_type, str):
            message_type = MessageType[message_type.upper()]
        elif isinstance(message_type, int):
            message_type = MessageType(message_type)
        elif message_type is None:
            message_type = self.logs[idx].message_type
        
        if mode == "replace":
            self.logs[idx] = Log(
                time=self.logs[idx].time,
                message=message,
                message_type=message_type,
            )
        elif mode == "append":
            self.logs[idx] = Log(
                time=self.logs[idx].time,
                message=self.logs[idx].message + message,
                message_type=message_type,
            )
        elif mode == "prepend":
            self.logs[idx] = Log(
                time=self.logs[idx].time,
                message=message + self.logs[idx].message,
                message_type=message_type,
            )
        else:
            raise ValueError(f"Invalid mode {mode}")
        self.render()

    def info(self, message):
        return self.log(message, MessageType.INFO)

    def trace(self, message):
        return self.log(message, MessageType.TRACE)

    def debug(self, message):
        return self.log(message, MessageType.DEBUG)

    def success(self, message):
        return self.log(message, MessageType.SUCCESS)

    def warning(self, message):
        return self.log(message, MessageType.WARNING)

    def error(self, message):
        return self.log(message, MessageType.ERROR)

    def critical(self, message):
        return self.log(message, MessageType.CRITICAL)

    def exception(self, ignore=False):
        idx = self.log(Traceback(), MessageType.ERROR)
        if not ignore:
            quit(1)
        return idx

    def clear(self):
        self.logs = []
        self.render()

    def split_row(self, *args, **kwargs):
        return self.layout.split_row(*args, **kwargs)
    
    def split_column(self, *args, **kwargs):
        return self.layout.split_column(*args, **kwargs)
    
    def add(self, *args, **kwargs):
        return self.layout.add(*args, **kwargs)

    def _check_can_write(self):
        if len(self.layout.children) != 0:
            rich.print("Layout \"{self.layout.name}\" has children, and therefore cannot be written to. Please write to a child layout instead.")
            rich.print(self.layout.tree)
            raise RuntimeError("Cannot write to layout with children.")

    @contextmanager
    def progress_bar(self, *args, indefinite = False, **kwargs):
        try:
            self._check_can_write()
            if indefinite:
                p = self._add_indefinite_length_process(*args, **kwargs)
            else:
                p = self._add_defined_length_process(*args, **kwargs)
            yield p
            p.finish()
            self.render()
        except Exception as e:
            p.fail()
            self.render()
            raise e

    # @contextmanager
    def timeit(self, *args, **kwargs):
        # alias for progress_bar with indefinite = True
        # remove indefinite from kwargs if it exists
        kwargs.pop("indefinite", None)
        return self.progress_bar(*args, indefinite = True, **kwargs)

    # create a wrapper for an iterator which creates and updates a progress bar, with a total of len(iterator)
    def track(self, iterator, *args, exits_early = False, **kwargs):
        self._check_can_write()
        p = self._add_defined_length_process(*args, total = len(iterator), **kwargs)
        need_to_finish = True
        for i in iterator:
            if exits_early:
                yield p, i
            else:
                yield i
            p.increment()
        else:
            need_to_finish = False # we don't need to finish if the iterator was done anyway, which it should be at this point
        if need_to_finish:
            p.finish()
        self.render()

    @contextmanager
    def inform_when_done(self, message: str, message_type = MessageType.INFO, done_message = " [green]Done[/green] in {elapsed_time}.", done_message_type = MessageType.SUCCESS, mode = "append", include_time = True):
        self._check_can_write()
        # create a log entry, and then update it when the context manager exits
        start_time = time.perf_counter_ns()
        idx = self.log(message, message_type)
        yield
        elapsed_time = time.perf_counter_ns() - start_time
        if include_time and "{elapsed_time}" in done_message: # fail quietly if elapsed_time is not in the message, since include_time is set by default
            done_message = done_message.format(elapsed_time = format_elapsed_time(elapsed_time))
        self.update_log(idx, done_message, mode = mode, message_type = done_message_type)


class LoggerLayout:
    def __init__(self, layout: Layout = None, console: Console = None):
        if layout is None:
            layout = Layout(name = "root")
        self._layout = layout
        self.loggers = Munch()
        self._layout_munch = Munch()
        self._add_to_loggers(layout)
        if console is None:
            console = Console()
        self.console = console
        self.file = None

    def set_console(self, console):
        self.console = console

    def redirect_output(self, file: Path):
        self.file = file

    

    @property
    def layout(self):
        return self._layout_munch
    
    def _throw_layout_not_found(self, key):
        g = Group(
            Text(f"Layout \"{key}\" not found. Current layout tree is as follows:"),
            self.layout.root.tree
        )
        self.layout.root.unsplit()
        self.layout.root.update(g)
        raise KeyError(f"Layout \"{key}\" not found.")
    
    def _throw_logger_or_layout_not_found(self, key):
        g = Group(
            Text(f"Logger or layout \"{key}\" not found. Current layout tree is as follows:"),
            self.layout.root.tree,
            Text("Current loggers are as follows:"),
            Text("\n".join(["\t\u2022 " + k for k in self.loggers.keys()]))
        )
        self.layout.root.unsplit()
        self.layout.root.update(g)
        raise KeyError(f"Logger or layout \"{key}\" not found.")
    
    def _throw_logger_not_found(self, key):
        # rich.print(f"Logger \"{key}\" not found. Current loggers are as follows:")
        # rich.print("\n".join(["\t\u2022 " + k for k in self.loggers.keys()]))
        g = Group(
            Text(f"Logger \"{key}\" not found. Current loggers are as follows:"),
            Text("\n".join(["\t\u2022 " + k for k in self.loggers.keys()]))
        )
        self.layout.root.unsplit()
        self.layout.root.update(g)
        raise KeyError(f"Logger \"{key}\" not found.")

    def _throw_layout_already_exists(self, key):
        # rich.print(f"Layout \"{key}\" already exists. Current layout tree is as follows:")
        # rich.print(self.layout.root.tree)
        g = Group(
            Text(f"Layout \"{key}\" already exists. Current layout tree is as follows:"),
            self.layout.root.tree
        )
        self.layout.root.unsplit()
        self.layout.root.update(g)
        raise KeyError(f"Layout \"{key}\" already exists.")

    def _add_to_loggers(self, layout):
        if len(layout.children) == 0:
            if layout.name is None:
                raise ValueError("Layout {layout} must have a name")
            if layout.name in self.loggers:
                raise self._throw_layout_already_exists(layout.name)
            self.loggers[layout.name] = RichLogger(layout, title = layout.name)
            self._layout_munch[layout.name] = layout
        else:
            for child in layout.children:
                self._add_to_loggers(child)

    def split_column(self, *args, parent = None, **kwargs):
        if parent is not None:
            if isinstance(parent, str):
                if parent not in self.layout:
                    self._throw_layout_not_found(parent)
                parent = self.layout[parent]
            elif not isinstance(parent, Layout):
                raise ValueError(f"Invalid parent {parent}")
        else:
            parent = self.layout.root
        # remove parent from self.loggers and delete the RichLogger
        # associated with it
        del self.loggers[parent.name]
        
        res = parent.split_column(*args, **kwargs)
        for a in args:
            if isinstance(a, Layout):
                self._add_to_loggers(a)
        return res
    
    def split_row(self, *args, parent = None, **kwargs):
        if parent is not None:
            if isinstance(parent, str):
                if parent not in self.layout:
                    self._throw_layout_not_found(parent)
                parent = self.layout[parent]
            elif not isinstance(parent, Layout):
                raise ValueError(f"Invalid parent {parent}")
        else:
            parent = self.layout.root
        # remove parent from self.loggers and delete the RichLogger
        # associated with it
        del self.loggers[parent.name]
        
        res = parent.split_row(*args, **kwargs)
        for a in args:
            if isinstance(a, Layout):
                self._add_to_loggers(a)
        return res
    
    def add(self, *args, parent = None, **kwargs):
        if parent is not None:
            if isinstance(parent, str):
                if parent not in self.layout:
                    self._throw_layout_not_found(parent)
                parent = self.layout[parent]
            elif not isinstance(parent, Layout):
                raise ValueError(f"Invalid parent {parent}")
        else:
            parent = self.layout.root
        
        res = parent.add(*args, **kwargs)
        for a in args:
            if isinstance(a, Layout):
                self._add_to_loggers(a)
        return res
    
    def log(self, message, target, message_type=MessageType.INFO):
        if isinstance(message_type, str):
            message_type = MessageType[message_type.upper()]
        elif isinstance(message_type, int):
            message_type = MessageType(message_type)
        if target not in self.loggers:
            self._throw_logger_not_found(target)
        self._check_layout_can_be_written_to(target)
        return self.loggers[target].log(message, message_type)

    def _check_layout_can_be_written_to(self, target):
        if not target in self.layout:
            self._throw_layout_not_found(target)
        if len(self.layout[target].children) != 0:
            rich.print("Target layout \"{target}\" has children, and therefore cannot be written to. The layout tree is as follows:")
            rich.print(self.layout.root.tree)
            raise ValueError(f"Target layout \"{target}\" has children, and therefore cannot be written to.")

    def info(self, message, target):
        return self.log(message, target, MessageType.INFO)

    def trace(self, message, target):
        return self.log(message, target, MessageType.TRACE)
    
    def debug(self, message, target):
        return self.log(message, target, MessageType.DEBUG)

    def success(self, message, target):
        return self.log(message, target, MessageType.SUCCESS)
    
    def warning(self, message, target):
        return self.log(message, target, MessageType.WARNING)
    
    def error(self, message, target):
        return self.log(message, target, MessageType.ERROR)
    
    def critical(self, message, target):
        return self.log(message, target, MessageType.CRITICAL)
    
    def exception(self, target, ignore=False):
        idx = self.log(Traceback(), target, MessageType.ERROR)
        if not ignore:
            quit(1)
        return idx

    def clear(self, target = None):
        if target is None:
            # clear all
            for l in self.loggers:
                self.loggers[l].clear()
        else:
            if target not in self.loggers:
                self._throw_logger_not_found(target)
            self.loggers[target].clear()

    @contextmanager
    def live(self, *args, **kwargs):
        # start a rich Live instance with self.layout, yield it, and stop it
        if self.file is not None:
            # open the file
            self.file = open(self.file, "w")
            self.console = Console(file = self.file)
        if "refresh_per_second" in kwargs:
            rps = kwargs["refresh_per_second"]
            del kwargs["refresh_per_second"]
        else:
            rps = 10
        with Live(self._layout, *args, refresh_per_second=rps, console = self.console, **kwargs) as live:
            for name, logger in self.loggers.items():
                logger.render()
            yield live
        if self.file is not None:
            self.file.close()
            self.console.file = None



    def __getitem__(self, key):
        if key in self.loggers:
            return self.loggers[key]
        elif key in self.layout:
            return self.layout[key]
        else:
            self._throw_logger_or_layout_not_found(key)
        
    def __getattr__(self, key):
        if key in self.loggers:
            return self.loggers[key]
        elif key in self.layout:
            return self.layout[key]
        else:
            self._throw_logger_or_layout_not_found(key)
    
    def __contains__(self, key):
        return key in self.loggers

    def __iter__(self):
        return iter(self.loggers)
    
    def __len__(self):
        return len(self.loggers)


def add_taichi_logging(ti, logs):
    def hijack_taichi_logging(msg, log_level):
        logs.log(msg, message_type = log_level)

    ti._logging.debug    = lambda x: hijack_taichi_logging(x, MessageType.DEBUG)
    ti._logging.trace    = lambda x: hijack_taichi_logging(x, MessageType.TRACE)
    ti._logging.info     = lambda x: hijack_taichi_logging(x, MessageType.INFO)
    ti._logging.warn     = lambda x: hijack_taichi_logging(x, MessageType.WARNING)
    ti._logging.error    = lambda x: hijack_taichi_logging(x, MessageType.ERROR)
    ti._logging.critical = lambda x: hijack_taichi_logging(x, MessageType.CRITICAL)
    ti.lang.misc.print   = lambda x: hijack_taichi_logging(x, MessageType.INFO)

