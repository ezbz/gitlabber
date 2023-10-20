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
    def __init__(self, node, path, recursive=False, dont_checkout=False, dont_store_token=False):
        self.node = node
        self.path = path
        self.recursive = recursive
        self.dont_checkout = dont_checkout
        self.dont_store_token = dont_store_token

def sync_tree(root, dest, concurrency=1, disable_progress=False, recursive=False, dont_checkout=False, dont_store_token=False):
    if not disable_progress:
        progress.init_progress(len(root.leaves))
    actions = get_git_actions(root, dest, recursive, dont_checkout, dont_store_token)
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        executor.map(clone_or_pull_project, actions)
    elapsed = progress.finish_progress()
    log.debug("Syncing projects took [%s]", elapsed)


def get_git_actions(root, dest, recursive, dont_checkout, dont_store_token):
    actions = []
    for child in root.children:
        path = "%s%s" % (dest, child.root_path)
        if not os.path.exists(path):
            os.makedirs(path)
        if child.is_leaf:
            actions.append(GitAction(child, path, recursive, dont_checkout, dont_store_token))            
        if not child.is_leaf:
            actions.extend(get_git_actions(child, dest, recursive, dont_checkout, dont_store_token))
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
            if(not action.dont_checkout):
                repo.remotes.origin.pull()
            else:
                repo.remotes.origin.fetch()
            if(action.recursive): 
                repo.submodule_update(recursive=True)
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
        multi_options = []
        if(action.recursive):
            multi_options.append('--recursive')
        if(action.dont_checkout):
            multi_options.append('--mirror')        
        try:
            git.Repo.clone_from(action.node.url, action.path, multi_options=multi_options)
                
        except KeyboardInterrupt:
            log.fatal("User interrupted")
            sys.exit(0)
        except Exception as e:
            log.debug("Error cloning project %s", action.path, exc_info=True)

