# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Alisan Object Replicate",
    "version": "1.1",
    "category": "Tools",
    "description": """
Synchronization objects.
""",
    "author": "Suhindra",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/base_synchro_view.xml",
        "views/base_synchro_view.xml",
        "views/res_request_view.xml",
    ],
    "installable": True,
    "auto_install": False,
}
