// Copyright (c) 2026, Barrio Farma and contributors
// For license information, please see license.txt

frappe.ui.form.on("Receta Medica", {
	refresh(frm) {
		// Placeholder para logica cliente futura (ej. boton cargar items a factura).
	},
	doctor(frm) {
		if (frm.doc.doctor && !frm.doc.doctor_name) {
			frappe.db.get_value("Doctor", frm.doc.doctor, "doctor_name").then(({ message }) => {
				if (message && message.doctor_name) {
					frm.set_value("doctor_name", message.doctor_name);
				}
			});
		}
	},
});
