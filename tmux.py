import libtmux

from tools import get_or_create_window, get_or_create_pane


SESSION_NAME = 'odoo-dev'
ODOO_ROOT = '/home/odoo/git/odoo'

tmux = libtmux.Server()
if not (session := tmux.sessions.get(session_name=SESSION_NAME, default=False)):
    session = tmux.new_session(SESSION_NAME, window_name=SESSION_NAME, x=230, y=60)
window = get_or_create_window(session, SESSION_NAME)
main_pane = window.panes[0]
def init_server_pane(pane: libtmux.Pane):
    main_pane.resize(height=5)
server_pane = get_or_create_pane(window, ODOO_ROOT, 'server', init_server_pane)
