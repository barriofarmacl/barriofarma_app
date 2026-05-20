frappe.ui.form.on("Stock Entry", {
	setup(frm) {
		frm.set_query("custom_from_shelf", "items", (doc, cdt, cdn) => {
			const row = locals[cdt][cdn];
			const filters = { disabled: 0 };
			if (row.s_warehouse) {
				filters.warehouse = row.s_warehouse;
			}
			return { filters };
		});

		frm.set_query("custom_to_shelf", "items", (doc, cdt, cdn) => {
			const row = locals[cdt][cdn];
			const filters = { disabled: 0 };
			if (row.t_warehouse) {
				filters.warehouse = row.t_warehouse;
			}
			return { filters };
		});
	},
});

frappe.ui.form.on("Stock Entry Detail", {
	s_warehouse(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.custom_from_shelf || !row.s_warehouse) return;
		frappe.db.get_value("Shelf", row.custom_from_shelf, "warehouse").then((r) => {
			if (r.message?.warehouse && r.message.warehouse !== row.s_warehouse) {
				frappe.model.set_value(cdt, cdn, "custom_from_shelf", "");
			}
		});
	},
	t_warehouse(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.custom_to_shelf || !row.t_warehouse) return;
		frappe.db.get_value("Shelf", row.custom_to_shelf, "warehouse").then((r) => {
			if (r.message?.warehouse && r.message.warehouse !== row.t_warehouse) {
				frappe.model.set_value(cdt, cdn, "custom_to_shelf", "");
			}
		});
	},
});
