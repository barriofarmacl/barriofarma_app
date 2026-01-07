// -*- coding: utf-8 -*-
// Copyright (c) 2026, Barrio Farma and Contributors
// See license.txt

/**
 * Client Script para Purchase Receipt
 * 
 * Story 3.2: Optimización de Registro de Lotes durante Recepción
 * 
 * Mejoras de UI:
 * - Autocompletado de Batch basado en item_code
 * - Validación de fechas de caducidad en tiempo real
 * - Advertencias para lotes próximos a vencer
 * - Copia de información de lote entre items similares
 */

frappe.ui.form.on('Purchase Receipt', {
    refresh: function(frm) {
        // Agregar botón para copiar información de lote desde primera fila
        if (frm.doc.items && frm.doc.items.length > 1) {
            if (!frm.custom_buttons) {
                frm.custom_buttons = {};
            }
            if (!frm.custom_buttons['Copiar Lote']) {
                frm.add_custom_button(__('Copiar Lote'), function() {
                    copy_batch_info_to_all_items(frm);
                }, __('Acciones'));
            }
        }
    }
});

frappe.ui.form.on('Purchase Receipt Item', {
    item_code: function(frm, cdt, cdn) {
        // Cuando cambia el item_code, buscar batches existentes para autocompletar
        let row = locals[cdt][cdn];
        if (row.item_code) {
            // Buscar batches existentes para este item
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Batch',
                    filters: {
                        item: row.item_code
                    },
                    fields: ['name', 'batch_id', 'expiry_date'],
                    limit: 10,
                    order_by: 'expiry_date desc'
                },
                callback: function(r) {
                    if (r.message && r.message.length > 0) {
                        // Si hay batches, sugerir el más reciente
                        let latest_batch = r.message[0];
                        if (!row.batch_no) {
                            // No sobrescribir si ya hay batch_no
                            frappe.model.set_value(cdt, cdn, 'batch_no', latest_batch.name);
                            // Si el batch tiene expiry_date, mostrar advertencia si está próximo a vencer
                            if (latest_batch.expiry_date) {
                                check_expiry_warning(frm, cdt, cdn, latest_batch.expiry_date);
                            }
                        }
                    }
                }
            });
        }
    },
    
    batch_no: function(frm, cdt, cdn) {
        // Cuando cambia batch_no, validar y obtener información del Batch
        let row = locals[cdt][cdn];
        if (row.batch_no && row.item_code) {
            // Obtener información del Batch
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Batch',
                    name: row.batch_no
                },
                callback: function(r) {
                    if (r.message) {
                        let batch = r.message;
                        // Validar que el Batch pertenece al item
                        if (batch.item !== row.item_code) {
                            frappe.msgprint({
                                title: __('Error de Validación'),
                                indicator: 'red',
                                message: __('El lote {0} no pertenece al item {1}. Por favor, seleccione un lote válido.').format(
                                    frappe.bold(batch.batch_id || batch.name),
                                    frappe.bold(row.item_code)
                                )
                            });
                            frappe.model.set_value(cdt, cdn, 'batch_no', '');
                            return;
                        }
                        
                        // Validar fecha de caducidad si existe
                        if (batch.expiry_date) {
                            check_expiry_warning(frm, cdt, cdn, batch.expiry_date);
                        } else {
                            // Advertencia si no tiene fecha de caducidad
                            frappe.msgprint({
                                title: __('Advertencia'),
                                indicator: 'orange',
                                message: __('El lote {0} no tiene fecha de caducidad configurada. Se recomienda agregarla.').format(
                                    frappe.bold(batch.batch_id || batch.name)
                                )
                            });
                        }
                    }
                }
            });
        }
    }
});

/**
 * Verificar y mostrar advertencia si el lote está próximo a vencer
 */
function check_expiry_warning(frm, cdt, cdn, expiry_date) {
    if (!expiry_date) return;
    
    frappe.call({
        method: 'frappe.utils.getdate',
        args: {
            date: expiry_date
        },
        callback: function(r) {
            if (r.message) {
                let expiry = new Date(r.message);
                let today = new Date();
                let months_until_expiry = (expiry.getFullYear() - today.getFullYear()) * 12 + 
                                         (expiry.getMonth() - today.getMonth());
                
                // Obtener umbral mínimo (default 6 meses)
                let minimum_months = 6; // Default, se puede obtener del Purchase Receipt si está configurado
                
                if (months_until_expiry < minimum_months) {
                    frappe.msgprint({
                        title: __('Advertencia de Vencimiento'),
                        indicator: 'orange',
                        message: __('El lote vence en {0} meses, lo cual está bajo el umbral mínimo de {1} meses. '
                                  + 'El producto será marcado automáticamente como "Cuarentena".').format(
                            frappe.bold(months_until_expiry),
                            frappe.bold(minimum_months)
                        )
                    });
                } else if (months_until_expiry < minimum_months + 3) {
                    // Advertencia suave si está cerca del umbral
                    frappe.show_alert({
                        message: __('El lote vence en {0} meses. Verifique que cumple con el umbral mínimo.').format(months_until_expiry),
                        indicator: 'orange'
                    }, 5);
                }
            }
        }
    });
}

/**
 * Copiar información de lote desde la primera fila a todas las demás filas
 * Versión simplificada: solo copia el batch_no si el item requiere batch
 */
function copy_batch_info_to_all_items(frm) {
    if (!frm.doc.items || frm.doc.items.length < 2) {
        frappe.msgprint(__('Se requieren al menos 2 items para copiar información de lote.'));
        return;
    }
    
    let first_row = frm.doc.items[0];
    if (!first_row.batch_no) {
        frappe.msgprint(__('La primera fila no tiene lote asignado. Asigne un lote primero.'));
        return;
    }
    
    frappe.confirm(
        __('¿Copiar lote desde la primera fila a todas las demás filas que requieren batch?'),
        function() {
            // Yes - copiar batch_no a todas las filas que requieren batch
            let copied = 0;
            frm.doc.items.forEach(function(row, index) {
                if (index > 0 && row.item_code && !row.batch_no) {
                    // Verificar si el item requiere batch (simplificado: asumir que sí si tiene item_code)
                    // El servidor validará si realmente requiere batch
                    frappe.model.set_value(row.doctype, row.name, 'batch_no', first_row.batch_no);
                    copied++;
                }
            });
            frm.refresh_field('items');
            if (copied > 0) {
                frappe.msgprint(__('Lote copiado a {0} fila(s).', [copied]));
            } else {
                frappe.msgprint(__('No se copió ningún lote. Verifique que las filas requieran batch.'));
            }
        },
        function() {
            // No
        }
    );
}

