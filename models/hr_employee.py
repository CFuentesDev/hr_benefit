from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import re

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    identification_type = fields.Selection([
        ('V', 'V'),
        ('E', 'E'),
    ], string='Tipo Identificación', default='V', help="Tipo de documento de identidad")

    cedula = fields.Char(string='Cédula')

    @api.constrains('cedula')
    def _check_identification_id_numeric(self):
        for employee in self:
            if employee.cedula and not employee.cedula.isdigit():
                raise ValidationError("La Cédula de Identidad debe contener solo números.")
            
    # Tu campo (tal como lo tenías)
    cedula = fields.Char(string='Cédula', compute='_compute_cedula_completa', store=True)

    @api.constrains('cedula')
    def _check_cedula_unique_with_company_info(self):
        for employee in self:
            if not employee.cedula:
                continue
            
            # Buscamos en toda la base de datos (sudo) si existe esa cédula
            # Excluimos al propio empleado que estamos editando (id != employee.id)
            duplicate = self.sudo().search([
                ('cedula', '=', employee.cedula),
                ('id', '!=', employee.id)
            ], limit=1)

            if duplicate:
                # Obtenemos el nombre de la empresa donde se encontró el duplicado
                company_name = duplicate.company_id.name or "Sin Empresa"
                raise ValidationError(_(
                    "La Cédula %s ya está registrada para el empleado '%s' en la empresa: %s"
                ) % (employee.cedula, duplicate.name, company_name))
