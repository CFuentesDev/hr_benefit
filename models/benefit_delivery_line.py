from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BenefitDeliveryLine(models.Model):
    _name = 'benefit.delivery.line'
    _description = 'Línea de Entrega de Beneficio'

    list_id = fields.Many2one('benefit.delivery.list', string='Lista de Entrega', ondelete='cascade', required=False) # Now optional
    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True)
    employee_department = fields.Many2one('hr.department', string='Departamento', related='employee_id.department_id', required=True)

    # State management
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('delivered', 'Entregado')
    ], string='Estado', default='draft', compute='_compute_state', store=True, readonly=False) 
    # Readonly=False to allow manual change if no list_id, but compute handles list logic.

    qty_delivered = fields.Float(string='Cantidad Entregada', default=1.0)
    
    # Session management
    session_id = fields.Many2one('benefit.session', string='Jornada', required=True, store=True, 
                                 compute='_compute_session', readonly=False) 
                                 # Compute sets it from list, but allows manual if no list.

    date_delivered = fields.Datetime(string='Fecha de Entrega', default=fields.Datetime.now)
    evidence_photo = fields.Binary(string="Foto Evidencia", attachment=True, help="Tome una foto al momento de la entrega como evidencia.")

    @api.model
    def default_get(self, fields_list):
        defaults = super(BenefitDeliveryLine, self).default_get(fields_list)
        if 'session_id' in fields_list and not defaults.get('session_id'):
            # Auto-select active session
            active_session = self.env['benefit.session'].search([
                ('is_active', '=', True)
            ], limit=1)
            if active_session:
                defaults['session_id'] = active_session.id
        return defaults

    @api.depends('list_id', 'list_id.state', 'list_id.session_id')
    def _compute_state(self):
        for record in self:
            if record.list_id:
                record.state = 'delivered' if record.list_id.state in ['delivered'] else 'draft'
                # Logic: If list is confirmed, lines are effectively draft until validated (delivered)? 
                # Or confirmed list means lines are confirmed? 
                # User prev req: "Entregado" when list is delivered.
            elif not record.state:
                record.state = 'draft'

    @api.depends('list_id', 'list_id.session_id')
    def _compute_session(self):
        for record in self:
            if record.list_id:
                record.session_id = record.list_id.session_id

    def action_confirm_delivery(self):
        self.ensure_one()
        if not self.evidence_photo:
            raise ValidationError(_("Debe adjuntar una foto de evidencia para confirmar la entrega."))

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
        if not self.session_id.is_active: # Relies on is_active being consistent with dates
             # Re-check explicitly just in case
             if not (self.session_id.start_date <= now <= self.session_id.end_date):
                 raise ValidationError("No se puede realizar entregas fuera del rango de fechas de la jornada.")

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        # Verifica si el empleado ya ha recibido el beneficio en esta jornada
        if self.employee_id and not self.employee_id.active:
            return {'warning':
                {
                    'title': 'Advertencia - Empleado Egresado',
                    'message': f"El empleado {self.employee_id.name} se encuentra marcado como desincorporado (Archivado)."
                }
            }