/** @odoo-module **/
import { Component, useState, onMounted } from "@odoo/owl";

export class HistorialDialogo extends Component {
    static props = ["cerrar", "orden_diseno"]

    setup() {
        this.state = useState({
            historial: []
        })

        onMounted(async () => {
            await this.getHistorial();
        })
    }

    async getHistorial() {
        const data = await fetch("/tiempo_status", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                orden_diseno: this.props.orden_diseno,
            }),
        });
        const result = await data.json();
        this.state.historial = (result.result || []).map((item) => ({
            ...item,
            inicial: this._formatFecha(item.inicial),
            final: this._formatFecha(item.final),
            totalHoras: item.total || 0,
            totalLabel: this._formatTotal(item.total),
        }));
    }

    _formatFecha(fechaIso) {
        if (!fechaIso) {
            return "";
        }
        const fecha = new Date(fechaIso);
        const dia = String(fecha.getDate()).padStart(2, "0");
        const mes = String(fecha.getMonth() + 1).padStart(2, "0");
        const horas = String(fecha.getHours()).padStart(2, "0");
        const minutos = String(fecha.getMinutes()).padStart(2, "0");
        return `${dia}/${mes} ${horas}:${minutos}`;
    }

    _formatTotal(horas) {
        if (!horas) {
            return "0s";
        }
        const segundosTotales = horas * 3600;

        if (segundosTotales < 60) {
            return `${Math.round(segundosTotales)}s`;
        }
        if (segundosTotales < 3600) {
            return `${Math.round(segundosTotales / 60)}min`;
        }
        return `${horas.toFixed(2)}h`;
    }



    get maxHoras() {
        const totales = this.state.historial.map((h) => h.totalHoras || 0);
        return Math.max(...totales, 1);
    }

    get barras() {
        return this.state.historial.map((h) => ({
            ...h,
            pct: Math.round(((h.totalHoras || 0) / this.maxHoras) * 100),
        }));
    }
}

HistorialDialogo.template = "dtm_procesos.historial_dialogo";