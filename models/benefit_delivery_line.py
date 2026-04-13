from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class BenefitDeliveryLine(models.Model):
    _name = 'benefit.delivery.line'
    _description = 'Línea de Entrega de Beneficio'
    # NOTA: Eliminamos el _inherit = 'hr.employee' de aquí.

    list_id = fields.Many2one('benefit.delivery.list', string='Lista de Entrega', ondelete='cascade', required=False)
    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True)
    employee_department = fields.Many2one('hr.department', string='Departamento', related='employee_id.department_id', required=True)

    # State management
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('delivered', 'Entregado')
    ], string='Estado', default='draft', compute='_compute_state', store=True, readonly=False) 

    qty_delivered = fields.Float(string='Cantidad Entregada', default=1.0)
    
    # Session management
    session_id = fields.Many2one('benefit.session', string='Jornada', required=True, store=True, 
                                 compute='_compute_session', readonly=False) 

    date_delivered = fields.Datetime(string='Fecha de Entrega', default=fields.Datetime.now)
    evidence_photo = fields.Binary(string="Foto Evidencia", attachment=True, help="Tome una foto al momento de la entrega como evidencia.")

    @api.model
    def default_get(self, fields_list):
        res = super(BenefitDeliveryLine, self).default_get(fields_list)
        
        # Lógica de auto-seleccionar la sesión activa
        if 'session_id' in fields_list and not res.get('session_id'):
            active_session = self.env['benefit.session'].search([
                ('is_active', '=', True)
            ], limit=1)
            if active_session:
                res['session_id'] = active_session.id
                
        return res

    @api.depends('list_id', 'list_id.state', 'list_id.session_id')
    def _compute_state(self):
        for record in self:
            if record.list_id:
                record.state = 'delivered' if record.list_id.state in ['delivered'] else 'draft'
            elif not record.state:
                record.state = 'draft'

    @api.depends('list_id', 'list_id.session_id')
    def _compute_session(self):
        for record in self:
            if record.list_id:
                record.session_id = record.list_id.session_id

    def action_confirm_delivery(self):
        self.ensure_one()

        if self.list_id:
            raise ValidationError("No puede confirmar individualmente una línea que pertenece a una lista.")
        
        self._check_date_range()
        self._check_unique_delivery()
        
        self.state = 'delivered'
        self.date_delivered = fields.Datetime.now()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.constrains('session_id', 'employee_id', 'state')
    def _check_unique_delivery(self):
        for record in self:
            if record.state == 'delivered':
                domain = [
                    ('session_id', '=', record.session_id.id),
                    ('employee_id', '=', record.employee_id.id),
                    ('state', '=', 'delivered'),
                    ('id', '!=', record.id)
                ]
                if self.search_count(domain) > 0:
                    raise ValidationError(_("El empleado %s ya ha recibido el beneficio en esta jornada.") % record.employee_id.name)

    def _check_date_range(self):
        now = fields.Datetime.now()
        if not self.session_id.is_active: 
             if not (self.session_id.start_date <= now <= self.session_id.end_date):
                 raise ValidationError("No se puede realizar entregas fuera del rango de fechas de la jornada.")

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id and not self.employee_id.active:
            return {'warning':
                {
                    'title': 'Advertencia - Empleado Egresado',
                    'message': f"El empleado {self.employee_id.name} se encuentra marcado como desincorporado (Archivado)."
                }
            }