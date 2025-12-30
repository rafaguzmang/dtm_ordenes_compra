/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { OrdenesTrabajo } from './dialogo/ordenes_dialogo'

export class Cotizaciones extends Component{
    static components = {OrdenesTrabajo}
    setup(){
        this.state = useState({
            cotizaciones: [],
            ordenes_dialogo:false,
            cotizaciones_filtradas:[],
            clientes:[],
            cotizacion:null,
            po_costo:0,
        });

        onWillStart(async () => {
            await this.fetchCotizaciones();
        });
    }



    async fetchCotizaciones(){
        const response = await fetch('/dtm_cotizaciones');
        const data = await response.json();
        this.state.cotizaciones = data;
        this.state.cotizaciones_filtradas = data;
        this.state.clientes = [...new Set(data.map(cotizacion => cotizacion.cliente))];
    }

    ordenesTrabajo(cotizacion,po_costo){
        this.state.ordenes_dialogo = true;        
        this.state.cotizacion=cotizacion;
        this.state.po_costo=po_costo;
    }

    cerrarOrdenesTrabajo = () => {
            this.state.ordenes_dialogo = false;
    };

//    Filtros
  // Filtro de busqueda por po
    poFiltro = (event) => {
        const po = event.target.value;    
        this.state.cotizaciones = this.state.cotizaciones_filtradas.filter(record => record.po == po);
        this.state.cotizaciones = event.target.value == '' ? this.state.cotizaciones_filtradas:this.state.cotizaciones;
    }
  // Filtro de busqueda por fecha de entrega
    fechaEntregaFiltro = (event) => {
        const fentrega = event.target.value;    
        let [year, month, day] = fentrega.split('-');
        let formattedDate = '';
        if(year != ''){
            formattedDate = `${day}/${month}/${year}`;            
        }
        const proveedor = event.target.closest('tr').querySelector('[name=proveedor_filtro]').value;
        const cliente = event.target.closest('tr').querySelector('[name=cliente_filtro]').value;
        this.filtroGeneral(proveedor.toUpperCase(),cliente,formattedDate)
    }
  // Filtro de busqueda por fecha de entrada
    fechaEntradaFiltro = (event) => {
        const fentrega = event.target.value;    
        let [year, month, day] = fentrega.split('-');
        let formattedDate = '';
        if(year != ''){
            formattedDate = `${day}/${month}/${year}`;            
        }
        this.state.cotizaciones = this.state.cotizaciones_filtradas.filter(record => record.fecha_entrada == formattedDate);
        this.state.cotizaciones = formattedDate == '' ? this.state.cotizaciones_filtradas:this.state.cotizaciones;
    }
  // Filtro de busqueda por proveedor
    proveedorFiltro = (event) => {
        const proveedor = event.target.value;    
        const cliente = event.target.closest('tr').querySelector('[name=cliente_filtro]').value;
        const fentrega = event.target.closest('tr').querySelector('[name=fentrega_filtro]').value;
        let [year, month, day] = fentrega.split('-');
        let formattedDate = '';
        if(year != ''){
            formattedDate = `${day}/${month}/${year}`;            
        }        
        this.filtroGeneral(proveedor.toUpperCase(),cliente,formattedDate)
    }
  // Filtro de busqueda por cotización
    cotizacionFiltro = (event) => {
        const cotizacion = event.target.value;    
        this.state.cotizaciones = this.state.cotizaciones_filtradas.filter(record => record.cotizacion == cotizacion);
        this.state.cotizaciones = event.target.value == '' ? this.state.cotizaciones_filtradas:this.state.cotizaciones;
    }
  // Filtro de busqueda por cliente
    clienteFiltro = (event) => {
        const cliente = event.target.value;
        const proveedor = event.target.closest('tr').querySelector('[name=proveedor_filtro]').value;
        const fentrega = event.target.closest('tr').querySelector('[name=fentrega_filtro]').value;
        let [year, month, day] = fentrega.split('-');
        let formattedDate = '';
        if(year != ''){
            formattedDate = `${day}/${month}/${year}`;            
        }
        this.filtroGeneral(proveedor.toUpperCase(),cliente,formattedDate)
    }

    filtroGeneral(proveedor,cliente,fentrega){
        let tabla = this.state.cotizaciones_filtradas;
        if(proveedor){
            tabla = tabla.filter(cotizacion => {
                return cotizacion.proveedor.includes(proveedor.toUpperCase());
            });
        }
        if(cliente){
            tabla = tabla.filter(cotizacion => {
                return cotizacion.cliente.includes(cliente);
            });
        }
        if(fentrega){
            tabla = tabla.filter(cotizacion => {
                return cotizacion.fecha_salida.includes(fentrega);
            });
        }

        this.state.cotizaciones = tabla;
        // console.log(!proveedor,!cliente,!fentrega);
        if(!proveedor && !cliente && !fentrega){
            this.state.cotizaciones = this.state.cotizaciones_filtradas;
        }
      
        
    }


}

Cotizaciones.template = "dtm_ordenes_compra.cotizaciones"
