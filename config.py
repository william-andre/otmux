from models import OdooRepo, OdooBase, Remote


ODOO_ROOT = '/home/odoo/git/odoo'

OdooRepo(
    name='odoo',
    path=ODOO_ROOT + '/odoo',
    addons_folder='/addons',
)
OdooRepo(
    name='enterprise',
    path=ODOO_ROOT + '/enterprise',
    addons_folder='',
)
OdooRepo(
    name='upgrade',
    versionned=False,
    path=ODOO_ROOT + '/upgrade',
)
OdooRepo(
    name='upgrade-util',
    versionned=False,
    path=ODOO_ROOT + '/upgrade-util',
)
OdooRepo(
    name='documentation',
    path=ODOO_ROOT + '/documentation',
)
OdooRepo(
    name='design-themes',
    path=ODOO_ROOT + '/design-themes',
    addons_folder='',
)
OdooRepo(
    name='debug',
    path=ODOO_ROOT + '/debug',
    versionned=False,
    addons_folder='',
)

OdooBase('master', ODOO_ROOT + '/.env3.11')
OdooBase('18.0', ODOO_ROOT + '/.env3.11')
OdooBase('saas-17.4', ODOO_ROOT + '/.env3.11')
OdooBase('saas-17.3', ODOO_ROOT + '/.env3.11')
OdooBase('saas-17.2', ODOO_ROOT + '/.env3.11')
OdooBase('saas-17.1', ODOO_ROOT + '/.env3.11')
OdooBase('17.0', ODOO_ROOT + '/.env3.11')
OdooBase('saas-16.4', ODOO_ROOT + '/.env3.11')
OdooBase('saas-16.3', ODOO_ROOT + '/.env3.11')
OdooBase('saas-16.2', ODOO_ROOT + '/.env3.11')
OdooBase('saas-16.1', ODOO_ROOT + '/.env3.11')
OdooBase('16.0', ODOO_ROOT + '/.env3.11')

Remote('origin', 'git@github.com:odoo/odoo')
Remote('dev', 'git@github.com:odoo-dev/odoo')
Remote('origin', 'git@github.com:odoo/enterprise')
Remote('dev', 'git@github.com:odoo-dev/enterprise')
Remote('origin', 'git@github.com:odoo/documentation')
