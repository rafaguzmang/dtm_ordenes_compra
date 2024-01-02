from odoo import api,fields,models
import datetime


class OrdenesCompra(models.Model):
    _name = "dtm.ordenes.compra"
    _description = "Se muestran todos los archivos de las ordenes de compra"

    no_cotizacion = fields.Char(string="No Cotización")
    cliente = fields.Char(string="Cliente")
    orden_compra = fields.Char(string="Orden de Compra")
    fecha_entrada = fields.Date(string="Fecha Entrada",default= datetime.datetime.today())
    fecha_salida = fields.Date(string="Fecha Entrega",default= datetime.datetime.today())
    descripcion = fields.Text(string="Descripción")
    precio_total = fields.Float(string="Precio Unitario")
    direccion = fields.Text(string="Dirección")
    proveedor = fields.Selection(string='Proveedor',default='dtm',
        selection=[('dtm', 'DISEÑO Y TRANSFORMACIONES METALICAS S DE RL DE CV'), ('mtd', 'METAL TRANSFORMATION & DESIGN')])

    archivos = fields.Binary(string="Archivo")
    nombre_archivo = fields.Char(string="Nombre")



