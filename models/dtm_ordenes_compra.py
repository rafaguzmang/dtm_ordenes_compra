from odoo import api,fields,models
import datetime


class OrdenesCompra(models.Model):
    _name = "dtm.ordenes.compra"
    _description = "Se muestran todos los archivos de las ordenes de compra"

    no_cotizacion_id = fields.Many2one("dtm.ordenes.compra.precotizaciones")
    cliente = fields.Char(string="Cliente")
    orden_compra = fields.Char(string="Orden de Compra")
    fecha_entrada = fields.Date(string="Fecha Entrada",default= datetime.datetime.today())
    fecha_salida = fields.Date(string="Fecha Entrega",default= datetime.datetime.today())
    descripcion_id = fields.One2many("dtm.compras.items", "model_id")
    # precio_unitario = fields.Float(string="Precio Unitario")
    # cantidad = fields.Integer(string="Cantidad")
    precio_total = fields.Float(string="Precio total", compute="_compute_precio_total")
    proveedor = fields.Selection(string='Proveedor',default='dtm',
        selection=[('dtm', 'DISEÑO Y TRANSFORMACIONES METALICAS S DE RL DE CV'), ('mtd', 'METAL TRANSFORMATION & DESIGN')])

    archivos = fields.Binary(string="Archivo")
    nombre_archivo = fields.Char(string="Nombre")


    def action_fill(self):
        # print(self.no_cotizacion_id.precotizacion)
        get_cliente = self.env['dtm.precotizacion'].search([("no_cotizacion","=",self.no_cotizacion_id.precotizacion)])
        get_servicios = self.env['dtm.requerimientos'].search([("servicio","=", self.no_cotizacion_id.precotizacion)])
        # print(get_cliente.cliente_ids)
        # print(get_servicios)
        self.cliente = get_cliente.cliente_ids

        lines = []
        line = (5,0,{})
        lines.append(line)
        self.env.cr.execute("DELETE FROM dtm_compras_items")
        num = 1
        for result in get_servicios:
            line =(0,0,{
                "id": num,
                "item": result.nombre,
                "cantidad": result.cantidad,
                "precio_unitario":result.precio_unitario
            })
            lines.append(line)
            num+=1

        self.descripcion_id = lines



    def action_actualizar_precotizaciones(self):# Llena la tabla dtm.ordenes.compra.precotizaciones con las cotizaciones pendientes
        get_info = self.env['dtm.precotizacion'].search([])
        #print(get_info)
        order = 1
        self.env.cr.execute("DELETE FROM  dtm_ordenes_compra_precotizaciones")
        for result in get_info:
            if result:
                self.env.cr.execute("INSERT INTO dtm_ordenes_compra_precotizaciones (id,precotizacion) VALUES ("+ str(order) +",'"+result.no_cotizacion+"') ")
                order += 1



    #-----------Acciones--------------
    @api.depends("descripcion_id")
    def _compute_precio_total(self): # Suma los precios de todos los servicios

        for total in self:
            # print(total.id)
            id = str(total.id)
            # print(id[6:])
            id = id[6:]

            get_info = total.env['dtm.compras.items'].search([('model_id','=',id)])
            # print(get_info)
            sum = 0
            for result in get_info:
                sum = sum + result.precio_total
            # print(sum)
            total.precio_total = sum



class ItemsCompras(models.Model):
    _name = "dtm.compras.items"
    _description = "Tabla con items, cantidad, precio unitario de las ordenes de compra"

    model_id = fields.Many2one("dtm.ordenes.compra")

    item = fields.Char(string="Artículo")
    cantidad = fields.Char(string="Cantidad", options='{"type": "number"}')
    precio_unitario = fields.Float(string="Precio Unitario")
    precio_total = fields.Float(string="Precio Total", compute="_compute_total")
    orden_trabajo = fields.Char(string="Orden de Trabajo")

    @api.depends("precio_unitario")
    def _compute_total(self):
        for result in self:
            result.precio_total = float(result.cantidad) * result.precio_unitario

    def acction_generar(self):# Genera orden de trabajo

        get_info = self.env['dtm.odt'].search([])
        # print(len(get_info))
        get_info = self.env['dtm.odt'].search([("id","=",str(len(get_info)))])
        # print(get_info.ot_number)
        # print(self.model_id.id)
        ot_number = int(get_info.ot_number) + 1
        name_client = self.model_id.id
        cantidad = self.cantidad
        product_name = self.item
        po_number = self.model_id.orden_compra
        date_in = self.model_id.fecha_entrada
        date_rel = self.model_id.fecha_salida
        print(ot_number,name_client,cantidad,product_name,po_number,date_in,date_rel)
        self.env.cr.execute("INSERT INTO dtm_odt (ot_number, name_client, cuantity, tipe_order, product_name, po_number, date_in, date_rel) " +
        "VALUES ('"+str(ot_number)+"',"+str(name_client) +", "+ str(cantidad)+ ", 'ot', '" +product_name +"', '"+str(po_number) +"', '"+str(date_in)+"', '"+ str(date_rel) +"')")


class Precotizaciones(models.Model): # Modelo para capturar las precotizaciones pendientes sin orden de compra
    _name = "dtm.ordenes.compra.precotizaciones"
    _description = "Tabla que almacena las precotizaciones sin ordenes de compra"
    _rec_name = "precotizacion"

    precotizacion = fields.Char()
    orden_compra = fields.Char()



