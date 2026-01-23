from odoo import models, api
import random

class BenefitDemo(models.AbstractModel):
    _name = 'benefit.demo'
    _description = 'Generador de Datos de Prueba'

    @api.model
    def generate_demo_data(self):
        # 1. Create Departments
        main_depts = ['Minpesca', 'Cenipa', 'Insopesca', 'Fonpesca', 'Corpesca']
        sub_depts_names = ['Despacho', 'RRHH', 'Administración', 'Tecnología', 'Operaciones']
        
        dept_objs = []
        # Support/Substantive departments for employee assignment
        assignable_depts = []

        for name in main_depts:
            # Main depts are decorative and top level
            parent = self.env['hr.department'].create({
                'name': name,
                'level': 'top',
                'decorative': True
            })
            dept_objs.append(parent)
            
            # Create sub-departments
            for sub in random.sample(sub_depts_names, 3): # Pick 3 random sub-depts
                # Sub depts are non-decorative and support/substantive
                level = random.choice(['support', 'substantive'])
                child = self.env['hr.department'].create({
                    'name': f"{name} - {sub}",
                    'parent_id': parent.id,
                    'level': level,
                    'decorative': False
                })
                dept_objs.append(child)
                assignable_depts.append(child)

        # 2. Create 200 Employees
        nombres = ['Juan', 'Maria', 'Carlos', 'Ana', 'Pedro', 'Luisa', 'Jose', 'Elena', 'Miguel', 'Sofia', 'David', 'Carmen', 'Luis', 'Rosa', 'Jorge', 'Isabel', 'Ramon', 'Patricia', 'Daniel', 'Andrea']
        apellidos = ['Perez', 'Gonzalez', 'Rodriguez', 'Hernandez', 'Garcia', 'Martinez', 'Lopez', 'Sanchez', 'Diaz', 'Ramirez', 'Torres', 'Flores', 'Rivera', 'Gomez', 'Castillo', 'Jimenez', 'Romero', 'Vazquez', 'Reyes', 'Morales']
        
        employees = []
        for i in range(200):
            first_name = random.choice(nombres)
            last_name = random.choice(apellidos)
            full_name = f"{first_name} {last_name} {i+1}" # Index to ensure uniqueness/tracking
            
            dept = random.choice(assignable_depts)
            job_title = random.choice(['Analista', 'Asistente', 'Gerente', 'Coordinador', 'Obrero', 'Chofer'])
            emp_type = random.choice(['employee', 'hp'])
            cedula = str(random.randint(1000000, 30000000))

            self.env['hr.employee'].create({
                'name': full_name,
                'department_id': dept.id,
                'job_title': job_title,
                'employee_type': emp_type,
                'identification_type': 'V',
                'identification_id': cedula,
                'work_email': f"{first_name.lower()}.{last_name.lower()}{i}@example.com"
            })
