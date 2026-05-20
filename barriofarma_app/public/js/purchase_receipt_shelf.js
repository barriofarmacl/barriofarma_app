frappe.ui.form.on("Purchase Receipt", {
	setup(frm) {
		frm.set_query("custom_to_shelf", "items", (doc, cdt, cdn) => {
			const row = locals[cdt][cdn];
			const filters = { disabled: 0 };
			if (row.warehouse) {
				filters.warehouse = row.warehouse;
			}
			return { filters };
		});
	},
});

frappe.ui.form.on("Purchase Receipt Item", {
	warehouse(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.custom_to_shelf || !row.warehouse) return;
		frappe.db.get_value("Shelf", row.custom_to_shelf, "warehouse").then((r) => {
			if (r.message?.warehouse && r.message.warehouse !== row.warehouse) {
				frappe.model.set_value(cdt, cdn, "custom_to_shelf", "");
			}
		});
	},
});
