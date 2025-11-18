"""Progress reporting for gitlabber operations.

This module provides progress bar functionality using the Rich library
for displaying progress during tree building and repository synchronization.
It supports multiple concurrent progress bars and context manager patterns.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Optional

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)


@dataclass
class ProgressTaskHandle:
    """Context manager for an individual progress task."""

    bar: "ProgressBar"
    task_id: int

    def advance(self, step: int = 1, description: Optional[str] = None) -> None:
        """Advance the task and optionally update its description."""
        self.bar._update_task(self.task_id, step=step, description=description)

    def complete(self) -> None:
        """Mark the task as complete."""
        self.bar._complete_task(self.task_id)

    def __enter__(self) -> "ProgressTaskHandle":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.complete()


class ProgressBar:
    """Manage rich progress bars with optional multi-task support."""

    def __init__(self, description: str = "", disabled: bool = False, console: Optional[Console] = None):
        self.progress: Optional[Progress] = None
        self.description = description or "* working"
        self.disabled = disabled
        self.console = console or Console()
        self.start: Optional[float] = None
        self.default_task_id: Optional[int] = None
        self.tasks: Dict[int, str] = {}

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------
    def __enter__(self) -> "ProgressBar":
        self._ensure_progress()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.finish_progress()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _ensure_progress(self) -> None:
        if self.disabled or self.progress is not None:
            return

        self.start = time.time()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(bar_width=None),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            console=self.console,
            transient=True,
            disable=self.disabled,
        )
        self.progress.start()

    def _add_task(self, description: str, total: int) -> int:
        self._ensure_progress()
        if self.progress is None:
            return -1
        task_id = self.progress.add_task(description, total=total)
        self.tasks[task_id] = description
        if self.default_task_id is None:
            self.default_task_id = task_id
        return task_id

    def _update_task(
        self,
        task_id: Optional[int],
        *,
        step: int = 0,
        description: Optional[str] = None,
    ) -> None:
        if self.disabled or self.progress is None or task_id is None:
            return
        kwargs = {}
        if description:
            kwargs["description"] = description
        self.progress.update(task_id, advance=step, **kwargs)

    def _complete_task(self, task_id: Optional[int]) -> None:
        if self.disabled or self.progress is None or task_id is None:
            return
        task = self.progress.tasks.get(task_id)
        if task is None:
            return
        # Mark task as finished
        remaining = (task.total or 0) - task.completed
        if remaining > 0:
            self.progress.update(task_id, advance=remaining)
        self.progress.remove_task(task_id)
        self.tasks.pop(task_id, None)
        if self.default_task_id == task_id:
            self.default_task_id = None

    # ------------------------------------------------------------------
    # Original single-task API (backward compatible)
    # ------------------------------------------------------------------
    def init_progress(self, total: int) -> None:
        if self.disabled:
            return
        self.default_task_id = self._add_task(self.description, total)

    def update_progress_length(self, length: int) -> None:
        if self.disabled or self.progress is None or self.default_task_id is None or length == 0:
            return
        task = self.progress.tasks[self.default_task_id]
        new_total = (task.total or 0) + length
        self.progress.update(self.default_task_id, total=new_total)

    def show_progress(self, text: str, category: str) -> None:
        if self.disabled or self.default_task_id is None:
            return
        # Enhanced description with more context
        desc = f"{self.description} ({category}: {text})"
        self._update_task(self.default_task_id, step=1, description=desc)
    
    def show_progress_detailed(self, text: str, category: str, operation: Optional[str] = None) -> None:
        """Show progress with detailed operation information.
        
        Args:
            text: Item name being processed
            category: Category of item (e.g., 'project', 'group', 'subgroup')
            operation: Optional specific operation (e.g., 'fetching', 'cloning', 'pulling')
        """
        if self.disabled or self.default_task_id is None:
            return
        if operation:
            desc = f"{self.description} ({operation} {category}: {text})"
        else:
            desc = f"{self.description} ({category}: {text})"
        self._update_task(self.default_task_id, step=1, description=desc)

    def finish_progress(self) -> str:
        if self.progress is not None:
            self.progress.stop()
            self.progress = None
            self.default_task_id = None
            self.tasks.clear()
        end = time.time()
        start = self.start or end
        duration = end - start
        hours, rem = divmod(duration, 3600)
        minutes, seconds = divmod(rem, 60)
        return f"{int(hours):02}:{int(minutes):02}:{seconds:05.2f}"

    # ------------------------------------------------------------------
    # New multi-task helpers
    # ------------------------------------------------------------------
    def create_task(self, description: str, total: int) -> ProgressTaskHandle:
        """Create a new task and return a handle for manual control."""
        task_id = self._add_task(description, total)
        return ProgressTaskHandle(self, task_id)

    def track(self, description: str, total: int) -> ProgressTaskHandle:
        """Context manager for tracking a task."""
        return self.create_task(description, total)
