import requests
from typing import Callable

from prompt_toolkit.contrib.regular_languages.compiler import Variables


from exceptions import AbortCommand
from tools import get_branch, get_dirty_repo, check_branch_compatibility, get_or_create_pane
from models import STORE, Command
from tmux import server_pane


def command(pattern):
    def wrapper(func: Callable):
        Command(
            name=func.__name__,
            callback=func,
            help=func.__doc__ or "",
            pattern=pattern
        )
        return func
    return wrapper

def common_command_line():
    return [
        'odoo/odoo-bin',
        '--addons-path', ','.join(
            str(repo.git_repo.working_dir) + repo.addons_folder
            for repo in STORE.repositories.values()
            if repo.addons_folder is not None
        ),
        '--upgrade-path', ','.join((
            str(STORE.repositories['upgrade'].git_repo.working_dir) + '/migrations',
            str(STORE.repositories['upgrade-util'].git_repo.working_dir) + '/src',
        )),
        '-d', STORE.repositories['odoo'].git_repo.active_branch.name,
    ]

@command(r"(?P<command>rebase) \s* (?P<base>\S*)")
def rebase(vars: Variables):
    """Pull the latest changes."""
    if dirty_repos := get_dirty_repo(STORE.repositories):
        raise AbortCommand('Dirty repos: ' + ', '.join(dirty_repos))
    for repo in STORE.repositories.values():
        if not repo.versionned:
            base = 'master'
        elif vars.get("base"):
            base = vars.get("base")
        else:
            base, _branch = get_branch(repo.git_repo)
        repo.tmux_pane.send_keys(f'git pull origin {base}', enter=True, suppress_history=True)


@command(r"(?P<command>switch) \s+ (?P<target>\S+)  \s* (?P<force>( --force)?)")
def switch(vars: Variables):
    """Checkout on another branch."""
    if dirty_repos := get_dirty_repo(STORE.repositories):
        raise AbortCommand('Dirty repos: ' + ', '.join(dirty_repos))
    force = vars.get("force")
    is_pr = (vars.get("target") or "").isdigit()
    response = requests.get(f'https://runbot.odoo.com/api/branch?name={vars.get("target")}')
    if not response.json():
        raise AbortCommand('Branch not found')
    bundle_id = max((int(x['bundle_id']) for x in response.json() if is_pr or x['bundle_name'] == vars.get("target")), default=None)
    if bundle_id is None:
        raise AbortCommand('No bundle found')
    response = requests.get(f'https://runbot.odoo.com/api/bundle?id={bundle_id}')
    bundle_data = response.json()
    branch_name = bundle_data['name']
    used_branches = {branch['repo']: branch for branch in bundle_data['branches']}
    for commit_info in bundle_data['commits']:
        if commit_info['repo'] not in STORE.repositories:
            if commit_info['repo'] in used_branches:
                raise AbortCommand('Unkown repo: ' + commit_info['repo'] + f'  {STORE.repositories}')
            continue
        repo = STORE.repositories[commit_info['repo']]
        base_branch, branch_name = get_branch(branch_name)
        target_branch = branch_name
        if branch_name in repo.git_repo.branches:
            repo.tmux_pane.send_keys(f'git checkout {branch_name}', enter=True, suppress_history=True)
        elif commit_info['repo'] in used_branches:
            remote = STORE.get_remote_name(used_branches[commit_info['repo']]['remote'])
            repo.tmux_pane.send_keys(f'git fetch {remote} {branch_name}', enter=True, suppress_history=True)
            repo.tmux_pane.send_keys(f'git checkout {branch_name}', enter=True, suppress_history=True)
        elif base_branch in repo.git_repo.branches:
            target_branch = base_branch
            repo.tmux_pane.send_keys(f'git checkout {base_branch}', enter=True, suppress_history=True)
        elif repo.versionned and base_branch in STORE.bases:
            remote = STORE.get_remote_name('git@github.com:odoo/odoo') or 'origin'  # TODO fix
            repo.tmux_pane.send_keys(f'git fetch {remote} {base_branch}', enter=True, suppress_history=True)
            repo.tmux_pane.send_keys(f'git checkout {base_branch}', enter=True, suppress_history=True)
        if force:
            repo.tmux_pane.send_keys(f'git fetch origin {target_branch}', enter=True, suppress_history=True)
            repo.tmux_pane.send_keys(f'git reset --hard {target_branch}', enter=True, suppress_history=True)


@command(r"(?P<command>start)  \s* (?P<args>.*)")
def start(args: Variables):
    """Start the server."""
    try:
        check_branch_compatibility(STORE.repositories, args)
    except Exception as e:
        raise AbortCommand(str(e))
    server_pane.send_keys('C-c', literal=False)
    version = get_branch(STORE.repositories['odoo'].git_repo)[0]
    server_pane.send_keys(f'. {STORE.bases[version].venv_path}/bin/activate', enter=True, suppress_history=True)
    command = common_command_line()
    server_pane.send_keys(' '.join(command), enter=True, suppress_history=True)


@command(r"(?P<command>clean)")
def clean(args: Variables):
    """Clean the terminals."""
    for repo in STORE.repositories.values():
        repo.tmux_pane.send_keys('clear', enter=True, suppress_history=True)


@command(r"(?P<command>push)")
def push(args: Variables):
    """Push the changes."""
    for repo in STORE.repositories.values():
        if repo.git_repo.active_branch.name in STORE.bases:
            continue
        repo.tmux_pane.send_keys('git pushf', enter=True, suppress_history=True)


@command(r"(?P<command>prepare)")
def prepare(args: Variables):
    """Install the dependences of a module."""


@command(r"(?P<command>test) \s* (?P<tags>\S+)")
def test(args: Variables):
    """Run the test tags."""
    try:
        check_branch_compatibility(STORE.repositories, args)
    except Exception as e:
        raise AbortCommand(str(e))
    server_pane.send_keys('C-c', literal=False)
    version = get_branch(STORE.repositories['odoo'].git_repo)[0]
    server_pane.send_keys(f'. {STORE.bases[version].venv_path}/bin/activate', enter=True, suppress_history=True)
    command = common_command_line() + [
        '--test-tags', args.get("tags"),
        '--stop-after-init',
    ]
    server_pane.send_keys(' '.join(command), enter=True, suppress_history=True)


@command(r"(?P<command>upgrade) \s+ (?P<database>\S+)")
def upgrade(args: Variables):
    """Upgrade the database to the checked out version."""


@command(r"(?P<command>backup)")
def backup(args: Variables):
    """Backup the database."""


@command(r"(?P<command>restore)")
def restore(args: Variables):
    """Restore the database to the backup."""


@command(r"(?P<command>show) \s+ (?P<repo>\S+)")
def show(args: Variables):
    """Show the pane."""
    pane_name = args.get("repo")
    if pane_name not in STORE.repositories:
        raise AbortCommand(f'Invalid pane name: {pane_name}')
    repo = STORE.repositories[pane_name]
    get_or_create_pane(server_pane.window, repo.path, show=True)


@command(r"(?P<command>hide) \s+ (?P<repo>\S+)")
def hide(args: Variables):
    """Hide the pane."""
    pane_name = args.get("repo")
    if pane_name not in STORE.repositories:
        raise AbortCommand(f'Invalid pane name: {pane_name}')
    repo = STORE.repositories[pane_name]
    get_or_create_pane(server_pane.window, repo.path, hide=True)
