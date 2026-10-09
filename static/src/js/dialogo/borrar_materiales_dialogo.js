/** @odoo-module **/
import { Component, useState } from "@odoo/owl";

export class BorrarMaterialesDialogo extends Component {
    static props = ["cerrar", "id", "name", "cantidad", "orden"];
    setup() {
        this.state = useState({
            proveedor: "",
            precio: "",
            orden_compra: "",
        });
    }
    async borrarCompra() {
        try {
            const response = await fetch("/dtm_borrar_compra", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    orden: this.props.orden,
                    id: this.props.id,
                    name: this.props.name,
                    cantidad: this.props.cantidad,
                })
            });
            const result = await response.json();
            this.props.cerrar();
        } catch (error) {
            console.error('Falló el fetch:', error);
        }

    }
}

BorrarMaterialesDialogo.template = 'dtm_ordenes_compra.borrar_materiales_dialogo'