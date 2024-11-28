import dataclasses

import git
import libtmux

from tools import get_or_create_pane


@dataclasses.dataclass
class OdooRepo:
    name: str
    path: str
    versionned: bool = True
    git_repo: git.Repo = dataclasses.field(init=False)
    tmux_pane: libtmux.Pane = dataclasses.field(init=False)
    addons_folder: str | None = None

    def __post_init__(self):
        from tmux import window
        def callback(pane):
            for repo in STORE.repositories.values():
                repo.tmux_pane.resize(width=int(window.width)//(len(STORE.repositories) + 1))

        self.git_repo = git.Repo(self.path)
        self.tmux_pane = get_or_create_pane(window, self.name, self.path, callback)

        STORE.repositories[self.name] = self


@dataclasses.dataclass
class OdooBase:
    name: str
    venv_path: str

    def __post_init__(self):
        STORE.bases[self.name] = self


@dataclasses.dataclass
class Remote:
    name: str
    remote_url: str

    def __post_init__(self):
        STORE.remotes[self.remote_url] = self


@dataclasses.dataclass
class Command:
    name: str
    callback: callable
    help: str
    pattern: str

    def __post_init__(self):
        STORE.commands[self.name] = self


class Store:
    repositories: dict[str, OdooRepo] = {}
    bases: dict[str, OdooBase] = {}
    remotes: dict[str, Remote] = {}
    commands: dict[str, Command] = {}

    def get_remote_name(self, remote_url):
        for remote in self.remotes.values():
            if remote.remote_url == remote_url:
                return remote.name


STORE = Store()
