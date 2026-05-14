/** @odoo-module **/
import { Component, useState, onMounted } from "@odoo/owl";

export class CorteDialogo extends Component {
    static props = ["cerrar", "orden", "version"]

    setup() {
        this.state = useState({
            orden: this.props.orden,
            version: this.props.version,
            cortes_primera: [],
            cortes_segunda: [],
            showPDF: false,
            pdf: null,
        })
        onMounted(async () => {
            await this.descargarCorte();
        })
    }

    async openPDF(pdf) {
        this.state.pdf = pdf;
        this.state.showPDF = true;
    }

    async closePDF() {
        this.state.pdf = null;
        this.state.showPDF = false;
    }

    async descargarCorte() {
        const response = await fetch("/seguimiento_corte_laser", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                orden: this.props.orden,
                version: this.props.version,
            }),
        });
        const data = await response.json();
        console.log("Cortadora", data.result);
        const primera_tabla = data.result.filter(row => row.primera_pieza === true);
        const segunda_tabla = data.result.filter(row => row.primera_pieza === false);
        let index = 0;
        this.state.cortes_primera = primera_tabla.map(row => ({ 'index': index++, ...row }));
        index = 0;
        this.state.cortes_segunda = segunda_tabla.map(row => ({ 'index': index++, ...row }));
    }
}

CorteDialogo.template = "dtm_ordenes_compra.corte_dialogo"