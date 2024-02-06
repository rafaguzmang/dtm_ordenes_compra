from odoo import api,fields,models
import datetime
from odoo.exceptions import ValidationError

class OrdenesCompra(models.Model):
    _name = "dtm.ordenes.compra"
    _description = "Se muestran todos los archivos de las ordenes de compra"

    no_cotizacion_id = fields.Many2one("dtm.ordenes.compra.precotizaciones")
    no_cotizacion = fields.Char(readonly=True, store=True)
    cotizacion_mas = fields.Integer()
    cliente = fields.Many2one('res.partner',string="Cliente")
    cliente_prov = fields.Char(string="Cliente", readonly=True, store=True)
    orden_compra = fields.Char(string="Orden de Compra")
    fecha_entrada = fields.Date(string="Fecha Entrada",default= datetime.datetime.today(),readonly=True,store=True)
    fecha_salida = fields.Date(string="Fecha Entrega",default= datetime.datetime.today())
    descripcion_id = fields.One2many("dtm.compras.items",'model_id')
    precio_total = fields.Float(string="Precio total")
    proveedor = fields.Selection(string='Proveedor',default='dtm',
        selection=[('dtm', 'DISEÑO Y TRANSFORMACIONES METALICAS S DE RL DE CV'), ('mtd', 'METAL TRANSFORMATION & DESIGN')])
    # archivos = fields.Binary(string="Archivo")
    archivos_id = fields.Many2many("ir.attachment",string="Archivos")
    prioridad = fields.Selection(string="Prioridad", selection=[('uno',1),('dos',2),('tres',3),('cuatro',4),('cinco',5),('seis',6),('siete',7),('ocho',8),('nueve',9),('diez',10)])
    currency = fields.Selection(string="Moneda",defaul="mx", selection=[('mx','MXN'),('usd','USD')], readonly = True)

    # facturado_toogle = fields.Boolean( defaul=False)
    no_factura = fields.Char(string="No Factura")
    notas = fields.Text()
    parcial = fields.Boolean(string="Parcial")

    @api.onchange("parcial")
    def _onchange_parcial(self):
        print(self.descripcion_id._origin.id)
        print(self.parcial)
        for par in self.descripcion_id:
            print(par._origin.id)
            if self.parcial:
                parcial = "true"
            else:
                parcial = "false"
            self.env.cr.execute("UPDATE dtm_compras_items SET parcial='"+parcial+"' WHERE id="+str(self.descripcion_id._origin.id))




    def action_facturado(self):
        # if self.no_factura and self.orden_compra and self.no_cotizacion and self.archivos:
        if self.no_factura:
            # print(self.no_cotizacion,self.no_cotizacion,self.orden_compra,self.fecha_entrada,datetime.datetime.today(),self.descripcion_id,self.precio_total,self.proveedor,self.archivos,self.nombre_archivo,self.currency,self.no_factura)


            get_fact = self.env['dtm.ordenes.compra.facturado'].search([("id","=",self.id)])
            if not get_fact:
                for result in self.descripcion_id:#Inserta los items en la tabla de facturado
                    self.env.cr.execute("UPDATE dtm_compras_items SET no_factura="+self.no_factura+" WHERE id="+str(result.id))
                    get_fact_item = self.env['dtm.compras.items'].search([("no_factura","=",self.no_factura)])
                    get_final = self.env['dtm.compra.facturado.item'].search([("no_factura","=",self.no_factura)])
                    if not get_final:
                        for item in get_fact_item:
                            # print(item.item,item.cantidad,item.precio_unitario,item.precio_total,item.orden_trabajo,item.no_factura,item.orden_compra)
                            self.env.cr.execute("INSERT INTO dtm_compra_facturado_item (item, cantidad, precio_unitario, precio_total ,orden_trabajo, no_factura, orden_compra) "+
                                                                               "VALUES ('"+item.item+"', "+str(item.cantidad)+", "+str(item.precio_unitario)+", "+str(item.precio_total)+", '"+str(item.orden_trabajo)+"', '"+str(item.no_factura)+"', '"+str(item.orden_compra)+"')")

                if not self.archivos_id:
                    archivos_id = 0
                else:
                    archivos_id = self.archivos_id[0].res_id
                #Inserta los datos del número de servicio
                self.env.cr.execute("INSERT INTO dtm_ordenes_compra_facturado(id,no_cotizacion, cliente_prov, orden_compra, fecha_factura, precio_total, proveedor,currency,factura, res_id, notas) " +
                                                                 "VALUES ("+str(self.id)+",'"+self.no_cotizacion+"', '"+self.cliente_prov+"', '"+str(self.orden_compra)+"', '"+str(datetime.datetime.today())+"','"+str(self.precio_total)+"','"+self.proveedor+"', '"+self.currency+"', '"+self.no_factura+"', "+str(archivos_id)+", '"+str(self.notas)+"')")
                self.env.cr.execute("DELETE FROM dtm_ordenes_compra WHERE id="+str(self.id))

            else:
                # self.env.cr.execute("UPDATE dtm_ordenes_compra_facturado SET cliente_prov='"+self.cliente_prov+"', no_cotizacion='"+self.no_cotizacion+"' WHERE id="+ str(self.id))

                raise ValidationError("Esta factura ya existe")
        else:
            raise ValidationError("No existe número de factura")


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
        # print(self.no_cotizacion_id.precotizacion)
        # print(get_cot)
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
        self.cotizacion_mas = len(get_cot)



    def get_view(self, view_id=None, view_type='form', **options):# Llena la tabla dtm.ordenes.compra.precotizaciones con las cotizaciones(NO PRECOTIZACIONES) pendientes
        res = super(OrdenesCompra,self).get_view(view_id, view_type,**options)

        get_pre = self.env['dtm.cotizaciones'].search([])
        for pre in get_pre:
            get_cot = self.env['dtm.ordenes.compra.precotizaciones'].search([('precotizacion','=',pre.no_cotizacion)])
            get_facturado = self.env['dtm.ordenes.compra.facturado'].search([('no_cotizacion','=',pre.no_cotizacion)])
            get_odc = self.env['dtm.ordenes.compra'].search([("no_cotizacion","=",pre.no_cotizacion)])
            # print(get_odc[0])
            if get_odc:
                get_odc = get_odc[0]
            if not get_cot and not get_facturado:
                self.env.cr.execute("INSERT INTO dtm_ordenes_compra_precotizaciones (precotizacion) VALUES ('"+pre.no_cotizacion+"') ")
            if get_odc:
                self.env.cr.execute("DELETE FROM dtm_ordenes_compra_precotizaciones WHERE precotizacion = '" + get_odc.no_cotizacion+"'")

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
    no_factura = fields.Char(string="No Factura")
    orden_compra = fields.Char(string="PO")
    archivos = fields.Binary(string="Archivo")
    nombre_archivo = fields.Char(string="Nombre")
    status = fields.Char(string="Status")
    parcial = fields.Boolean(default=False)





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





