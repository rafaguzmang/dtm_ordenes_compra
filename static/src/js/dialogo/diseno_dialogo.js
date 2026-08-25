/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { PlanosDialogo } from "./planos_dialogo";

export class DisenoDialogo extends Component {
    static props = ["cerrar", "orden"]
    static components = { PlanosDialogo };
    setup() {
        this.state = useState({
            orden: this.props.orden,
            materiales: [],
            materiales_len: 0,
            revision: 0,
            cantidad: 0,
            color: '',
            resumen: '',
            firma_ventas: '',
            planos: [],
            abrirPlanos: false,
            aprobado: false,
        })
        this.rpc = useService("rpc");
        onWillStart(async () => {
            await this.getOrden();
            await this.getMateriales();
        });
    }

    aprovarFirma = async () => {
        console.log(this.props.orden)
        try {
            const data = await this.rpc('/diseno_firma', {
                'orden': this.props.orden,

            })
        } catch (error) {
            console.log(error)
        }
        await this.getOrden();
        await this.getMateriales();
    }

    abrirPlanos = () => {
        this.state.abrirPlanos = true;
    }

    cerrarPlanos = () => {
        this.state.abrirPlanos = false;
    }

    async getOrden() {
        const response = await fetch('/dtm_ot_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                orden: this.props.orden,
            })
        })

        const data = await response.json();
        this.state.revision = data.result.revision;
        this.state.cantidad = data.result.cantidad;
        this.state.color = data.result.color;
        this.state.resumen = data.result.resumen;
        this.state.firma_ventas = data.result.firma_ventas;
        this.state.aprobado = data.result.aprobado;
        let id = 0;
        this.state.planos = data.result.planos.map((item) => { return { 'index': id++, ...item } });
    }

    async getMateriales() {
        const response = await fetch('/dtm_diseno_materiales', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                orden: this.props.orden,
            }),
        })
        const data = await response.json();
        let id = 0;
        const data2 = data.result.map((item) => { return { 'index': id++, ...item } })
        this.state.materiales = data2;
        this.state.materiales_len = data2.length;
    }
}

DisenoDialogo.template = "dtm_ordenes_compra.diseno_dialogo";

