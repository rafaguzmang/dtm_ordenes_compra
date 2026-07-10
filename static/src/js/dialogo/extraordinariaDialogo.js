/** @odoo-module **/
import { Component, useRef, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";


export class ExtraordinariaDialogo extends Component {
    static props = ["cerrar", "orden_id", "material", "codigo", "cantidad", "refresh"];

    setup() {
        this.state = {};
        this.formRef = useRef("formRef");
        this.notification = useState(useService("notification"));
    }

    mandarComprar = async (event) => {
        const proveedor = this.formRef.el.querySelector('[name="proveedor"]').value;
        const precio = this.formRef.el.querySelector('[name="precio"]').value;
        const orden_compra = this.formRef.el.querySelector('[name="orden_compra"]').value;

        if (!precio) {
            this.notification.add("Falta el precio", { type: "danger" });
            return;
        }

        const result = await fetch("/comprar_extraordinaria", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                orden_id: this.props.orden_id,
                material: this.props.material,
                codigo: this.props.codigo,
                proveedor: proveedor,
                precio: precio,
                orden_compra: orden_compra,
                cantidad: this.props.cantidad,
            }),
        });

        this.props.refresh();
        this.props.cerrar();
    }
}

ExtraordinariaDialogo.template = "dtm_ordenes_compra.extraordinariaDialogo";