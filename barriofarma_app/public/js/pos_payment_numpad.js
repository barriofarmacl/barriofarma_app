// BarrioFarma: no completar POS si el pago es menor al total (allow_partial_payment=0).
(function (root, factory) {
	const api = factory();
	if (typeof module !== "undefined" && module.exports) {
		module.exports = api;
	}
	root.barriofarma_app = root.barriofarma_app || {};
	root.barriofarma_app.pos_payment_numpad = api;
})(typeof window !== "undefined" ? window : globalThis, function () {
	function to_number(value) {
		const n = Number(value);
		return Number.isFinite(n) ? n : 0;
	}

	function invoice_total(grand_total, rounded_total, disable_rounded_total) {
		if (disable_rounded_total) {
			return to_number(grand_total);
		}
		const rounded = to_number(rounded_total);
		return rounded || to_number(grand_total);
	}

	function can_complete_order(opts) {
		const item_count = to_number(opts.item_count);
		if (!item_count) {
			return { ok: false, reason: "empty" };
		}
		if (to_number(opts.additional_discount_percentage) === 100) {
			return { ok: true, reason: "full_discount" };
		}
		const total = invoice_total(
			opts.grand_total,
			opts.rounded_total,
			opts.disable_rounded_total
		);
		const paid = to_number(opts.paid_amount);
		const allow_partial = !!opts.allow_partial_payment;
		if (paid === 0 && !allow_partial) {
			return { ok: false, reason: "no_payment" };
		}
		if (!allow_partial && paid < total) {
			return { ok: false, reason: "partial" };
		}
		return { ok: true, reason: "ok" };
	}

	return { can_complete_order, invoice_total };
});
