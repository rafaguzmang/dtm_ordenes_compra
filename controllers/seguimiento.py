from datetime import datetime
from docutils.nodes import revision
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

            atencion_material = False
            for ot in orden.descripcion_id:
                if ot.orden_trabajo:
                    get_compras = request.env['dtm.compras.requerido'].sudo().search([('orden_trabajo','=',ot.orden_trabajo)],limit=1)
                    if get_compras:
                        atencion_material = True
                        break

            # atencion_material = True if get_ordenes.filtered(lambda x: x.status == 'atencion') else False


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
                'terminado': terminado,
                'atencion_material': atencion_material,
                'po_date': orden.fecha_po.strftime("%x") if orden.fecha_po else '---',
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
                porciento_material = (existencia * 100)/numero_ordenes if numero_ordenes > 0 else 0
                get_compras = request.env['dtm.compras.realizado'].sudo().search([("orden_trabajo","=",data.ot_number),('comprado','in',['Recibido','Parcial'])])
                get_status = request.env['dtm.proceso'].sudo().search([('ot_number', '=', data.ot_number)],limit=1)
                status_value = get_status._fields['status'].selection
                status_value = dict(status_value).get(get_status.status)

            get_corte_orden = request.env['dtm.materiales.laser'].sudo().search([('orden_trabajo','=',data.ot_number)])
            get_corte_orden_realizado = request.env['dtm.laser.realizados'].sudo().search([('orden_trabajo','=',data.ot_number)])

            get_cotizacion = request.env['dtm.compras.requerido'].sudo().search([('orden_trabajo','=',str(data.ot_number))])

            corte_porcentaje = 0
            if get_corte_orden_realizado:
                corte_porcentaje = 100
            elif get_corte_orden:
                corte_porcentaje = round(sum(get_corte_orden.mapped('status'))/len(get_corte_orden),2)
            
            
            vals = {
                "od":orden,
                "ot":data.ot_number,
                "V":data.revision_ot,
                "R":data.version_ot,
                "nombre":data.product_name,
                "cantidad":data.cuantity,
                "disenador":data.disenador,
                "nesteo":'No' if data.nesteo_chk else 'Si',
                "costo_diseno": round(sum(data.lista_material_id.mapped('precio')),2) if data.ot_number else 'N/A',
                "costo_ingenieria": round(sum(data.materials_ids.mapped('costo')),2) if data.ot_number else 'N/A',
                "compras":round(sum(get_compras.mapped('costo')),2) if data.ot_number else 'N/A',
                "status":status_value if data.ot_number else 'N/A',
                "material":round(porciento_material,2) if data.ot_number else 'N/A',
                "maquinados":'N/A',
                "corte":f"{corte_porcentaje}%" if data.ot_number else 'N/A',
                "material_diseno":True if data.ot_number else False,
                "firma_ventas":data.firma_ventas,
                "en_cotizacion":True if get_cotizacion else False,
            }
            result.append(vals)
            print(vals)


        return result

    @http.route('/dtm_precio_dollar', type='json', auth='public')
    def precioDollar(self):
        try:
            result = requests.get("https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF60653/datos/oportuno?token=48ae5fcf525e8658eb784d0c4030054d7aa97bf2b5859747015820245978f739",timeout=5)
            result.raise_for_status()
            return result.json()
        except  Exception as e:
            return {"error": str(e)}

    @http.route('/dtm_ventas_materiales', type='json',auth='public')
    def ventasMateriales(self):
        raw = request.httprequest.data
        data = json.loads(raw)
        orden = data.get('orden')
        get_orden = request.env['dtm.odt'].sudo().search([('ot_number','=',orden)])
        get_materiales = get_orden.materials_ids
        lista = []
        for material in get_materiales:
            get_compras = request.env['dtm.compras.requerido'].sudo().search([('orden_trabajo','=',orden),('tipo_orden','in',['OT','NPI']),('codigo','=',material.materials_list.id)],limit=1)           
            get_old_compras = request.env['dtm.compras.material'].sudo().search([('codigo','=',material.materials_list.id),('nombre','=',get_compras.nombre)],limit=1) if get_compras else None
            get_compras_requerido = request.env['dtm.compras.realizado'].sudo().search([('orden_trabajo','=',orden),('tipo_orden','in',['OT','NPI']),('codigo','=',material.materials_list.id)],limit=1)
            get_cotizaciones_id = request.env['dtm.compras.requerido'].sudo().search([('nombre','=',get_compras.nombre)]) if get_compras else None
            cotizaciones_material_orden = get_cotizaciones_id.mapped('orden_trabajo') if get_cotizaciones_id else None           
            cotizaciones_ordenes = []
            if cotizaciones_material_orden:
                for cotizacion in cotizaciones_material_orden:
                    if int(cotizacion) != orden:
                        get_cotizacion = request.env['dtm.odt'].sudo().search([('ot_number','=',cotizacion)],limit=1)
                        cotizaciones_ordenes.append(f"{get_cotizacion.ot_number} {get_cotizacion.name_client} {get_cotizacion.product_name}")

            lista.append({
                'nombre': f"{get_orden.name_client} - {get_orden.product_name}",
                'id':material.materials_list.id,
                'name': f"{material.materials_list.nombre} {material.materials_list.medida}",
                'proveedor':get_old_compras.proveedor_id.nombre if get_old_compras and get_old_compras.proveedor_id.nombre else '---------',
                'cantidad': material.materials_cuantity,
                'inventario': material.materials_availabe,
                'requerido':material.materials_required,
                'precio': get_old_compras.unitario if get_old_compras else 0,
                'total': round(get_old_compras.unitario * material.materials_cuantity,2) if get_old_compras else 0,
                'status':'recibido' if get_compras_requerido.comprado == "Recibido" else 
                        "comprado" if get_compras_requerido else
                        "cotizacion" if get_compras else
                        "almacen" if material.materials_cuantity == material.materials_availabe and material.almacen else
                        "revision" if not material.almacen else 
                        "pendiente",
                'cotizaciones_id':cotizaciones_ordenes if cotizaciones_ordenes else None,
            })
        return lista

    # Liberar materiales ya autorizados
    @http.route('/dtm_autorizar_material', type='json', auth='public')
    def autorizarMaterial(self):
        raw = request.httprequest.data
        data = json.loads(raw)
        id = data.get("id")
        orden = data.get("orden")
        user = request.env.user.name
        material = data.get("material")

        get_realizado = request.env['dtm.compras.realizado'].search([("orden_trabajo","=",orden),("codigo","=",id)],limit=1)
        get_cotizaciones = request.env['dtm.compras.material'].search([("nombre","=",material),("codigo","=",id)],limit=1)
        get_requerido = request.env['dtm.compras.requerido'].search([("orden_trabajo","=",orden),("codigo","=",id)])

        for material in get_requerido:
            create = {
                "orden_trabajo":orden,            
                "tipo_orden":material.tipo_orden,
                "revision_ot":material.revision_ot,
                "solicitado":material.create_date,
                "proveedor":get_cotizaciones.proveedor_id.nombre,
                "codigo":id,
                "nombre":material.nombre,
                "cantidad":material.cantidad,
                "orden_compra":get_cotizaciones.orden_compra,
                "mostrador":get_cotizaciones.mostrador,
                "mayoreo":get_cotizaciones.mayoreo,
                "unitario":get_cotizaciones.unitario,
                "costo":get_cotizaciones.unitario * material.cantidad,
                "fecha_compra":datetime.now(),
                "autoriza":user,
            }
            get_realizado.write(create) if get_realizado else get_realizado.create(create)
            material.unlink()
        get_cotizaciones.unlink()
        return True

    @http.route('/dtm_get_all_materiales', type='json', auth='public')
    def getAllMateriales(self):
        raw = request.httprequest.data
        data = json.loads(raw)
        id = data.get("id")
        name = data.get("name")
        get_proveedor = request.env['dtm.compras.material'].sudo().search([('codigo','=',id),('nombre','=',name)])
        get_materiales = request.env['dtm.compras.requerido'].sudo().search([('codigo','=',id),('nombre','=',name)])
        result = []
        for material in get_materiales:
            get_orden = request.env['dtm.odt'].sudo().search([('ot_number','=',material.orden_trabajo)],limit=1)
            result.append({
                'proveedor':get_proveedor.proveedor_id.nombre,
                'unitario':get_proveedor.unitario,
                'orden':material.orden_trabajo,
                'proyecto':get_orden.product_name,
                'cliente':get_orden.name_client,
                'disenador':get_orden.disenador,
                'cantidad':material.cantidad,
                'nesteo':material.nesteo,
            })



        print(get_materiales)
        return result

    @http.route('/dtm_diseno_materiales', type='json', auth='public')
    def disenoMateriales(self):
        raw = request.httprequest.data
        data = json.loads(raw)
        orden = data.get("orden")
        get_orden = request.env['dtm.odt'].sudo().search([('ot_number','=',orden)],limit=1)
        get_materiales = get_orden.lista_material_id
        result = []
        for material in get_materiales:
            result.append({
                'material':f"{material.material_id.id} - {material.material_id.nombre} {material.material_id.medida}",
                'cantidad':material.cantidad,
                'precio_unitario':round(material.unitario,2),
                'total':round(material.precio,2),
            })
        return result

    @http.route('/dtm_ot_data', type='json', auth='public')
    def dtmOtData(self):
        raw = request.httprequest.data
        data = json.loads(raw)
        orden = data.get("orden")
        get_orden = request.env['dtm.odt'].sudo().search([('ot_number','=',orden)],limit=1)
        get_planos = get_orden.anexos_id
        planos = []
        for plano in get_planos:
            planos.append({
                'nombre':plano.name,
                'data':plano.datas,
            })
        result = {
            'revision':get_orden.version_ot,
            'cantidad':get_orden.cuantity,
            'color':get_orden.color,
            'resumen':get_orden.description,
            'firma_ventas':get_orden.firma_ventas,
            'planos':planos,
        }
        return result
