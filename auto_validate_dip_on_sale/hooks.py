# hooks.py
from odoo import api, SUPERUSER_ID

def post_init_hook(cr, registry):
    """Called after module installation / upgrade"""
    # Create environment if you need to use models
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Example: set default values on all companies
    companies = env['res.company'].search([])
    companies.write({
        'auto_validate_delivery': False,
        'auto_invoice_on_delivery': False,
        'auto_register_payment': False,
    })

def uninstall_hook(cr, registry):
    """Drop columns on uninstall"""
    cr.execute("""
        ALTER TABLE res_company
        DROP COLUMN IF EXISTS auto_validate_delivery,
        DROP COLUMN IF EXISTS auto_invoice_on_delivery,
        DROP COLUMN IF EXISTS auto_register_payment;
    """)


