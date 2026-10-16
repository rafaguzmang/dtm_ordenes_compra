/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { OrdenesTrabajo } from "@dtm_ordenes_compra/js/dialogo/ordenes_dialogo";

export class CalidadDialogo extends Component {

    static components = { OrdenesTrabajo };
    static props = ['cerrar'];
    setup() {
        this.state = useState({
            calidad: [],
            datos: false,
            ot_number: 0,
            cotizacion: 0,
            po_costo: 0,
            cliente: "",
            fcotizaciones: 0,
            facturado: false,
            numero_factura: 0,
        });
        onWillStart(async () => {
            await this.cargaDatos();
        });
    }
    showData = async (ot_number) => {
        this.state.ot_number = ot_number;
        await this.fetchOrdenDatos();
        this.state.datos = true;
    }
    closeShowData = () => {
        this.state.datos = false;
        this.state.ot_number = 0;
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
    async cargaDatos() {
        const response = await fetch("dtm_contizacion_calidad");
        const data = await response.json();
        this.state.calidad = data;
    }
}
CalidadDialogo.template = "dtm_ordenes_compra.calidad_dialogo";