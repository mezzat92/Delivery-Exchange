# -*- coding: utf-8 -*-

from odoo.addons.stock.tests.common2 import TestStockCommon


class TestDeliveryExchange(TestStockCommon):

    def test_delivery_exchange_process(self):
        """
        Test a SO with a product invoiced on delivery. Deliver and invoice the SO, then do a exchange
        of the picking and check product quantities.
        """
        # intial so
        self.partner = self.env.ref('base.res_partner_1')
        productA = self.env['product.product'].create(
            {'name': 'Product A', 'type': 'product', 'invoice_policy': 'delivery'})
        productB = self.env['product.product'].create(
            {'name': 'Product B', 'type': 'product', 'invoice_policy': 'delivery'})
        stock_location = self.env.ref('stock.stock_location_stock')
        so_vals = {
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
            'order_line': [(0, 0, {
                'name': productA.name,
                'product_id': productA.id,
                'product_uom_qty': 5.0,
                'product_uom': productA.uom_id.id,
                'price_unit': productA.list_price})],
            'pricelist_id': self.env.ref('product.list0').id,
        }
        self.so = self.env['sale.order'].create(so_vals)
        # confirm our standard so, check the picking
        self.so.action_confirm()
        self.assertTrue(self.so.picking_ids,
                        'Sale Stock: no picking created for "invoice on delivery" storable products')

        # invoice in on delivery, nothing should be invoiced
        self.assertEqual(self.so.invoice_status, 'no',
                         'Sale Stock: so invoice_status should be "no" instead of "%s".' % self.so.invoice_status)

        # deliver completely
        pick = self.so.picking_ids
        pick.move_lines.write({'quantity_done': 5})
        pick.button_validate()

        # Check quantity delivered
        del_qty = sum(sol.qty_delivered for sol in self.so.order_line)
        self.assertEqual(del_qty, 5.0,
                         'Sale Stock: delivered quantity should be 5.0 instead of %s after complete delivery' % del_qty)

        # Check invoice
        self.assertEqual(self.so.invoice_status, 'to invoice',
                         'Sale Stock: so invoice_status should be "to invoice" instead of "%s" before invoicing' % self.so.invoice_status)
        inv_1_id = self.so.action_invoice_create()
        self.assertEqual(self.so.invoice_status, 'invoiced',
                         'Sale Stock: so invoice_status should be "invoiced" instead of "%s" after invoicing' % self.so.invoice_status)
        self.assertEqual(len(inv_1_id), 1,
                         'Sale Stock: only one invoice instead of "%s" should be created' % len(inv_1_id))
        self.inv_1 = self.env['account.invoice'].browse(inv_1_id)
        self.assertEqual(self.inv_1.amount_untaxed, self.inv_1.amount_untaxed,
                         'Sale Stock: amount in SO and invoice should be the same')
        self.inv_1.action_invoice_open()

        # Create return picking
        StockReturnPicking = self.env['stock.return.picking']
        default_data = StockReturnPicking.with_context(active_ids=pick.ids, active_id=pick.ids[0]).default_get(
            ['move_dest_exists', 'original_location_id', 'product_return_moves', 'parent_location_id', 'location_id'])
        return_wiz = StockReturnPicking.with_context(active_ids=pick.ids, active_id=pick.ids[0]).create(default_data)
        return_wiz.product_return_moves.quantity = 2.0  # Return only 2
        return_wiz.product_return_moves.to_refund = True  # Refund these 2
        return_wiz.product_return_moves.exchange_product_id = productB.id  # exchange product
        return_wiz.product_return_moves.exchange_quantity = 2  # exchange quantity
        return_wiz.with_context(delivery_exchange=True).create_returns()

        # Validate return and new delivery pickings
        related_pickings = self.so.picking_ids.filtered(lambda r: r.state != 'done')

        for related_picking in related_pickings:
            related_picking.move_lines.write({'quantity_done': 2})
            related_picking.button_validate()

        # check quantity on hand
        product_quant = self.env['stock.quant'].search(
            [('product_id', '=', productA.id), ('location_id', '=', stock_location.id)])
        self.assertEqual(sum(product_quant.mapped('quantity')), -3)

        exchange_quant = self.env['stock.quant'].search(
            [('product_id', '=', productB.id), ('location_id', '=', stock_location.id)])
        self.assertEqual(sum(exchange_quant.mapped('quantity')), -2)

        # Check invoice
        self.assertEqual(self.so.invoice_status, 'to invoice',
                         'Sale Stock: so invoice_status should be "to invoice" instead of "%s" after picking return' % self.so.invoice_status)
        self.assertAlmostEqual(self.so.order_line[0].qty_delivered, 3.0,
                               msg='Sale Stock: delivered quantity should be 3.0 instead of "%s" after picking return' %
                                   self.so.order_line[0].qty_delivered)

    def test_delivery_exchange_process_with_new_products(self):
        """
        Test a SO with a product invoiced on delivery. Deliver and invoice the SO, then do a exchange
        of the picking and add new products while exchange process then check product quantities.
        """
        # intial so
        self.partner = self.env.ref('base.res_partner_1')
        productA = self.env['product.product'].create(
            {'name': 'Product A', 'type': 'product', 'invoice_policy': 'delivery'})
        productB = self.env['product.product'].create(
            {'name': 'Product B', 'type': 'product', 'invoice_policy': 'delivery'})

        # new products in exchange process
        productC = self.env['product.product'].create(
            {'name': 'Product c', 'type': 'product', 'invoice_policy': 'delivery'})
        productD = self.env['product.product'].create(
            {'name': 'Product D', 'type': 'product', 'invoice_policy': 'delivery'})
        stock_location = self.env.ref('stock.stock_location_stock')
        so_vals = {
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
            'order_line': [(0, 0, {
                'name': productA.name,
                'product_id': productA.id,
                'product_uom_qty': 5.0,
                'product_uom': productA.uom_id.id,
                'price_unit': productA.list_price})],
            'pricelist_id': self.env.ref('product.list0').id,
        }
        self.so = self.env['sale.order'].create(so_vals)
        # confirm our standard so, check the picking
        self.so.action_confirm()
        self.assertTrue(self.so.picking_ids,
                        'Sale Stock: no picking created for "invoice on delivery" storable products')

        # invoice in on delivery, nothing should be invoiced
        self.assertEqual(self.so.invoice_status, 'no',
                         'Sale Stock: so invoice_status should be "no" instead of "%s".' % self.so.invoice_status)

        # deliver completely
        pick = self.so.picking_ids
        pick.move_lines.write({'quantity_done': 5})
        pick.button_validate()
        product1_quant = self.env['stock.quant'].search(
            [('product_id', '=', productA.id), ('location_id', '=', stock_location.id)])

        # Check quantity delivered
        del_qty = sum(sol.qty_delivered for sol in self.so.order_line)
        self.assertEqual(del_qty, 5.0,
                         'Sale Stock: delivered quantity should be 5.0 instead of %s after complete delivery' % del_qty)

        # Check invoice
        self.assertEqual(self.so.invoice_status, 'to invoice',
                         'Sale Stock: so invoice_status should be "to invoice" instead of "%s" before invoicing' % self.so.invoice_status)
        inv_1_id = self.so.action_invoice_create()
        self.assertEqual(self.so.invoice_status, 'invoiced',
                         'Sale Stock: so invoice_status should be "invoiced" instead of "%s" after invoicing' % self.so.invoice_status)
        self.assertEqual(len(inv_1_id), 1,
                         'Sale Stock: only one invoice instead of "%s" should be created' % len(inv_1_id))
        self.inv_1 = self.env['account.invoice'].browse(inv_1_id)
        self.assertEqual(self.inv_1.amount_untaxed, self.inv_1.amount_untaxed,
                         'Sale Stock: amount in SO and invoice should be the same')
        self.inv_1.action_invoice_open()

        # Create return picking
        StockReturnPicking = self.env['stock.return.picking']
        default_data = StockReturnPicking.with_context(active_ids=pick.ids, active_id=pick.ids[0]).default_get(
            ['move_dest_exists', 'original_location_id', 'product_return_moves', 'parent_location_id', 'location_id'])
        return_wiz = StockReturnPicking.with_context(active_ids=pick.ids, active_id=pick.ids[0]).create(default_data)
        return_wiz.product_return_moves.quantity = 2.0  # Return only 2
        return_wiz.product_return_moves.to_refund = True  # Refund these 2
        return_wiz.product_return_moves.exchange_product_id = productB.id  # exchange product
        return_wiz.product_return_moves.exchange_quantity = 2  # exchange quantity

        # add new products in exchange process
        return_wiz.delivery_exchange_line_ids = [
            (0, 0, {'product_id': productC.id, 'quantity': 2.0, 'to_refund': True}),
            (0, 0, {'product_id': productD.id, 'quantity': 2.0, 'to_refund': True})]

        return_wiz.with_context(delivery_exchange=True).create_returns()

        # Validate return and new delivery pickings
        related_pickings = self.so.picking_ids.filtered(lambda r: r.state != 'done')

        for related_picking in related_pickings:
            related_picking.move_lines.write({'quantity_done': 2})
            related_picking.button_validate()

        # check quantity on hand
        product_quant = self.env['stock.quant'].search(
            [('product_id', '=', productA.id), ('location_id', '=', stock_location.id)])
        self.assertEqual(sum(product_quant.mapped('quantity')), -3)

        exchange_quant = self.env['stock.quant'].search(
            [('product_id', '=', productB.id), ('location_id', '=', stock_location.id)])
        self.assertEqual(sum(exchange_quant.mapped('quantity')), -2)

        productC_quant = self.env['stock.quant'].search(
            [('product_id', '=', productC.id), ('location_id', '=', stock_location.id)])
        self.assertEqual(sum(productC_quant.mapped('quantity')), -2)

        productD_quant = self.env['stock.quant'].search(
            [('product_id', '=', productD.id), ('location_id', '=', stock_location.id)])
        self.assertEqual(sum(productD_quant.mapped('quantity')), -2)

        # Check invoice
        self.assertEqual(self.so.invoice_status, 'to invoice',
                         'Sale Stock: so invoice_status should be "to invoice" instead of "%s" after picking return' % self.so.invoice_status)
        self.assertAlmostEqual(self.so.order_line[0].qty_delivered, 3.0,
                               msg='Sale Stock: delivered quantity should be 3.0 instead of "%s" after picking return' %
                                   self.so.order_line[0].qty_delivered)
