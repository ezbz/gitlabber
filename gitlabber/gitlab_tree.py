from gitlab import Gitlab
from gitlab.exceptions import GitlabGetError, GitlabListError
from gitlab.exceptions import GitlabGetError
from anytree import Node, RenderTree
from anytree.exporter import DictExporter, JsonExporter
from anytree.importer import DictImporter
from .git import sync_tree
from .format import PrintFormat
from .method import CloneMethod
from .naming import FolderNaming
from .progress import ProgressBar
import yaml
import globre
import logging
import os
log = logging.getLogger(__name__)


class GitlabTree:
    def __init__(self, url, token, method, naming=None, archived=None, includes=[], excludes=[], in_file=None, concurrency=1, recursive=False, disable_progress=False,
                include_shared=True, use_fetch=False, hide_token=False, user_projects=False, group_search=None):
        self.includes = includes
        self.excludes = excludes
        self.url = url
        self.root = Node("", root_path="", url=url, type="root")
        self.gitlab = Gitlab(url, private_token=token,
                             ssl_verify=GitlabTree.get_ca_path())
        self.method = method
        self.naming = naming
        self.archived = archived
        self.in_file = in_file
        self.concurrency = concurrency
        self.recursive = recursive
        self.disable_progress = disable_progress
        self.progress = ProgressBar('* loading tree', disable_progress)
        self.token = token
        self.include_shared = include_shared
        self.use_fetch = use_fetch
        self.hide_token = hide_token
        self.user_projects = user_projects
        self.group_search = group_search

    @staticmethod
    def get_ca_path():
        """
        returns REQUESTS_CA_BUNDLE, CURL_CA_BUNDLE, or True
        """
        return next(item for item in [os.getenv('REQUESTS_CA_BUNDLE', None), os.getenv('CURL_CA_BUNDLE', None), True]
                    if item is not None)

    def is_included(self, node):
        '''
        returns True if the node should be included.
        if there are no include patterns then everything is included
        any include patterns matching the root path will result in inclusion
        '''
        if self.includes is not None:
            for include in self.includes:
                log.debug(f"Checking requested include: {include} with path: {node.root_path}, match {globre.match(include, node.root_path)}")
                if globre.match(include, node.root_path):
                    return True
        else:
            return True

    def is_excluded(self, node):
        '''
        returns True if the node should be excluded
        if the are no exclude patterns then nothing is excluded
        any exclude pattern matching the root path will result in exclusion
        '''
        if self.excludes is not None:
            for exclude in self.excludes:
                log.debug(f"Checking requested exclude: {exclude} with path: {node.root_path}, match {globre.match(exclude, node.root_path)}")
                if globre.match(exclude, node.root_path):
                    return True
        
        return False

    def filter_tree(self, parent):
        for child in parent.children:
            if not child.is_leaf:
                self.filter_tree(child)
                if child.is_leaf:
                    if not self.is_included(child):
                        child.parent = None
                    if self.is_excluded(child):
                        child.parent = None
            else:
                if not self.is_included(child):
                    child.parent = None
                if self.is_excluded(child):
                    child.parent = None

    def root_path(self, node):
        return "/".join([str(n.name) for n in node.path])

    def make_node(self, type, name, parent, url):
        node = Node(name=name, parent=parent, url=url, type=type)
        node.root_path = self.root_path(node)
        return node

    def add_projects(self, parent, projects):
        for project in projects:
            project_id = project.name if self.naming == FolderNaming.NAME else project.path
            project_url = project.ssh_url_to_repo if self.method is CloneMethod.SSH else project.http_url_to_repo
            if self.token is not None and self.method is CloneMethod.HTTP:
              if (not self.hide_token):
                  project_url = project_url.replace('://', '://gitlab-token:%s@' % self.token)
                  log.debug("Generated URL: %s", project_url)
              else:
                  log.debug("Hiding token from project url: %s", project_url)
            node = self.make_node("project", project_id, parent,
                                  url=project_url)
            self.progress.show_progress(node.name, 'project')

    def get_projects(self, group, parent):
        try:
            projects = group.projects.list(archived=self.archived, with_shared=self.include_shared, get_all=True)
            self.progress.update_progress_length(len(projects))
            self.add_projects(parent, projects)
        except GitlabListError as error:
            log.error(f"Error getting projects on {group.name} id: [{group.id}]  error message: [{error.error_message}]")

    def get_subgroups(self, group, parent):
        subgroups = group.subgroups.list(as_list=False, get_all=True)
        self.progress.update_progress_length(len(subgroups))
        for subgroup_def in subgroups:
            try:
                subgroup = self.gitlab.groups.get(subgroup_def.id)
                subgroup_id = subgroup.name if self.naming == FolderNaming.NAME else subgroup.path
                node = self.make_node("subgroup", subgroup_id, parent, url=subgroup.web_url)
                self.progress.show_progress(node.name, 'group')
                self.get_subgroups(subgroup, node)
                self.get_projects(subgroup, node)
            except GitlabListError as error:
                if error.response_code == 404:
                    log.error(f"{error.response_code} error while listing subgroup with name: {group.name} [id: {group.id}]. Check your permissions as you may not have access to it. Message: {error.error_message}")
                    continue
                else:
                    raise error

    def load_gitlab_tree(self):
        log.debug(f"Starting group search with archived: {self.archived} search term: {self.group_search}")
                    
        groups = self.gitlab.groups.list(as_list=False, archived=self.archived, get_all=True, search=self.group_search)
        self.progress.init_progress(len(groups))
        for group in groups:
            if group.parent_id is None:
                group_id = group.name if self.naming == FolderNaming.NAME else group.path
                node = self.make_node("group", group_id, self.root, url=group.web_url)
                self.progress.show_progress(node.name, 'group')
                self.get_subgroups(group, node)
                self.get_projects(group, node)        

        elapsed = self.progress.finish_progress()
        log.debug("Loading projects tree from gitlab took [%s]", elapsed)

    def load_file_tree(self):
        with open(self.in_file, 'r') as stream:
            dct = yaml.safe_load(stream)
            self.root = DictImporter().import_(dct)

    def load_user_tree(self):
        log.debug(f"Starting user project search with archived: {self.archived}")
        self.gitlab.auth()
        user = self.gitlab.users.get(self.gitlab.user.id)
        username = user.username
        projects = user.projects.list(as_list=False, archived=self.archived, get_all=True)
        self.progress.init_progress(len(projects))
        root = self.make_node("group", f"{username}-prsonal-projects", self.root, url=f"{self.url}/users/{username}/projects")
        self.add_projects(root, projects)


    def load_tree(self):
        if self.in_file:
            log.debug("Loading tree from file [%s]", self.in_file)
            self.load_file_tree()
        elif self.user_projects:
            log.debug("Loading user personal projects from gitlab server [%s]", self.url)
            self.load_user_tree()
        else:
            log.debug("Loading projects tree from gitlab server [%s]", self.url)
            self.load_gitlab_tree()

        log.debug("Fetched root node with [%d] projects" % len(
            self.root.leaves))
        self.filter_tree(self.root)

    def print_tree(self, format=PrintFormat.TREE):
        if format is PrintFormat.TREE:
            self.print_tree_native()
        elif format is PrintFormat.YAML:
            self.print_tree_yaml()
        elif format is PrintFormat.JSON:
            self.print_tree_json()
        else:
            log.fatal("Invalid print format [%s]", format)

    def print_tree_native(self):
        for pre, _, node in RenderTree(self.root):
            line = ""
            if node.is_root:
                line = "%s%s [%s]" % (pre, "root", self.url)
            else:
                line = "%s%s [%s]" % (pre, node.name, node.root_path)
            print(line)

    def print_tree_yaml(self):
        dct = DictExporter().export(self.root)
        print(yaml.dump(dct, default_flow_style=False))

    def print_tree_json(self):
        exporter = JsonExporter(indent=2, sort_keys=True)
        print(exporter.export(self.root))

    def sync_tree(self, dest):
        log.debug("Going to clone/pull [%s] groups and [%s] projects" %
                  (len(self.root.descendants) - len(self.root.leaves), len(self.root.leaves)))
        sync_tree(self.root, dest, concurrency=self.concurrency,
                  disable_progress=self.disable_progress, recursive=self.recursive,
                  use_fetch=self.use_fetch, hide_token=self.hide_token)

    def is_empty(self):
        return self.root.height < 1
