// Copyright (c) 2025, Barrio Farma and Contributors
// See license.txt

function barriofarma_prompt_add_receta_items_to_invoice(frm) {
	if (!frm.doc.custom_receta_medica || frm.doc.__islocal) {
		return;
	}
	frappe.confirm(
		__('¿Desea agregar todos los medicamentos de la receta {0} a esta venta?', [
			frm.doc.custom_receta_medica,
		]),
		function () {
			frappe.call({
				method:
					'barriofarma_app.barriofarma_app.api.receta_medica.add_receta_medica_items_to_invoice_api',
				args: {
					invoice_name: frm.doc.name,
					receta_name: frm.doc.custom_receta_medica,
					warehouse: frm.doc.set_warehouse,
				},
				callback: function (r) {
					if (!r.message) {
						return;
					}
					let msg = __('Se agregaron {0} medicamentos de la receta.', [
						r.message.items_added.length,
					]);
					if (r.message.items_skipped.length > 0) {
						msg +=
							' ' +
							__('{0} medicamentos ya estaban en la venta.', [
								r.message.items_skipped.length,
							]);
					}
					frappe.show_alert({ message: msg, indicator: 'green' }, 5);
					frm.reload_doc();
				},
			});
		},
	);
}

frappe.ui.form.on('POS Invoice', {
	custom_patient: function (frm) {
		if (frm.doc.custom_patient) {
			frappe.db.get_value('Patient', frm.doc.custom_patient, 'customer').then((r) => {
				if (r && r.message && r.message.customer) {
					frm.set_value('customer', r.message.customer);
					frm.refresh_field('customer');
				} else {
					frappe.msgprint({
						title: __('Advertencia'),
						indicator: 'orange',
						message: __(
							'El paciente seleccionado no tiene un Customer asociado. Se creará automáticamente al guardar si aplica.',
						),
					});
				}
			});
		}
	},

	customer: function (frm) {
		if (frm.doc.customer && !frm.doc.custom_patient) {
			frappe.db.get_value('Patient', { customer: frm.doc.customer }, 'name').then((r) => {
				if (r && r.message && r.message.name) {
					frm.set_value('custom_patient', r.message.name);
					frm.refresh_field('custom_patient');
				}
			});
		}
	},

	custom_receta_medica: function (frm) {
		barriofarma_prompt_add_receta_items_to_invoice(frm);
	},
});
