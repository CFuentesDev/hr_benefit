from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    employee_type = fields.Selection([
        ('employee', 'Empleado'),
        ('hp', 'HP')
    ], string='Tipo de Empleado', default='employee', help="Clasificación del empleado para beneficios.")

    identification_type = fields.Selection([
        ('V', 'V'),
        ('E', 'E'),
        ('J', 'J'),
        ('RIF', 'RIF')
    ], string='Tipo Identificación', default='V', help="Tipo de documento de identidad")

    @api.constrains('department_id')
    def _check_department_decorative(self):
        for employee in self:
            if employee.department_id and employee.department_id.decorative:
                raise ValidationError("No se puede asignar un empleado a un departamento decorativo.")

    @api.constrains('identification_id')
    def _check_identification_id_numeric(self):
        for employee in self:
            if employee.identification_id and not employee.identification_id.isdigit():
                raise ValidationError("La Cédula de Identidad debe contener solo números.")

    @api.depends('name', 'identification_id', 'identification_type')
    def _compute_display_name(self):
        for employee in self:
            if employee.identification_id:
                prefix = employee.identification_type or ''
                employee.display_name = f"{employee.name} - {prefix}-{employee.identification_id}" if prefix else f"{employee.name} - {employee.identification_id}"
            else:
                employee.display_name = employee.name
