/** @odoo-module **/
import { Component, useState } from "@odoo/owl";

export class DisenoDialogo extends Component {
    static props = ["cerrar", "orden"]
    setup() {
        this.state = useState({
            orden: this.props.orden,
            materiales: [],
            materiales_len: 0,
        })
        this.getMateriales();
    }

    aprovar() {
        console.log('aprovar');
    }

    async getMateriales() {
        const response = await fetch('/dtm_diseno_materiales', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                orden: this.props.orden,
            }),
        })
        const data = await response.json();
        console.log(data);
        let id = 0;
        const data2 = data.result.map((item) => { return { 'index': id++, ...item } })
        this.state.materiales = data2;
        this.state.materiales_len = data2.length;
    }
}

DisenoDialogo.template = "dtm_ordenes_compra.diseno_dialogo";

