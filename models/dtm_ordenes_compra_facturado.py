from odoo import api,fields,models

class Facturado(models.Model):
    _name="dtm.ordenes.compra.facturado"
    _description="Tabla donde se almacenarán las ordenes de compra facturadas"


    no_cotizacion = fields.Char(readonly=True, store=True)
    cliente_prov = fields.Char(string="Cliente", readonly=True)
    orden_compra = fields.Char(string="Orden de Compra",readonly=True)
    fecha_factura = fields.Date(string="Fecha de Facturación",readonly=True)
    descripcion_id = fields.One2many("dtm.compras.items",'model_id',readonly=True,)
    precio_total = fields.Float(string="Precio total",readonly=True)
    proveedor = fields.Selection(string='Proveedor',readonly=True,
        selection=[('dtm', 'DISEÑO Y TRANSFORMACIONES METALICAS S DE RL DE CV'), ('mtd', 'METAL TRANSFORMATION & DESIGN')])

    archivos = fields.Binary(string="Archivo",compute= "compute_archivo_correspondiente")
    nombre_archivo = fields.Char(string="Nombre")
    currency = fields.Selection(defaul="mx", selection=[('mx','MXN'),('usd','USD')], readonly = True)
    factura = fields.Char(string="Factura",readonly=True)

    def compute_archivo_correspondiente(self):
        get_cliente = self.env['dtm.client.needs'].search([("no_cotizacion", "=", self.no_cotizacion_id.precotizacion)])
        get_cot = self.env['dtm.cotizaciones'].search([("no_cotizacion", "=", self.no_cotizacion_id.precotizacion)])
        self.proveedor = get_cot.proveedor
        if self.cliente:
            self.cliente_prov = self.cliente.name
        else:
            self.cliente_prov = get_cliente.cliente_ids.name

        self.currency = get_cot.curency
        self.no_cotizacion = self.no_cotizacion_id.precotizacion
        lines = []
        sum = 0
        line = (5, 0, {})
        lines.append(line)
        for result in get_cot.servicios_id:
            line = (4, result.id, {})
            lines.append(line)
            sum += result.total
        self.precio_total = sum
        self.descripcion_id = lines




