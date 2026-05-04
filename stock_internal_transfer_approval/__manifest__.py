# -*- coding: utf-8 -*-
#############################################################################
#
#    Sami and Co.
#
#    Copyright (C) 2026-TODAY Sami and Co(<https://www.samiandco.net>)
#    Author: Sami and Co(<https://www.samiandco.net>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Stock Internal Transfer Approval',
    'version': '17.0.1.1.0',
    'description': '''
           This module enables the assignment of a dedicated manager at the warehouse level and 
           introduces a 2-step approval workflow for internal transfers, requiring validation 
           from both the source and destination managers
        ''',
    'author': 'Sami and Co',
    'company': 'Sami and Co',
    'maintainer': 'Sami and Co',
    'website': "https://www.samiandco.net",
    'category': 'Inventory',
    'summary': 'Internal transfer approval workflow',
    'depends': ['stock', 'mail', 'approvals'],
    'data': [
        'views/stock_warehouse_views.xml',
        'views/stock_picking_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
