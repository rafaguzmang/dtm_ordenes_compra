
/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl"
import { useService } from "@web/core/utils/hooks";
import { MaterialesDialogo } from "./materiales_dialogo";
import { CorteDialogo } from "./corte_dialogo";
import { DisenoDialogo } from "./diseno_dialogo";

export class OrdenesTrabajo extends Component {
    static props = ["cerrar", "cotizacion", "po_costo", "cliente", "fcotizaciones"]
    static components = { MaterialesDialogo, CorteDialogo, DisenoDialogo };

    setup() {
        this.state = useState({
            ordenes: [],
            costo_diseno: 0.0,
            costo_ingenieria: 0.0,
            costo_compras: 0.0,
            precio_dollar: 0.0,
            precio_mxn: 0.0,
            showMaterialesModal: false,
            orden: 0,
            showCorteModal: false,
            version: 0,
            showDisenoModal: false,
            cliente: "",
        })
        this.rpc = useService("rpc")

        onWillStart(async () => {
            await this.ordenesTrabajo();
            await this.precioDollar();
        });

    }

    abrirDiseno = (orden) => {
        console.log(orden);
        this.state.showDisenoModal = true;
        this.state.orden = orden;
    }

    cerrarDiseno = () => {
        this.state.showDisenoModal = false;
    }

    abrirCorte = (orden, version) => {
        console.log(orden);
        this.state.showCorteModal = true;
        this.state.orden = orden;
        this.state.version = version;
    }

    cerrarCorte = () => {
        this.state.showCorteModal = false;
    }

    abrirMateriales = (orden) => {
        console.log(orden);
        this.state.showMaterialesModal = true;
        this.state.orden = orden;
    }

    cerrarMateriales = () => {
        this.state.showMaterialesModal = false;
    }

    async precioDollar() {
        try {
            const data = await this.rpc("dtm_precio_dollar", {})
            this.state.precio_dollar = Math.round(data.bmx.series[0].datos[0].dato * 100) / 100;
            this.state.precio_mxn = this.props.po_costo.includes("dlls") ? Math.round(parseFloat(this.props.po_costo.split("dlls")[0].trim()) * this.state.precio_dollar * 100) / 100 : parseFloat(this.props.po_costo);
        } catch (error) {
            console.error("Error de comunicación con el banco de México:", error);
        }
    }

    async ordenesTrabajo() {
        const response = await fetch("/dtm_ordenes_cotizacion", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(
                {
                    'cotizacion': this.props.cotizacion,
                }),
        });
        const data = await response.json();
        this.state.ordenes = data.result;
        console.log(data.result);
        console.log(this.state.ordenes);
        this.state.costo_diseno = data.result.map(costo => costo.costo_diseno).reduce((a, b) => a + b, 0);
        this.state.costo_ingenieria = data.result.map(costo => costo.costo_ingenieria).reduce((a, b) => a + b, 0);
        this.state.costo_compras = data.result.map(costo => costo.compras).reduce((a, b) => a + b, 0);
    }
}

OrdenesTrabajo.template = "dtm_ordenes_compra.ordenes_dialogo"
