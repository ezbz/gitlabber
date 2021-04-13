        

from tqdm import tqdm
import time
class ProgressBar:
    def __init__(self, description='', disabled=False):
        self.progress = None
        self.description = description
        self.disabled = disabled
        self.start = None

    def init_progress(self, total):
        if self.progress is None:
            self.start = time.time()
            self.progress = tqdm(total=total, unit="projects",
                                 bar_format="{desc}: {percentage:.1f}%|{bar:80}| {n_fmt}/{total_fmt}{postfix}", desc=self.description, leave=False, disable=self.disabled)

    def update_progress_length(self, added):
        if self.progress is not None:
            self.progress.total = self.progress.total + added
            self.progress.refresh()

    def show_progress(self, text, category='~'):
        if self.progress is not None:
            self.progress.update(1)
            postfix = {category : text}
            self.progress.set_postfix(postfix)

    def finish_progress(self):
        if self.progress is not None:
            self.progress.close()
            end = time.time()
            hours, rem = divmod(end-self.start, 3600)
            minutes, seconds = divmod(rem, 60)
            return "{:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), seconds)
