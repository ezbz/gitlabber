"""Packaging settings."""


from codecs import open
import os
from os.path import abspath, dirname, join
from subprocess import call

from setuptools import Command, find_packages, setup

from gitlabber import __version__


this_dir = abspath(dirname(__file__))
with open(join(this_dir, 'README.rst'), encoding='utf-8') as file:
    long_description = file.read()


class RunTests(Command):
    """Run all tests."""
    description = 'run tests'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        """Run all tests!"""
        errno = call(['py.test'])
        raise SystemExit(errno)
setup(
    python_requires='>=3',
    name = 'gitlabber',
    packages = ['gitlabber'],
    version = __version__,
    description = 'A Gitlab clone/pull utility for backing up or cloning Gitlab groups',
    long_description = long_description,
    url = 'https://github.com/ezbz/gitlabber',
    download_url = 'https://github.com/ezbz/gitlabber/archive/master.zip',
    author = 'Erez Mazor',
    author_email = 'erezmazor@gmail.com',
    license = 'MIT',
    keywords = ['gitlab', 'python', 'cli'], 
    include_package_data = True,

    classifiers = [
        'Development Status :: 4 - Beta',   
        'Intended Audience :: Developers',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',     
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9'
    ],
    setup_requires = [
            'docopt', 
            'anytree', 
            'globre',
            'pyyaml',
            'tqdm',
            'GitPython', 
            'python-gitlab'
    ],
    install_requires = [
            'docopt', 
            'anytree', 
            'globre', 
            'pyyaml',
            'tqdm',
            'GitPython', 
            'python-gitlab'
    ],
    tests_require=  ['coverage', 'pytest', 'pytest-cov', 'pytest-integration'],
    entry_points = {
        'console_scripts': [
            'gitlabber=gitlabber.cli:main',
        ],
    },
    cmdclass = {'test': RunTests},
)
