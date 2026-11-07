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
	refresh(frm) {
		schedule_negative_ledger_alert(frm);
	},
	posting_date(frm) {
		schedule_negative_ledger_alert(frm);
	},
	posting_time(frm) {
		schedule_negative_ledger_alert(frm);
	},
	purpose(frm) {
		schedule_negative_ledger_alert(frm);
	},
});

function schedule_negative_ledger_alert(frm) {
	clearTimeout(frm._bf_neg_ledger_timer);
	frm._bf_neg_ledger_timer = setTimeout(() => refresh_negative_ledger_alert(frm), 300);
}

function refresh_negative_ledger_alert(frm) {
	const items = (frm.doc.items || [])
		.filter((row) => row.item_code && row.warehouse)
		.map((row) => ({
			idx: row.idx,
			item_code: row.item_code,
			warehouse: row.warehouse,
			qty: row.qty,
		}));
	if (!frm.doc.posting_date || !items.length || frm.doc.purpose === "Opening Stock") {
		clear_negative_ledger_alert(frm);
		return;
	}
	frappe.call({
		method:
			"barriofarma_app.barriofarma_app.utils.stock_reconciliation_negative_ledger.negative_ledger_warning",
		args: {
			posting_date: frm.doc.posting_date,
			posting_time: frm.doc.posting_time,
			purpose: frm.doc.purpose,
			items,
		},
		callback(response) {
			if (response.message) {
				frm.dashboard.set_headline_alert(response.message, "red");
				frm._bf_negative_ledger_alert = true;
				return;
			}
			clear_negative_ledger_alert(frm);
		},
	});
}

function clear_negative_ledger_alert(frm) {
	if (!frm._bf_negative_ledger_alert) {
		return;
	}
	frm.dashboard.clear_headline();
	frm._bf_negative_ledger_alert = false;
}

frappe.ui.form.on("Stock Reconciliation Item", {
	item_code(frm) {
		schedule_negative_ledger_alert(frm);
	},
	qty(frm) {
		schedule_negative_ledger_alert(frm);
	},
	warehouse(frm, cdt, cdn) {
		schedule_negative_ledger_alert(frm);
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
