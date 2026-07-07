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
            material_a_liberar: false,
            material_a_liberar_count: 0,
            facturado: false,
            factura_pdf: "",
            numero_factura: "",
        });
        this.rpc = useService("rpc");

        onWillStart(async () => {
            await this.fetchPrecioDollar();
            await this.fetchCotizaciones();
        });
    }

    materialALiberar() {
        if (this.state.material_a_liberar) {
            this.fetchCotizaciones();
        }
        this.state.material_a_liberar = !this.state.material_a_liberar;
        this.state.cotizaciones = this.state.material_a_liberar ? this.state.cotizaciones_filtradas.filter(cotizacion => cotizacion.atencion_material) : this.state.cotizaciones_filtradas;
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
        this.state.cotizaciones = data.sort((a, b) => b.facturado - a.facturado);
        this.state.cotizaciones_filtradas = data.sort((a, b) => b.facturado - a.facturado);
        this.state.clientes = [...new Set(data.map(cotizacion => cotizacion.cliente))];
        this.state.cotizaciones_totales = data.length;
        const precios = data.map(cotizacion => cotizacion.precio.includes(' dlls') ? parseFloat(cotizacion.precio.replace(' dlls', '')) * this.state.precio_dollar : parseFloat(cotizacion.precio.replace(' mx', '')));
        this.state.acumulado = Math.round(precios.reduce((acc, precio) => acc + precio) * 100) / 100;
        this.state.terminadas = data.filter(cotizacion => cotizacion.facturado).length;
        this.state.material_a_liberar_count = data.filter(cotizacion => cotizacion.atencion_material).length;
    }

    async fetchPrecioDollar() {
        try {
            const data = await this.rpc("dtm_precio_dollar", {})
            console.log(data)
            console.log(data.bmx.series[0].datos[0].dato)
            this.state.precio_dollar = Math.round(data.bmx.series[0].datos[0].dato * 100) / 100;
        } catch (error) {
            console.error("Error de comunicación con el banco de México:", error);
        }
    }

    ordenesTrabajo(cotizacion, po_costo, cliente, facturado, numero_factura) {
        this.state.ordenes_dialogo = true;
        this.state.cotizacion = cotizacion;
        this.state.po_costo = po_costo;
        this.state.cliente = cliente;
        this.state.facturado = facturado;
        this.state.numero_factura = numero_factura;
    }

    cerrarOrdenesTrabajo = () => {
        this.state.ordenes_dialogo = false;
    };

    //    Filtros
    // Filtro para busqueda de orden por status en procesos
    async ordenTrabajoStatusFiltro(event) {
        const select = event.target;
        const texto = select.options[select.selectedIndex].text;

        const data = await fetch("/ordenes_status_filtro",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    status: texto,
                }),
            }
        )
        const response = await data.json();
        const orden_trabajo = response.result.lista;
        const filtrado = this.state.cotizaciones_filtradas.filter(record => orden_trabajo.includes(record.cotizacion));
        this.state.cotizaciones = filtrado.length == 0 ? this.state.cotizaciones_filtradas : filtrado;

    }

    // Filtro por orden de trabajo
    async ordenTrabajoFiltro(event) {
        const ot = event.target.value;
        if (ot) {
            const data = await fetch("/ordenes_trabajo_filtro",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        ot: ot,
                    }),
                }
            )
            const response = await data.json();
            const orden_trabajo = response.result.cotizacion;
            this.state.cotizaciones = this.state.cotizaciones_filtradas.filter(record => record.cotizacion == orden_trabajo);
        }
        else {
            this.state.cotizaciones = this.state.cotizaciones_filtradas;
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
        const status = event.target.closest('tr').querySelector('[name=terminado_filtro]').value;
        let [year, month, day] = fentrega.split('-');
        let formattedDate = '';
        if (year != '') {
            formattedDate = `${day}/${month}/${year}`;
        }
        this.filtroGeneral(proveedor.toUpperCase(), cliente, formattedDate, status)
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
        const status = event.target.closest('tr').querySelector('[name=terminado_filtro]').value;
        let [year, month, day] = fentrega.split('-');
        let formattedDate = '';
        if (year != '') {
            formattedDate = `${day}/${month}/${year}`;
        }
        this.filtroGeneral(proveedor.toUpperCase(), cliente, formattedDate, status)
    }

    // Filtro de busqueda por status
    terminadoFiltro = (event) => {
        const status = event.target.value;
        const proveedor = event.target.closest('tr').querySelector('[name=proveedor_filtro]').value;
        const cliente = event.target.closest('tr').querySelector('[name=cliente_filtro]').value;
        const fentrega = event.target.closest('tr').querySelector('[name=fentrega_filtro]').value;
        let [year, month, day] = fentrega.split('-');
        let formattedDate = '';
        if (year != '') {
            formattedDate = `${day}/${month}/${year}`;
        }
        this.filtroGeneral(proveedor.toUpperCase(), cliente, formattedDate, status)
    }

    filtroGeneral(proveedor, cliente, fentrega, status) {
        let tabla = this.state.cotizaciones_filtradas;
        console.log(tabla)
        if (proveedor) {
            tabla = tabla.filter(cotizacion => {
                return (cotizacion.proveedor || '').includes(proveedor.toUpperCase());
            });
        }
        if (cliente) {
            tabla = tabla.filter(cotizacion => {
                return (cotizacion.cliente || '').includes(cliente);
            });
        }
        if (fentrega) {
            tabla = tabla.filter(cotizacion => {
                return (cotizacion.fecha_salida || '').includes(fentrega);
            });
        }
        if (status) {
            switch (status) {
                case '0':
                    tabla = tabla;
                    break;
                case '1':
                    tabla = tabla.filter(record => (record.status || '').includes('Terminado'));
                    break;
                case '2':
                    tabla = tabla.filter(record => (record.status || '').includes('Calidad'));
                    break;
                case '3':
                    tabla = tabla.filter(record => (record.status || '').includes('Proceso'));
                    break;
                case '4':
                    tabla = tabla.filter(record => (record.status || '').includes('OT'));
                    break;
                case '5':
                    tabla = tabla.filter(record => (record.status || '').includes('OD'));
                    break;
                case '6':
                    tabla = tabla.filter(record => (record.status || '').includes('N/A'));
                    break;
            }
        }

        this.state.cotizaciones = tabla;
        if (!proveedor && !cliente && !fentrega && !status) {
            this.state.cotizaciones = this.state.cotizaciones_filtradas;
        }
    }




}

Cotizaciones.template = "dtm_ordenes_compra.cotizaciones"
