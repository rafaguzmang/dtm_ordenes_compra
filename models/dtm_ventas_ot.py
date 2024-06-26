from odoo import fields,models
from datetime import datetime

class OrdenTrabajo(models.Model):
    _name = "dtm.ventas.ot"
    _inherit = ['mail.thread']
    _description = "Orden de trabajo para el área de ventas"
    _order = "ot_number desc"

    status = fields.Char(readonly=True)
    ot_number = fields.Integer(string="NÚMERO",readonly=True)
    tipe_order = fields.Char(string="TIPO",readonly=True)
    name_client = fields.Char(string="CLIENTE",readonly=True)
    product_name = fields.Char(string="NOMBRE DEL PRODUCTO",readonly=True)
    date_in = fields.Date(string="FECHA DE ENTRADA", default= datetime.today(),readonly=True)
    po_number = fields.Char(string="PO",readonly=True)
    date_rel = fields.Date(string="FECHA DE ENTREGA", default= datetime.today(),readonly=True)
    version_ot = fields.Integer(string="VERSIÓN OT",default=1)
    color = fields.Char(string="COLOR",default="N/A",readonly=True)
    cuantity = fields.Integer(string="CANTIDAD",readonly=True)
    materials_ids = fields.Many2many("dtm.materials.line",string="Lista")
    firma = fields.Char(string="Firma Ventas", readonly = True)
    disenador = fields.Char(string="Diseñador",readonly=True)
    planos = fields.Boolean(string="Planos",default=False,readonly=True)
    nesteos = fields.Boolean(string="Nesteos",default=False,readonly=True)

    rechazo_id = fields.Many2many("dtm.odt.rechazo",readonly=True)

    anexos_id = fields.Many2many("dtm.proceso.anexos",readonly=True)
    cortadora_id = fields.Many2many("dtm.proceso.cortadora",readonly=True)
    primera_pieza_id = fields.Many2many("dtm.proceso.primer",readonly=True)
    tubos_id = fields.Many2many("dtm.proceso.tubos",readonly=True)

    notes = fields.Text(string="Notas")

    pausa = fields.Boolean()
    pausa_motivo = fields.Text()


    #---------------------Resumen de descripción------------

    description = fields.Text(string="DESCRIPCIÓN",readonly=True)

    def action_firma(self):
        self.firma = self.env.user.partner_id.name
        get_ot = self.env['dtm.odt'].search([("ot_number","=",self.ot_number)])
        get_ot.write({"firma_ventas": self.firma})
        get_procesos = self.env['dtm.proceso'].search([("ot_number","=",self.ot_number)])
        get_procesos.write({
            "firma_ventas": self.firma,
            "firma_ventas_kanba":"Ventas"
        })

    def action_detener(self):
        get_pro = self.env['dtm.proceso'].search([("ot_number","=",self.ot_number),("tipe_order","=",self.tipe_order)])
        get_pro.write({
            "pausado":"Pausado por Ventas",
            "status_pausado": get_pro.status,
            "pausa_motivo": self.pausa_motivo
        })
        self.pausa = True

    def action_continuar(self):
        get_pro = self.env['dtm.proceso'].search([("ot_number","=",self.ot_number),("tipe_order","=",self.tipe_order)])
        get_pro.write({
                "pausado":"",
                "status_pausado": ""
            })
        self.pausa = False

    def get_view(self, view_id=None, view_type='form', **options):
        res = super(OrdenTrabajo,self).get_view(view_id, view_type,**options)

        get_process = self.env['dtm.proceso'].search([])
        for proceso in get_process:
            vals = {
                "status": proceso.status,
                "ot_number": proceso.ot_number,
                "tipe_order": proceso.tipe_order,
                "name_client": proceso.name_client,
                "product_name": proceso.product_name,
                "date_in": proceso.date_in,
                "po_number": proceso.po_number,
                "date_rel": proceso.date_rel,
                "version_ot": proceso.version_ot,
                "color": proceso.color,
                "cuantity": proceso.cuantity,
                "materials_ids": proceso.materials_ids,
                "planos": proceso.planos,
                "nesteos": proceso.nesteos,
                "description":proceso.description,
                "rechazo_id":proceso.rechazo_id,
                "anexos_id":proceso.anexos_id,
                "cortadora_id":proceso.cortadora_id,
                "primera_pieza_id":proceso.primera_pieza_id,
                "tubos_id":proceso.tubos_id,
                # "firma_proceso": proceso.firma,
                # "firma_compras": proceso.firma_compras,
                # "firma_diseno": proceso.firma_diseno,
                # "firma_almacen": proceso.firma_almacen,
                # "firma_ventas": proceso.firma_ventas
            }

            get_self = self.env['dtm.ventas.ot'].search([("ot_number","=", proceso.ot_number)])
            if get_self:
                get_self.write(vals)
            else:
                get_self.create(vals)

        return res



