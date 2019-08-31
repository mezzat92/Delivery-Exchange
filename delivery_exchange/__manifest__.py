# -*- encoding: utf-8 -*-

{
    'name': 'Delivery Exchange',
    'version': '1.0',
    'category': 'Warehouse',
    'sequence': 50,
    'summary': 'Delivery Exchange Process',
    'depends': ['sale_management','stock','stock_account','sale_stock'],
    'description': """
Delivery Exchange Process
==========================

Allow the customer to exchange an already delivered and paid product

It also adds the possibility for the customer to add other products as well in
the exchange process.
""",
    'data': [
        'views/stock_picking_return_views.xml',
        'views/stock_picking_views.xml',
    ],
    'application': False,
    'license': 'OEEL-1',
}
