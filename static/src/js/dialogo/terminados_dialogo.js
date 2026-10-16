/**@odoo-module**/
import { Component, useState, onWillStart } from "@odoo/owl";
import { OrdenesTrabajo } from "@dtm_ordenes_compra/js/dialogo/ordenes_dialogo";


export class TerminadoDialogo extends Component {
    static components = { OrdenesTrabajo };
    static props = ['cerrar'];
    setup() {
        this.state = useState({
            terminados: [],
            showOrden: false,
            ot_number: 0,
            cotizacion: 0,
            po_costo: 0,
            cliente: "",
            fcotizaciones: 0,
            facturado: false,
            numero_factura: 0,
        });

        onWillStart(async () => {
            await this.fetchTerminados();
        });
    }

    openDialogoOrden = (ot_number) => {
        this.state.showOrden = true;
        this.state.ot_number = ot_number;
        this.fetchOrdenDatos();
    }
    closeDialogoOrden = () => {
        this.state.showOrden = false;
    }

    fetchOrdenDatos = async () => {
        try {
            const response = await fetch("/calidad_dtm_orden_datos", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    'ot_number': this.state.ot_number,
                }),
            });
            const data = await response.json();
            this.state.cotizacion = data.result.cotizacion;
            this.state.po_costo = data.result.po_costo;
        } catch (error) {
            console.error("Error de comunicación con el banco de México:", error);
        }
    }

    async fetchTerminados() {
        const request = await fetch('/cotizacion_terminados');
        const response = await request.json();
        this.state.terminados = response;
    }
}
TerminadoDialogo.template = 'dtm_ordenes_compra.terminados_dialogo';