/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { ActivosDialogo } from "./dialogo/activos_dialogo";

const ORDEN_MESES = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN",
    "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"];

export class ActivosEntradas extends Component {
    static components = { ActivosDialogo };
    setup() {
        this.state = useState({
            entradas: {}, // objeto, no arreglo, para que coincida con el JSON del endpoint
            totalDebioEntrar: 0,
            totalFacturada: 0,
            totalPagadas: 0,
            porcentaje: 0,
            abrirActivosDialogo: false,
            cerrarActivosDialogo: false,
        });
        onWillStart(async () => {
            await this.getDatos();
        });
    }

    abrirEntradasActivos() {
        this.state.abrirActivosDialogo = true;
    }
    cerrarActivosDialogo() {
        this.state.cerrarActivosDialogo = false;
    }

    async getDatos() {
        try {
            const response = await fetch('/dtm_activos_main');
            const data = await response.json();
            this.state.entradas = data;
            this.state.totalDebioEntrar = Math.round(Object.values(data).reduce((total, registros) => {
                return total + registros.reduce((sumaMes, registro) => sumaMes + registro.precio_total, 0);
            }, 0) * 100) / 100;

            this.state.totalFacturada = Math.round(Object.values(data).reduce((total, registros) => {
                return total + registros.reduce((sumaMes, registro) => {
                    return (registro.facturada === true && registro.pagada === false)
                        ? sumaMes + registro.precio_total
                        : sumaMes;
                }, 0);
            }, 0) * 100) / 100;

            this.state.totalPagadas = Math.round(Object.values(data).reduce((total, registros) => {
                return total + registros.reduce((sumaMes, registro) => {
                    return (registro.pagada === true)
                        ? sumaMes + registro.precio_total
                        : sumaMes;
                }, 0);
            }, 0) * 100) / 100;
        } catch (error) {
            console.error("Error al obtener las cotizaciones:", error);
        }
    }

    get mesesVisibles() {
        const mesActual = new Date().getMonth(); // 0 = enero, 8 = septiembre
        return Object.keys(this.state.entradas).filter(mes => {
            const indice = ORDEN_MESES.indexOf(mes);
            return indice !== -1 && indice <= mesActual;
        });
    }

    // Regresa {total, facturadas, pagadas} ya contados para un mes
    getConteos(mes) {
        const registros = this.state.entradas[mes] || [];
        return {
            total: registros.length,
            facturadas: registros.filter(r => r.facturada).length,
            pagadas: registros.filter(r => r.pagada).length,
        };
    }

    get maxCotizaciones() {
        const valores = this.mesesVisibles.map(mes => (this.state.entradas[mes] || []).length);
        return Math.max(...valores, 1);
    }
}

ActivosEntradas.template = "dtm_ordenes_compra.activosentradas";