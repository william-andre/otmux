import re
import time
from functools import lru_cache, partial

import git
import libtmux
import libtmux.constants
from libtmux.exc import LibTmuxException
from prompt_toolkit.contrib.regular_languages.compiler import Variables
import psycopg2


def get_or_create_window(session: libtmux.Session, window_name: str):
    try:
        window = session.select_window(window_name)
    except LibTmuxException:
        window = session.new_window(attach=True, window_name=window_name)
    return window


def get_or_create_pane(window: libtmux.Window, pane_name: str, directory: str, create_callback=None):
    if not (pane := window.panes.get(pane_current_path=directory, default=False)):
        direction = libtmux.constants.PaneDirection.Right
        if len(window.panes) <= 2:
            direction = libtmux.constants.PaneDirection.Below
        pane = window.panes[-1].split(attach=True, start_directory=directory, direction=direction)
        pane.cmd('select-pane', '-T', pane_name)
        if create_callback:
            create_callback(pane)
    return pane


def ttl_cache(ttl):
    def decorator(func):
        @lru_cache(maxsize=1)
        def wrapper(_ttl, *args, **kwargs):
            return func(*args, **kwargs)
        return partial(wrapper, time.time() // ttl)
    return decorator


def get_branch(src: git.Repo | str) -> tuple[str, str]:
    branch_name = src.active_branch.name if isinstance(src, git.Repo) else src
    branch_base_re = re.compile(r'^((master)|(saas-\d{2}\.\d)|(\d{2}\.\d))')
    branch_match = branch_base_re.match(branch_name)
    if not branch_match:
        raise Exception('Invalid branch name')
    base_branch = branch_match.group(1)
    return base_branch, branch_name


def get_dirty_repo(repos):
    return [repo.name for repo in repos.values() if repo.git_repo.is_dirty()]


def check_branch_compatibility(repos, vars: Variables):
    if vars.get("ignore_compatibility"):
        return
    base = branch = None
    for repo in repos.values():
        if not repo.versionned:
            continue
        _base, _branch = get_branch(repo.git_repo)
        if not base:
            base = _base
            branch = _branch
        if base != _base:
            raise Exception(f'Version missmatch: {base} != {_base} in {repo.name}')
        if _branch != _base and branch == base:
            branch = _branch
        if branch != _branch and _branch != _base:
            raise Exception(f'Branch missmatch: {branch} != {_branch} in {repo.name}')


@ttl_cache(10)
def existing_branches():
    from models import STORE
    return sorted({
        branch.name
        for repo in STORE.repositories.values()
        for branch in repo.git_repo.branches
    })


@ttl_cache(10)
def existing_databases():
    cnx = psycopg2.connect("dbname=postgres")
    cursor = cnx.cursor()
    cursor.execute("""
        SELECT datname
          FROM pg_database
         WHERE datistemplate = false
      ORDER BY datname
    """)
    return [row[0] for row in cursor.fetchall()]
