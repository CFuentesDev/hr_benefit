from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class BenefitSession(models.Model):
    _name = 'benefit.session'
    _description = 'Jornada de Beneficios'
    _order = 'start_date desc, id desc'

    name = fields.Char(string='Nombre de Jornada', required=True)
    start_date = fields.Datetime(string='Fecha Inicio', required=True, default=fields.Datetime.now)
    end_date = fields.Datetime(string='Fecha Fin', required=True, default=fields.Datetime.now)
    
    is_active = fields.Boolean(string='Activa', compute='_compute_is_active', search='_search_is_active')
    
    line_ids = fields.One2many('benefit.session.line', 'session_id', string='Productos del Beneficio')
    department_ids = fields.Many2many('hr.department', string='Departamentos Permitidos')
    
    product_tag_ids = fields.Many2many('product.product', compute='_compute_product_tags', string='Productos (Etiquetas)', store=True)

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('done', 'Finalizado')
    ], string='Estado', default='draft', required=True)

    @api.depends('start_date', 'end_date', 'state')
    def _compute_is_active(self):
        now = fields.Datetime.now()
        for record in self:
            record.is_active = record.state == 'confirmed' and record.start_date <= now <= record.end_date

    def _search_is_active(self, operator, value):
        now = fields.Datetime.now()
        if operator == '=' and value is True:
            return [('state', '=', 'confirmed'), ('start_date', '<=', now), ('end_date', '>=', now)]
        return [('state', '=', 'confirmed')] # Fallback

    @api.depends('line_ids.product_id')
    def _compute_product_tags(self):
        for record in self:
            record.product_tag_ids = record.line_ids.mapped('product_id')

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date > record.end_date:
                raise ValidationError("La fecha de inicio no puede ser mayor a la fecha de fin.")

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_draft(self):
        self.write({'state': 'draft'})
