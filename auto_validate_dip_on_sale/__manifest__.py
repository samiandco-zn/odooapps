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
    'name': "Auto (Delivery + Invoice + Payment) Sale Order",
    'version': '18.0.1.1.0',
    'summary': "Automatically validate (Delivery + Invoice + Payment) , when confirming sales orders  per company",
    'description': """
        This module automates key sales processes by immediately validating 
        Delivery Orders, generating Invoices, and processing Payments upon Sale Order 
        confirmation. Additionally, it provides alerts for low-stock products in Sale Orders, 
        applicable only for companies where this feature is enabled.
    """,
    'author': 'Sami and Co',
    'company': 'Sami and Co',
    'maintainer': 'Sami and Co',
    'website': "https://www.samiandco.net",
    'category': 'Sales',
    'depends': ['base','sale_stock','account'],
    'data': [
        'views/res_company_views.xml',
        'views/sale_order_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,

    'uninstall_hook': 'uninstall_hook',
    #'post_init_hook': 'post_init_hook',
}