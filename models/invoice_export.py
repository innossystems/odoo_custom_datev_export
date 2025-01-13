from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_export_to_csv(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'export.wizard',
            'view_mode': 'form',
            'target': 'new',
        }