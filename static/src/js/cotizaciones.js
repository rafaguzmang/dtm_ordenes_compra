/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { OrdenesTrabajo } from './dialogo/ordenes_dialogo'
import { ActivosEntradas } from "./activosentradas"


export class Cotizaciones extends Component {
    static components = { OrdenesTrabajo, ActivosEntradas }
    setup() {
        this.state = useState({
            cotizaciones: [],
            ordenes_dialogo: false,
            cotizaciones_filtradas: [],
            clientes: [],
            cotizaciones_no_pagadas: 0,
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
            ordenes_atoradas: false,
            ordenes_atoradas_count: 0,
            por_aprobar: false,
            por_aprobar_count: 0,
            facturado: false,
            factura_pdf: "",
            numero_factura: "",
        });
        this.rpc = useService("rpc");
        this.ultimoFiltro = null;

        onWillStart(async () => {
            await this.fetchPrecioDollar();
            await this.fetchCotizaciones();
        });
    }

    // Material a liberar para compras
    materialALiberar() {
        if (this.state.material_a_liberar) {
            this.fetchCotizaciones();
        }
        this.state.material_a_liberar = !this.state.material_a_liberar;
        this.ultimoFiltro = this.state.material_a_liberar ? { tipo: 'material' } : null;
        this.state.cotizaciones = this.state.material_a_liberar
            ? this.state.cotizaciones_filtradas.filter(c => c.atencion_material)
            : this.state.cotizaciones_filtradas;
        this.state.ordenes_atoradas = false;
        this.state.por_aprobar = false;
    }

    // Filtrar por ordenes con firma de diseño pero sin firma de ventas
    porAprobar() {
        if (this.state.por_aprobar) {
            this.fetchCotizaciones();
        }
        this.state.por_aprobar = !this.state.por_aprobar;
        this.ultimoFiltro = this.state.por_aprobar ? { tipo: 'aprobar' } : null;
        this.state.cotizaciones = this.state.por_aprobar
            ? this.state.cotizaciones_filtradas.filter(c => c.por_aprobar)
            : this.state.cotizaciones_filtradas;
        this.state.material_a_liberar = false;
        this.state.ordenes_atoradas = false;
    }

    // Ordenes con mas de 24 horas sin cambio de estatus
    ordenesAtoradas() {
        if (this.state.ordenes_atoradas) {
            this.fetchCotizaciones();
        }
        this.state.ordenes_atoradas = !this.state.ordenes_atoradas;
        this.ultimoFiltro = this.state.ordenes_atoradas ? { tipo: 'atoradas' } : null;
        this.state.cotizaciones = this.state.ordenes_atoradas
            ? this.state.cotizaciones_filtradas.filter(c => c.atorada)
            : this.state.cotizaciones_filtradas;
        this.state.material_a_liberar = false;
        this.state.por_aprobar = false;
    }

    openPDF(pdf) {
        this.state.pdf = pdf;
        this.state.showPDF = true;
    }

    closePDF() {
        this.state.showPDF = false;
    }

    async fetchCotizaciones() {
        try {
            const response = await fetch('/dtm_cotizaciones');
            const data = await response.json();
            this.state.cotizaciones = data.sort((a, b) => b.facturado - a.facturado);
            this.state.cotizaciones_filtradas = data.sort((a, b) => b.facturado - a.facturado);
            this.state.clientes = [...new Set(data.map(cotizacion => cotizacion.cliente))];
            this.state.cotizaciones_totales = data.length;
            const ordenes_sin_terminar = data.filter(orden => orden.status !== 'Facturado');
            const precios = ordenes_sin_terminar.map(cotizacion => cotizacion.precio.includes(' dlls') ? parseFloat(cotizacion.precio.replace(' dlls', '')) * this.state.precio_dollar : parseFloat(cotizacion.precio.replace(' mx', '')));
            const ordenes_con_factura = data.filter(orden => orden.status == 'Facturado');
            const precios_con_factura = ordenes_con_factura.map(cotizacion => cotizacion.precio.includes(' dlls') ? parseFloat(cotizacion.precio.replace(' dlls', '')) * this.state.precio_dollar : parseFloat(cotizacion.precio.replace(' mx', '')));
            this.state.acumulado = Math.round(precios.reduce((acc, precio) => acc + precio) * 100) / 100;
            this.state.cotizaciones_no_pagadas = Math.round(precios_con_factura.reduce((acc, precio) => acc + precio) * 100) / 100;
            this.state.terminadas = data.filter(cotizacion => cotizacion.facturado).length;
            this.state.material_a_liberar_count = data.filter(cotizacion => cotizacion.atencion_material).length;
            this.state.ordenes_atoradas_count = data.filter(cotizacion => cotizacion.atorada).length;
            this.state.por_aprobar_count = data.filter(cotizacion => cotizacion.por_aprobar).length;
        } catch (error) {
            console.error("Error al obtener las cotizaciones:", error);
        }
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

    cerrarOrdenesTrabajo = async () => {
        this.state.ordenes_dialogo = false;
        await this.fetchPrecioDollar();
        await this.fetchCotizaciones();
        await this.aplicarUltimoFiltro();

    };

    //    Filtros

    async aplicarUltimoFiltro() {
        if (!this.ultimoFiltro) return;

        switch (this.ultimoFiltro.tipo) {
            case 'material':
                this.state.cotizaciones = this.state.cotizaciones_filtradas.filter(c => c.atencion_material);
                break;
            case 'aprobar':
                this.state.cotizaciones = this.state.cotizaciones_filtradas.filter(c => c.por_aprobar);
                break;
            case 'atoradas':
                this.state.cotizaciones = this.state.cotizaciones_filtradas.filter(c => c.atorada);
                break;
            case 'general': {
                const { proveedor, cliente, fentrega, status } = this.ultimoFiltro;
                this.filtroGeneral(proveedor, cliente, fentrega, status);
                break;
            }
            case 'po':
                this.state.cotizaciones = this.ultimoFiltro.valor === ''
                    ? this.state.cotizaciones_filtradas
                    : this.state.cotizaciones_filtradas.filter(r => r.po == this.ultimoFiltro.valor);
                break;
            case 'cotizacion':
                this.state.cotizaciones = this.ultimoFiltro.valor === ''
                    ? this.state.cotizaciones_filtradas
                    : this.state.cotizaciones_filtradas.filter(r => r.cotizacion == this.ultimoFiltro.valor);
                break;
            case 'fechaEntrada':
                this.state.cotizaciones = this.ultimoFiltro.valor === ''
                    ? this.state.cotizaciones_filtradas
                    : this.state.cotizaciones_filtradas.filter(r => r.fecha_entrada == this.ultimoFiltro.valor);
                break;
            case 'ot': {
                if (!this.ultimoFiltro.valor) {
                    this.state.cotizaciones = this.state.cotizaciones_filtradas;
                    break;
                }
                const data = await fetch("/ordenes_trabajo_filtro", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ ot: this.ultimoFiltro.valor }),
                });
                const response = await data.json();
                const orden_trabajo = response.result.cotizacion;
                this.state.cotizaciones = this.state.cotizaciones_filtradas.filter(record => record.cotizacion == orden_trabajo);
                break;
            }
            case 'otStatus': {
                const data = await fetch("/ordenes_status_filtro", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ status: this.ultimoFiltro.valor }),
                });
                const response = await data.json();
                const orden_trabajo = response.result.lista;
                const filtrado = this.state.cotizaciones_filtradas.filter(record => orden_trabajo.includes(record.cotizacion));
                this.state.cotizaciones = filtrado.length == 0 ? this.state.cotizaciones_filtradas : filtrado;
                break;
            }
        }
    }

    // Filtro para busqueda de orden por status en procesos
    async ordenTrabajoStatusFiltro(event) {
        this.ultimoFiltro = { tipo: 'otStatus', valor: texto };
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
        this.ultimoFiltro = { tipo: 'ot', valor: ot };
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
        this.ultimoFiltro = { tipo: 'po', valor: event.target.value };
        this.ultimoFiltro = { tipo: 'ot', valor: ot };
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
        this.ultimoFiltro = { tipo: 'fechaEntrada', valor: formattedDate };
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
        this.ultimoFiltro = { tipo: 'cotizacion', valor: event.target.value };
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
        this.ultimoFiltro = { tipo: 'general', proveedor, cliente, fentrega, status };
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
