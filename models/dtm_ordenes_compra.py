import base64, io

from odoo import api,fields,models
import datetime
import re
from odoo.exceptions import ValidationError, AccessError, MissingError,Warning

class OrdenesCompra(models.Model):
    _name = "dtm.ordenes.compra"
    _inherit = ['mail.thread']
    _description = "Se muestran todos los archivos de las ordenes de compra"
    _order = "id desc"
    _rec_name = "no_cotizacion"


    no_cotizacion_id = fields.Many2one("dtm.ordenes.compra.precotizaciones")
    no_cotizacion = fields.Char(readonly=True)
    cotizacion_mas = fields.Integer()
    # cliente = fields.Many2one('res.partner',string="Cliente")
    cliente_prov = fields.Char(string="Cliente", readonly=True, store=True)
    orden_compra = fields.Char(string="Orden de Compra")
    fecha_entrada = fields.Date(string="Fecha Entrada",default= datetime.datetime.today(),readonly=True,store=True)
    fecha_salida = fields.Date(string="Fecha Entrega",default= datetime.datetime.today())
    fecha_po = fields.Date(string="Fecha de la PO")
    fecha_captura_po = fields.Date(string="Fecha Captura PO", readonly= True)

    descripcion_id = fields.One2many("dtm.compras.items",'model_id')#Modelo donde se almacenan los requerimientos

    precio_total = fields.Float(string="Precio total",compute="_compute_action_sumar")
    proveedor = fields.Selection(string='Proveedor',default='dtm',
        selection=[('dtm', 'DISEÑO Y TRANSFORMACIONES METALICAS S DE RL DE CV'), ('mtd', 'METAL TRANSFORMATION & DESIGN')])
    archivos_id = fields.Many2many("ir.attachment","archivos_id",string="P.O.")
    anexos_id = fields.Many2many("ir.attachment")
    currency = fields.Selection(string="Moneda",default="mx", selection=[('mx','MXN'),('us','USD')], readonly = True)

    # facturado_toogle = fields.Boolean( defaul=False)
    no_factura = fields.Char(string="No Factura")
    notas = fields.Text()
    parcial = fields.Boolean(string="Parcial")

    ot_asignadas = fields.Char(string="OTs")

    status = fields.Char(string="Estatus", readonly=True)
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

            self.env['dtm.ordenes.compra.facturado'].create(vals)
            get_id=self.env['dtm.ordenes.compra.facturado'].search([('factura','=',self.no_factura)])

            for item in self.descripcion_id: #Inserta los items asociados a las ordenes de trabajo
                vals = {
                    'item': item.item,
                    'cantidad': item.cantidad,
                    'precio_unitario': item.precio_unitario,
                    'precio_total': item.precio_total,
                    'orden_trabajo': item.orden_trabajo,
                    'no_factura': self.no_factura,
                    'orden_compra': item.orden_compra
                }
                self.env['dtm.compra.facturado.item'].create(vals)
            archivos_id = ""
            for archivo in self.archivos_id: # Inserta los archivos anexos jalandolos de ir_attachment y pasandolos al modelo de dtm.compras.facturado.archivos
                attachment = self.env['ir.attachment'].browse(archivo.id)
                vals = {
                    'archivo':attachment.datas,
                    'nombre': attachment.name,
                    'model_id':get_id.id,

                }
                self.env['dtm.compras.facturado.archivos'].create(vals)

            #Borra la orden de compra de este modelo principal
            get_items = self.env['dtm.compras.items'].search([("model_id","=",self.id)])
            get_items.unlink()
            get_unlink = self.env["dtm.ordenes.compra"].browse(self.id)
            get_unlink.unlink()
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
        for req in get_req_ext.servicios_id:
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

        # get_desc = self.env['dtm.ordenes.compra'].search([])#Revisa si todas las ordenes de esta cotización ya están realizadas y de ser así las marca en color verde
        # for ordenes_compra in get_desc:
        #     for ordenes_trabajo in ordenes_compra:
        #         line_set = set()
        #         for orden in ordenes_trabajo.descripcion_id:
        #             get_ot_status = self.env['dtm.proceso'].search([("ot_number","=",orden.orden_trabajo),("tipe_order","=","OT")])
        #             line_set.add(get_ot_status.status)
        #         line = list(line_set)
        #         if len(line) == 1 and line[0] == "terminado":
        #             ordenes_trabajo.write({"terminado": True})
        # get_for_import = self.env['dtm.ordenes.compra'].search(["|",("exportacion","=","definitiva"),("exportacion","=","virtual")])
        # for compra in get_for_import:
        #     vals = {
        #         "no_cotizacion":compra.no_cotizacion,
        #         "proveedor":compra.proveedor,
        #         "cliente":compra.cliente_prov,
        #         "order_compra":compra.orden_compra,
        #         "fecha_entrada":compra.fecha_entrada,
        #         "fecha_salida":compra.fecha_salida,
        #         "precio_total":compra.precio_total,
        #         "currency":compra.currency,
        #         "odt_ids":compra.descripcion_id,
        #     }
        #     get_compra_import = self.env['dtm.exportaciones'].search([("no_cotizacion","=",compra.no_cotizacion)])#Busca que la compra exista y de no ser así la crea
        #     get_compra_import.write(vals) if get_compra_import else get_compra_import.create(vals)
        #     get_compra_import = self.env['dtm.exportaciones'].search([("no_cotizacion","=",compra.no_cotizacion)])#Busca que la compra exista y de no ser así la crea
        #
        #     trabajos = compra.descripcion_id.mapped("orden_trabajo")
        #
        #     get_compra_import.write({'planos_id': [(5, 0, {})]})
        #     lines = []
        #     for trabajo in trabajos:
        #         get_planos = self.env['dtm.proceso'].search([("ot_number","=",trabajo),("tipe_order","=","OT")])
        #         if get_planos:
        #             for planos in get_planos.anexos_id:
        #                 datos = {
        #                     "nombre":planos.nombre,
        #                     "archivo":planos.documentos,
        #                     "orden":trabajo
        #                 }
        #                 get_copra_ots = self.env['dtm.exportaciones.planos'].search([("nombre","=",planos.nombre),("orden","=",trabajo)])
        #                 get_copra_ots.write(datos) if get_copra_ots else get_copra_ots.create(datos)
        #                 get_copra_ots = self.env['dtm.exportaciones.planos'].search([("nombre","=",planos.nombre),("orden","=",trabajo)])
        #                 lines.append(get_copra_ots[0].id)
        #     get_compra_import.write({'planos_id': [(6, 0, lines)]})


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
    orden_trabajo = fields.Integer(string="Orden de Trabajo")
    no_factura = fields.Char(string="No Factura")
    orden_compra = fields.Char(string="PO")
    archivos = fields.Binary(string="Archivo")
    nombre_archivo = fields.Char(string="Nombre")
    status = fields.Char(string="Status")
    parcial = fields.Boolean(default=False)
    prediseno = fields.Selection(string="Prediseño",selection=[("no","No"),("si","Si")], default="no")

    tipo_servicio = fields.Selection(string="Compra/Servicio", selection=[("servicio","Servicio"),
                                         ("compra","Compra")],default="servicio")
    firma = fields.Char(string="Firmado")
    firma_diseno = fields.Selection(string="Diseñador", selection=[("orozco","Andrés Orozco"),
                                         ("garcia","Luís García"),("na","N/A")],required=True,default="na")

    def action_duplicar(self):
        # print(self.model_id.id)
        get_inf = self.env['dtm.compras.items'].search([("model_id","=",self.model_id.id),("item","!=","")])
        for iter in get_inf:
            self.item = iter.item
            self.cantidad = iter.cantidad
            self.precio_unitario = iter.precio_unitario
            self.precio_total = iter.precio_total

    @api.onchange("cantidad")
    def _onchange_cantidad(self):
        # print("funciona")
        self.precio_total =self.precio_unitario * float(self.cantidad)

    @api.onchange("precio_unitario")
    def _onchange_precio_unitario(self):
        self.precio_total = float(self.precio_unitario) * float(self.cantidad)

    def acction_generar(self):# Genera orden de trabajo
        ot_number = self.orden_trabajo
        tipo_orden = "OT" if self.prediseno == "no" else "SK" #Se obtine el último valor de la orden correspondiente
        if not self.orden_trabajo:
            get_odt = self.env['dtm.odt'].search([("tipe_order","=",tipo_orden)],order='ot_number desc', limit=1).mapped('ot_number')
            get_odtf = self.env['dtm.facturado.odt'].search([("tipe_order","=",tipo_orden)],order='ot_number desc', limit=1).mapped('ot_number')
            get_odt = get_odt[0] if get_odt else 0
            get_odtf = get_odtf[0] if get_odtf else 0
            ot_number = get_odt + 1 if get_odt > get_odtf else get_odtf + 1
            self.orden_trabajo = ot_number
        get_oc = self.env['dtm.ordenes.compra'].search([])
        po_n = 0
        for oc in get_oc: #Se obtienen los datos del la orden de compra al cual esta ligado este servicio
            if self._origin.id in oc.descripcion_id.mapped('id'):
                po_n = oc.id
        get_po = self.env['dtm.ordenes.compra'].browse(po_n)
        disenador = "N/A"
        if self.firma_diseno == "orozco":
            disenador = "Andrés Orozco"
        elif self.firma_diseno == "garcia":
            disenador = "Luís Gracía"

        vals = {
            "cuantity":self.cantidad,
            "product_name":self.item,
            "po_number":get_po.orden_compra if self.prediseno == "no" else get_po.no_cotizacion,
            "date_rel":get_po.fecha_salida,
            "name_client":get_po.cliente_prov,
            "product_name":self.item,
            "no_cotizacion":get_po.no_cotizacion,
            "disenador":disenador,
            "po_fecha_creacion":get_po.fecha_captura_po if self.prediseno == "no" else None,
            "tipe_order":tipo_orden,
            "ot_number":self.orden_trabajo,
            "po_fecha":get_po.fecha_po if self.prediseno == "no" else None,
            "description":', '.join(self.env['dtm.cotizacion.requerimientos'].search([("id","=",self.id_item)]).items_id.mapped('name'))
        }
        get_otd = self.env["dtm.odt"].search([("ot_number","=",ot_number),("tipe_order","=",tipo_orden)])
        get_otd.write(vals) if get_otd else get_otd.create(vals)
        get_otd = self.env["dtm.odt"].search([("ot_number","=",ot_number),("tipe_order","=",tipo_orden)])
        get_otd.write({'orden_compra_pdf': [(5, 0, {})]})
        if self.prediseno == "si":
            get_otd.write({'orden_compra_pdf': [(6, 0, get_po.anexos_id.mapped('id'))]})
        else:
            lines = []
            lines.extend(get_po.archivos_id.mapped('id'))
            lines.extend(get_po.anexos_id.mapped('id'))
            get_otd.write({'orden_compra_pdf': [(6, 0, lines)]})
        #------------------------------------------------------------------------------------------------------
        # Se encarga de ver los servicios y a quien están asignados así como si el diseñador ya firmó
        get_orden_compra =  self.env['dtm.ordenes.compra'].search([("id", "=", self.model_id.id)]).descripcion_id.mapped('id')
        list_items = [item for item in get_orden_compra if self.env['dtm.compras.items'].search([("id", "=", item)]).tipo_servicio == "servicio"]
        list_orm = [self.env['dtm.compras.items'].search([("id", "=", item)]) for item in list_items]
        lista = [f"|𝓐 {item.orden_trabajo}✔|" if item.firma_diseno == "orozco" and item.firma == "Andrés Alberto Orozco Martínez" else f"|𝓐 {item.orden_trabajo}❌| " if item.firma_diseno == "orozco" and not item.firma  else f"|𝓛 {item.orden_trabajo}✔|" if item.firma_diseno == "garcia" and item.firma == "Luís Donaldo García Rayos" else f"|𝓛 {item.orden_trabajo}❌|" if item.firma_diseno == "garcia" and not item.firma else f"|{item.orden_trabajo}❌|" for item in list_orm]
        self.env['dtm.ordenes.compra'].search([("id", "=", self.model_id.id)]).write({
            "ot_asignadas":" ".join(lista),
        })

class Precotizaciones(models.Model): # Modelo para capturar las precotizaciones pendientes sin orden de compra
    _name = "dtm.ordenes.compra.precotizaciones"
    _description = "Tabla que almacena las precotizaciones sin ordenes de compra"
    _rec_name = "precotizacion"

    precotizacion = fields.Char()
    orden_compra = fields.Char()





