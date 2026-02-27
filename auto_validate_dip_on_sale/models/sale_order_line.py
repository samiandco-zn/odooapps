from odoo import api, models, _
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id', 'product_uom_qty', 'warehouse_id')
    def _onchange_stock_check(self):
        """ Raise a warning popup during data entry """
        if self.product_id and self.product_id.type == 'consu':
            warehouse = self.order_id.warehouse_id
            qty_available = self.product_id.with_context(warehouse=warehouse.id).virtual_available

            if self.product_uom_qty > qty_available:
                return {
                    'warning': {
                        'title': _('Low Stock Warning'),
                        'message': _(
                            "You are trying to sell %s units of %s, but only %s are available in %s."
                        ) % (self.product_uom_qty, self.product_id.name, qty_available, warehouse.name)
                    }
                }