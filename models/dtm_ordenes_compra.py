from odoo import api,fields,models
import datetime


class OrdenesCompra(models.Model):
    _name = "dtm.ordenes.compra"
    _description = "Se muestran todos los archivos de las ordenes de compra"

    no_cotizacion_id = fields.Many2one("dtm.ordenes.compra.precotizaciones")
    no_cotizacion = fields.Char(readonly=True, store=True)
    cliente = fields.Many2one('res.partner',string="Cliente")
    cliente_prov = fields.Char(string="Cliente", readonly=True)
    orden_compra = fields.Char(string="Orden de Compra")
    fecha_entrada = fields.Date(string="Fecha Entrada",default= datetime.datetime.today())
    fecha_salida = fields.Date(string="Fecha Entrega",default= datetime.datetime.today())
    descripcion_id = fields.Many2many("dtm.compras.items")
    precio_total = fields.Float(string="Precio total")
    proveedor = fields.Selection(string='Proveedor',default='dtm',
        selection=[('dtm', 'DISEÑO Y TRANSFORMACIONES METALICAS S DE RL DE CV'), ('mtd', 'METAL TRANSFORMATION & DESIGN')])
    archivos = fields.Binary(string="Archivo")
    nombre_archivo = fields.Char(string="Nombre")
    prioridad = fields.Selection(string="Prioridad", selection=[('uno','1'),('dos','2'),('tres','3'),('cuatro','4'),('cinco','5'),('seis','6'),('siete','7'),('ocho','8'),('nueve','9'),('diez','10')])
    currency = fields.Selection(defaul="mx", selection=[('mx','MXN'),('usd','USD')], readonly = True)

    @api.onchange("cliente")
    def _onchange_cliente(self):
        # print(self.cliente)
        self.cliente_prov = self.cliente.name
        self.env.cr.execute("UPDATE dtm_ordenes_compra SET cliente_prov='"+self.cliente.name+"' WHERE id="+ str(self._origin.id))

    def action_sumar(self): # Obtine el precio total si este sale en cero
        sum=0
        for result in self.descripcion_id:
            sum+= result.precio_total
        self.precio_total = sum

    @api.onchange("no_cotizacion_id")
    def _action_fill(self):# Autocompleta los datos de la orden de compra de la tabla de cotizaciones
        get_cliente = self.env['dtm.client.needs'].search([("no_cotizacion","=",self.no_cotizacion_id.precotizacion)])
        get_cot = self.env['dtm.cotizaciones'].search([("no_cotizacion","=",self.no_cotizacion_id.precotizacion)])
        self.proveedor = get_cot.proveedor
        self.cliente_prov = get_cliente.cliente_ids.name
        self.currency = get_cot.curency
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
        self.no_cotizacion = self.no_cotizacion_id.precotizacion
        self.env.cr.execute("UPDATE dtm_ordenes_compra SET no_cotizacion = '"+ self.no_cotizacion + "' WHERE id="+str(self._origin.id))


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

        get_oc = self.env['dtm.ordenes.compra'].search([])
        for result in get_oc:
             if result.cliente.name:
                self.env.cr.execute("UPDATE dtm_ordenes_compra SET cliente_prov = '"+result.cliente.name +"' WHERE id ="+str(result.id))

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

    item = fields.Char(string="Artículo")
    cantidad = fields.Char(string="Cantidad", options='{"type": "number"}')
    precio_unitario = fields.Float(string="Precio Unitario")


    precio_total = fields.Float(string="Precio Total", store=True)
    orden_trabajo = fields.Char(string="Orden de Trabajo")


    def acction_generar(self):# Genera orden de trabajo
        pass


class Precotizaciones(models.Model): # Modelo para capturar las precotizaciones pendientes sin orden de compra
    _name = "dtm.ordenes.compra.precotizaciones"
    _description = "Tabla que almacena las precotizaciones sin ordenes de compra"
    _rec_name = "precotizacion"

    precotizacion = fields.Char()
    orden_compra = fields.Char()





