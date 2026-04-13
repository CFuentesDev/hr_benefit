from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HrDepartment(models.Model):
    _inherit = 'hr.department'