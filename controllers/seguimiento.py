from datetime import datetime
from docutils.nodes import revision
from odoo import http
from odoo.http import request, Response
import json,requests

class WebSiteDirectios(http.Controller):


    @http.route('/dtm_cotizaciones', type='http', auth='public')
    def cotizaciones(self):
        get_po = request.env['dtm.ordenes.compra'].sudo().search([])
        get_transito = request.env['dtm.compras.realizado'].sudo().search([('listo_btn','=',True),('comprado','!=','Recibido'),('proveedor','!=','DTM')])
        get_importantes = request.env['dtm.odt'].sudo().search([('prioridad_date','!=',False)])
        endiseno_len = request.env['dtm.odt'].sudo().search(['|', '&', ('version_ot', '>', 1), ('firma', '=', False), ('ot_number', '=', 0)])
        ennesteo_len = request.env['dtm.odt'].sudo().search([('firma', '!=', False), ('firma_ventas', '!=', False), ('firma_ingenieria', '=', False)])
        get_en_maquinados = request.env['dtm.maquinados'].sudo().search([])
        result = []
        for orden in get_po:
            # Se obtiene si está facturado
            get_ordenes = orden.descripcion_id
            if len(get_ordenes) == 1:
                status = request.env['dtm.proceso'].sudo().search([('ot_number','=',get_ordenes.orden_trabajo)],limit=1).status
                get_status = 'Terminado' if status == 'terminado' else 'Calidad' if status == 'calidad' else 'Proceso' if status else 'OT' if get_ordenes.orden_trabajo else 'OD'
                get_facturado = request.env['dtm.facturado.odt'].sudo().search([('ot_number','=',get_ordenes.orden_trabajo)],limit=1) if get_ordenes else False
                facturado = True if get_facturado else False
            
            elif len(get_ordenes) > 1:
                get_procesos = [request.env['dtm.proceso'].sudo().search([('ot_number','=',ot)],limit=1).status for ot in get_ordenes.mapped('orden_trabajo')]
                od_list = list(set(orden.descripcion_id.mapped('orden_diseno')))
                ot_list = list(set(orden.descripcion_id.mapped('orden_trabajo')))
                get_status = f"Terminado {len(list(filter(lambda x: x == 'terminado', get_procesos)))}/{len(get_ordenes)}"if 'terminado' in get_procesos else f"Calidad {len(list(filter(lambda x: x == 'calidad', get_procesos)))}/{len(get_ordenes)}" if 'calidad' in get_procesos else f"Proceso {len(get_procesos)}/{len(get_ordenes)}" if True in get_procesos else  f"OT {len(list(filter(lambda x: x != 0,ot_list)))}/{len(get_ordenes)}" if len(ot_list) > 1 else f"OD {len(list(filter(lambda x: x != 0,od_list)))}/{len(get_ordenes)}" if len(od_list) > 1 else f"N/A {len(get_ordenes)}/{len(get_ordenes)}"
                # print('get_procesos',get_ordenes.mapped('orden_trabajo'))
                get_facturado = request.env['dtm.facturado.odt'].sudo().search([('ot_number','in',get_ordenes.mapped('orden_trabajo'))])
                facturado = True if get_facturado else False   

            else:
                get_status = 'PO'
            # Variables para ayudar a filtrar en los botones ml-btn de cotizaciones
            atencion_material = False # Filtrado por material a liberar de cotizaciones
            atorado = False # Filtra las ordenes que tienen mas de dos días con el mismo status
            por_aprobar = False # Filtra por la ordenes con firma de ingeniería y sin firma de ventas
            for ot in orden.descripcion_id: # Se itera por las ordenes de trabajo de la PO no de dtm_odt
                if not ot.orden_trabajo and not ot.orden_diseno:
                    continue

                # Caso 1: solo tiene od_number (aún no genera ot_number)
                if not ot.orden_trabajo:
                    get_diseno = request.env['dtm.odt'].sudo().search(
                        [('od_number', '=', ot.orden_diseno)], limit=1
                    )
                    if get_diseno and get_diseno.create_date:
                        delta = datetime.now() - get_diseno.create_date
                        atorado = atorado or (delta.total_seconds() / 3600 > 24)
                    continue

                # Caso 2: tiene ot_number pero firma_ingenieria aún no se firma (sigue en nesteo)
                get_odt = request.env['dtm.odt'].sudo().search(
                    [('ot_number', '=', ot.orden_trabajo)], limit=1
                )
                if get_odt and get_odt.firma and not get_odt.firma_ventas:
                    por_aprobar = True
                    
                if get_odt and not get_odt.firma_ingenieria:
                    if get_odt.nesteo_inicio:
                        delta = datetime.now() - get_odt.nesteo_inicio
                        atorado = atorado or (delta.total_seconds() / 3600 > 24)
                    continue

                # Caso 3: firma_ingenieria ya firmada -> dtm.proceso ya existe, se lee lo que dice el cron
                get_proceso = request.env['dtm.proceso'].sudo().search(
                    [('ot_number', '=', ot.orden_trabajo)], limit=1
                )
                if get_proceso:
                    atorado = atorado or get_proceso.atorado

                get_compras = request.env['dtm.compras.requerido'].sudo().search(
                    [('orden_trabajo', '=', ot.orden_trabajo), ('tipo_orden', 'in', ['OT', 'NPI'])], limit=1
                )
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
                'status':  'Facturado' if facturado else get_status,
                'facturado': facturado, 
                'numero_factura':','.join(orden.mapped('factura_pdf.name')) if facturado else '---',
                'atencion_material': atencion_material,
                'por_aprobar':por_aprobar,
                'po_date': orden.fecha_po.strftime("%x") if orden.fecha_po else '---',
                'atorada': True if atorado else False,
                'transito_len':len(get_transito),
                'transito_check': bool(get_transito.filtered(lambda r: r.status in ('retraso', 'cancelado'))),
                'importantes_len':len(get_importantes),
                'endiseno_len':len(endiseno_len),
                'ennesteo_len':len(ennesteo_len),
                'maquinados_len':len(get_en_maquinados),
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
                "nesteo":'Si' if data.firma_ingenieria else 'No',
                "costo_diseno": round(sum(data.lista_material_id.mapped('precio')),2) if data.ot_number else 'N/A',
                "costo_ingenieria": round(sum(data.materials_ids.mapped('costo')),2) if data.ot_number else 'N/A',
                "compras":round(sum(get_compras.mapped('costo')),2) if data.ot_number else 'N/A',
                "status":status_value if data.firma_ingenieria else 'N/A',
                "material":round(porciento_material,2) if data.ot_number else 'N/A',
                "maquinados":'N/A',
                "corte":f"{corte_porcentaje}%" if data.ot_number else 'N/A',
                "material_diseno":True if data.ot_number else False,
                "firma_ventas":data.firma_ventas,
                "en_cotizacion":True if get_cotizacion else False,
                "por_aprobar":True if data.firma and not data.firma_ventas else False,
                "prioridad_date": data.prioridad_date.strftime("%Y-%m-%d") if data.prioridad_date else ''
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

    @http.route('/dtm_ventas_materiales', type='json',auth='public')
    def ventasMateriales(self):
        raw = request.httprequest.data
        data = json.loads(raw)
        orden = data.get('orden')
        get_orden = request.env['dtm.odt'].sudo().search([('ot_number','=',orden)])
        get_materiales = get_orden.materials_ids
        lista = []
        for material in get_materiales:
            get_compras = request.env['dtm.compras.requerido'].sudo().search([('orden_trabajo','=',orden),('tipo_orden','in',['OT','NPI']),('codigo','=',material.materials_list.id),('extra_materials','=',material.extra_materials)],limit=1)           
            get_old_compras = request.env['dtm.compras.material'].sudo().search([('codigo','=',material.materials_list.id),('nombre','=',get_compras.nombre)],limit=1) if get_compras else None
            get_compras_requerido = request.env['dtm.compras.realizado'].sudo().search([('orden_trabajo','=',orden),('tipo_orden','in',['OT','NPI']),('codigo','=',material.materials_list.id),('extra_materials','=',material.extra_materials)],limit=1)
            get_cotizaciones_id = request.env['dtm.compras.requerido'].sudo().search([('nombre','=',get_compras.nombre),('extra_materials','=',material.extra_materials)]) if get_compras else None
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
                'precio': get_old_compras.unitario if get_old_compras else get_compras_requerido.unitario if get_compras_requerido else 0,
                'total': round(get_old_compras.unitario * material.materials_cuantity,2) if get_old_compras else round(get_compras_requerido.unitario * material.materials_cuantity,2) if get_compras_requerido else 0,
                'status':'recibido' if get_compras_requerido.comprado == "Recibido" else 
                        "comprado" if get_compras_requerido else
                        "cotizacion" if get_compras else
                        "almacen" if material.materials_cuantity == material.materials_availabe and material.almacen else
                        "revision" if not material.almacen else 
                        "pendiente",
                'cotizaciones_id':cotizaciones_ordenes if cotizaciones_ordenes else None,
                'notas':material.notas if material.notas else '',
                'extra_material':material.extra_materials
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
        extra_material = data.get("extra_material")

        get_realizado = request.env['dtm.compras.realizado'].search([("orden_trabajo","=",orden),("codigo","=",id),("extra_materials","=",extra_material)],limit=1)
        get_cotizaciones = request.env['dtm.compras.material'].search([("nombre","=",material),("codigo","=",id)],limit=1)
        get_requerido = request.env['dtm.compras.requerido'].search([("orden_trabajo","=",orden),("codigo","=",id),("extra_materials","=",extra_material)])

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
                "mostrador":get_cotizaciones.mostrador,
                "mayoreo":get_cotizaciones.mayoreo,
                "unitario":get_cotizaciones.unitario,
                "costo":get_cotizaciones.unitario * material.cantidad,
                "fecha_compra":datetime.now(),
                "autoriza":user,
                "extra_materials":extra_material
            }
            get_realizado.create(create)
            material.unlink()
        return True
    # Liberar materiales ya autorizados de esta y de otras OTs
    @http.route('/dtm_autorizar_material2', type='json', auth='public')
    def autorizarMaterial2(self):
        raw = request.httprequest.data
        data = json.loads(raw)
        id = data.get("id")
        nombre = data.get("nombre")
        orden = data.get("orden")
        disenador = data.get("disenador")
        cliente = data.get("cliente")
        proveedor = data.get("proveedor")
        proyecto = data.get("proyecto")
        extra_material = data.get("extra_material")
        cantidad = data.get("cantidad")
        user = request.env.user.name

        get_realizado = request.env['dtm.compras.realizado'].search([("orden_trabajo","=",orden),("codigo","=",id),("nombre","=",nombre),("extra_materials","=",extra_material)],limit=1)
        get_cotizaciones = request.env['dtm.compras.material'].search([("nombre","=",nombre),("codigo","=",id)],limit=1)
        get_requerido = request.env['dtm.compras.requerido'].search([("orden_trabajo","=",orden),("codigo","=",id),("nombre","=",nombre),("extra_materials","=",extra_material)])

        create = {
            "orden_trabajo":orden,            
            "tipo_orden":get_requerido.tipo_orden,
            "revision_ot":get_requerido.revision_ot,
            "solicitado":get_requerido.create_date,
            "proveedor":proveedor,
            "codigo":id,
            "nombre":nombre,
            "cantidad":cantidad,
            "mostrador":get_cotizaciones.mostrador,
            "mayoreo":get_cotizaciones.mayoreo,
            "unitario":get_cotizaciones.unitario,
            "costo":get_cotizaciones.unitario * cantidad,
            "fecha_compra":datetime.now(),
            "autoriza":user,
            "extra_materials":extra_material
        }
        get_realizado.create(create)
        get_requerido.unlink()
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
                'nombre_material':material.nombre,
                'extra_material':material.extra_materials,
            })
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
            'aprobado':True if get_orden.firma_ventas else False,
        }
        return result


    @http.route('/ordenes_trabajo_filtro', type='json', auth='public')
    def dtmOrdenesTrabajoFiltro(self):
        raw = request.httprequest.data
        data = json.loads(raw)
        ot = data.get("ot")
        get_orden = request.env['dtm.compras.items'].sudo().search([('orden_trabajo','=',int(ot))],limit=1)
        get_materiales = get_orden.model_id        
        return {'cotizacion':get_materiales.no_cotizacion}
   
    @http.route('/ordenes_status_filtro', type='json', auth='public')
    def dtmOrdenesStatusFiltro(self):
        raw = request.httprequest.data
        data = json.loads(raw)
        status = data.get("status")
        status_dict = {        
            "aprobacion":"Nesteo",
            "corte":"Corte",
            "revision":"Revisión FAI",
            "doblado":"Doblado",
            "soldadura":"Soldadura",
            "maquinado":"Maquinado",
            "pintura":"Pintura",
            "ensamble":"Ensamble",
            "externo":"Servicio Externo",
            "calidad":"Calidad",
            "instalacion":"Instalación",
            "terminado":"Terminado"
        }
        clave = [k for k,v in status_dict.items() if v == status]
        get_orden = request.env['dtm.proceso'].sudo().search([('status','in',clave)])  
        lista_ordenes = get_orden.mapped('ot_number')               
        get_ordenes_compra = request.env['dtm.compras.items'].sudo().search([('orden_trabajo','in',lista_ordenes)])
        lista = get_ordenes_compra.mapped('model_id.no_cotizacion')
        return {'lista':lista}


    @http.route('/comprar_extraordinaria', type='json', auth='public')
    def comprarExtraordinaria(self):
        raw = request.httprequest.data
        data = json.loads(raw)
        orden = data.get("orden_id")
        material = data.get("material")
        codigo = data.get("codigo")
        proveedor = data.get("proveedor")
        precio = data.get("precio")
        cantidad = data.get("cantidad")
        orden_compra = data.get("orden_compra")       
        user = request.env.user.name
        get_orden = request.env['dtm.odt'].sudo().search([('ot_number','=',int(orden))],limit=1)

        get_realizado = request.env['dtm.compras.realizado'].sudo().search([('codigo','=',int(codigo)),('orden_trabajo','like',orden),('nombre','=',material)],limit=1)
        vals = {
            'orden_trabajo':orden,
            'tipo_orden':get_orden.tipe_order,
            'revision_ot':get_orden.revision_ot,
            'proveedor':proveedor,
            'codigo':int(codigo),
            'nombre':material,
            'cantidad':int(cantidad),
            'unitario':float(precio),
            'costo':float(precio) * int(cantidad),
            'orden_compra':orden_compra,
            'fecha_compra':datetime.now(),
            'mostrador':float(precio),
            'mayoreo':float(precio),
            'autoriza':user,
            'listo_btn':True,
        }
        get_realizado.write(vals) if get_realizado else get_realizado.create(vals)
        get_requerido_old = request.env['dtm.compras.requerido'].sudo().search([('codigo','=',int(codigo)),('orden_trabajo','like',orden),('nombre','=',material)],limit=1)
        get_requerido_old.unlink()
        return {'success':True}
        
    @http.route('/tiempo_status', type='json', auth='public')
    def tiempoStatus(self):
        raw = request.httprequest.data
        data = json.loads(raw)
        orden = data.get("orden_diseno")
        get_orden = request.env['dtm.odt'].sudo().search([('od_number','=',int(orden))],limit=1)
        get_proceso = get_orden.tiempo_status
        result = []
        for proceso in get_orden.tiempo_status:
            result.append({
                'estacion': proceso.estacion,
                'inicial': proceso.inicial and proceso.inicial.isoformat(),
                'final': proceso.final and proceso.final.isoformat(),
                'total': proceso.total,
        })
        return result

    @http.route('/diseno_firma', type='json', auth='public')
    def firmaDiseno(self, orden=None):

        if not orden:
            return {'success': False, 'error': 'Falta el número de orden'}
        try:
            orden_int = int(orden)
        except (TypeError, ValueError):
            return {'success': False, 'error': 'Orden inválida'}       
       
        get_orden = request.env['dtm.odt'].sudo().search([('ot_number','=',int(orden))],limit=1)
        if not get_orden:
            return {'success': False, 'error': 'Orden no encontrada'}
        user = request.env.user.name
        get_orden.write({'firma_ventas': user, 'nesteo_chk':True})
        
        Line = request.env['dtm.materials.line']
    
        for item in get_orden.lista_material_id:
            to_materiales = get_orden.materials_ids.search([
                ('model_id', '=', item.model_id.id),
                ('materials_list', '=', item.material_id.id),
                ], limit=1)

            vals = {
                'model_id': item.model_id.id,
                'nombre': item.material_id.nombre,
                'medida': item.material_id.medida,
                'materials_list': item.material_id.id,
                'materials_cuantity': item.cantidad,
                'usuario': item.usuario,
            }
            vals.update(Line._consumir_stock(item.material_id, item.cantidad, to_materiales))
            to_materiales.write(vals) if to_materiales else Line.create(vals)
        return {'success': True}

    @http.route('/dtm_ordenes_compra_transito', type='http', auth='public')
    def dtm_ordenes_compra_transito(self):
        get_transito = request.env['dtm.compras.realizado'].sudo().search([('listo_btn','=',True),('comprado','!=','Recibido'),('proveedor','!=','DTM')])
        transito = []
        for item in get_transito:
            transito.append({
                'proveedor': item.proveedor,
                'orden': item.orden_trabajo,
                'codigo': item.codigo,
                'descripcion': item.nombre,
                'status': dict(item._fields['status'].selection).get(item.status),
                'entrega':dict(item._fields['entrega'].selection).get(item.entrega),
                'cantidad': item.cantidad,
                'cantidad_recibida': item.cantidad_almacen,
                'precio': item.costo,
                'fecha_tentativa': item.fecha_compra.strftime('%d-%m-%Y') if item.fecha_compra else '-',
                'autoriza':item.autoriza,   
            })


        return request.make_response(
            json.dumps(transito),
            headers={
                'Content-Type':'application/json',
                'Access-Control-Allow-Origin':'*'
            }
        )

    @http.route('/dtm_prioridad_date', type='json', auth='public')
    def dtm_prioridad_date(self):
        raw = request.httprequest.data
        data = json.loads(raw)
        od = data.get("od")
        prioridad_date = data.get("prioridad_date")
        get_orden = request.env['dtm.odt'].sudo().search([('od_number','=',int(od))],limit=1)
        get_orden.write({'prioridad_date':prioridad_date})
        return {'success':True}
       
    @http.route('/dtm_ordenes_compra/en_maquinados', type='http', auth='public')
    def dtm_ordenes_compra_en_maquinados(self):        
        get_en_maquinados = request.env['dtm.maquinados'].sudo().search([])
        en_maquinados = []
        for item in get_en_maquinados:
            get_odt = request.env['dtm.odt'].sudo().search([('ot_number','=',item.orden_trabajo),('revision_ot','=',item.revision_ot)],limit=1)
            en_maquinados.append({
                'orden_trabajo': item.orden_trabajo,
                'tipo': item.tipo_orden,
                'version': item.revision_ot,
                'cliente': get_odt.name_client,
                'proyecto': get_odt.product_name,
                'disenador': item.disenador,
                'status': round(item.status,0),
            })
        return request.make_response(
            json.dumps(en_maquinados),
            headers={
                'Content-Type':'application/json',
                'Access-Control-Allow-Origin':'*'
            }
        ) 
            