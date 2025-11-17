// Copyright (c) 2025, Barrio Farma and Contributors
// See license.txt

frappe.ui.form.on('POS Invoice', {
	/**
	 * Sincronizar Patient → Customer automáticamente
	 * Cuando se selecciona un Patient, buscar su Customer asociado y asignarlo
	 */
	custom_patient: function(frm) {
		if (frm.doc.custom_patient) {
			// Obtener el Customer asociado al Patient
			frappe.db.get_value('Patient', frm.doc.custom_patient, 'customer')
				.then(r => {
					if (r && r.message && r.message.customer) {
						// Asignar el Customer asociado
						frm.set_value('customer', r.message.customer);
						frm.refresh_field('customer');
					} else {
						frappe.msgprint({
							title: __('Advertencia'),
							indicator: 'orange',
							message: __('El paciente seleccionado no tiene un Customer asociado. Se creará automáticamente al guardar.')
						});
					}
				});
		}
	},

	/**
	 * Si se cambia el Customer manualmente, intentar encontrar el Patient asociado
	 */
	customer: function(frm) {
		if (frm.doc.customer && !frm.doc.custom_patient) {
			// Buscar Patient que tenga este Customer asociado
			frappe.db.get_value('Patient', {'customer': frm.doc.customer}, 'name')
				.then(r => {
					if (r && r.message && r.message.name) {
						frm.set_value('custom_patient', r.message.name);
						frm.refresh_field('custom_patient');
					}
				});
		}
	}
});

