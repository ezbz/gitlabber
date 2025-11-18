from gitlabber.progress import ProgressBar


def test_progress_track_context_manager():
    bar = ProgressBar(disabled=True)
    with bar.track("task", total=2) as handle:
        handle.advance()
    # No exceptions mean success when disabled


def test_progress_create_task_handle_methods():
    bar = ProgressBar(disabled=True)
    handle = bar.create_task("task", total=3)
    handle.advance()
    handle.complete()


def test_progress_init_progress():
    """Test init_progress creates default task."""
    bar = ProgressBar(disabled=True)
    bar.init_progress(10)
    # Should not raise when disabled


def test_progress_update_progress_length():
    """Test update_progress_length updates task total."""
    bar = ProgressBar(disabled=True)
    bar.init_progress(5)
    bar.update_progress_length(3)
    # Should not raise when disabled


def test_progress_update_progress_length_zero():
    """Test update_progress_length with zero length does nothing."""
    bar = ProgressBar(disabled=True)
    bar.init_progress(5)
    bar.update_progress_length(0)
    # Should not raise


def test_progress_show_progress():
    """Test show_progress updates task description."""
    bar = ProgressBar(disabled=True)
    bar.init_progress(5)
    bar.show_progress("test", "category")
    # Should not raise when disabled


def test_progress_finish_progress():
    """Test finish_progress returns duration string."""
    bar = ProgressBar(disabled=True)
    bar.init_progress(5)
    duration = bar.finish_progress()
    assert isinstance(duration, str)
    assert ":" in duration


def test_progress_context_manager():
    """Test ProgressBar as context manager."""
    with ProgressBar(disabled=True) as bar:
        bar.init_progress(5)
    # Should clean up properly


def test_progress_task_handle_context_manager():
    """Test ProgressTaskHandle as context manager."""
    bar = ProgressBar(disabled=True)
    with bar.track("task", total=5) as handle:
        handle.advance(2)
    # Should complete task on exit


def test_progress_add_task_when_disabled():
    """Test _add_task returns -1 when disabled."""
    bar = ProgressBar(disabled=True)
    task_id = bar._add_task("test", 10)
    assert task_id == -1


def test_progress_update_task_when_disabled():
    """Test _update_task does nothing when disabled."""
    bar = ProgressBar(disabled=True)
    bar._update_task(1, step=1)
    # Should not raise


def test_progress_complete_task_when_disabled():
    """Test _complete_task does nothing when disabled."""
    bar = ProgressBar(disabled=True)
    bar._complete_task(1)
    # Should not raise


def test_progress_complete_task_nonexistent():
    """Test _complete_task handles nonexistent task."""
    bar = ProgressBar(disabled=True)
    bar._complete_task(999)
    # Should not raise

