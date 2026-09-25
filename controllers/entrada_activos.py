from odoo import http
from odoo.http import request, Response
import json, requests
import calendar
from datetime import date

class WebActivos(http.Controller):

    @http.route('/dtm_activos_main', type='http', auth='public')
    def activosMain(self):
        anio_actual = date.today().year

        # Diccionario con los 12 meses en español, cada uno con lista vacía
        meses_dicc = {
            "ENE": [], "FEB": [], "MAR": [], "ABR": [],
            "MAY": [], "JUN": [], "JUL": [], "AGO": [],
            "SEP": [], "OCT": [], "NOV": [], "DIC": []
        }

        get_pos = request.env['dtm.cotizaciones'].sudo().search([
            ("create_date", ">=", f"{anio_actual}-01-01 00:00:00"),
            ("create_date", "<=", f"{anio_actual}-12-31 23:59:59"),
        ])

        lista_meses = list(meses_dicc.keys())

        for record in get_pos:
            get_facturada = request.env["dtm.ordenes.compra"].sudo().search([("no_cotizacion","=",record.no_cotizacion)],limit=1)
            factura = get_facturada.factura_pdf
            get_pagada = request.env["dtm.ordenes.compra.facturado"].sudo().search([("no_cotizacion","=",record.no_cotizacion)],limit=1)
            pagada = get_pagada.pago_pdf
            mes_nombre = lista_meses[record.create_date.month - 1]
            precio_total = sum(get_pagada.descripcion_id.mapped("precio_total")) if get_pagada else sum(get_facturada.descripcion_id.mapped("precio_total"))
            meses_dicc[mes_nombre].append({
                "id": record.id,
                "no_cotizacion": int(record.no_cotizacion),
                "facturada":True if factura else False,
                "pagada": True if pagada else False,
                "precio_total": precio_total,
                # agrega aquí los demás campos que necesites del record
            })

        return request.make_response(
            json.dumps(meses_dicc),
            headers={
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        )
