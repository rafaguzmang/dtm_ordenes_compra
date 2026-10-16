/** @odoo-module */
import { Component, useState, onWillStart } from "@odoo/owl";
import { OrdenesTrabajo } from "@dtm_ordenes_compra/js/dialogo/ordenes_dialogo";


export class EnNesteoDialogo extends Component {
    static components = { OrdenesTrabajo };
    static props = ['cerrar'];
    setup() {
        this.state = useState({
            data: [],
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
            this.fetchData();
        });

    }
    openDialogoOrden(ot_number) {
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

    async fetchData() {
        const data = await fetch("/dtm_odt/get_nesteo_data");
        this.state.data = await data.json();
        this.state.data.sort((a, b) => {
            const parseDate = (str) => {
                // Suponiendo formato "dd/mm/yyyy"
                const [d, m, y] = str.split("/");
                return new Date(`${y}-${m}-${d}`);
            };

            const dateA = parseDate(a.fecha_llegada);
            const dateB = parseDate(b.fecha_llegada);

            if (!dateA && !dateB) return 0;   // ambos sin fecha
            if (!dateA) return 1;             // A sin fecha → va después
            if (!dateB) return -1;            // B sin fecha → va después

            return dateA - dateB;             // comparación normal
        });

    }
}

EnNesteoDialogo.template = 'dtm_ordenes_compra.EnNesteoDialogo';