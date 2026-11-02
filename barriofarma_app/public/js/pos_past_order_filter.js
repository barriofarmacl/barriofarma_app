// BarrioFarma: Recent Orders scoped to active POS Profile (multi-channel POS).
// Issue: whiteboard #88
(() => {
	const PATCH_FLAG = "__barriofarma_past_orders_pos_profile_v2";

	function patchPastOrderListPrototype() {
		const klass = erpnext?.PointOfSale?.PastOrderList;
		if (!klass || klass.prototype[PATCH_FLAG]) {
			return Boolean(klass);
		}

		klass.prototype.refresh_list = function refresh_list_with_pos_profile() {
			frappe.dom.freeze();
			this.events.reset_summary();
			const search_term = this.search_field.get_value();
			const status = this.status_field.get_value();
			const pos_profile =
				this._barriofarma_pos_profile ||
				window.cur_pos?.pos_profile ||
				null;

			this.$invoices_container.html("");

			return frappe.call({
				method: "erpnext.selling.page.point_of_sale.point_of_sale.get_past_order_list",
				freeze: true,
				args: { search_term, status, pos_profile },
				callback: (response) => {
					frappe.dom.unfreeze();
					(response.message || []).forEach((invoice) => {
						this.$invoices_container.append(this.get_invoice_html(invoice));
					});
				},
			});
		};

		klass.prototype[PATCH_FLAG] = true;
		return true;
	}

	function patchControllerInitRecentOrderList() {
		const proto = erpnext?.PointOfSale?.Controller?.prototype;
		if (!proto || proto[PATCH_FLAG]) {
			return Boolean(proto);
		}

		const originalInit = proto.init_recent_order_list;
		proto.init_recent_order_list = function init_recent_order_list_patched() {
			originalInit.call(this);
			if (this.recent_order_list) {
				this.recent_order_list._barriofarma_pos_profile = this.pos_profile;
			}
		};

		proto[PATCH_FLAG] = true;
		return true;
	}

	function applyPosPastOrderPatches() {
		patchPastOrderListPrototype();
		patchControllerInitRecentOrderList();
		return Boolean(erpnext?.PointOfSale?.PastOrderList);
	}

	function wrapPointOfSalePageLoad() {
		const page = frappe.pages["point-of-sale"];
		if (!page || page[PATCH_FLAG]) {
			return;
		}

		const originalOnPageLoad = page.on_page_load;
		page.on_page_load = function on_page_load_with_past_order_filter(wrapper) {
			const boot = () => {
				applyPosPastOrderPatches();
				originalOnPageLoad(wrapper);
			};

			if (erpnext?.PointOfSale?.PastOrderList) {
				boot();
			} else {
				frappe.require("point-of-sale.bundle.js", boot);
			}
		};

		page[PATCH_FLAG] = true;
	}

	wrapPointOfSalePageLoad();

	// If POS bundle was already loaded (cached navigation), patch immediately too.
	frappe.require("point-of-sale.bundle.js", applyPosPastOrderPatches);
})();
