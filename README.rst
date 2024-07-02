.. image:: https://github.com/ezbz/gitlabber/actions/workflows/python-app.yml/badge.svg?branch=master
    :target: https://github.com/ezbz/gitlabber/actions/workflows/python-app.yml

.. image:: https://codecov.io/gh/ezbz/gitlabber/branch/main/graph/badge.svg
  :target: https://codecov.io/gh/ezbz/gitlabber
  
.. image:: https://badge.fury.io/py/gitlabber.svg
    :target: https://badge.fury.io/py/gitlabber
  
.. image:: https://img.shields.io/pypi/l/gitlabber.svg
    :target: https://pypi.python.org/pypi/gitlabber/

.. image:: https://img.shields.io/pypi/pyversions/gitlabber
    :target: https://pypi.python.org/pypi/gitlabber/

.. image:: https://readthedocs.org/projects/gitlabber/badge/?version=latest&style=plastic
    :target: https://gitlabber.readthedocs.io/en/latest/README.html


Gitlabber
=========

* A utility to clone and pull GitLab groups, subgroups, projects based on path selection


Purpose
-------

Gitlabber clones or pulls all projects under a subset of groups / subgroups by building a tree from the GitLab API and allowing you to specify which subset of the tree you want to clone using glob patterns and/or regex expressions.


Installation
------------

* You can install Gitlabber from `PyPi <https://pypi.org/project/gitlabber>`_:

.. code-block:: bash

    pip install gitlabber

* You'll need to create an `access token <https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html>`_ from GitLab with API scopes `read_repository`
  and ``read_api`` (or ``api``, for GitLab versions <12.0)

Usage
-----

* Arguments can be provided via the CLI arguments directly or via environment variables:

    +---------------+---------------+---------------------------+
    | Argument      | Flag          | Environment Variable      |
    +===============+===============+===========================+
    | token         | -t            | `GITLAB_TOKEN`            |
    +---------------+---------------+---------------------------+
    | url           | -u            | `GITLAB_URL`              |
    +---------------+---------------+---------------------------+
    | method        | -m            | `GITLABBER_CLONE_METHOD`  |
    +---------------+---------------+---------------------------+
    | naming        | -n            | `GITLABBER_FOLDER_NAMING` |
    +---------------+---------------+---------------------------+
    | include       | -i            | `GITLABBER_INCLUDE`       |
    +---------------+---------------+---------------------------+
    | exclude       | -x            | `GITLABBER_EXCLUDE`       |
    +---------------+---------------+---------------------------+

* To view the tree run the command with your includes/excludes and the ``-p`` flag. It will print your tree like so:

.. code-block:: bash

    root [http://gitlab.my.com]
    ├── group1 [/group1]
    │   └── subgroup1 [/group1/subgroup1]
    │       └── project1 [/group1/subgroup1/project1]
    └── group2 [/group2]
        ├── subgroup1 [/group2/subgroup1]
        │   └── project2 [/group2/subgroup1/project2]
        ├── subgroup2 [/group2/subgroup2]
        └── subgroup3 [/group2/subgroup3]

* To see how to use glob patterns and regex to filter tree nodes, see the `globre project page <https://pypi.org/project/globre/#details>`_.

* Include/Exclude patterns do not work at the API level but work on the results returned from the API, for large Gitlab installations this can take a lot of time, if you need to reduce the amound of API calls for such projects use the ``--group-search`` parameter to search only for the top level groups the interest you using the `Gitlab Group Search API <https://docs.gitlab.com/ee/api/groups.html#search-for-group>` which allows you to do a partial like query for a Group's path or name

* Cloning vs Pulling: when running Gitlabber consecutively with the same parameters, it will scan the local tree structure; if the project directory exists and is a valid git repository (has .git folder in it) Gitlabber will perform a git pull in the directory, otherwise the project directory will be created and the GitLab project will be cloned into it.

* Cloning submodules: use the ``-r`` flag to recurse git submodules, uses the ``--recursive`` for cloning and utilizes `GitPython's smart update method <https://github.com/gitpython-developers/GitPython/blob/20f4a9d49b466a18f1af1fdfb480bc4520a4cdc2/git/objects/submodule/root.py#L67>`_ for updating cloned repositories

* Printed Usage:

.. code-block:: bash

    usage: gitlabber [-h] [-t token] [-T] [-u url] [--verbose] [-p] [--print-format {json,yaml,tree}] [-n {name,path}] [-m {ssh,http}]
                    [-a {include,exclude,only}] [-i csv] [-x csv] [-r] [-F] [-d] [-s] [-g term] [-U] [--version]
                    [dest]

    Gitlabber - clones or pulls entire groups/projects tree from gitlab

    positional arguments:
    dest                  destination path for the cloned tree (created if doesn't exist)

    options:
    -h, --help            show this help message and exit
    -t token, --token token
                            gitlab personal access token https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html
    -T, --hide-token      use an inline URL token (avoids storing the gitlab personal access token in the .git/config)
    -u url, --url url     base gitlab url (e.g.: 'http://gitlab.mycompany.com')
    --verbose             print more verbose output
    -p, --print           print the tree without cloning
    --print-format {json,yaml,tree}
                            print format (default: 'tree')
    -n {name,path}, --naming {name,path}
                            the folder naming strategy for projects from the gitlab API attributes (default: "name")
    -m {ssh,http}, --method {ssh,http}
                            the git transport method to use for cloning (default: "ssh")
    -a {include,exclude,only}, --archived {include,exclude,only}
                            include archived projects and groups in the results (default: "include")
    -i csv, --include csv
                            comma delimited list of glob patterns of paths to projects or groups to clone/pull
    -x csv, --exclude csv
                            comma delimited list of glob patterns of paths to projects or groups to exclude from clone/pull
    -r, --recursive       clone/pull git submodules recursively
    -F, --use-fetch       clone/fetch git repository (mirrored repositories)
    -d, --dont-checkout   don't checkout pulled git repository
    -s, --include-shared  include shared projects in the results
    -g term, --group-search term
                            only include groups matching the search term, filtering done at the API level (useful for large projects, see: https://docs.gitlab.com/ee/api/groups.html#search-for-group works with partial names of path or name)
    -U, --user-projects   fetch only user personal projects (skips the group tree altogether, group related parameters are ignored). Clones personal projects to '{gitlab-username}-personal-projects'
    --version             print the version

    examples:

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



Debugging
---------
* You can use the ``--verbose`` flag to print Gitlabber debug messages
* For more verbose GitLab messages, you can get the `GitPython <https://gitpython.readthedocs.io/en/stable>`_ module to print more debug messages by setting the environment variable:

.. code-block:: bash

    export GIT_PYTHON_TRACE='full'

Troubleshooting
---------------
* ``GitlabHttpError: 503``: make sure you provide the base URL to your GitLab installation (e.g., `https://gitlab.my.com` and not `https://gitlab.my.com/some/nested/path`)
* ``git.exc.GitCommandError: Cmd('git') failed due to: exit code(128)`` OR ``ERROR: The project you were looking for could not be found or you don't have permission to view it.``: if you are using Git's SSH method, follow the `SSH Guide <https://docs.gitlab.com/ee/user/ssh.html>`_ from Gitlab and ensure you have your SSH key in Gitlab for clone or use the HTTP method (``-m http`` flag)
  
Known Limitations
-----------------
* Renaming, moving and deleting projects: Gitlabber doesn't maintain local tree state (projects and groups). For that reason is does not rename move or delete local projects when they are modified on the server. When projects are moved or renamed, Gitlabber will clone them again under their new name or location. When deleted, Gitlabber will not delete the local project.
* Folder naming strategy: Consecutively running Gitlabber with different values for the ``-n`` parameter will produce undesirable results. Use the same value as previous runs, or simply don't change it from the default (project name).
* If you're going to clone a large number of projects, observe rate limits `for gitlab.com <https://docs.gitlab.com/ee/user/gitlab_com/index.html#gitlabcom-specific-rate-limits/>`_, and `for on-premise installations <https://docs.gitlab.com/ee/security/rate_limits.html>`_.
