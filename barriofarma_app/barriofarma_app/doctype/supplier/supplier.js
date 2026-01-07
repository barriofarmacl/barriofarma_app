// -*- coding: utf-8 -*-
// Copyright (c) 2026, Barrio Farma and Contributors
// See license.txt

/**
 * Client Script para Supplier
 * 
 * Story 3.3: Gestión Mejorada de Proveedores
 * 
 * Mejoras de UI:
 * - Botón para ver historial de compras
 * - Resumen de compras recientes
 * - Información de contacto destacada
 */

frappe.ui.form.on('Supplier', {
    refresh: function(frm) {
        // Agregar botón para ver historial de compras
        if (frm.doc.name) {
            frm.add_custom_button(__('Historial de Compras'), function() {
                frappe.set_route('query-report', 'Supplier Purchase History', {
                    supplier: frm.doc.name
                });
            }, __('Ver Reportes'));
            
            // Agregar botón para ver Purchase Orders
            frm.add_custom_button(__('Purchase Orders'), function() {
                frappe.set_route('List', 'Purchase Order', {
                    supplier: frm.doc.name
                });
            }, __('Ver Documentos'));
            
            // Agregar botón para ver Purchase Receipts
            frm.add_custom_button(__('Purchase Receipts'), function() {
                frappe.set_route('List', 'Purchase Receipt', {
                    supplier: frm.doc.name
                });
            }, __('Ver Documentos'));
        }
        
        // Mostrar resumen de compras recientes si está disponible (opcional)
        // Comentado por ahora para evitar complejidad innecesaria
        // if (frm.doc.name && !frm.is_new()) {
        //     load_purchase_summary(frm);
        // }
    }
});

/**
 * Cargar resumen de compras recientes
 */
function load_purchase_summary(frm) {
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Purchase Order',
            filters: {
                supplier: frm.doc.name,
                docstatus: 1
            },
            fields: ['name', 'transaction_date', 'grand_total', 'status'],
            limit: 5,
            order_by: 'transaction_date desc'
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                let summary_html = '<div class="purchase-summary" style="margin-top: 10px; padding: 10px; background: #f8f9fa; border-radius: 4px;">';
                summary_html += '<h6 style="margin-bottom: 10px;">Compras Recientes (Purchase Orders)</h6>';
                summary_html += '<table class="table table-bordered table-sm">';
                summary_html += '<thead><tr><th>Documento</th><th>Fecha</th><th>Monto</th><th>Estado</th></tr></thead>';
                summary_html += '<tbody>';
                
                r.message.forEach(function(po) {
                    summary_html += '<tr>';
                    summary_html += `<td><a href="/app/purchase-order/${po.name}">${po.name}</a></td>`;
                    summary_html += `<td>${po.transaction_date || ''}</td>`;
                    summary_html += `<td>${format_currency(po.grand_total)}</td>`;
                    summary_html += `<td>${po.status || ''}</td>`;
                    summary_html += '</tr>';
                });
                
                summary_html += '</tbody></table>';
                summary_html += '</div>';
                
                // Agregar al dashboard si existe
                if (frm.dashboard) {
                    frm.dashboard.add_section(summary_html, __('Resumen de Compras'));
                }
            }
        }
    });
}

/**
 * Formatear moneda
 */
function format_currency(amount) {
    if (!amount) return '0.00';
    return new Intl.NumberFormat('es-CL', {
        style: 'currency',
        currency: 'CLP'
    }).format(amount);
}

