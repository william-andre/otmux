import os

from tmux import main_pane, tmux, SESSION_NAME
from gui import serve
import config
import commands


if __name__ == '__main__':
    is_nested = bool(os.environ.get('TMUX'))
    if is_nested:
        serve()
    else:
        main_pane.send_keys(f'python3 {__file__}', enter=True, suppress_history=True)
        tmux.attach_session(SESSION_NAME)
