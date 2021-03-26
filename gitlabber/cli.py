
import os
import sys
import logging
import logging.handlers
import enum
from argparse import ArgumentParser, RawTextHelpFormatter, FileType, SUPPRESS
from .gitlab_tree import GitlabTree
from .format import PrintFormat
from .method import CloneMethod
from .naming import FolderNaming
from .archive import ArchivedResults
from . import __version__ as VERSION

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def main():
    args = parse_args(argv=None if sys.argv[1:] else ['--help'])
    if args.version:
        print(VERSION)
        sys.exit(0) 

    if args.token is None:
        print('Please specify a valid token with the -t flag or the \'GITLAB_TOKEN\' environment variable')
        sys.exit(1)

    if args.url is None:
        print('Please specify a valid gitlab base url with the -u flag or the \'GITLAB_URL\' environment variable')
        sys.exit(1)

    elif args.dest is None and args.print is False:
        print('Please specify a destination for the gitlab tree')
        sys.exit(1)

    config_logging(args)
    includes=split(args.include)
    excludes=split(args.exclude)

    tree = GitlabTree(args.url, args.token, args.method, args.naming, args.archived.api_value, includes,
                      excludes, args.file, args.concurrency, args.recursive, args.verbose)
    log.debug("Reading projects tree from gitlab at [%s]", args.url)
    tree.load_tree()

    if tree.is_empty():
        log.fatal("The tree is empty, check your include/exclude patterns or run with more verbosity for debugging")
        sys.exit(1) 

    if args.print:
        tree.print_tree(args.print_format)
    else:
        tree.sync_tree(args.dest)


def split(arg):
    return arg.split(",") if arg != "" else None

def config_logging(args):
    if args.verbose:
        handler = logging.StreamHandler(sys.stdout)
        logging.root.handlers = []
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logging.root.addHandler(handler)
        level = logging.ERROR if args.print else logging.DEBUG
        logging.root.setLevel(level)
        log.debug("verbose=[%s], print=[%s], log level set to [%s] level", args.verbose, args.print, level)
        os.environ["GIT_PYTHON_TRACE"] = 'full'


def parse_args(argv=None):
    example_text = '''examples:

    clone an entire gitlab tree using a url and a token:
    gitlabber -t <personal access token> -u <gitlab url>

    only print the gitlab tree:
    gitlabber -p .

    clone only projects under subgroup 'MySubGroup' to location '~/GitlabRoot':
    gitlabber -i '/MyGroup/MySubGroup**' ~/GitlabRoot

    clone only projects under group 'MyGroup' excluding any projects under subgroup 'MySubGroup':
    gitlabber -i '/MyGroup**' -x '/MyGroup/MySubGroup**' .

    clone an entire gitlab tree except projects under groups named 'ArchiveGroup':
    gitlabber -x '/ArchiveGroup**' .

    clone projects that start with a case insensitive 'w' using a regular expression:
    gitlabber -i '/{[w].*}' .
    '''

    parser = ArgumentParser(
        description='Gitlabber - clones or pulls entire groups/projects tree from gitlab',
        prog="gitlabber",
        epilog=example_text,
        formatter_class=RawTextHelpFormatter)    
    parser.add_argument(
        'dest',
        nargs='?', 
        type=validate_path,
        help='destination path for the cloned tree (created if doesn\'t exist)')
    parser.add_argument(
        '-t',
        '--token',
        metavar=('token'),
        default=os.environ.get('GITLAB_TOKEN'),
        help='gitlab personal access token https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html')
    parser.add_argument(
        '-u',
        '--url',
        metavar=('url'),
        default=os.environ.get('GITLAB_URL'),
        help='base gitlab url (e.g.: \'http://gitlab.mycompany.com\')')
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='print more verbose output')
    parser.add_argument(
        '-f',
        '--file',
        metavar=('file'),
        help=SUPPRESS)    
    parser.add_argument(
        '-c',
        '--concurrency',
        default=os.environ.get('GITLABBER_GIT_CONCURRENCY', 1),
        type=int,
        metavar=('concurrency'),
        help=SUPPRESS)
    parser.add_argument(
        '-p',
        '--print',
        action='store_true',
        help='print the tree without cloning')
    parser.add_argument(
        '--print-format', 
        type=PrintFormat.argparse,
        default=PrintFormat.TREE,
        choices=list(PrintFormat),
        help='print format (default: \'tree\')')
    parser.add_argument(
        '-n',
        '--naming',
        type=FolderNaming.argparse,
        choices=list(FolderNaming),
        default=FolderNaming.argparse(os.environ.get('GITLABBER_FOLDER_NAMING', "name")),
        help='the folder naming strategy for projects from the gitlab API attributes (default: "name")')
    parser.add_argument(
        '-m',
        '--method',
        type=CloneMethod.argparse,
        choices=list(CloneMethod),
        default=os.environ.get('GITLABBER_CLONE_METHOD', "ssh"),
        help='the git transport method to use for cloning (default: "ssh")')
    parser.add_argument(
        '-a',
        '--archived',
        type=ArchivedResults.argparse,
        choices=list(ArchivedResults),
        default=ArchivedResults.INCLUDE,
        help='include archived projects and groups in the results (default: "include")')
    parser.add_argument(
        '-i',
        '--include',
        metavar=('csv'),
        default=os.environ.get('GITLABBER_INCLUDE', ""),
        help='comma delimited list of glob patterns of paths to projects or groups to clone/pull')
    parser.add_argument(
        '-x',
        '--exclude',
        metavar=('csv'),
        default=os.environ.get('GITLABBER_EXCLUDE', ""),
        help='comma delimited list of glob patterns of paths to projects or groups to exclude from clone/pull')
    parser.add_argument(
        '-r',
        '--recursive',
        action='store_true',
        default=False,
        help='clone/pull git submodules recursively')
    parser.add_argument(
        '--version',
        action='store_true',
        help='print the version')

    args = parser.parse_args(argv)
    args_print = vars(args).copy()
    args_print['token'] = 'xxxxx'
    log.debug("running with args [%s]", args_print)
    return args

def validate_path(value):
    if value.endswith('/'):
        return value[:-1]
    return value

