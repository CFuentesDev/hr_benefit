from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class BenefitDeliveryList(models.Model):
    _name = 'benefit.delivery.list'
    _description = 'Lista de Entrega de Beneficios'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Referencia', required=True, copy=False, readonly=True, default=lambda self: _('Nuevo'))
    session_id = fields.Many2one('benefit.session', string='Jornada', required=True, domain=[('is_active', '=', True)], default=lambda self: self._default_session())
    responsible_id = fields.Many2one('hr.employee', string='Responsable de Retiro', required=True)
    department_ids = fields.Many2many('hr.department', string='Departamentos', help='Departamentos para carga masiva de empleados')
    line_ids = fields.One2many('benefit.delivery.line', 'list_id', string='Beneficiarios')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('delivered', 'Entregado')
    ], string='Estado', default='draft', track_visibility='onchange')
    date_delivered = fields.Datetime(string='Fecha de Entrega', readonly=True)
    evidence_photo = fields.Binary(string="Foto Responsable", attachment=True, help="Evidencia visual de la entrega al responsable.")
    
    total_delivered = fields.Float(string='Total Entregado', compute='_compute_total_delivered', store=True)

    @api.depends('line_ids', 'line_ids.qty_delivered')
    def _compute_total_delivered(self):
        for record in self:
            record.total_delivered = sum(record.line_ids.mapped('qty_delivered'))

    @api.model
    def _default_session(self):
        return self.env['benefit.session'].search([('is_active', '=', True)], limit=1)
    
    # Logic for Sequence
    @api.model
    def create(self, vals):
        if vals.get('name', _('Nuevo')) == _('Nuevo'):
            vals['name'] = self.env['ir.sequence'].next_by_code('benefit.delivery.list') or _('Nuevo')
        return super(BenefitDeliveryList, self).create(vals)

    def action_load_employees(self):
        self.ensure_one()
        if not self.department_ids:
            raise ValidationError(_("Seleccione al menos un departamento para cargar empleados."))
        
        # Determine allowed departments from session
        allowed_depts = self.session_id.department_ids
        target_depts = self.department_ids
        
        # Check if selected departments are allowed in the session
        if allowed_depts:
            invalid_depts = target_depts - allowed_depts
            if invalid_depts:
                 # Optional: raise error or just ignore invalid ones? 
                 # Let's clean it up or raise. Raising is safer.
                 raise ValidationError(_("Los siguientes departamentos no están permitidos en esta jornada: %s") % ", ".join(invalid_depts.mapped('name')))

        employees = self.env['hr.employee'].search([
            ('department_id', 'in', target_depts.ids),
            ('active', '=', True)
        ])
        
        # Prepare lines
        lines_to_create = []
        current_employee_ids = self.line_ids.mapped('employee_id.id')
        
        for emp in employees:
            if emp.id not in current_employee_ids:
                lines_to_create.append((0, 0, {
                    'employee_id': emp.id,
                    'qty_delivered': 1.0
                }))
        
        self.write({'line_ids': lines_to_create})

    def action_validate(self):
        for record in self:
            # Check for duplicates across ALL lists for this session
            record._check_integrity()
            record.write({
                'state': 'delivered',
                'date_delivered': fields.Datetime.now()
            })

    def action_confirm(self):
        self._check_integrity()
        self.write({'state': 'confirmed'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def _check_integrity(self):
        """
        Verifies that employees in this list are not in other VALIDATED/DELIVERED lists for the same session.
        Exclude the current list from search.
        """
        self.ensure_one()
        employee_ids = self.line_ids.mapped('employee_id.id')
        if not employee_ids:
            return

        # Search for other lines in the same session, different list, where state is not draft (or maybe just check all states except cancelled?)
        # Requirement: "impedir guardar o validar si uno de los empleados ya aparece en otra lista validada o en proceso"
        # "en proceso" implies confirmed/delivered. Draft lists might be ignored or maybe checked too?
        # Let's be strict: if it's in another list that is NOT cancelled (assuming we don't have cancel, so just all lists).
        # Wait, if I have two drafts for same person, I can't enable both. 
        # But commonly, constraint checks on Validate.
        # "impedir ... guardar o validar". So even saving logic.
        
        domain = [
            ('session_id', '=', self.session_id.id),
            ('list_id', '!=', self.id),
            ('employee_id', 'in', employee_ids),
            ('list_id.state', '!=', 'draft') # Only check against confirmed/delivered lists to allow multiple drafts?
            # User said "ya aparece en otra lista validada o en proceso".
            # "en proceso" likely means Confirmed. Validated = Delivered?
            # Let's assume Confirmed and Delivered lists create the lock.
        ]
        
        duplicates = self.env['benefit.delivery.line'].search(domain)
        if duplicates:
            # Get first duplicate for error message
            dup = duplicates[0]
            raise ValidationError(_("El empleado %s ya tiene una entrega asignada o procesada en esta jornada (Lista: %s).") % (dup.employee_id.name, dup.list_id.name))

    @api.constrains('line_ids')
    def _check_employee_unique_in_list(self):
        for record in self:
            employees = record.line_ids.mapped('employee_id')
            if len(employees) != len(record.line_ids):
                raise ValidationError(_("No puede haber empleados duplicados en la misma lista."))
