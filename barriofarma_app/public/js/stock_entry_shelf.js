// Copyright (c) 2026, Barrio Farma — estantes en Stock Entry (Issue #58)

function bf_autofill_shelf_for_row(frm, cdt, cdn, warehouse, fieldname) {
	if (!warehouse) {
		return;
	}
	const row = locals[cdt][cdn];
	if (row[fieldname]) {
		return;
	}
	frappe.db
		.get_list("Shelf", {
			filters: { warehouse, disabled: 0 },
			fields: ["name"],
			limit: 2,
		})
		.then((shelves) => {
			if (shelves.length === 1) {
				frappe.model.set_value(cdt, cdn, fieldname, shelves[0].name);
			}
		});
}

function bf_toggle_shelf_grid_columns(frm) {
	const grid = frm.fields_dict.items && frm.fields_dict.items.grid;
	if (!grid) {
		return;
	}
	["custom_from_shelf", "custom_to_shelf"].forEach((fieldname) => {
		grid.update_docfield_property(fieldname, "hidden", 0);
		grid.update_docfield_property(fieldname, "in_list_view", 1);
	});
}

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

	refresh(frm) {
		bf_toggle_shelf_grid_columns(frm);
	},
});

frappe.ui.form.on("Stock Entry Detail", {
	s_warehouse(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.custom_from_shelf && row.s_warehouse) {
			frappe.db.get_value("Shelf", row.custom_from_shelf, "warehouse").then((r) => {
				if (r.message?.warehouse && r.message.warehouse !== row.s_warehouse) {
					frappe.model.set_value(cdt, cdn, "custom_from_shelf", "");
				}
			});
		}
		bf_autofill_shelf_for_row(frm, cdt, cdn, row.s_warehouse, "custom_from_shelf");
	},

	t_warehouse(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.custom_to_shelf && row.t_warehouse) {
			frappe.db.get_value("Shelf", row.custom_to_shelf, "warehouse").then((r) => {
				if (r.message?.warehouse && r.message.warehouse !== row.t_warehouse) {
					frappe.model.set_value(cdt, cdn, "custom_to_shelf", "");
				}
			});
		}
		bf_autofill_shelf_for_row(frm, cdt, cdn, row.t_warehouse, "custom_to_shelf");
	},

	items_add(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		bf_autofill_shelf_for_row(frm, cdt, cdn, row.s_warehouse, "custom_from_shelf");
		bf_autofill_shelf_for_row(frm, cdt, cdn, row.t_warehouse, "custom_to_shelf");
	},
});
