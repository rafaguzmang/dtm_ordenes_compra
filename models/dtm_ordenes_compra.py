from odoo import api,fields,models
import datetime
from odoo.exceptions import ValidationError, AccessError, MissingError,Warning

class OrdenesCompra(models.Model):
    _name = "dtm.ordenes.compra"
    _inherit = ['mail.thread']
    _description = "Se muestran todos los archivos de las ordenes de compra"
    _order = "id desc"
    _rec_name = "no_cotizacion"


    no_cotizacion_id = fields.Many2one("dtm.ordenes.compra.precotizaciones", string='Cotización')
    no_cotizacion = fields.Char(readonly=True)
    cotizacion_mas = fields.Integer()
    # cliente = fields.Many2one('res.partner',string="Cliente")
    cliente_prov = fields.Char(string="Cliente", readonly=True, store=True)
    orden_compra = fields.Char(string="P.O.")
    fecha_entrada = fields.Date(string="Fecha Entrada",default= datetime.datetime.today(),readonly=True,store=True)
    fecha_salida = fields.Date(string="Fecha Entrega",default= datetime.datetime.today())
    fecha_po = fields.Date(string="Fecha de la PO")
    fecha_captura_po = fields.Date(string="Fecha Captura PO", readonly= True)

    descripcion_id = fields.One2many("dtm.compras.items",'model_id')#Modelo donde se almacenan los requerimientos

    precio_total = fields.Float(string="Precio total",compute="_compute_action_sumar")
    proveedor = fields.Selection(string='Proveedor',default='dtm',
        selection=[('dtm', 'DTM'), ('mtd', 'MTD')])
    archivos_id = fields.Many2many("ir.attachment","archivos_id",string="P.O.")
    anexos_id = fields.Many2many("ir.attachment")
    currency = fields.Selection(string="Moneda",default="mx", selection=[('mx','MXN'),('us','USD')], readonly = True)

    # facturado_toogle = fields.Boolean( defaul=False)
    no_factura = fields.Char(string="No Factura")
    notas = fields.Text()

    ot_asignadas = fields.Char(string="OTs")

    status = fields.Selection(string="Status",selection=[('no','N/A'),('od','O.D.'),('ot','O.T.'),('p','P'),('q','Q'),('t','T')], readonly=False,default='no')
    parcial = fields.Boolean(string="Parcial",readonly=True)
    exportacion = fields.Selection(string="Exportación", selection=[('definitiva','Definitiva'),('virtual','Virtual')])
    terminado = fields.Boolean()

    comentarios = fields.Char(string="Comentarios")


    #Acciones para los smart buttons
    def action_sumar(self):
        pass

    def action_pasive(self):
        pass

    @api.onchange("fecha_po")
    def _onchange_fecha_po(self):
        self.fecha_captura_po = datetime.datetime.now()

    # email_img = fields.Image(string="Imagen")
    @api.depends("descripcion_id")
    def _compute_action_sumar(self):
        for result in self:
            get_total = result.descripcion_id.mapped("precio_total")
            result.precio_total = sum(get_total)

    @api.onchange("orden_compra")
    def _onchange_orden_compra(self):
        get_odc = self.env['dtm.ordenes.compra'].search([("orden_compra","=",self.orden_compra)])
        get_cotizaciones =  self.env['dtm.cotizaciones'].search([("no_cotizacion", "=", self.no_cotizacion)])
        val = {
            "po_number": self.orden_compra
        }
        get_cotizaciones.write(val)
        self.env['dtm.ordenes.compra.precotizaciones'].search([("precotizacion","=",self.no_cotizacion)]).unlink()

        if get_odc and self.orden_compra and self.orden_compra != "Pendiente" and self.orden_compra != "N/A":
             raise ValidationError("Esta orden de compra ya existe")

    @api.onchange("parcial")
    def _onchange_parcial(self):
        # print(self.descripcion_id._origin.id)
        # print(self.parcial)
        for par in self.descripcion_id:
            # print(par._origin.id)
            if self.parcial:
                parcial = "true"
            else:
                parcial = "false"
            self.env.cr.execute("UPDATE dtm_compras_items SET parcial='"+parcial+"' WHERE id="+str(par._origin.id))

    def action_facturado(self): # Pasa los trabajos con orden o ordenes de compra al modelo de facturados
        if self.no_factura:
            ordenes_lts = []
            for orden in self.descripcion_id:
                if self.env['dtm.proceso'].search([('ot_number','=',str(orden.orden_trabajo))]):#Vamos a revisar si todas las ordenes ya están terminadas
                    ordenes_lts.append(self.env['dtm.proceso'].search([('ot_number','=',str(orden.orden_trabajo))]).status)
            if len(list(set(ordenes_lts))) == 1 and list(set(ordenes_lts))[0] == 'terminado':
                vals = {
                    'no_cotizacion': self.no_cotizacion,
                    'cliente_prov': self.cliente_prov,
                    'orden_compra': self.orden_compra,
                    'fecha_factura': datetime.datetime.today(),
                    'precio_total': self.precio_total,
                    'proveedor': self.proveedor,
                    'currency': self.currency,
                    'factura': self.no_factura,
                    'notas': self.notas
                }

                self.env['dtm.ordenes.compra.facturado'].create(vals)# Crea el objeto en el modelo de facturado
                get_id=self.env['dtm.ordenes.compra.facturado'].search([('factura','=',self.no_factura)])# Apunto al nuevo objeto para manipulación

                for item in self.descripcion_id: #Inserta los items asociados a las ordenes de trabajo tabla one2many
                    vals = {
                        'item': item.item,
                        'cantidad': item.cantidad,
                        'precio_unitario': item.precio_unitario,
                        'precio_total': item.precio_total,
                        'orden_trabajo': item.orden_trabajo,
                        'no_factura': self.no_factura,
                        'orden_compra': self.orden_compra,
                        'orden_diseno': item.orden_diseno,
                        'disenador': "Andrés Orozco" if item.firma_diseno == "orozco" else "Luis Donaldo García Rayos" if item.firma_diseno == "garcia" else "Bryan Banda" if item.firma_diseno == "bryan" else "N/A"
                    }
                    self.env['dtm.compra.facturado.item'].create(vals)
                for archivo in self.archivos_id: # Inserta los archivos anexos jalandolos de ir_attachment y pasandolos al modelo de dtm.compras.facturado.archivos
                    attachment = self.env['ir.attachment'].browse(archivo.id)
                    vals = {
                        'archivo':attachment.datas,
                        'nombre': attachment.name,
                        'model_id':get_id.id,
                    }
                    self.env['dtm.compras.facturado.archivos'].create(vals)

                #Pasa la información del modulo de proceso a facturado
                for orden in self.descripcion_id:
                    get_proceso =  self.env['dtm.proceso'].search([('ot_number','=',str(orden.orden_trabajo))])#Vamos a recabar la información
                    # print('orden de compra',self.env['dtm.ordenes.compra.facturado'].search([("orden_compra","=",get_proceso.po_number)], limit=1).factura,get_proceso.po_number)
                    if get_proceso:
                        vals = {
                                "status": self.env['dtm.ordenes.compra.facturado'].search([("orden_compra","=",get_proceso.po_number)], limit=1).factura if get_proceso.po_number else 'Sin P.O.',
                                "ot_number": get_proceso.ot_number,
                                "tipe_order": get_proceso.tipe_order,
                                "name_client": get_proceso.name_client,
                                "product_name": get_proceso.product_name,
                                "date_in": get_proceso.date_in,
                                "po_number": get_proceso.po_number,
                                "date_rel": get_proceso.date_rel,
                                "version_ot": get_proceso.version_ot,
                                "color": get_proceso.color,
                                "cuantity": get_proceso.cuantity,
                                # "materials_ids": get_proceso.materials_ids,
                                "planos": get_proceso.planos,
                                "nesteos": get_proceso.nesteos,
                                "rechazo_id":get_proceso.rechazo_id,
                                "anexos_id":get_proceso.anexos_id,
                                "cortadora_id":get_proceso.cortadora_id,
                                "primera_pieza_id":get_proceso.primera_pieza_id,
                                "tubos_id":get_proceso.tubos_id,
                                "firma": get_proceso.firma,
                                "firma_compras": get_proceso.firma_compras,
                                "firma_diseno": get_proceso.firma_diseno,
                                "firma_almacen": get_proceso.firma_almacen,
                                "firma_ventas": get_proceso.firma_ventas,
                                "description": get_proceso.description,
                                "firma_calidad":get_proceso.firma_calidad,
                                "calidad_liberacion":get_proceso.calidad_liberacion,
                                "date_terminado":get_proceso.date_terminado,
                                "date_inicio":get_proceso.create_date
                            }
                        get_facturado = self.env['dtm.facturado.odt'].search([("ot_number","=",orden.orden_trabajo)])
                        get_facturado.write(vals) if get_facturado else get_facturado.create(vals)
                        get_facturado = self.env['dtm.facturado.odt'].search([("ot_number","=",orden.orden_trabajo)])
                        get_facturado.write({'materieales_id': [(5, 0, {})]})
                        lines = []
                        for item in get_proceso.materials_ids:#Se agrega o se actualiza material de la tabla dtm.facturado.materiales y se obtienen los id para casarlos con la orden correspondiente
                            valmat = {
                                "material":f"{item.nombre} {item.medida}",
                                "cantidad":item.materials_cuantity,
                            }
                            get_facturado_material = self.env['dtm.facturado.materiales'].search([("material","=",f"{item.nombre} {item.medida}"),("cantidad","=",item.materials_cuantity)])
                            get_facturado_material.write(valmat) if get_facturado_material else get_facturado_material.create(valmat)
                            get_facturado_material = self.env['dtm.facturado.materiales'].search([("material","=",f"{item.nombre} {item.medida}"),("cantidad","=",item.materials_cuantity)])
                            lines.append(get_facturado_material.id)
                        get_facturado.write({'materieales_id': [(6, 0, lines)]})
                # -------------------------------------------------------------------------------------------------------------------------------
                        if get_facturado:
                            self.env['dtm.odt'].search([('ot_number','=',int(orden.orden_trabajo))]).unlink()
                            self.env['dtm.proceso'].search([('ot_number','=',str(orden.orden_trabajo))]).unlink()
                            self.env['dtm.compras.realizado'].search([('orden_trabajo','=',int(orden.orden_trabajo))]).unlink()

                # Borra la orden de compra de este modelo principal
                get_items = self.env['dtm.compras.items'].search([("model_id","=",self.id)])
                get_items.unlink()
                get_unlink = self.env["dtm.ordenes.compra"].browse(self.id)
                get_unlink.unlink()
                # ----------
            else:
                raise ValidationError("Todas las ordenes deben de estar en \"Estatus de Terminado\"!!")
        else:
            raise ValidationError("No existe número de factura")

    @api.onchange("nombre_archivo")
    def action_archivos(self):
        for result in self:
            if result.nombre_archivo:
                result.fecha_entrada = datetime.datetime.today()

    def action_fill(self):# Autocompleta los datos de la orden de compra de la tabla de cotizaciones
        if not self.no_cotizacion:
            self.no_cotizacion = self.no_cotizacion_id.precotizacion
            get_cot = self.env['dtm.cotizaciones'].search([("no_cotizacion","=",self.no_cotizacion_id.precotizacion)])
        else:
            get_cot = self.env['dtm.cotizaciones'].search([("no_cotizacion","=",self.no_cotizacion)])

        get_compras = self.env['dtm.ordenes.compra'].search([("no_cotizacion","=",get_cot.no_cotizacion)])
        self.proveedor = get_cot.proveedor
        self.cliente_prov = get_cot.cliente_id.name
        self.currency = get_cot.curency
        get_req_ext = self.env['dtm.cotizaciones'].search([("no_cotizacion","=",self.no_cotizacion)])#Tabla con los items de Cotizaciones
        get_compras.write({"descripcion_id":[(5,0,{})]})#Tabla con los items de ordenes de compra
        lines = []
        sum = 0
        # Se busca si esta compra ya fué facturada y de ser así entra como reetrabajo
        get_facturado = self.env['dtm.ordenes.compra.facturado'].search([('no_cotizacion', '=', self.no_cotizacion)],limit=1)
        # En caso de encontrar esta venta en facturado
        if get_facturado:
            # Busca coincidencias en item y cantidad para poder obtener el número de orden de trabajo y de diseño
            for item in get_facturado.descripcion_id:
                get_items = self.env['dtm.compras.items'].search([("id_item","=",get_req_ext.id)])
                sum += item.precio_total
                vals = {
                    "item": item.item,
                    "id_item": get_req_ext.id,
                    "cantidad": item.cantidad,
                    "precio_unitario": item.precio_unitario,
                    "precio_total": item.precio_total,
                    "orden_trabajo":item.orden_trabajo,
                    "orden_diseno":item.orden_diseno,
                    "tipo_servicio":'retrabajo'
                }
                get_items.write(vals) if get_items else get_items.create(vals)
                lines.append(self.env['dtm.compras.items'].search([("id_item", "=", get_req_ext.id)]).id)
        else:
            # Se itera por todos los items de la cotización
            for req in get_req_ext.servicios_id:
                # Suma el costo total del item
                sum += req.total
                get_items = self.env['dtm.compras.items'].search([("id_item","=",req.id)])
                vals = {
                        "item":req.descripcion,
                        "id_item":req.id,
                        "cantidad":req.cantidad,
                        "precio_unitario":req.precio_unitario,
                        "precio_total":req.total,
                    }
                get_items.write(vals) if get_items else get_items.create(vals)
                lines.append(self.env['dtm.compras.items'].search([("id_item","=",req.id)]).id)
        get_compras.write({"descripcion_id":[(6,0,lines)]})
        self.precio_total = sum
        self.env['dtm.cotizaciones'].search([("no_cotizacion", "=", self.no_cotizacion)]).write({"po_number": self.orden_compra})

    def get_view(self, view_id=None, view_type='form', **options):# Llena la tabla dtm.ordenes.compra.precotizaciones con las cotizaciones(NO PRECOTIZACIONES) pendientes
        res = super(OrdenesCompra,self).get_view(view_id, view_type,**options)
        get_cotizaciones =  self.env['dtm.cotizaciones'].search([("po_number", "!=", "po")])
        for cotizaciones in get_cotizaciones:
            if not self.env['dtm.ordenes.compra.precotizaciones'].search([("precotizacion","=",cotizaciones.no_cotizacion)]):
                cot = {
                    "precotizacion":cotizaciones.no_cotizacion
                }
                self.env['dtm.ordenes.compra.precotizaciones'].create(cot)

        # Lógica para darle status a las ordenes
        get_this = self.env['dtm.ordenes.compra'].search([])
        # Obtiene todas las ordenes y sus atibutos
        for orden in get_this:
            orden.ot_asignadas = ','.join(str(ot)for ot in orden.descripcion_id.mapped('orden_trabajo') if ot !=0 )#Asigna las ots existentes para poder filtrar
            # revisa los items uno por uno
            orden.write({'status':'no'})
            if not 0 in orden.descripcion_id.mapped('orden_diseno'):
                orden.write({'status':'od'})
                orden.write({'parcial':False})
            elif len(list(set(orden.descripcion_id.mapped('orden_diseno'))))>1 and 0 in list(set(orden.descripcion_id.mapped('orden_diseno'))):
                orden.write({'status':'od'})
                orden.write({'parcial':True})

            if not 0 in orden.descripcion_id.mapped('orden_trabajo'):
                orden.write({'status':'ot'})
                orden.write({'parcial':False})
            elif len(list(set(orden.descripcion_id.mapped('orden_trabajo'))))>1 and 0 in list(set(orden.descripcion_id.mapped('orden_trabajo'))):
                orden.write({'status':'ot'})
                orden.write({'parcial':True})


            # Busca si las ordenes ya estan en producción de se así marca parcial si solo hay una y quita parcial si estan todas
            firma_list = list(set(orden.descripcion_id.mapped('firma')))
            if len(firma_list)>1 and False in firma_list:
                orden.write({'status':'p','parcial':True})
            if len(firma_list)==1 and not False in firma_list:
                orden.write({'status':'p','parcial':False})
            proceso_ot = orden.descripcion_id.mapped('orden_trabajo')
            status_proceso = [self.env['dtm.proceso'].search([('ot_number','=',orden)]).status for orden in proceso_ot]
            # Busca si hay ordenes en calidad para poner parcial o quitarlo si todad están en calidad
            if 'calidad' in list(set(status_proceso)) and len(list(set(status_proceso)))>1:
                orden.write({'status':'q','parcial':True})
            if 'calidad' in list(set(status_proceso)) and len(list(set(status_proceso)))==1:
                orden.write({'status':'q','parcial':False})
            # Busca si hay ordenes en terminado para poner parcial o quitarlo si todad están en terminado
            if 'terminado' in list(set(status_proceso)) and len(list(set(status_proceso)))>1:
                orden.write({'status':'t','parcial':True})
            if 'terminado' in list(set(status_proceso)) and len(list(set(status_proceso)))==1:
                orden.write({'status':'t','parcial':False})
        return res

class ItemsCompras(models.Model):
    _name = "dtm.compras.items"
    _description = "Tabla con items, cantidad, precio unitario de las ordenes de compra"

    model_id = fields.Many2one('dtm.ordenes.compra')

    item = fields.Char(string="Artículo")
    id_item = fields.Integer()
    cantidad = fields.Integer(string="Cantidad")
    precio_unitario = fields.Float(string="Precio Unitario")
    precio_total = fields.Float(string="Precio Total", store=True)
    orden_trabajo = fields.Integer(string="OT", readonly=False)
    orden_diseno = fields.Integer(string="OD", readonly=False)
    no_factura = fields.Char(string="No Factura")
    archivos = fields.Binary(string="Archivo")
    nombre_archivo = fields.Char(string="Nombre")
    status = fields.Char(string="Notas")
    parcial = fields.Boolean(default=False)
    date_disign_finish = fields.Date(string="Diseño")
    # prediseno = fields.Selection(string="Prediseño",selection=[("no","No"),("si","Si")], default="no")
    tipo_servicio = fields.Selection(string="Tipo", selection=[("fabricacion","Fabricación"),("servicio","Servicio"),
                                         ("compra","Compra"),("retrabajo","Retrabajo")],default="fabricacion")
    firma = fields.Char(string="Firmado")
    firma_diseno = fields.Selection(string="Diseñador", selection=[("orozco","Andrés Orozco"),
                                         ("garcia","Luís García"), ("bryan","Bryan Banda"),("na","N/A")],required=True,default="na")
    intervencion_calidad = fields.Boolean(string='Calidad',default=False)

    @api.onchange("cantidad")
    def _onchange_cantidad(self):
        self.precio_total =self.precio_unitario * float(self.cantidad)

    @api.onchange("precio_unitario")
    def _onchange_precio_unitario(self):
        self.precio_total = float(self.precio_unitario) * float(self.cantidad)

    def acction_generar(self):# Genera orden de diseño si existe la actualiza
            get_father = self.env['dtm.ordenes.compra'].search([('id','=',self.model_id.id)])
            # Obtine el nombre del diseñador asignado
            disenador = "Andrés Orozco" if self.firma_diseno == "orozco" else "garcia" if self.firma_diseno == "garcia" else "bryan" if self.firma_diseno == "bryan" else "N/A"
            # print(self.env['dtm.cotizacion.requerimientos'].search([('id','=',self.id_item)]).mapped('attachment_ids').mapped('id'))
            if not self.orden_diseno and not self.orden_trabajo:
                # Busca el ultimo registro de la orden de diseño y le suma uno
                get_diseno_odt = self.env['dtm.odt'].search([('od_number','!=',False)],order='od_number desc',limit=1)
                get_diseno_fact = self.env['dtm.compra.facturado.item'].search([('orden_diseno','!=',False)],order='orden_diseno desc',limit=1)
                self.orden_diseno = max(get_diseno_odt.od_number,get_diseno_fact.orden_diseno) + 1
                # print(get_diseno_odt.od_number,get_diseno_fact.orden_diseno)
                # print(list(set(self.env['dtm.cotizacion.requerimientos'].search([("model_id","=",self.env['dtm.cotizaciones'].search([('no_cotizacion','=',str(get_father.no_cotizacion))]).id)]).items_id.mapped('name'))).remove(False))
                self.env['dtm.odt'].create( {
                    "od_number": self.orden_diseno,
                    "cuantity":self.cantidad,
                    "product_name":self.item,
                    "po_number": self.env['dtm.ordenes.compra'].search([('id','=',self.model_id.id)]).orden_compra if self.env['dtm.ordenes.compra'].search([('id','=',self.model_id.id)]) else 'N/A',
                    "date_rel":get_father.fecha_salida,
                    "name_client":get_father.cliente_prov,
                    "no_cotizacion":get_father.no_cotizacion,
                    "disenador":disenador,
                    "po_fecha_creacion":self.env['dtm.ordenes.compra'].search([('id','=',self.model_id.id)]).fecha_captura_po if self.env['dtm.ordenes.compra'].search([('id','=',self.model_id.id)]) else '',
                    "tipe_order":"OT", #Se obtine el último valor de la orden correspondiente,
                    "po_fecha":self.env['dtm.ordenes.compra'].search([('id','=',self.model_id.id)]).fecha_po if self.env['dtm.ordenes.compra'].search([('id','=',self.model_id.id)]) else '',
                    "description":', '.join(list(set(self.env['dtm.cotizacion.requerimientos'].search([("model_id","=",self.env['dtm.cotizaciones'].search([('no_cotizacion','=',str(get_father.no_cotizacion))]).id)]).items_id.mapped('name')))),
                    "anexos_ventas_id":get_father.anexos_id,
                    "orden_compra_pdf":get_father.archivos_id,
                    "ot_number":0,
                    "archivos_id":[(6,0,self.env['dtm.cotizacion.requerimientos'].search([('id','=',self.id_item)]).mapped('attachment_ids').mapped('id'))],
                    "date_disign_finish":self.date_disign_finish,
                    "intervencion_calidad":self.intervencion_calidad
                })
            else:
                vals = {
                    "cuantity":self.cantidad,
                    "product_name":self.item,
                    "po_number":self.env['dtm.ordenes.compra'].search([('id','=',self.model_id.id)]).orden_compra if self.env['dtm.ordenes.compra'].search([('id','=',self.model_id.id)]) else 'N/A',
                    "date_rel":get_father.fecha_salida,
                    "name_client":get_father.cliente_prov,
                    "no_cotizacion":get_father.no_cotizacion,
                    "disenador":disenador,
                    "po_fecha_creacion":self.env['dtm.ordenes.compra'].search([('id','=',self.model_id.id)]).fecha_captura_po if self.env['dtm.ordenes.compra'].search([('id','=',self.model_id.id)]) else '',
                    "tipe_order": "RT" if self.tipo_servicio == "retrabajo" else "OT", #Se obtine el último valor de la orden correspondiente,
                    "po_fecha":self.env['dtm.ordenes.compra'].search([('id','=',self.model_id.id)]).fecha_po if self.env['dtm.ordenes.compra'].search([('id','=',self.model_id.id)]) else '',
                    "description":', '.join(self.env['dtm.cotizacion.requerimientos'].search([("id","=",self.id_item)]).items_id.mapped('name')),
                    "anexos_ventas_id":[(6,0,get_father.anexos_id.mapped('id'))],
                    "orden_compra_pdf":get_father.archivos_id,
                    "archivos_id":[(6,0,self.env['dtm.cotizacion.requerimientos'].search([('id','=',self.id_item)]).mapped('attachment_ids').mapped('id'))],
                    "date_disign_finish":self.date_disign_finish,
                    "intervencion_calidad": self.intervencion_calidad,
                    "ot_number":self.orden_trabajo if self.orden_trabajo else 0,
                    "od_number":self.orden_diseno if self.orden_diseno else 0,
                }
                if self.orden_trabajo > 0:
                    if self.tipo_servicio == 'retrabajo' and self.env['dtm.facturado.odt'].search([('ot_number','=',self.orden_trabajo)]) :
                        retrabajo = self.env['dtm.odt'].search([('ot_number','=',self.orden_trabajo),('tipe_order','=','RT')], limit=1)
                        retrabajo.write(vals) if retrabajo else retrabajo.create(vals)

                    else:
                        self.env['dtm.odt'].search(["|",("od_number",'=', self.orden_diseno),("ot_number",'=', self.orden_trabajo)]).write(vals)
                else:
                    self.env['dtm.odt'].search([("od_number", '=', self.orden_diseno)]).write(vals)
            # Proceso para facturar de forma parcial
            get_proceso = self.env['dtm.proceso'].search([("status","=","terminado"),("ot_number","=",self.orden_trabajo)])
            if get_proceso:
                vals = {
                        "status": self.status,
                        "ot_number": get_proceso.ot_number,
                        "tipe_order": get_proceso.tipe_order,
                        "name_client": get_proceso.name_client,
                        "product_name": get_proceso.product_name,
                        "date_in": get_proceso.date_in,
                        "po_number": get_proceso.po_number,
                        "date_rel": get_proceso.date_rel,
                        "version_ot": get_proceso.version_ot,
                        "color": get_proceso.color,
                        "cuantity": get_proceso.cuantity,
                        # "materials_ids": get_proceso.materials_ids,
                        "planos": get_proceso.planos,
                        "nesteos": get_proceso.nesteos,
                        "rechazo_id":get_proceso.rechazo_id,
                        "anexos_id":get_proceso.anexos_id,
                        "cortadora_id":get_proceso.cortadora_id,
                        "primera_pieza_id":get_proceso.primera_pieza_id,
                        "tubos_id":get_proceso.tubos_id,
                        "firma": get_proceso.firma,
                        "firma_compras": get_proceso.firma_compras,
                        "firma_diseno": get_proceso.firma_diseno,
                        "firma_almacen": get_proceso.firma_almacen,
                        "firma_ventas": get_proceso.firma_ventas,
                        "description": get_proceso.description,
                        "firma_calidad":get_proceso.firma_calidad,
                        "calidad_liberacion":get_proceso.calidad_liberacion,
                        "date_disign_finish":self.date_disign_finish
                    }
                get_facturado = self.env['dtm.facturado.odt'].search([('ot_number','=',self.orden_trabajo)])
                get_facturado.write(vals) if get_facturado else get_facturado.create(vals)
                get_facturado.write({'materieales_id': [(5, 0, {})]})
                lines = []
                for item in get_proceso.materials_ids:#Se agrega o se actualiza material de la tabla dtm.facturado.materiales y se obtienen los id para casarlos con la orden correspondiente
                    valmat = {
                        "material":f"{item.nombre} {item.medida}",
                        "cantidad":item.materials_cuantity,
                    }
                    get_facturado_material = self.env['dtm.facturado.materiales'].search([("material","=",f"{item.nombre} {item.medida}"),("cantidad","=",item.materials_cuantity)])
                    get_facturado_material.write(valmat) if get_facturado_material else get_facturado_material.create(valmat)
                    get_facturado_material = self.env['dtm.facturado.materiales'].search([("material","=",f"{item.nombre} {item.medida}"),("cantidad","=",item.materials_cuantity)])
                    lines.append(get_facturado_material.id)
                get_facturado.write({'materieales_id': [(6, 0, lines)]})
                #-------------------------------------------------------------------------------------------------------------------------------
                if get_facturado:
                    self.env['dtm.odt'].search([('ot_number','=',self.orden_trabajo)]).unlink()
                    self.env['dtm.compras.odt'].search([('ot_number','=',self.orden_trabajo)]).unlink()
                    self.env['dtm.proceso'].search([('ot_number','=',self.orden_trabajo)]).unlink()
                    self.env['dtm.compras.realizado'].search([('orden_trabajo','=',self.orden_trabajo)]).unlink()

class Precotizaciones(models.Model): # Modelo para capturar las precotizaciones pendientes sin orden de compra
    _name = "dtm.ordenes.compra.precotizaciones"
    _description = "Tabla que almacena las precotizaciones sin ordenes de compra"
    _rec_name = "precotizacion"

    precotizacion = fields.Char()
    orden_compra = fields.Char()





