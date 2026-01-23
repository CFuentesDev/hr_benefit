{
    'name': 'Gestión de Beneficios (RRHH)',
    'version': '1.0',
    'summary': 'Control de entrega de beneficios y combos a empleados',
    'description': """
        Módulo para la gestión y cuantificación de entregas de beneficios (ej. combos de alimentos)
        a los empleados, con control por jornadas y listas de entrega masiva.
    """,
    'category': 'Human Resources',
    'author': 'Antigravity',
    'depends': ['base', 'hr', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/benefit_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_department_views.xml',
        'report/benefit_report.xml',
        'data/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'assets': {
        'web.assets_backend': [
            'hr_benefit/static/src/js/webcam_widget.js',
            'hr_benefit/static/src/xml/webcam_widget.xml',
        ],
    },
    'license': 'LGPL-3',
}
