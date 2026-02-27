from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    auto_process_mode = fields.Selection([
        ('none', 'No Automation'),
        ('full', 'Auto Full Process'),
        ('invoice', 'Delivery & Invoice'),
        ('delivery', 'Only Delivery'),
    ],
        string="Automation Mode",
        default='full',
    )
    show_auto_process = fields.Boolean(
        compute='_compute_show_auto_process',
        store=False,
    )

    auto_payment_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string="Payment Journal",
        domain="[('type', 'in', ['bank', 'cash']), ('inbound_payment_method_line_ids', '!=', False), ('company_id', "
               "'=', company_id)]",
        default=lambda self: self._default_auto_payment_journal(),
        help="Select the bank or cash journal to be used for automatic payment registration.\n"
             "Only journals with inbound payment methods are shown.",
        tracking=True,
    )

    show_payment_journal = fields.Boolean(
        compute='_compute_show_payment_journal',
        store=False,
    )
    @api.depends('auto_process_mode')
    def _compute_show_payment_journal(self):
        for order in self:
            order.show_payment_journal = (order.auto_process_mode == 'full')

    @api.depends('company_id')
    def _compute_show_auto_process(self):
        for order in self:
            c = order.company_id or order.env.company
            order.show_auto_process = (
                    c.auto_validate_delivery or
                    c.auto_invoice_on_delivery or
                    c.auto_register_payment
            )

    @api.model
    def _auto_validate_picking(self, picking):
        if picking and picking.state == 'assigned':
            try:
                picking.with_context(skip_backorder=True).button_validate()
            except Exception as e:
                self.env['ir.logging'].create({
                    'name': 'Auto-validate delivery failed',
                    'type': 'server',
                    'level': 'error',
                    'message': str(e),
                    'path': __file__,
                    'func': '_auto_validate_picking',
                    'line': '0',
                })

    @api.model
    def _auto_create_and_post_invoice(self, order):
        if order.invoice_status != 'invoiced':
            try:
                invoice = order._create_invoices(grouped=False, final=True)
                if invoice:
                    invoice.action_post()
                return invoice
            except Exception as e:
                self.env['ir.logging'].create({
                    'name': 'Auto-create/post invoice failed',
                    'type': 'server',
                    'level': 'error',
                    'message': str(e),
                    'path': __file__,
                    'func': '_auto_create_and_post_invoice',
                    'line': '0',
                })
        return False

    def _auto_register_full_payment(self, invoice):
        self.ensure_one()

        if invoice.state != 'posted' or invoice.amount_residual <= 0:
            return
        journal = self.auto_payment_journal_id

        if not journal:
            _logger.warning("No payment journal selected on sale order for invoice %s", invoice.name)
            return
        if journal.company_id != invoice.company_id or not journal.inbound_payment_method_line_ids:
            _logger.warning("Selected journal %s is invalid or from wrong company for invoice %s",
                            journal.display_name, invoice.name)
            return

        payment_method_line = journal.inbound_payment_method_line_ids[:1]
        if not payment_method_line:
            _logger.warning("Selected journal %s has no inbound payment method line", journal.name)
            return

        try:
            payment = self.env['account.payment'].create({
                'partner_type': 'customer',
                'payment_type': 'inbound',
                'partner_id': invoice.partner_id.id,
                'amount': invoice.amount_residual,
                'currency_id': invoice.currency_id.id,
                'journal_id': journal.id,  # ← uses selected journal
                'payment_method_line_id': payment_method_line.id,
                'date': fields.Date.context_today(self),
                'memo': f"Auto payment for {invoice.name}",
                'company_id': invoice.company_id.id,
            })

            payment.action_post()

            wizard = self.env['account.payment.register'].with_context(
                active_model='account.move',
                active_ids=invoice.ids,
            ).create({
                'amount': invoice.amount_residual,
                'currency_id': invoice.currency_id.id,
                'payment_date': fields.Date.context_today(self),
                'journal_id': journal.id,
                'payment_method_line_id': payment_method_line.id,
                'partner_id': invoice.partner_id.id,
                'communication': f"Auto payment for {invoice.name}",
                'group_payment': False,
            })
            wizard.action_create_payments()
            _logger.info("Auto payment registered using selected journal %s for invoice %s",
                         journal.name, invoice.name)
        except Exception as e:
            _logger.exception("Auto payment failed for invoice %s using journal %s",
                              invoice.name, journal.name or '(none)')

    def _default_auto_payment_journal(self):
        company = self.env.company

        # First try exact name "Cash"
        journal = self.env['account.journal'].search([
            ('name', '=', 'Cash'),
            ('type', '=', 'cash'),
            ('company_id', '=', company.id),
        ], limit=1)

        # fallback to any cash journal
        if not journal:
            journal = self.env['account.journal'].search([
                ('type', '=', 'cash'),
                ('company_id', '=', company.id),
            ], limit=1)

        return journal.id

    def action_confirm(self):
        for order in self:
            for line in order.order_line:
                if line.product_id.type == 'consu':
                    qty_available = line.product_id.with_context(
                        warehouse=order.warehouse_id.id
                    ).virtual_available

                    if line.product_uom_qty > qty_available:
                        raise ValidationError(_(
                            "Insufficient stock for product '%s' in warehouse '%s'.\n"
                            "Available: %s\n"
                            "Requested: %s"
                        ) % (line.product_id.display_name, order.warehouse_id.name, qty_available,
                             line.product_uom_qty))

        res = super().action_confirm()
        for order in self:
            company = order.company_id
            do_delivery = False
            do_invoice = False
            do_payment = False
            if order.auto_process_mode == 'full':
                do_delivery = do_invoice = do_payment = True
            elif order.auto_process_mode == 'invoice':
                do_delivery = do_invoice = True
            elif order.auto_process_mode == 'delivery':
                do_delivery = True
            do_delivery = do_delivery and company.auto_validate_delivery
            do_invoice = do_invoice and company.auto_invoice_on_delivery
            do_payment = do_payment and company.auto_register_payment

            if do_delivery:
                for picking in order.picking_ids:
                    if picking.picking_type_id.code == 'outgoing' and picking.state == 'assigned':
                        order._auto_validate_picking(picking)
            invoices = False
            if do_invoice:
                invoices = order._create_invoices(grouped=False, final=True)
                if invoices:
                    invoices.action_post()
            if do_payment and invoices:
                for inv in invoices:
                    if inv.state == 'posted' and inv.amount_residual > 0:
                        order._auto_register_full_payment(inv)
        return res
