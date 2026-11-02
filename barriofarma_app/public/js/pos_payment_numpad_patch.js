// BarrioFarma: bloquear Pedido completo si paid < total (el teclado CLP se corrige con currency_precision=0).
frappe.provide("barriofarma_app.pos");

frappe.require("point-of-sale.bundle.js", function () {
	const klass = erpnext?.PointOfSale?.Payment;
	const numpad = barriofarma_app?.pos_payment_numpad;
	if (!klass || !numpad || klass.__barriofarma_pos_complete_guard_v1) {
		return;
	}

	const original_bind_events = klass.prototype.bind_events;
	klass.prototype.bind_events = function () {
		original_bind_events.call(this);
		this.$component.off("click", ".submit-order-btn");
		this.$component.on("click", ".submit-order-btn", () => {
			const doc = this.events.get_frm().doc;
			const decision = numpad.can_complete_order({
				item_count: (doc.items || []).length,
				paid_amount: doc.paid_amount,
				grand_total: doc.grand_total,
				rounded_total: doc.rounded_total,
				disable_rounded_total: cint(frappe.sys_defaults.disable_rounded_total),
				allow_partial_payment: this.allow_partial_payment,
				additional_discount_percentage: doc.additional_discount_percentage,
			});
			if (!decision.ok) {
				const message =
					decision.reason === "empty"
						? __("You cannot submit empty order.")
						: __("You cannot submit the order without payment.");
				frappe.show_alert({ message, indicator: "orange" });
				frappe.utils.play_sound("error");
				return;
			}
			if (!this.validate_reqd_invoice_fields()) {
				return;
			}
			this.events.submit_invoice();
		});
	};

	klass.__barriofarma_pos_complete_guard_v1 = true;
});
