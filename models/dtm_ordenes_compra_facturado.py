from odoo import api,fields,models

class Facturado(models.Model):
    _name="dtm.ordenes.compra.facturado"
    _description="Tabla donde se almacenarán las ordenes de compra facturadas"
    _order = "id desc"
    _rec_name = "no_cotizacion"


    no_cotizacion = fields.Char(readonly=True, store=True)
    cliente_prov = fields.Char(string="Cliente", readonly=True)
    orden_compra = fields.Char(string="Orden de Compra",readonly=True)
    fecha_factura = fields.Date(string="Fecha de Facturación",readonly=True)
    descripcion_id = fields.Many2many("dtm.compra.facturado.item",compute="_compute_descripcion_id", readonly=False)
    precio_total = fields.Float(string="Precio total",readonly=True)
    proveedor = fields.Selection(string='Proveedor',readonly=True,
        selection=[('dtm', 'DISEÑO Y TRANSFORMACIONES METALICAS S DE RL DE CV'), ('mtd', 'METAL TRANSFORMATION & DESIGN')])
    archivos_id = fields.One2many("dtm.compras.facturado.archivos","model_id",string="Archivos")
    currency = fields.Selection(default="mx", selection=[('mx','MXN'),('us','USD')], readonly = True)
    factura = fields.Char(string="Factura/s",readonly=False)
    notas = fields.Text(string="notas", default="solo notas")
    res_id = fields.Integer()

    def _compute_descripcion_id(self):
        for result in self:
            # print("descripcion_id",result.descripcion_id)
            get_cot = self.env['dtm.compra.facturado.item'].search([("no_factura", "=", result.factura)])
            lines = []
            line = (5, 0, {})
            lines.append(line)
            for cot in get_cot:
                # print(cot.id)
                line = (4, cot.id, {})
                lines.append(line)
            result.descripcion_id = lines

class ItemFactura(models.Model):
    _name = "dtm.compra.facturado.item"
    _description = "Guarda los servicios de las cotizaciones ya facturadas"
    item = fields.Char(string="Artículo")
    cantidad = fields.Char(string="Cantidad")
    precio_unitario = fields.Float(string="Precio Unitario")
    precio_total = fields.Float(string="Precio Total", store=True)
    orden_trabajo = fields.Char(string="OT")
    no_factura = fields.Char(string="No Factura")
    orden_compra = fields.Char(string="PO")
    orden_diseno = fields.Integer(string="OD")
    disenador = fields.Char(string="Diseñador")


class ArchivosAnexos(models.Model):
    _name = "dtm.compras.facturado.archivos"
    _description = "modelo donde se guardarán los archivos"

    model_id = fields.Many2one("dtm.ordenes.compra.facturado")
    archivo = fields.Binary()
    nombre = fields.Char()


