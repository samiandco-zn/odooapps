from odoo import models, api
from odoo.exceptions import AccessError


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model
    def create(self, vals):
        picking = self.env['stock.picking'].browse(vals.get('picking_id'))

        if picking.source_approved or picking.destination_approved:
            raise AccessError("Line cannot be modified after approval.")

        return super().create(vals)

    def write(self, vals):
        blocked_fields = {'product_id', 'product_uom_qty', 'location_id', 'location_dest_id'}

        for rec in self:
            picking = rec.picking_id
            if picking.source_approved or picking.destination_approved:
                if blocked_fields.intersection(vals):
                    raise AccessError("Quantity, product and locations cannot be modified after approval.")

        return super().write(vals)

    def unlink(self):
        for rec in self:
            picking = rec.picking_id

            if picking.source_approved or picking.destination_approved:
                raise AccessError("Lines cannot be deleted after approval.")

        return super().unlink()