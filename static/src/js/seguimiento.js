/** @odoo-module **/
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { Cotizaciones } from "./cotizaciones"


export class Seguimiento extends Component{
    static components = {Cotizaciones};

}
Seguimiento.template = "dtm_ordenes_compra.seguimiento"

registry.category("actions").add("dtm_ordenes_compra.seguimiento",Seguimiento)
