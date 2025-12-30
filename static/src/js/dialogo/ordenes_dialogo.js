
/** @odoo-module **/
import { Component, useState,onWillStart} from "@odoo/owl"

export class OrdenesTrabajo extends Component{
   static props = ["cerrar", "cotizacion", "po_costo"]

    setup(){
        this.state = useState({
            ordenes: [],
        })

        onWillStart(async () => {
            await this.ordenesTrabajo();
        });

    }

    async ordenesTrabajo(){
        console.log(this.props.cotizacion);
        const response = await fetch("/dtm_ordenes_cotizacion",{
            method:"POST",
            headers:{
                "Content-Type":"application/json",
            },
            body: JSON.stringify(
                {
                'cotizacion':this.props.cotizacion,
                }),
        });
        const data = await response.json();
        this.state.ordenes = data.result;
        console.log(this.state.ordenes);
    }
}

OrdenesTrabajo.template = "dtm_ordenes_compra.ordenes_dialogo"
