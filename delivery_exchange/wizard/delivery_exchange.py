# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class DeliveryExchangeLine(models.TransientModel):
    _name = 'delivery.exchange.line'
    _description = 'Delivery Exchange Line'

    product_id = fields.Many2one('product.product', string="Product", required=True, )
    quantity = fields.Float("Quantity", digits=dp.get_precision('Product Unit of Measure'), required=True)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', readonly=False)
    wizard_id = fields.Many2one('stock.return.picking', string="Wizard")
