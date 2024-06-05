{
    "name":"Ordenes de compra",

    'version': '1.0',
    'author': "Rafael Guzmán",
    "description": "Visualización de las ordenes de compra",
    "depends":["dtm_cotizaciones","dtm_procesos","dtm_odt"],
    "data":[
        'security/ir.model.access.csv',
        #Views
        'views/dtm_ordenes_compra_views.xml',
        'views/dtm_ordenes_compra_facturado_views.xml',
        'views/dtm_ventas_ot_view.xml'
    ]
}

