from odoo import http
from odoo.http import request, Response
import json,requests

class WebSiteDirectios(http.Controller):


    @http.route('/dtm_cotizaciones', type='http', auth='public')
    def cotizaciones(self):
        get_po = request.env['dtm.ordenes.compra'].sudo().search([])
        result = []
        for orden in get_po:

            get_ordenes = orden.descripcion_id
            terminado = False
            if len(get_ordenes) == 1:
                status = request.env['dtm.proceso'].sudo().search([('ot_number','=',get_ordenes.orden_trabajo)],limit=1).status
                get_status = 'Terminado' if status == 'terminado' else 'Calidad' if status == 'calidad' else 'Proceso' if status else 'OT' if get_ordenes.orden_trabajo else 'OD'
                terminado = True if get_status == 'Terminado' else False
            elif len(get_ordenes) > 1:
                get_procesos = [request.env['dtm.proceso'].sudo().search([('ot_number','=',ot)],limit=1).status for ot in get_ordenes.mapped('orden_trabajo')]
                od_list = list(set(orden.descripcion_id.mapped('orden_diseno')))
                ot_list = list(set(orden.descripcion_id.mapped('orden_trabajo')))
                get_status = f"Terminado {len(list(filter(lambda x: x == 'terminado', get_procesos)))}/{len(get_ordenes)}"if 'terminado' in get_procesos else f"Calidad {len(list(filter(lambda x: x == 'calidad', get_procesos)))}/{len(get_ordenes)}" if 'calidad' in get_procesos else f"Proceso {len(get_procesos)}/{len(get_ordenes)}" if True in get_procesos else  f"OT {len(list(filter(lambda x: x != 0,ot_list)))}/{len(get_ordenes)}" if len(ot_list) > 1 else f"OD {len(list(filter(lambda x: x != 0,od_list)))}/{len(get_ordenes)}" if len(od_list) > 1 else f"N/A {len(get_ordenes)}/{len(get_ordenes)}"
                terminado = True if (len(list(filter(lambda x: x == 'terminado', get_procesos)))/len(get_ordenes)) == 1 else False
            else:
                get_status = 'N/A'

            result.append({
                'cotizacion': orden.no_cotizacion,
                'proveedor': 'DTM' if orden.proveedor == 'dtm' else 'MTD',
                'cliente': orden.cliente_prov,
                'po': orden.orden_compra,
                'pdf': orden.archivos_id[0].datas.decode('utf-8') if orden.archivos_id else '',
                'precio': f"{round(orden.precio_total, 2)} {'mx' if request.env['dtm.cotizaciones'].sudo().search([('no_cotizacion','=',orden.no_cotizacion)],limit=1).curency == 'mx' else 'dlls'}",
                'fecha_entrada': orden.fecha_entrada.strftime("%x") if orden.fecha_entrada else '---',
                'fecha_salida': orden.fecha_salida.strftime("%x") if orden.fecha_salida else '---',
                'status': get_status,
                'terminado': terminado
            })

        return request.make_response(
            json.dumps(result),
            headers={
                'Content-Type':'application/json',
                'Access-Control-Allow-Origin':'*'
            }
        )

    @http.route('/dtm_ordenes_cotizacion', type='json', auth='public')
    def ordenesTrabajo(self):
        raw = request.httprequest.data
        data = json.loads(raw)
        cotizacion = data.get('cotizacion')
        get_ordenes = request.env['dtm.ordenes.compra'].sudo().search([('no_cotizacion','=',int(cotizacion))])
        list_ordenes = get_ordenes.descripcion_id.mapped('orden_diseno')
        result = []
        for orden in list_ordenes:
            data = request.env['dtm.odt'].sudo().search([('od_number','=',orden)])
            if data.ot_number:
                numero_ordenes = len(data.materials_ids)
                materiales_estado = data.materials_ids.mapped('materials_required')
                existencia = len([x for x in materiales_estado if x==0])
                porciento_material = (existencia * 100)/numero_ordenes
                get_compras = request.env['dtm.compras.realizado'].sudo().search([("orden_trabajo","=",data.ot_number),('comprado','in',['Recibido','Parcial'])])
                get_status = request.env['dtm.proceso'].sudo().search([('ot_number', '=', data.ot_number)],limit=1)
                status_value = get_status._fields['status'].selection
                status_value = dict(status_value).get(get_status.status)
            vals = {
                "od":orden,
                "ot":data.ot_number,
                "V":data.revision_ot,
                "R":data.version_ot,
                "nombre":data.product_name,
                "disenador":data.disenador,
                "nesteo":'No' if data.nesteo_chk else 'Si',
                "costo_diseno": round(sum(data.lista_material_id.mapped('precio')),2) if data.ot_number else 'N/A',
                "costo_ingenieria": round(sum(data.materials_ids.mapped('costo')),2) if data.ot_number else 'N/A',
                "compras":round(sum(get_compras.mapped('costo')),2) if data.ot_number else 'N/A',
                "status":status_value if data.ot_number else 'N/A',
                "material":round(porciento_material,2) if data.ot_number else 'N/A',
            }
            result.append(vals)


        return result

    @http.route('/dtm_precio_dollar', type='json', auth='public')
    def precioDollar(self):
        try:
            result = requests.get("https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF60653/datos/oportuno?token=48ae5fcf525e8658eb784d0c4030054d7aa97bf2b5859747015820245978f739",timeout=5)
            result.raise_for_status()
            return result.json()
        except  Exception as e:
            return {"error": str(e)}
