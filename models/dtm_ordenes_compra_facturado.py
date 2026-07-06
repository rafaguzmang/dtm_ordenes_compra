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
    descripcion_id = fields.One2many("dtm.compra.facturado.item", "model_id", string="Items", readonly=True)
    precio_total = fields.Float(string="Precio total",readonly=True)
    proveedor = fields.Selection(string='Proveedor',readonly=True,
        selection=[('dtm', 'DISEÑO Y TRANSFORMACIONES METALICAS S DE RL DE CV'), ('mtd', 'METAL TRANSFORMATION & DESIGN')])
    archivos_id = fields.One2many("dtm.compras.facturado.archivos","model_id",string="Archivos", readonly=True)
    currency = fields.Selection(default="mx", selection=[('mx','MXN'),('us','USD')], readonly = True)
    factura = fields.Char(string="Factura/s",readonly=False)
    notas = fields.Text(string="notas", default="solo notas", readonly=True)
    res_id = fields.Integer()
    cantidad_pagada = fields.Float(string="Cantidad pagada", readonly=True)
    cantidad_pagada_date = fields.Date(string="Fecha de pago", readonly=True)
    # En dtm.ordenes.compra.facturado
    factura_pdf = fields.Many2many("ir.attachment", "dtm_orden_facturado_factura_pdf_rel", string="Factura")
    pago_pdf = fields.Many2many("ir.attachment", "dtm_orden_facturado_pago_pdf_rel", string="Recibo Electrónico de Pago")

    # def get_view(self, view_id=None, view_type='form', **options):
    #     res = super(Facturado, self).get_view(view_id, view_type, **options)

    #     # Migración: rellena model_id en items viejos que quedaron huérfanos del compute anterior
    #     facturados = self.env['dtm.ordenes.compra.facturado'].search([])
    #     for fact in facturados:
    #         items_viejos = self.env['dtm.compra.facturado.item'].search([
    #             ('no_factura', '=', fact.factura),
    #             ('model_id', '=', False),  # solo los que aún no tienen padre asignado
    #         ])
    #         if items_viejos:
    #             items_viejos.write({'model_id': fact.id})

    #     return res
    

class ItemFactura(models.Model):
    _name = "dtm.compra.facturado.item"
    _description = "Guarda los servicios de las cotizaciones ya facturadas"
    model_id = fields.Many2one("dtm.ordenes.compra.facturado", string="Orden Facturada")
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


