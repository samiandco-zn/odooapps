from odoo import models, fields, api
from odoo.exceptions import AccessError
from datetime import date

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    source_approved = fields.Boolean(string="Source Approved")
    destination_approved = fields.Boolean(string="Destination Approved")
    cancel_requested = fields.Boolean(string="Cancel Requested", default=False)
    reopened = fields.Boolean(string="Reopened", default=False)

    source_manager_id = fields.Many2one(
        'res.users',
        string="Source Manager",
        compute="_compute_managers",
        store=True,
    )

    destination_manager_id = fields.Many2one(
        'res.users',
        string="Destination Manager",
        compute="_compute_managers",
        store=True,
    )
    can_approve_source = fields.Boolean(
        compute="_compute_can_approve"
    )

    can_approve_destination = fields.Boolean(
        compute="_compute_can_approve"
    )


    @api.depends('picking_type_id', 'location_dest_id', 'location_id')
    def _compute_managers(self):
        for rec in self:
            # Source warehouse manager
            sour_wh = self.env['stock.warehouse'].search([
                ('lot_stock_id', 'child_of', rec.location_id.id)
            ], limit=1)
            rec.source_manager_id = sour_wh.manager_id if sour_wh else False

            dest_wh = self.env['stock.warehouse'].search([
                ('lot_stock_id', 'child_of', rec.location_dest_id.id)
            ], limit=1)

            rec.destination_manager_id = dest_wh.manager_id if dest_wh else False

    @api.depends(
        'source_manager_id',
        'destination_manager_id',
        'source_approved',
        'destination_approved',
        'picking_type_id.code'
    )
    def _compute_can_approve(self):
        current_user = self.env.user
        for rec in self:
            is_internal = rec.picking_type_id.code == 'internal'

            rec.can_approve_source = (
                    is_internal
                    and rec.source_manager_id
                    and rec.source_manager_id == current_user
                    and not rec.source_approved
            )

            rec.can_approve_destination = (
                    is_internal
                    and rec.destination_manager_id
                    and rec.destination_manager_id == current_user
                    and not rec.destination_approved
            )

    def approve_source(self):
        for rec in self:

            if rec.picking_type_id.code != 'internal':
                raise AccessError("Approval only applies to internal transfers.")

            if self.env.user.id != rec.source_manager_id.id:
                raise AccessError(
                    f"Access Denied: Only {rec.source_manager_id.name} can approve this as Source Manager.")

            if rec.source_approved:
                raise AccessError("Source warehouse already approved.")

            rec.source_approved = True

            rec.message_post(
                body=f"{self.env.user.name} approved as Source Warehouse Manager."
            )
            activities = self.env['mail.activity'].search([
                ('res_id', '=', rec.id),
                ('res_model', '=', 'stock.picking'),
                ('user_id', '=', self.env.user.id)
            ])

            activities.action_feedback()
            if rec.destination_manager_id and not rec.destination_approved:
                activity_type = self.env.ref('approvals.mail_activity_data_approval')

                existing_activity = self.env['mail.activity'].search([
                    ('res_id', '=', rec.id),
                    ('res_model', '=', 'stock.picking'),
                    ('user_id', '=', rec.destination_manager_id.id),
                    ('activity_type_id', '=', activity_type.id)
                ], limit=1)

                if not existing_activity:
                    self.env['mail.activity'].create({
                        'activity_type_id': activity_type.id,
                        'summary': "Approve Internal Transfer (Destination)",
                        'note': f"Source approved transfer {rec.name}. Please approve as Destination Manager.",
                        'res_id': rec.id,
                        'res_model_id': self.env['ir.model']._get_id('stock.picking'),
                        'user_id': rec.destination_manager_id.id,
                        'date_deadline': date.today(),
                    })

    def approve_destination(self):
        for rec in self:

            if rec.picking_type_id.code != 'internal':
                raise AccessError("Approval only applies to internal transfers.")

            if rec.destination_manager_id != self.env.user:
                raise AccessError("You are not the destination warehouse manager.")

            if rec.destination_approved:
                raise AccessError("Destination warehouse already approved.")

            rec.destination_approved = True

            rec.message_post(
                body=f"{self.env.user.name} approved as Destination Warehouse Manager."
            )
            activities = self.env['mail.activity'].search([
                ('res_id', '=', rec.id),
                ('res_model', '=', 'stock.picking'),
                ('user_id', '=', self.env.user.id)
            ])

            activities.action_feedback()

            if rec.source_manager_id and not rec.source_approved:
                activity_type = self.env.ref('approvals.mail_activity_data_approval')

                existing_activity = self.env['mail.activity'].search([
                    ('res_id', '=', rec.id),
                    ('res_model', '=', 'stock.picking'),
                    ('user_id', '=', rec.source_manager_id.id),
                    ('activity_type_id', '=', activity_type.id)
                ], limit=1)

                if not existing_activity:
                    self.env['mail.activity'].create({
                        'activity_type_id': activity_type.id,
                        'summary': "Approve Internal Transfer (Source)",
                        'note': f"Destination approved transfer {rec.name}. Please approve as Source Manager.",
                        'res_id': rec.id,
                        'res_model_id': self.env['ir.model']._get_id('stock.picking'),
                        'user_id': rec.source_manager_id.id,
                        'date_deadline': date.today(),
                    })

    def cancel_request(self):
        for rec in self:

            #if self.env.user != rec.destination_manager_id:
             #   raise AccessError("Only destination manager can cancel the request.")

            rec.source_approved = True
            rec.destination_approved = True
            rec.cancel_requested = True

            rec.message_post(
                body=f"{self.env.user.name} requested to cancel and reopen this transfer."
            )
            activities = self.env['mail.activity'].search([
                ('res_id', '=', rec.id),
                ('res_model', '=', 'stock.picking'),
                ('user_id', '=', rec.destination_manager_id.id)
            ])

            activities.unlink()

            activity_type = self.env.ref('approvals.mail_activity_data_approval')

            self.env['mail.activity'].create({
                'activity_type_id': activity_type.id,
                'summary': "Reopen Internal Transfer",
                'note': f"Destination manager requested changes for transfer {rec.name}.",
                'res_id': rec.id,
                'res_model_id': self.env['ir.model']._get_id('stock.picking'),
                'user_id': rec.source_manager_id.id,
                'date_deadline': date.today(),
            })

    def reopen_transfer(self):
        for rec in self:

            if self.env.user != rec.source_manager_id:
                raise AccessError("Only source manager can reopen this transfer.")

            if not rec.cancel_requested:
                raise AccessError("No cancel request exists.")

            rec.reopened = True
            rec.cancel_requested = False
            rec.source_approved = False
            rec.destination_approved = False

            rec.message_post(
                body=f"{self.env.user.name} reopened the transfer for editing."
            )
    def button_validate(self):
        for rec in self:
            if rec.picking_type_id.code != 'internal':
                continue
            if rec.source_manager_id and not rec.source_approved:
                raise AccessError(
                    f"Source warehouse ({rec.location_id.display_name}) "
                    f"manager ({rec.source_manager_id.name}) must approve first."
                )

            if rec.destination_manager_id and not rec.destination_approved:
                raise AccessError(
                    f"Destination warehouse ({rec.location_dest_id.display_name}) "
                    f"manager ({rec.destination_manager_id.name}) must approve first."
                )

        return super().button_validate()

    @api.model
    def create(self, vals):
        return super().create(vals)