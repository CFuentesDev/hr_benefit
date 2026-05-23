from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import re

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    identification_type = fields.Selection([
        ('V', 'V'),
        ('E', 'E'),
    ], string='Tipo Identificación', default='V', help="Tipo de documento de identidad")
    cedula = fields.Char(string='Cédula', size=8)

class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    identification_type = fields.Selection([
        ('V', 'V'),
        ('E', 'E'),
    ], string='Tipo Identificación', readonly=True)
    cedula = fields.Char(string='Cédula', readonly=True)

    parent_id = fields.Many2one('hr.employee', string="Director/Gerente")
    coach_id = fields.Many2one('hr.employee', string="Supervisor")
    job_id = fields.Many2one('hr.job', string="Cargo Administrativo")
    company_id = fields.Many2one('res.company', default=False)

    # Función para autocompletar el gerente al seleccionar un departamento
    @api.onchange('department_id')
    def _onchange_department_id(self):
        # Si se selecciona un departamento y ese departamento tiene un gerente asignado
        if self.department_id and self.department_id.manager_id:
            self.parent_id = self.department_id.manager_id
        else:
            # Opcional: vaciar el campo si el departamento no tiene gerente
            self.parent_id = False

    # Función para validar que la cédula solo contenga números
    @api.constrains('cedula')
    def _check_identification_id_numeric(self):
        for employee in self:
            if employee.cedula and not employee.cedula.isdigit():
                raise ValidationError("La Cédula de Identidad debe contener solo números.")

     # Función para validar que la cédula sea única en toda la base de datos, sin importar la empresa
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

    # Función para quitar alerta de cambio de empresa
    @api.onchange('company_id')
    def _onchange_company_id(self):
        pass

    _rec_names_search = ['name', 'cedula']

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            name_val = vals.get('name', '')
            
            # 1. Limpiamos el nombre para ver si es una cédula
            clean_name = str(name_val).replace('-', '').replace('.', '').replace('V', '').replace('E', '').strip()

            # 2. Si el nombre que llega es solo números (la cédula que te pone Odoo)
            if clean_name.isdigit():
                # La movemos al campo cédula si este viene vacío
                if not vals.get('cedula'):
                    vals['cedula'] = name_val
                
                # 3. EL BLOQUEO REAL:
                # Si llegamos aquí y el nombre sigue siendo igual a la cédula, 
                # detenemos todo. Odoo NO podrá guardar.
                raise ValidationError("¡Atención! El sistema detectó la cédula en el campo Nombre. "
                                    "Por favor, borre los números y escriba el nombre real del empleado.")
        
        return super(HrEmployee, self).create(vals_list)

    @api.model
    def default_get(self, fields_list):
        # En el default_get NO tocaremos el name para evitar errores de Index o de contactos.
        # Solo lo usaremos para capturar la cédula silenciosamente.
        res = super(HrEmployee, self).default_get(fields_list)
        if 'name' in res and res['name']:
            clean_name = str(res['name']).replace('-', '').replace('.', '').replace('V', '').replace('E', '').strip()
            if clean_name.isdigit():
                res['cedula'] = res['name']
        return res