/**@odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";

export class EnDisenoDialogo extends Component {
    static props = ["cerrar"]
    setup() {
        this.state = useState({
            ordenes: [],
            clients: [],
            ordenes_filtro: [],
            productos: [],
            asc: "",
            showPDF: false,
            currentPDF: null,
            pdfTitle: "",
        });

        onWillStart(async () => {
            this.loadOrdenes();
        });
    }

    openPDF(po_file) {
        this.state.currentPDF = po_file;
        this.state.showPDF = true;
    }

    closePDF() {
        this.state.showPDF = false;
    }

    async loadOrdenes() {
        const response = await fetch("/dtm_diseno");
        const data = await response.json();
        data.sort((a, b) => {
            const parseDate = (str) => {
                if (!str || str === "--/--/--") return null;
                // Suponiendo formato "dd/mm/yyyy"
                const [d, m, y] = str.split("/");
                return new Date(`${y}-${m}-${d}`);
            };

            const dateA = parseDate(a.fecha_termino_diseno);
            const dateB = parseDate(b.fecha_termino_diseno);

            if (!dateA && !dateB) return 0;   // ambos sin fecha
            if (!dateA) return 1;             // A sin fecha → va después
            if (!dateB) return -1;            // B sin fecha → va después

            return dateA - dateB;             // comparación normal
        });
        this.state.ordenes = data;
        this.state.ordenes_filtro = data;
        const clientes = data.map(x => x.cliente);
        this.state.clients = [...new Set(clientes)];
        const productos = data.map(x => x.producto);
        this.state.productos = [...new Set(productos)];
    }

    // Filtros
    clienteFiltro(ev) {
        const cliente = ev.target.value;
        this.state.ordenes = cliente === "" ? this.state.ordenes_filtro : this.state.ordenes_filtro.filter(item => item.cliente === cliente);
        const productos = this.state.ordenes.map(x => x.producto);
        this.state.productos = [...new Set(productos)];
    }

    productoFiltro(ev) {
        const producto = ev.target.value;
        this.state.ordenes = producto === "" ? this.state.ordenes_filtro : this.state.ordenes_filtro.filter(item => item.producto === producto);
        const clientes = this.state.ordenes.map(x => x.cliente);
        this.state.clients = [...new Set(clientes)];
    }

    sortColumn(column) {
        if (this.state.asc !== column) {
            this.state.ordenes.sort((a, b) => {
                if (a[column] < b[column]) return -1;
                if (a[column] > b[column]) return 1;
                return 0;
            });
            this.state.asc = column;
        } else {
            this.state.ordenes.sort((a, b) => {
                if (a[column] > b[column]) return -1;
                if (a[column] < b[column]) return 1;
                return 0;
            });
            this.state.asc = "";
        }

    }

    searchODT(ev) {
        const search = ev.target.value;
        console.log(search);
        this.state.ordenes = search === "" ? this.state.ordenes_filtro : this.state.ordenes_filtro.filter(item => item.orden_diseno === parseInt(search));
        console.log("this.state.ordenes", this.state.ordenes);
    }
}
EnDisenoDialogo.template = "dtm_ordenes_compra.endiseno_dialogo";