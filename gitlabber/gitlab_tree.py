from gitlab import Gitlab
from anytree import Node, RenderTree
from anytree.exporter import DictExporter, JsonExporter
from anytree.importer import DictImporter
from .git import sync_tree
from .format import PrintFormat
from .method import CloneMethod
from .progress import ProgressBar
import yaml
import io
import globre
import logging
import os
log = logging.getLogger(__name__)


class GitlabTree:

    def __init__(self, url, token, method, includes=[], excludes=[], in_file=None, concurrency=1, disable_progress=False):
        self.includes = includes
        self.excludes = excludes
        self.url = url
        self.root = Node("", root_path="", url=url)
        self.gitlab = Gitlab(url, private_token=token)
        self.method = method
        self.in_file = in_file
        self.concurrency = concurrency
        self.disable_progress = disable_progress
        self.progress = ProgressBar('* loading tree', disable_progress)

    def is_included(self, node):
        '''
        returns True if the node should be included.
        if there are no include patterns then everything is included
        any include patterns matching the root path will result in inclusion
        '''
        if self.includes is not None:
            for include in self.includes:
                if globre.match(include, node.root_path):
                    log.debug(
                        "Matched include path [%s] to node [%s]", include, node.root_path)
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
                if globre.match(exclude, node.root_path):
                    log.debug(
                        "Matched exclude path [%s] to node [%s]", exclude, node.root_path)
                    return True
        return False

    def filter_tree(self, parent):
        for child in parent.children:
            if not self.is_included(child):
                child.parent = None
            if self.is_excluded(child):
                child.parent = None
            self.filter_tree(child)

    def root_path(self, node):
        return "/".join([str(n.name) for n in node.path])

    def make_node(self, name, parent, url):
        node = Node(name=name, parent=parent, url=url)
        node.root_path = self.root_path(node)
        return node

    def add_projects(self, parent, projects):
        for project in projects:
            project_url = project.ssh_url_to_repo if self.method is CloneMethod.SSH else project.http_url_to_repo
            node = self.make_node(project.name, parent,
                                  url=project_url)
            self.progress.show_progress(node.name, 'project')

    def get_projects(self, group, parent):
        projects = group.projects.list(as_list=False)
        self.progress.update_progress_length(len(projects))
        self.add_projects(parent, projects)
       

    def get_subgroups(self, group, parent):
        subgroups = group.subgroups.list(as_list=False)
        self.progress.update_progress_length(len(subgroups))
        for subgroup_def in subgroups:
            subgroup = self.gitlab.groups.get(subgroup_def.id)
            node = self.make_node(subgroup.name, parent, url=subgroup.web_url)
            self.progress.show_progress(node.name, 'group')
            self.get_subgroups(subgroup, node)
            self.get_projects(subgroup, node)

    def load_gitlab_tree(self):
        groups = self.gitlab.groups.list(as_list=False)
        self.progress.init_progress(len(groups))
        for group in groups:
            node = self.make_node(group.name, self.root, url=group.web_url)
            self.progress.show_progress(node.name, 'group')
            self.get_subgroups(group, node)
            self.get_projects(group, node)
        
        elapsed = self.progress.finish_progress()
        log.debug("Loading projects tree from gitlab took [%s]", elapsed)

    def load_file_tree(self):
        with open(self.in_file, 'r') as stream:
            dct = yaml.safe_load(stream)
            self.root = DictImporter().import_(dct)

    def load_tree(self):
        if self.in_file:
            log.debug("Loading tree from file [%s]", self.in_file)
            self.load_file_tree()
        else:
            log.debug("Loading projects tree gitlab server [%s]", self.url)
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
                  disable_progress=self.disable_progress)

    def is_empty(self):
        return self.root.height < 1
