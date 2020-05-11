import logging
import os
import sys
import subprocess
import git
import concurrent.futures
log = logging.getLogger(__name__)


class Action:
    def __init__(self, node, path):
        self.node = node
        self.path = path

    def __repr__(self):
        return "<Action n:%s p:%s>" % (self.node, self.path)

def collect_actions(root, dest):
    actions = []
    for child in root.children:
        path = "%s%s" % (dest, child.root_path)
        if not os.path.exists(path):
            os.makedirs(path)
        if child.is_leaf:
            actions.append(Action(node=child, path=path))
            # clone_or_pull_project(child, path)
        if not child.is_leaf:
            actions.extend(collect_actions(child, dest))
    return actions


def sync_tree(root, dest):
    actions = collect_actions(root, dest)
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(clone_or_pull_project, actions)
# def sync_tree(root, dest):
#     for child in root.children:
#         path = "%s%s" % (dest, child.root_path)
#         if not os.path.exists(path):        
#             os.makedirs(path)
#         if child.is_leaf:
#             clone_or_pull_project(child, path)
#         if not child.is_leaf:
#             sync_tree(child, dest)

def is_git_repo(path):
    try:
        _ = git.Repo(path).git_dir
        return True
    except git.InvalidGitRepositoryError:
        return False

def clone_or_pull_project(action):
    node = action.node
    path = action.path
    if is_git_repo(path):
        '''
        Update existing project
        '''
        log.info("updating existing project %s", path)
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
        log.info("cloning new project %s", path)
        try:
            git.Repo.clone_from(node.url, path)
        except KeyboardInterrupt:
            log.error("User interrupted")
            sys.exit(0)        
        except Exception as e:
            log.error("Error cloning project %s", path)
            log.error(e)



