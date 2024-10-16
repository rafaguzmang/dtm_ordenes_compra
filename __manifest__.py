{
    "name":"Ordenes de compra",

    'version': '1.0',
    'author': "Rafael Guzmán",
    "description": "Visualización de las ordenes de compra",
    "depends":["base","dtm_cotizaciones","dtm_procesos","dtm_odt","mail"],
    "data":[
        'security/ir.model.access.csv',
        #Views
        'views/dtm_ordenes_compra_views.xml',
        'views/dtm_ordenes_compra_facturado_views.xml',
        'views/dtm_ordenes_minutas_views.xml',
    ],
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'dtm_ordenes_compra/static/src/css/styles.css',
        ],
    },
}

