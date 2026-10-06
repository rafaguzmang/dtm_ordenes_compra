/** @odoo-module */
import { Component, useState, onWillStart } from "@odoo/owl";

export class EnNesteoDialogo extends Component {
    static props = ['cerrar'];
    setup() {
        this.state = useState({
            data: [],

        });

        onWillStart(async () => {
            this.fetchData();
        });

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