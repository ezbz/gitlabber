        

from tqdm import tqdm

class ProgressBar:
    def __init__(self):
        self.progress = None

    def init_progress(self, total):
        if self.progress is None:
            self.progress = tqdm(total=total, unit="projects",
                                 bar_format="{desc}: {percentage:.1f}%|{bar:100}| {n_fmt}/{total_fmt}{postfix}", leave=False)

    def update_progress_length(self, added):
        if self.progress is not None:
            self.progress.total = self.progress.total + added
            self.progress.refresh()

    def show_progress(self, text, category='~'):
        if self.progress is not None:
            self.progress.update(1)
            self.progress.set_postfix({category: text})

    def finish_progress(self):
        if self.progress is not None:
            self.progress.close()
