from odoo import models, fields, api

class BenefitSessionLine(models.Model):
    _name = 'benefit.session.line'
    _description = 'Línea de Producto en Jornada'

    session_id = fields.Many2one('benefit.session', string='Jornada', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Producto', required=True)
    quantity = fields.Float(string='Cantidad', default=1.0, required=True)
