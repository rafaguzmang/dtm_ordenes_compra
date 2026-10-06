/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { DialogMaquinados } from "@dtm_procesos/js/seguimiento/pantallas_dialogo/dialog_maquinados";

export class EnMaquinadosDialogo extends Component {
    static components = { DialogMaquinados };
    static props = ['cerrar'];
    setup() {
        this.state = useState({
            maquinados: [],
            showMaquinadoDialogo: false,
            orden_trabajo: null,
            version: null,
        });

        onWillStart(async () => {
            await this.fetchMaquinados();
        });
    }

    openMaquinado = (orden_trabajo, version) => {
        this.state.showMaquinadoDialogo = true;
        this.state.orden_trabajo = orden_trabajo;
        this.state.version = version;
    }

    cerrarMaquinados_dialogo = () => {
        this.state.showMaquinadoDialogo = false;
    }


    async fetchMaquinados() {
        const result = await fetch('/dtm_ordenes_compra/en_maquinados');
        const maquinados = await result.json();
        this.state.maquinados = maquinados;
    }


}

EnMaquinadosDialogo.template = "dtm_ordenes_compra.enmaquinados_dialogo";