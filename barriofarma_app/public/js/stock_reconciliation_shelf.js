frappe.ui.form.on("Stock Reconciliation", {
	setup(frm) {
		frm.set_query("shelf", "items", (doc, cdt, cdn) => {
			const row = locals[cdt][cdn];
			const filters = { disabled: 0 };
			if (row.warehouse) {
				filters.warehouse = row.warehouse;
			}
			return { filters };
		});
	},
});

frappe.ui.form.on("Stock Reconciliation Item", {
	warehouse(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.shelf && row.warehouse) {
			frappe.db.get_value("Shelf", row.shelf, "warehouse").then((r) => {
				if (r.message && r.message.warehouse && r.message.warehouse !== row.warehouse) {
					frappe.model.set_value(cdt, cdn, "shelf", "");
				}
			});
		}
	},
});
