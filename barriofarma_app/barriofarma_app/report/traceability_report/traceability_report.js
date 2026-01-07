// Copyright (c) 2026, Barrio Farma and Contributors
// See license.txt

/*
 * Reporte de Trazabilidad de Medicamento
 * 
 * Story 2.2: Reporte de Trazabilidad de Medicamento
 * 
 * Filtros para el reporte de trazabilidad
 */

frappe.query_reports["Traceability Report"] = {
    filters: [
        {
            fieldname: "item_code",
            label: __("Producto"),
            fieldtype: "Link",
            options: "Item",
            reqd: 0,
            get_query: function() {
                return {
                    filters: {
                        "has_batch_no": 1  // Solo productos que requieren lote
                    }
                };
            }
        },
        {
            fieldname: "batch_no",
            label: __("Lote"),
            fieldtype: "Link",
            options: "Batch",
            reqd: 0,
            get_query: function() {
                var filters = {};
                if (frappe.query_report.get_filter_value("item_code")) {
                    filters["item"] = frappe.query_report.get_filter_value("item_code");
                }
                return {
                    filters: filters
                };
            }
        },
        {
            fieldname: "from_date",
            label: __("Desde Fecha"),
            fieldtype: "Date",
            reqd: 0,
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -12)  // Últimos 12 meses por defecto
        },
        {
            fieldname: "to_date",
            label: __("Hasta Fecha"),
            fieldtype: "Date",
            reqd: 0,
            default: frappe.datetime.get_today()
        }
    ],
    
    onload: function(report) {
        // Validar que al menos item_code o batch_no estén especificados
        report.page.add_inner_button(__("Validar Filtros"), function() {
            var item_code = report.get_filter_value("item_code");
            var batch_no = report.get_filter_value("batch_no");
            
            if (!item_code && !batch_no) {
                frappe.msgprint({
                    title: __("Filtro Requerido"),
                    message: __("Debe especificar al menos un Producto o un Lote para generar el reporte de trazabilidad."),
                    indicator: "orange"
                });
            } else {
                frappe.msgprint({
                    title: __("Filtros Válidos"),
                    message: __("Los filtros están configurados correctamente. Puede ejecutar el reporte."),
                    indicator: "green"
                });
            }
        });
    }
};

