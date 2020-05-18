import logging
import os
import sys
import subprocess
import git
from .progress import ProgressBar
import concurrent.futures

log = logging.getLogger(__name__)

progress = ProgressBar('* syncing projects')


class GitAction:
    def __init__(self, node, path):
        self.node = node
        self.path = path

def sync_tree(root, dest, concurrency=1, disable_progress=False):
    if not disable_progress:
        progress.init_progress(len(root.leaves))
    actions = get_git_actions(root, dest)
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        executor.map(clone_or_pull_project, actions)
    elapsed = progress.finish_progress()
    log.debug("Syncing projects took [%s]", elapsed)


def get_git_actions(root, dest):
    actions = []
    for child in root.children:
        path = "%s%s" % (dest, child.root_path)
        if not os.path.exists(path):
            os.makedirs(path)
        if child.is_leaf:
            actions.append(GitAction(child, path))            
        if not child.is_leaf:
            actions.extend(get_git_actions(child, dest))
    return actions


def is_git_repo(path):
    try:
        _ = git.Repo(path).git_dir
        return True
    except git.InvalidGitRepositoryError:
        return False


def clone_or_pull_project(action):
    if is_git_repo(action.path):
        '''
        Update existing project
        '''
        log.debug("updating existing project %s", action.path)
        progress.show_progress(action.node.name, 'pull')
        try:
            repo = git.Repo(action.path)
            repo.remotes.origin.pull()
        except KeyboardInterrupt:
            log.fatal("User interrupted")
            sys.exit(0)
        except Exception as e:
            log.debug("Error pulling project %s", action.path, exc_info=True)
    else:
        '''
        Clone new project
        '''
        log.debug("cloning new project %s", action.path)
        progress.show_progress(action.node.name, 'clone')
        try:
            git.Repo.clone_from(action.node.url, action.path)
        except KeyboardInterrupt:
            log.fatal("User interrupted")
            sys.exit(0)
        except Exception as e:
            log.debug("Error cloning project %s", action.path, exc_info=True)

