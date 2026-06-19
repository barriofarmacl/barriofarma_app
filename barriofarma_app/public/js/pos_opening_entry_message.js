// BarrioFarma: mensaje claro cuando la apertura POS es de un día anterior (ERPNext "outdated").
frappe.provide("barriofarma_app.pos");

frappe.require("point-of-sale.bundle.js", function () {
	if (!erpnext?.PointOfSale?.Controller?.prototype) {
		return;
	}

	erpnext.PointOfSale.Controller.prototype.check_outdated_pos_opening_entry = function () {
		const opening_raw = this.pos_opening_time;
		if (!opening_raw) {
			return;
		}

		const opening_date = (String(opening_raw).slice(0, 10) || "").trim();
		const today = frappe.datetime.get_today();
		const days_since_opening = frappe.datetime.get_day_diff(today, opening_date);

		// Solo avisar si la apertura es estrictamente anterior a hoy (no "outdated" genérico).
		if (days_since_opening <= 0) {
			return;
		}

		frappe.msgprint({
			title: __("POS opening from a previous day"),
			message: __(
				"This cash register was opened on {0}. To sell today, close the shift (POS Closing Entry) and open a new session.",
				[frappe.datetime.str_to_user(opening_date)]
			),
			indicator: "orange",
		});
	};
});
