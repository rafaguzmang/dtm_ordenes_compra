/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { PorAprobarDialogo } from "./poraprobar_dialogo";
import { ExtraordinariaDialogo } from "./extraordinariaDialogo";

export class MaterialesDialogo extends Component {
    static props = ["cerrar", "orden"]
    static components = { PorAprobarDialogo, ExtraordinariaDialogo };
    setup() {
        this.state = useState({
            materiales: [],
            materialesFiltrados: [],
            filtroSize: 0,
            cliente: "",
            proyecto: "",
            total: 0,
            todos: 0,
            revision: 0,
            almacen: 0,
            cotizacion: 0,
            comprado: 0,
            recibido: 0,
            pendiente: 0,
            showTabla: 'todos',
            activeTab: 'todos',
            showPorAprobarModal: false,
            showExtraordinaria: false,
            // Modal
            id_pa: 0,
            name_pa: "",
            orden: 0,
        });

        onWillStart(async () => {
            await this.getMateriales();
        });
    }

    compraExtraordinaria = (id) => {
        console.log('compraExtraordinaria', id);
        this.state.showExtraordinaria = true;
    }

    cerrarExtraordinaria = () => {
        this.state.showExtraordinaria = false;
    }

    borrarHijo(respuesta) {
        if (respuesta) {
            const indice = this.state.materialesFiltrados.findIndex(item => item.id === this.state.id_pa);
            this.state.materialesFiltrados.splice(indice, 1);
            this.setTab("cotizacion");
        }
        this.cerrarPorAprobar();
    }

    cerrarPorAprobar = () => {
        this.state.showPorAprobarModal = false;
    }

    openPorAprobar = (id, name) => {
        this.state.showPorAprobarModal = true;
        this.state.id_pa = id;
        this.state.name_pa = name;
    }

    async confirmarMaterial(id, material) {
        try {
            const response = await fetch("/dtm_autorizar_material", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    orden: this.props.orden,
                    id: id,
                    material: material,
                })
            })
            const indice = this.state.materialesFiltrados.findIndex(item => item.id === id);
            this.state.materialesFiltrados.splice(indice, 1);
            this.setTab("cotizacion");
        } catch (error) {
            console.log('Falló el fetch:', error);
        }

    }

    async rechazarMaterial(id) {
        console.log('rechazarMaterial', id, orden);
    }

    setTab(tab) {
        console.log('tab', tab);
        if (tab == 'todos') {
            this.state.materiales = this.state.materialesFiltrados;
            this.state.filtroSize = this.state.materiales.length;
            this.state.showTabla = 'todos';
            this.state.activeTab = 'todos';
            this.getMateriales();
        }
        if (tab == 'recibido') {
            this.state.materiales = this.state.materialesFiltrados.filter(material => material.status === 'recibido');
            this.state.filtroSize = this.state.materiales.length;
            this.state.showTabla = 'excepto_cotizacion';
            this.state.activeTab = 'recibido';
        }
        if (tab == 'comprado') {
            this.state.materiales = this.state.materialesFiltrados.filter(material => material.status === 'comprado');
            this.state.filtroSize = this.state.materiales.length;
            this.state.showTabla = 'excepto_cotizacion';
            this.state.activeTab = 'comprado';

        }
        if (tab == 'cotizacion') {
            this.state.materiales = this.state.materialesFiltrados.filter(material => material.status === 'cotizacion');
            this.state.filtroSize = this.state.materiales.length;
            this.state.cotizacion = this.state.materiales.length;
            this.state.showTabla = 'cotizacion';
            this.state.activeTab = 'cotizacion';
            console.log('Cotización', this.state.cotizacion);

        }
        if (tab == 'almacen') {
            this.state.materiales = this.state.materialesFiltrados.filter(material => material.status === 'almacen');
            this.state.filtroSize = this.state.materiales.length;
            this.state.showTabla = 'excepto_cotizacion';
            this.state.activeTab = 'almacen';
        }
        if (tab == 'revision') {
            this.state.materiales = this.state.materialesFiltrados.filter(material => material.status === 'revision');
            this.state.filtroSize = this.state.materiales.length;
            this.state.showTabla = 'excepto_cotizacion';
            this.state.activeTab = 'revision';
        }
        if (tab == 'pendiente') {
            this.state.materiales = this.state.materialesFiltrados.filter(material => material.status === 'pendiente');
            this.state.filtroSize = this.state.materiales.length;
            this.state.showTabla = 'excepto_cotizacion';
            this.state.activeTab = 'pendiente';
        }
    }

    async getMateriales() {
        const response = await fetch("/dtm_ventas_materiales", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                orden: this.props.orden,
            })
        });
        const result = await response.json();
        this.state.materiales = result.result;
        this.state.materialesFiltrados = result.result;
        const nombre = this.state.materiales[0].nombre;
        this.state.cliente = nombre.substring(0, nombre.indexOf('-') - 2);
        this.state.proyecto = nombre.substring(nombre.indexOf('-') + 1);
        this.state.total = this.state.materiales.reduce((acc, material) => acc + material.total, 0);
        this.state.todos = this.state.materiales.length;
        this.state.filtroSize = this.state.materiales.length;
        this.state.recibido = this.state.materiales.filter(material => material.status === 'recibido').length;
        this.state.comprado = this.state.materiales.filter(material => material.status === 'comprado').length;
        this.state.cotizacion = this.state.materiales.filter(material => material.status === 'cotizacion').length;
        this.state.almacen = this.state.materiales.filter(material => material.status === 'almacen').length;
        this.state.revision = this.state.materiales.filter(material => material.status === 'revision').length;
        this.state.pendiente = this.state.materiales.filter(material => material.status === 'pendiente').length;
        this.state.orden = this.props.orden;
    }
}

MaterialesDialogo.template = "dtm_ordenes_compra.materiales_dialogo";
