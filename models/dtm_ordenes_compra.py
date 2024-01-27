from odoo import api,fields,models
import datetime
from odoo.exceptions import ValidationError

class OrdenesCompra(models.Model):
    _name = "dtm.ordenes.compra"
    _description = "Se muestran todos los archivos de las ordenes de compra"

    no_cotizacion_id = fields.Many2one("dtm.ordenes.compra.precotizaciones")
    no_cotizacion = fields.Char(readonly=True, store=True)
    cliente = fields.Many2one('res.partner',string="Cliente")
    cliente_prov = fields.Char(string="Cliente", readonly=True, store=True)
    orden_compra = fields.Char(string="Orden de Compra")
    fecha_entrada = fields.Date(string="Fecha Entrada",default= datetime.datetime.today(),readonly=True,store=True)
    fecha_salida = fields.Date(string="Fecha Entrega",default= datetime.datetime.today())
    descripcion_id = fields.One2many("dtm.compras.items",'model_id')
    precio_total = fields.Float(string="Precio total")
    proveedor = fields.Selection(string='Proveedor',default='dtm',
        selection=[('dtm', 'DISEÑO Y TRANSFORMACIONES METALICAS S DE RL DE CV'), ('mtd', 'METAL TRANSFORMATION & DESIGN')])
    archivos = fields.Binary(string="Archivo")
    nombre_archivo = fields.Char(string="Nombre")
    prioridad = fields.Selection(string="Prioridad", selection=[('uno',1),('dos',2),('tres',3),('cuatro',4),('cinco',5),('seis',6),('siete',7),('ocho',8),('nueve',9),('diez',10)])
    currency = fields.Selection(defaul="mx", selection=[('mx','MXN'),('usd','USD')], readonly = True)

    @api.onchange("nombre_archivo")
    def action_archivos(self):
        for result in self:
            if result.nombre_archivo:
                result.fecha_entrada = datetime.datetime.today()

    @api.onchange("cliente")
    def _onchange_cliente(self):
        # print(self.cliente)
        self.cliente_prov = self.cliente.name

    def action_sumar(self): # Obtine el precio total si este sale en cero
        sum=0
        for result in self.descripcion_id:
            sum+= result.precio_total
        self.precio_total = sum


    def action_fill(self):# Autocompleta los datos de la orden de compra de la tabla de cotizaciones
        get_cliente = self.env['dtm.client.needs'].search([("no_cotizacion","=",self.no_cotizacion_id.precotizacion)])
        get_cot = self.env['dtm.cotizaciones'].search([("no_cotizacion","=",self.no_cotizacion_id.precotizacion)])
        self.proveedor = get_cot.proveedor
        if self.cliente:
            self.cliente_prov = self.cliente.name
        else:
            self.cliente_prov = get_cliente.cliente_ids.name

        self.currency = get_cot.curency
        self.no_cotizacion = self.no_cotizacion_id.precotizacion
        lines = []
        sum = 0
        line =(5,0,{})
        lines.append(line)
        for result in get_cot.servicios_id:
            line =(4,result.id,{})
            lines.append(line)
            sum += result.total
        self.precio_total = sum
        self.descripcion_id = lines



    def get_view(self, view_id=None, view_type='form', **options):# Llena la tabla dtm.ordenes.compra.precotizaciones con las cotizaciones(NO PRECOTIZACIONES) pendientes
        res = super(OrdenesCompra,self).get_view(view_id, view_type,**options)

        get_pre = self.env['dtm.cotizaciones'].search([])
        for pre in get_pre:
            get_cot = self.env['dtm.ordenes.compra.precotizaciones'].search([('precotizacion','=',pre.no_cotizacion)])
            get_odc = self.env['dtm.ordenes.compra'].search([("no_cotizacion","=",pre.no_cotizacion)])
            if not get_cot:
                self.env.cr.execute("INSERT INTO dtm_ordenes_compra_precotizaciones (precotizacion) VALUES ('"+pre.no_cotizacion+"') ")
            if get_odc:
                self.env.cr.execute("DELETE FROM dtm_ordenes_compra_precotizaciones WHERE precotizacion = '" + get_odc.no_cotizacion+"'")
                # print(get_odc.no_cotizacion)

        # get_oc = self.env['dtm.ordenes.compra'].search([])
        # for result in get_oc:
        #      if result.cliente.name:
        #         self.env.cr.execute("UPDATE dtm_ordenes_compra SET cliente_prov = '"+result.cliente.name +"' WHERE id ="+str(result.id))

        get_cot = self.env['dtm.cotizacion.requerimientos'].search([])
        for cot in get_cot:
            get_compras = self.env['dtm.compras.items'].search([('id','=',cot.id)])
            if get_compras:
              self.env.cr.execute("UPDATE dtm_compras_items SET item = '"+cot.descripcion +"', cantidad= "+ str(cot.cantidad) +", precio_unitario="+str(cot.precio_unitario) +" , "+
                                "precio_total="+str(cot.total) +" WHERE id ="+str(cot.id))
            else:
              self.env.cr.execute("INSERT INTO dtm_compras_items (id, item, cantidad, precio_unitario, precio_total) VALUES " +
                                  "("+str(cot.id)+",'" +cot.descripcion+ "', "+str(cot.cantidad)+", "+str(cot.precio_unitario)+","+str(cot.total)+") ")


        return res

class ItemsCompras(models.Model):
    _name = "dtm.compras.items"
    _description = "Tabla con items, cantidad, precio unitario de las ordenes de compra"

    model_id = fields.Many2one('dtm.ordenes.compra')
    item = fields.Char(string="Artículo")
    cantidad = fields.Char(string="Cantidad", options='{"type": "number"}')
    precio_unitario = fields.Float(string="Precio Unitario")
    precio_total = fields.Float(string="Precio Total", store=True)
    orden_trabajo = fields.Char(string="Orden de Trabajo")


    def acction_generar(self):# Genera orden de trabajo
        get_odt = self.env['dtm.odt'].search([])
        get_oc = self.env['dtm.ordenes.compra'].search([])
        list = []
        for ot in get_odt:
            no = int(ot.ot_number)
            list.append(no)
        list.sort(reverse = True)
        ot_number = list[0] + 1
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

        print(get_rec.descripcion)
        print(self.item)

        if self.orden_trabajo:
            raise ValidationError("Ya hay una orden de trabajo generada")
        elif get_odc.orden_compra:
            self.orden_trabajo = ot_number
            self.env.cr.execute("INSERT INTO dtm_odt (cuantity, ot_number, tipe_order, product_name, po_number, date_in, date_rel, name_client, description) "+
                                "VALUES ("+str(self.cantidad)+", '"+str(ot_number)+"', 'ot', '"+str(self.item)+"', '"+po_number+"', '"+str(date_in)+"', '"+str(date_rel)+"', '"+name_client+"', '"+str(get_rec.descripcion)+"' )")
        else:
             raise ValidationError("No existe número de compra")

class Precotizaciones(models.Model): # Modelo para capturar las precotizaciones pendientes sin orden de compra
    _name = "dtm.ordenes.compra.precotizaciones"
    _description = "Tabla que almacena las precotizaciones sin ordenes de compra"
    _rec_name = "precotizacion"

    precotizacion = fields.Char()
    orden_compra = fields.Char()





