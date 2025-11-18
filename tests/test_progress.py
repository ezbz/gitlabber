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

