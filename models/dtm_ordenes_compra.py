import base64, io

from odoo import api,fields,models
import datetime
import re
from odoo.exceptions import ValidationError

class OrdenesCompra(models.Model):
    _name = "dtm.ordenes.compra"
    _description = "Se muestran todos los archivos de las ordenes de compra"
    _order = "id desc"

    no_cotizacion_id = fields.Many2one("dtm.ordenes.compra.precotizaciones")
    no_cotizacion = fields.Char(readonly=True)
    cotizacion_mas = fields.Integer()
    # cliente = fields.Many2one('res.partner',string="Cliente")
    cliente_prov = fields.Char(string="Cliente", readonly=True, store=True)
    orden_compra = fields.Char(string="Orden de Compra")
    fecha_entrada = fields.Date(string="Fecha Entrada",default= datetime.datetime.today(),readonly=True,store=True)
    fecha_salida = fields.Date(string="Fecha Entrega",default= datetime.datetime.today())

    descripcion_id = fields.One2many("dtm.compras.items",'model_id')#Modelo donde se almacenan los requerimientos

    precio_total = fields.Float(string="Precio total")
    proveedor = fields.Selection(string='Proveedor',default='dtm',
        selection=[('dtm', 'DISEÑO Y TRANSFORMACIONES METALICAS S DE RL DE CV'), ('mtd', 'METAL TRANSFORMATION & DESIGN')])
    # archivos = fields.Binary(string="Archivo")
    archivos_id = fields.Many2many("ir.attachment",string="Archivos")
    prioridad = fields.Selection(string="Prioridad", selection=[('uno',1),('dos',2),('tres',3),('cuatro',4),('cinco',5),('seis',6),('siete',7),('ocho',8),('nueve',9),('diez',10)])
    currency = fields.Selection(string="Moneda",defaul="mx", selection=[('mx','MXN'),('us','USD')], readonly = True)

    # facturado_toogle = fields.Boolean( defaul=False)
    no_factura = fields.Char(string="No Factura")
    notas = fields.Text()
    parcial = fields.Boolean(string="Parcial")

    # email_img = fields.Image(string="Imagen")

    def action_sumar(self):
        get_total = self.env['dtm.compras.items'].search([('model_id',"=",self.id)])
        sum = 0
        for total in get_total:
            sum += total.precio_total
        self.precio_total = sum

    @api.onchange("orden_compra")
    def _onchange_orden_compra(self):
        get_odc = self.env['dtm.ordenes.compra'].search([("orden_compra","=",self.orden_compra)])
        get_cotizaciones =  self.env['dtm.cotizaciones'].search([("no_cotizacion", "=", self.no_cotizacion)])
        val = {
            "po_number": "po"
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
        get_cot = self.env['dtm.cotizaciones'].search([("no_cotizacion","=",self.no_cotizacion_id.precotizacion)])
        get_compras = self.env['dtm.ordenes.compra'].search([("no_cotizacion","=",get_cot.no_cotizacion)])

        if not get_compras:
            self.proveedor = get_cot.proveedor
            self.cliente_prov = get_cot.cliente_id.name
            self.currency = get_cot.curency
            self.no_cotizacion = self.no_cotizacion_id.precotizacion

            get_req_ext = self.env['dtm.cotizacion.requerimientos'].search([("model_id","=",get_cot.id)])
            # print(get_req_ext.descripcion)
            sum = 0
            for req in get_req_ext:
                contador = self.env['dtm.compras.items'].search_count([])
                id = contador + 1
                for cont in range(1, contador):
                    if not self.env['dtm.compras.items'].search([("id", "=", cont)]):
                        id = cont
                        break
                sum += req.total
                self.env.cr.execute("INSERT INTO dtm_compras_items (id,item,cantidad,precio_unitario,precio_total,model_id)"
                        + " VALUES (" + str(id) + ",'" + str(req.descripcion) + "'," + str(req.cantidad) + "," +
                        str(req.precio_unitario) + "," + str(req.total) + "," + str(self.id) + ")")
            self.precio_total = sum
        self.env['dtm.ordenes.compra.precotizaciones'].search([("precotizacion", "=", self.no_cotizacion)]).unlink()



    def get_view(self, view_id=None, view_type='form', **options):# Llena la tabla dtm.ordenes.compra.precotizaciones con las cotizaciones(NO PRECOTIZACIONES) pendientes
        res = super(OrdenesCompra,self).get_view(view_id, view_type,**options)
        get_cotizaciones =  self.env['dtm.cotizaciones'].search([("po_number", "!=", "po")])
        # print(get_cotizaciones)
        for cotizaciones in get_cotizaciones:
            if not self.env['dtm.ordenes.compra.precotizaciones'].search([("precotizacion","=",cotizaciones.no_cotizacion)]):
                cot = {
                    "precotizacion":cotizaciones.no_cotizacion
                }
                self.env['dtm.ordenes.compra.precotizaciones'].create(cot)

        return res


class ItemsCompras(models.Model):
    _name = "dtm.compras.items"
    _description = "Tabla con items, cantidad, precio unitario de las ordenes de compra"

    model_id = fields.Many2one('dtm.ordenes.compra')

    item = fields.Char(string="Artículo")
    cantidad = fields.Integer(string="Cantidad", options='{"type": "number"}')
    precio_unitario = fields.Float(string="Precio Unitario")
    precio_total = fields.Float(string="Precio Total", store=True)
    orden_trabajo = fields.Integer(string="Orden de Trabajo")
    no_factura = fields.Char(string="No Factura")
    orden_compra = fields.Char(string="PO")
    archivos = fields.Binary(string="Archivo")
    nombre_archivo = fields.Char(string="Nombre")
    status = fields.Char(string="Status")
    parcial = fields.Boolean(default=False)

    # @api.onchange("item")
    # def action_item(self):
    #     self.env['dtm.compras.items'].create()

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
        get_odt = self.env['dtm.odt'].search([],order='ot_number desc', limit=1)
        get_oc = self.env['dtm.ordenes.compra'].search([])
        ot_number = get_odt.ot_number + 1
        po_number = ""
        date_in = ""
        date_rel = ""
        name_client = ""

        for po in get_oc:
            for order in po:
                for item in order.descripcion_id:
                    if item.id == self.id:
                        po_number = order.orden_compra
                        date_in = order.fecha_entrada
                        date_rel = order.fecha_salida
                        name_client = order.cliente_prov
                        no_cotizacion = order.no_cotizacion

        get_rec = self.env['dtm.requerimientos'].search(['&',('servicio','=',no_cotizacion),('nombre','=',self.item)])
        get_odc = self.env['dtm.ordenes.compra'].search([('no_cotizacion','=', no_cotizacion)])
        get_desc = self.env['dtm.cotizaciones'].search([('no_cotizacion','=', no_cotizacion)])
        descripcion = ""
        for item in get_desc.servicios_id:
            if item.descripcion == self.item:
                for desc in item.items_id:
                    descripcion +=  desc.name + ", "
        descripcion = re.sub(", $",".",descripcion)
        if self.orden_trabajo:
            raise ValidationError("Ya hay una orden de trabajo generada")
        elif get_odc.orden_compra:
            self.orden_trabajo = ot_number
            self.env.cr.execute("INSERT INTO dtm_odt (cuantity, ot_number, tipe_order, product_name, po_number, date_in, date_rel, name_client, description) "+
                                "VALUES ("+str(self.cantidad)+", '"+str(ot_number)+"', 'OT', '"+str(self.item)+"', '"+str(po_number)+"', '"+str(date_in)+"', '"+str(date_rel)+"', '"+str(name_client)+"', '"+descripcion+"' )")
        else:
             raise ValidationError("No existe número de compra")

class Precotizaciones(models.Model): # Modelo para capturar las precotizaciones pendientes sin orden de compra
    _name = "dtm.ordenes.compra.precotizaciones"
    _description = "Tabla que almacena las precotizaciones sin ordenes de compra"
    _rec_name = "precotizacion"

    precotizacion = fields.Char()
    orden_compra = fields.Char()





