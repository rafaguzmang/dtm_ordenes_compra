/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { OrdenesTrabajo } from './dialogo/ordenes_dialogo'

export class Cotizaciones extends Component {
    static components = { OrdenesTrabajo }
    setup() {
        this.state = useState({
            cotizaciones: [],
            ordenes_dialogo: false,
            cotizaciones_filtradas: [],
            clientes: [],
            cotizacion: null,
            po_costo: 0,
            cotizaciones_totales: 0,
            precio_dollar: 0,
            acumulado: 0,
            terminadas: 0,
            pdf: '',
            showPDF: false,
        });
        this.rpc = useService("rpc");

        onWillStart(async () => {
            await this.fetchPrecioDollar();
            await this.fetchCotizaciones();
        });
    }

    openPDF(pdf) {
        this.state.pdf = pdf;
        this.state.showPDF = true;
    }

    closePDF() {
        this.state.showPDF = false;
    }

    async fetchCotizaciones() {
        const response = await fetch('/dtm_cotizaciones');
        const data = await response.json();
        this.state.cotizaciones = data.sort((a, b) => b.terminado - a.terminado);
        this.state.cotizaciones_filtradas = data.sort((a, b) => b.terminado - a.terminado);
        this.state.clientes = [...new Set(data.map(cotizacion => cotizacion.cliente))];
        this.state.cotizaciones_totales = data.length;
        const precios = data.map(cotizacion => cotizacion.precio.includes(' dlls') ? parseFloat(cotizacion.precio.replace(' dlls', '')) * this.state.precio_dollar : parseFloat(cotizacion.precio.replace(' mx', '')));
        this.state.acumulado = Math.round(precios.reduce((acc, precio) => acc + precio, 2));
        this.state.terminadas = data.filter(cotizacion => cotizacion.terminado).length;
    }

    async fetchPrecioDollar() {
        try {
            const data = await this.rpc("dtm_precio_dollar", {})
            this.state.precio_dollar = Math.round(data.bmx.series[0].datos[0].dato * 100) / 100;
        } catch (error) {
            console.error("Error de comunicación con el banco de México:", error);
        }
    }



    ordenesTrabajo(cotizacion, po_costo) {
        this.state.ordenes_dialogo = true;
        this.state.cotizacion = cotizacion;
        this.state.po_costo = po_costo;
    }

    cerrarOrdenesTrabajo = () => {
        this.state.ordenes_dialogo = false;
    };

    //    Filtros
    // Filtro de busqueda por status

    terminadoFiltro = (event) => {
        const option = event.target.value;
        switch (option) {
            case '0':
                this.state.cotizaciones = this.state.cotizaciones_filtradas;
                break;
            case '1':
                this.state.cotizaciones = this.state.cotizaciones_filtradas.filter(record => record.terminado);
                break;
            case '2':
                this.state.cotizaciones = this.state.cotizaciones_filtradas.filter(record => record.status.includes('Calidad'));
                break;
            case '3':
                this.state.cotizaciones = this.state.cotizaciones_filtradas.filter(record => record.status.includes('Proceso'));
                break;
            case '4':
                this.state.cotizaciones = this.state.cotizaciones_filtradas.filter(record => record.status.includes('OT'));
                break;
            case '5':
                this.state.cotizaciones = this.state.cotizaciones_filtradas.filter(record => record.status.includes('OD'));
                break;
            case '6':
                this.state.cotizaciones = this.state.cotizaciones_filtradas.filter(record => record.status.includes('N/A'));
                break;
        }
    }
    // Filtro de busqueda por po
    poFiltro = (event) => {
        const po = event.target.value;
        this.state.cotizaciones = this.state.cotizaciones_filtradas.filter(record => record.po == po);
        this.state.cotizaciones = event.target.value == '' ? this.state.cotizaciones_filtradas : this.state.cotizaciones;
    }
    // Filtro de busqueda por fecha de entrega
    fechaEntregaFiltro = (event) => {
        const fentrega = event.target.value;
        let [year, month, day] = fentrega.split('-');
        let formattedDate = '';
        if (year != '') {
            formattedDate = `${day}/${month}/${year}`;
        }
        const proveedor = event.target.closest('tr').querySelector('[name=proveedor_filtro]').value;
        const cliente = event.target.closest('tr').querySelector('[name=cliente_filtro]').value;
        this.filtroGeneral(proveedor.toUpperCase(), cliente, formattedDate)
    }
    // Filtro de busqueda por fecha de entrada
    fechaEntradaFiltro = (event) => {
        const fentrega = event.target.value;
        let [year, month, day] = fentrega.split('-');
        let formattedDate = '';
        if (year != '') {
            formattedDate = `${day}/${month}/${year}`;
        }
        this.state.cotizaciones = this.state.cotizaciones_filtradas.filter(record => record.fecha_entrada == formattedDate);
        this.state.cotizaciones = formattedDate == '' ? this.state.cotizaciones_filtradas : this.state.cotizaciones;
    }
    // Filtro de busqueda por proveedor
    proveedorFiltro = (event) => {
        const proveedor = event.target.value;
        const cliente = event.target.closest('tr').querySelector('[name=cliente_filtro]').value;
        const fentrega = event.target.closest('tr').querySelector('[name=fentrega_filtro]').value;
        let [year, month, day] = fentrega.split('-');
        let formattedDate = '';
        if (year != '') {
            formattedDate = `${day}/${month}/${year}`;
        }
        this.filtroGeneral(proveedor.toUpperCase(), cliente, formattedDate)
    }
    // Filtro de busqueda por cotización
    cotizacionFiltro = (event) => {
        const cotizacion = event.target.value;
        this.state.cotizaciones = this.state.cotizaciones_filtradas.filter(record => record.cotizacion == cotizacion);
        this.state.cotizaciones = event.target.value == '' ? this.state.cotizaciones_filtradas : this.state.cotizaciones;
    }
    // Filtro de busqueda por cliente
    clienteFiltro = (event) => {
        const cliente = event.target.value;
        const proveedor = event.target.closest('tr').querySelector('[name=proveedor_filtro]').value;
        const fentrega = event.target.closest('tr').querySelector('[name=fentrega_filtro]').value;
        let [year, month, day] = fentrega.split('-');
        let formattedDate = '';
        if (year != '') {
            formattedDate = `${day}/${month}/${year}`;
        }
        this.filtroGeneral(proveedor.toUpperCase(), cliente, formattedDate)
    }

    filtroGeneral(proveedor, cliente, fentrega) {
        let tabla = this.state.cotizaciones_filtradas;
        if (proveedor) {
            tabla = tabla.filter(cotizacion => {
                return cotizacion.proveedor.includes(proveedor.toUpperCase());
            });
        }
        if (cliente) {
            tabla = tabla.filter(cotizacion => {
                return cotizacion.cliente.includes(cliente);
            });
        }
        if (fentrega) {
            tabla = tabla.filter(cotizacion => {
                return cotizacion.fecha_salida.includes(fentrega);
            });
        }

        this.state.cotizaciones = tabla;
        if (!proveedor && !cliente && !fentrega) {
            this.state.cotizaciones = this.state.cotizaciones_filtradas;
        }


    }


}

Cotizaciones.template = "dtm_ordenes_compra.cotizaciones"
