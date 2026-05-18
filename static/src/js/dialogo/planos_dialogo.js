/** @odoo-module **/
import { Component, useState } from "@odoo/owl";

export class PlanosDialogo extends Component {
    static props = ["cerrar", "planos"]
    setup() {
        this.state = useState({
            pdf: null,
            showPDF: false,
        });
    }

    openPDF = (pdfData) => {
        this.state.pdf = pdfData;
        this.state.showPDF = true;
    }

    closePDF = () => {
        this.state.pdf = null;
        this.state.showPDF = false;
    }

}

PlanosDialogo.template = "dtm_ordenes_compra.planos_dialogo";