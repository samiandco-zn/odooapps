from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    auto_validate_delivery = fields.Boolean(
        string="Auto Validate Delivery",
        help="If checked, when a sale order is confirmed in this company, "
             "the related delivery order(s) will be automatically validated (marked as done).",
        default=False,
    )

    auto_invoice_on_delivery = fields.Boolean(
        string="Auto Create & Post Invoice",
        help="If checked, once the delivery is validated, the customer invoice will be "
             "automatically created and posted.",
        default=False,
    )

    auto_register_payment = fields.Boolean(
        string="Auto Register Payment",
        help="If checked, once the invoice is posted, a full payment will be automatically registered using the "
             "default payment method.",
        default=False,
    )
