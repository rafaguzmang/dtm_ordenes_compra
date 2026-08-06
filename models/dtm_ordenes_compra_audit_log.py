from odoo import api, fields, models


class OrdenesCompraAuditLog(models.Model):
    _name = "dtm.ordenes.compra.audit.log"
    _description = "Bitácora de alta/borrado de órdenes de compra (independiente del registro auditado)"
    _order = "id desc"

    accion = fields.Selection(
        [('alta', 'Alta'), ('borrado', 'Borrado')],
        required=True,
    )
    fecha_evento = fields.Datetime(default=fields.Datetime.now, required=True)
    usuario_id = fields.Many2one('res.users', default=lambda self: self.env.user, required=True)
    orden_id_original = fields.Integer(string="ID original")
    no_cotizacion = fields.Char()
    orden_compra = fields.Char()
    origen = fields.Char(string="Método que disparó la acción")