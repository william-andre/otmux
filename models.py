import dataclasses
from typing import Callable

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
    show: bool = True

    def __post_init__(self):
        from tmux import window
        self.git_repo = git.Repo(self.path)
        self.tmux_pane = get_or_create_pane(window, self.path, self.name, hide=not self.show)
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
    callback: Callable
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
