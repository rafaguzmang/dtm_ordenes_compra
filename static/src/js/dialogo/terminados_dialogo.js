/**@odoo-module**/
import { Component, useState, onWillStart } from "@odoo/owl";

export class TerminadoDialogo extends Component {
    static props = ['cerrar'];
    setup() {
        this.state = useState({
            terminados: [],
        });

        onWillStart(async () => {
            await this.fetchTerminados();
        });
    }

    async fetchTerminados() {
        const request = await fetch('/cotizacion_terminados');
        const response = await request.json();
        this.state.terminados = response;
    }
}
TerminadoDialogo.template = 'dtm_ordenes_compra.terminados_dialogo';