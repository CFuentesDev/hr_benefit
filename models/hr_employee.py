from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re

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

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        # Solo aplicamos la lógica si el contexto lo pide y hay un término de búsqueda
        if name and self.env.context.get('benefit_search_cedula'):
            # 1. Búsqueda estándar (Nombre O Cédula tal cual la escribieron)
            domain = ['|', ('name', operator, name), ('identification_id', operator, name)]
            
            # 2. Búsqueda inteligente (Solo números)
            # Esto permite encontrar "12345678" aunque escriban "V-12.345.678"
            numeric_name = re.sub(r'[^0-9]', '', name)
            
            # Solo agregamos el criterio extra si el input tenía basura (letras, puntos, guiones)
            if numeric_name and numeric_name != name:
                # Estructura: A or (B or C)
                domain = ['|', ('name', operator, name), 
                          '|', ('identification_id', operator, name), 
                               ('identification_id', operator, numeric_name)]
            
            # Retornamos usando lista de tuplas manual ya que name_get() no existe en Odoo 17+
            employees = self.search(domain + args, limit=limit)
            return [(record.id, record.display_name) for record in employees]
            
        return super(HrEmployee, self).name_search(name, args=args, operator=operator, limit=limit)

