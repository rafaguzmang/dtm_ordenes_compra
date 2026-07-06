{
    "name":"Ordenes de compra",

    'version': '1.0',
    'author': "Rafael Guzmán",
    "description": "Visualización de las ordenes de compra",
    "depends":["base","dtm_cotizaciones","dtm_procesos","dtm_odt","mail"],
    # "depends":["base","dtm_cotizaciones","mail"],
    "data":[
        'security/ir.model.access.csv',
        #Views
        'views/dtm_ordenes_compra_views.xml',
        'views/dtm_ordenes_compra_facturado_views.xml',
        'views/dtm_ordenes_minutas_views.xml',
        'views/dtm_seguimiento_view.xml',
    ],
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            # CSS
            'dtm_ordenes_compra/static/src/css/styles.css',
            'dtm_ordenes_compra/static/src/css/cotizaciones.css',
            'dtm_ordenes_compra/static/src/css/ordenes_dialogo.css',
            'dtm_ordenes_compra/static/src/css/materiales_dialogo.css',
            'dtm_ordenes_compra/static/src/css/poraprobar_dialogo.css',
            'dtm_ordenes_compra/static/src/css/diseno_dialogo.css',
            # JS
            'dtm_ordenes_compra/static/src/js/seguimiento.js',
            'dtm_ordenes_compra/static/src/js/cotizaciones.js',
            'dtm_ordenes_compra/static/src/js/dialogo/ordenes_dialogo.js',
            'dtm_ordenes_compra/static/src/js/dialogo/materiales_dialogo.js',
            'dtm_ordenes_compra/static/src/js/dialogo/poraprobar_dialogo.js',
            'dtm_ordenes_compra/static/src/js/dialogo/corte_dialogo.js',
            'dtm_ordenes_compra/static/src/js/dialogo/diseno_dialogo.js',
            'dtm_ordenes_compra/static/src/js/dialogo/planos_dialogo.js',
            'dtm_ordenes_compra/static/src/js/dialogo/extraordinariaDialogo.js',
            # XML
            'dtm_ordenes_compra/static/src/xml/seguimiento.xml',
            'dtm_ordenes_compra/static/src/xml/cotizaciones.xml',
            'dtm_ordenes_compra/static/src/xml/dialogo/ordenes_dialogo.xml',
            'dtm_ordenes_compra/static/src/xml/dialogo/materiales_dialogo.xml',
            'dtm_ordenes_compra/static/src/xml/dialogo/poraprobar_dialogo.xml',
            'dtm_ordenes_compra/static/src/xml/dialogo/corte_dialogo.xml',
            'dtm_ordenes_compra/static/src/xml/dialogo/diseno_dialogo.xml',
            'dtm_ordenes_compra/static/src/xml/dialogo/planos_dialogo.xml',
            'dtm_ordenes_compra/static/src/xml/dialogo/extraordinariaDialogo.xml',
        ],
    },
}

