from odoo import api,fields,models

class Facturado(models.Model):
    _name="dtm.ordenes.compra.facturado"
    _description="Tabla donde se almacenarán las ordenes de compra facturadas"


    no_cotizacion = fields.Char(readonly=True, store=True)
    cliente_prov = fields.Char(string="Cliente", readonly=True)
    orden_compra = fields.Char(string="Orden de Compra",readonly=True)
    fecha_factura = fields.Date(string="Fecha de Facturación",readonly=True)
    descripcion_id = fields.Many2many("dtm.compra.facturado.item",compute="_compute_descripcion_id", readonly=True)
    precio_total = fields.Float(string="Precio total",readonly=True)
    proveedor = fields.Selection(string='Proveedor',readonly=True,
        selection=[('dtm', 'DISEÑO Y TRANSFORMACIONES METALICAS S DE RL DE CV'), ('mtd', 'METAL TRANSFORMATION & DESIGN')])
    archivos_id = fields.Many2many("ir.attachment",string="Archivos", compute="_compute_delete")
    currency = fields.Selection(defaul="mx", selection=[('mx','MXN'),('us','USD')], readonly = True)
    factura = fields.Char(string="Factura",readonly=True)
    notas = fields.Text(string="notas", default="solo notas")
    res_id = fields.Integer()

    def _compute_delete(self):
        self.env.cr.execute("SELECT * FROM ir_attachment WHERE res_model= 'dtm.ordenes.compra' AND res_id=" + str(self.res_id))
        get_attc = list(line[0] for line in self.env.cr.fetchall())
        # get_attc = self.env['ir.attachment'].search([("res_id","=",self.res_id),("res_model","=","dtm.ordenes.compra")])
        print(get_attc, self.res_id)
        lines = []
        line = (5, 0, {})
        lines.append(line)
        for attc in get_attc:
            line = (4, attc, {})
            lines.append(line)
        self.archivos_id = lines

    def _compute_descripcion_id(self):
        for result in self:
            # print("descripcion_id",result.descripcion_id)
            get_cot = self.env['dtm.compra.facturado.item'].search([("no_factura", "=", result.factura)])
            # print("get_cot",get_cot)
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
    cantidad = fields.Char(string="Cantidad", options='{"type": "number"}')
    precio_unitario = fields.Float(string="Precio Unitario")
    precio_total = fields.Float(string="Precio Total", store=True)
    orden_trabajo = fields.Char(string="Orden de Trabajo")
    no_factura = fields.Char(string="No Factura")
    orden_compra = fields.Char(string="PO")


