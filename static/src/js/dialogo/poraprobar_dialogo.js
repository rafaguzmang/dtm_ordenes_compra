/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";

export class PorAprobarDialogo extends Component {
    static props = ["cerrar", "id", "name", "thisorden", "padre"];

    setup() {
        this.state = useState({
            id: this.props.id,
            name: this.props.name,
            materiales: [],
            proveedor: "",
            unitario: 0,
            cantidad: 0,
            costo_total: 0,
        });

        onWillStart(async () => {
            await this.getAllMateriales();
        });
    }

    // async confirmar() {
    //     for (const item of this.state.materiales) {
    //         fetch("/dtm_autorizar_material", {
    //             method: 'POST',
    //             headers: {
    //                 'Content-Type': 'application/json',
    //             },
    //             body: JSON.stringify({
    //                 id: this.props.id,
    //                 orden: item.orden
    //             })

    //         })
    //     }
    //     await this.getAllMateriales();
    // }

    confirmar() {
        const thisorden = this.state.materiales.find(item => item.orden === this.props.thisorden.toString());
        this.props.padre(thisorden ? true : false);
    }



    quitarMaterial(num) {
        const index = this.state.materiales.findIndex((material) => material.num === num);
        this.state.materiales.splice(index, 1);
    }

    async getAllMateriales() {
        const response = await fetch('/dtm_get_all_materiales', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                id: this.state.id,
                name: this.state.name,
            }),
        });
        const data = await response.json();
        let num = 1;
        this.state.materiales = data.result.map((material) => {
            return {
                num: num++,
                ...material,
            };
        });
        this.state.proveedor = this.state.materiales[0].proveedor;
        this.state.unitario = this.state.materiales[0].unitario;
        this.state.cantidad = this.state.materiales.reduce((acc, material) => acc + material.cantidad, 0);
        this.state.costo_total = this.state.unitario * this.state.cantidad;


    }
}

PorAprobarDialogo.template = "dtm_ordenes_compra.poraprobar_dialogo";
