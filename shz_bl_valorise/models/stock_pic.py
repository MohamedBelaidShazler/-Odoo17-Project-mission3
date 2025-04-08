from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    price_unit = fields.Float(
        string='Prix Unitaire',
        compute='_compute_price_unit',
        store=True,
        digits=(12, 3)
    )

    price_subtotal = fields.Float(
        string='Prix HT',
        compute='_compute_amounts',
        store=True,
        digits=(12, 3)
    )

    @api.depends('sale_line_id', 'product_id')
    def _compute_price_unit(self):
        for move in self:
            if move.sale_line_id:
                move.price_unit = move.sale_line_id.price_unit
            else:
                move.price_unit = move.product_id.list_price

    @api.depends('price_unit', 'quantity')
    def _compute_amounts(self):
        for move in self:
            move.price_subtotal = move.price_unit * move.quantity


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    amount_untaxed = fields.Float(
        string='Total HT',
        compute='_compute_picking_totals',
        store=True,
        digits=(12, 3)
    )

    amount_tax = fields.Float(
        string='Total TVA',
        compute='_compute_picking_totals',
        store=True,
        digits=(12, 3)
    )

    amount_total = fields.Float(
        string='Total TTC',
        compute='_compute_picking_totals',
        store=True,
        digits=(12, 3)
    )

    @api.depends('move_ids.price_subtotal', 'move_ids.sale_line_id.tax_id')
    def _compute_picking_totals(self):
        for picking in self:

            amount_untaxed = sum(picking.move_ids.mapped('price_subtotal'))  # Montant total hors taxe
            amount_tax = 0.0
            amount_total = 0.0

            for move in picking.move_ids:
                sale_line = move.sale_line_id

                if sale_line and sale_line.tax_id:
                    taxes = sale_line.tax_id.compute_all(
                        move.price_subtotal,
                        quantity=1.0,
                        product=sale_line.product_id,
                        partner=sale_line.order_id.partner_id,
                    )
                    tax_total = taxes.get('total_included', 0.0) - taxes.get('total_excluded', 0.0)
                    amount_tax += tax_total

                    amount_total += move.price_subtotal + tax_total

            picking.amount_untaxed = amount_untaxed
            picking.amount_tax = amount_tax
            picking.amount_total = amount_total

    def action_print_delivery_note(self):
        return self.env.ref('shz_bl_valorise.action_report_delivery_value').report_action(self)






