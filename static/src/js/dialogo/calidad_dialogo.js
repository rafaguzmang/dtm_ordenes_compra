/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";

export class CalidadDialogo extends Component {
    static props = ['cerrar'];
    setup() {
        this.state = useState({
            calidad: [],
        });
        onWillStart(async () => {
            await this.cargaDatos();
        });
    }
    async cargaDatos() {
        const response = await fetch("dtm_contizacion_calidad");
        const data = await response.json();
        this.state.calidad = data;
    }
}
CalidadDialogo.template = "dtm_ordenes_compra.calidad_dialogo";