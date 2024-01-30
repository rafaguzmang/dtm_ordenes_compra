from odoo import api,fields,models

class Facturado(models.Model):
    _name="dtm.ordenes.compra.facturado"
    _description="Tabla donde se almacenarán las ordenes de compra facturadas"


    no_cotizacion = fields.Char(readonly=True, store=True)
    cliente_prov = fields.Char(string="Cliente", readonly=True)
    orden_compra = fields.Char(string="Orden de Compra",readonly=True)
    fecha_factura = fields.Date(string="Fecha de Facturación",readonly=True)
    descripcion_id = fields.One2many("dtm.compras.items",'model_id',readonly=True)
    precio_total = fields.Float(string="Precio total",readonly=True)
    proveedor = fields.Selection(string='Proveedor',readonly=True,
        selection=[('dtm', 'DISEÑO Y TRANSFORMACIONES METALICAS S DE RL DE CV'), ('mtd', 'METAL TRANSFORMATION & DESIGN')])

    archivos = fields.Binary(string="Archivo",compute= "compute_archivo_correspondiente")
    nombre_archivo = fields.Char(string="Nombre")
    currency = fields.Selection(defaul="mx", selection=[('mx','MXN'),('usd','USD')], readonly = True)
    factura = fields.Char(string="Factura",readonly=True)

    def compute_archivo_correspondiente(self):
        for result in self:
            get_com = self.env['dtm.ordenes.compra'].search([("id","=",self.id)])
            if get_com.archivos:
                result.archivos = get_com.archivos
                result.nombre_archivo = get_com.nombre_archivo




