import logging
import os
import sys
import subprocess
import git
from .progress import ProgressBar

log = logging.getLogger(__name__)

progress = ProgressBar()

def sync_tree(root, dest):
    progress.init_progress(len(root.leaves))
    sync_tree_internal(root, dest)
    progress.finish_progress()


def sync_tree_internal(root, dest):    
    for child in root.children:
        path = "%s%s" % (dest, child.root_path)
        if not os.path.exists(path):
            os.makedirs(path)
        if child.is_leaf:
            clone_or_pull_project(child, path)
        if not child.is_leaf:
            sync_tree_internal(child, dest)


def is_git_repo(path):
    try:
        _ = git.Repo(path).git_dir
        return True
    except git.InvalidGitRepositoryError:
        return False


def clone_or_pull_project(node, path):
    if is_git_repo(path):
        '''
        Update existing project
        '''
        log.debug("updating existing project %s", path)
        progress.show_progress(node.name, 'update')
        try:
            repo = git.Repo(path)
            repo.remotes.origin.pull()
        except KeyboardInterrupt:
            log.error("User interrupted")
            sys.exit(0)
        except Exception as e:
            log.error("Error pulling project %s", path)
            log.error(e)
    else:
        '''
        Clone new project
        '''
        log.debug("cloning new project %s", path)
        progress.show_progress(node.name, 'clone')
        try:
            git.Repo.clone_from(node.url, path)
        except KeyboardInterrupt:
            log.error("User interrupted")
            sys.exit(0)
        except Exception as e:
            log.error("Error cloning project %s", path)
            log.error(e)

