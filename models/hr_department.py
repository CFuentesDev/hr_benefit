from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HrDepartment(models.Model):
    _inherit = 'hr.department'

    level = fields.Selection([
        ('top', 'Nivel Superior'),
        ('support', 'Nivel de Apoyo'),
        ('substantive', 'Nivel Sustantivo')
    ], string='Nivel Jerárquico')

    decorative = fields.Boolean(string='Es Decorativo', default=False, help="Si está marcado, este departamento no puede tener empleados asignados.")

    @api.constrains('decorative')
    def _check_decorative_no_employees(self):
        for dept in self:
            if dept.decorative and dept.member_ids:
                raise ValidationError(_("No puede marcar como decorativo un departamento que tiene empleados asignados."))
