# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    delivery_exchange_line_ids = fields.One2many('delivery.exchange.line', 'wizard_id', 'Exchange Lines')

    @api.model
    def default_get(self, fields):
        # setting delivery exchange fields
        res = super(ReturnPicking, self).default_get(fields)
        if self.env.context.get('delivery_exchange') and res.get('product_return_moves'):
            for move in res.get('product_return_moves'):
                move[2]['to_refund'] = True
                move[2]['exchange_quantity'] = move[2]['quantity']
        return res

    def _prepare_so_values(self, sale_id, product, quantity):
        '''
            This function prepares the value to use for the creation of the sales order lines

            :param sale_id: sale order for which the lines will be created
            :param product: product that will be added in sales order line
            :param quantity: quantity of sales order line
            :return: sales order line
            :rtype: dict
        '''
        sale_order_line_obj = self.env['sale.order.line']
        sale_order_line_id = sale_order_line_obj.create({
            'name': product.description_sale or product.display_name,
            'product_id': product.id,
            'product_uom_qty': quantity,
            'price_unit': product.list_price,
            'order_id': sale_id.id,
            'company_id': sale_id.company_id.id,
        })
        return sale_order_line_id

    def _create_returns(self):
        # extending method to create new sales order lines based on exchange process
        res = super(ReturnPicking, self)._create_returns()
        sale_id = self.picking_id.sale_id if self.picking_id else False
        if self.env.context.get('delivery_exchange'):
            if sale_id:
                if sale_id.state != 'sale':
                    raise UserError(_("Related sales order must be in sales order State."))

                for line in self.product_return_moves:
                    if line.exchange_quantity > 0 and line.exchange_product_id:
                        product = line.exchange_product_id
                        quantity = line.exchange_quantity
                        self._prepare_so_values(sale_id, product, quantity)
                    else:
                        raise UserError(_("Please specify non-zero quantity for new products."))

                for line in self.delivery_exchange_line_ids:
                    if line.quantity > 0 and line.product_id:
                        product = line.product_id
                        quantity = line.quantity
                        self._prepare_so_values(sale_id, product, quantity)
                    else:
                        raise UserError(_("Please specify non-zero quantity for new products."))
            else:
                raise UserError(_("You Can Only Exchange Products Coming from Sales Orders."))

        return res


class ReturnPickingLine(models.TransientModel):
    _inherit = 'stock.return.picking.line'

    exchange_product_id = fields.Many2one('product.product', string="Exchange Product by", )
    exchange_quantity = fields.Float("Exchange Quantity", digits=dp.get_precision('Product Unit of Measure'), )
