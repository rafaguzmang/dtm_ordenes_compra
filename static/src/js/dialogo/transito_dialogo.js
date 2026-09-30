/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";


export class TransitoDialogo extends Component {
    static props = ["cerrar"]
    setup() {
        this.state = useState({
            tabla: [],
        })

        onWillStart(async () => {
            this.fetchTransito();
        })
    }

    async fetchTransito() {
        try {
            const response = await fetch('/dtm_ordenes_compra_transito');
            const data = await response.json();
            this.state.tabla = data;
            console.log(this.state.tabla);

        } catch (error) {
            console.error("Error al obtener las cotizaciones:", error);
        }
    }


}

TransitoDialogo.template = "dtm_ordenes_compra.transito_dialogo";