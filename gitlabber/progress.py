from typing import Optional
import time
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)


class ProgressBar:
    """Render progress information using Rich."""

    def __init__(self, description: str = "", disabled: bool = False):
        self.progress: Optional[Progress] = None
        self.task_id: Optional[int] = None
        self.description = description or "* working"
        self.disabled = disabled
        self.start = time.time()
        self.console = Console()

    def init_progress(self, total: int) -> None:
        if self.disabled or self.progress is not None:
            return

        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(bar_width=None),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console,
            transient=True,
            disable=self.disabled,
        )
        self.progress.start()
        self.task_id = self.progress.add_task(self.description, total=total)

    def update_progress_length(self, length: int) -> None:
        if (
            self.disabled
            or self.progress is None
            or self.task_id is None
            or length == 0
        ):
            return
        task = self.progress.tasks[self.task_id]
        new_total = (task.total or 0) + length
        self.progress.update(self.task_id, total=new_total)

    def show_progress(self, text: str, category: str) -> None:
        if self.disabled or self.progress is None or self.task_id is None:
            return
        desc = f"{self.description} ({category}: {text})"
        self.progress.update(self.task_id, advance=1, description=desc)

    def finish_progress(self) -> str:
        if self.progress is not None:
            self.progress.stop()
            self.progress = None
            self.task_id = None
        end = time.time()
        hours, rem = divmod(end - self.start, 3600)
        minutes, seconds = divmod(rem, 60)
        return f"{int(hours):02}:{int(minutes):02}:{seconds:05.2f}"
