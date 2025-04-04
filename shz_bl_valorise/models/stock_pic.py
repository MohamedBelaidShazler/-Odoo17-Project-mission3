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

    @api.depends('price_unit', 'product_uom_qty')
    def _compute_amounts(self):
        for move in self:
            move.price_subtotal = move.price_unit * move.product_uom_qty


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

    @api.depends('move_ids.price_subtotal')
    def _compute_picking_totals(self):
        for picking in self:
            picking.amount_untaxed = sum(picking.move_ids.mapped('price_subtotal'))
            picking.amount_tax = picking.amount_untaxed * 0.19  # TVA 19%
            picking.amount_total = picking.amount_untaxed + picking.amount_tax

    def action_print_delivery_note(self):
        return self.env.ref('shz_bl_valorise.action_report_delivery_value').report_action(self)