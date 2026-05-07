(() => {
	const PATCH_FLAG = "__barriofarma_shelf_info_patch";

	function buildShelfInfoHtml(text) {
		return `
			<div class="shelf-info-inline" style="margin-top: 6px; font-size: 12px; color: var(--text-muted);">
				<div><strong>${__("Estantes")}</strong></div>
				<div>${frappe.utils.escape_html(text || __("Sin estantes configurados"))}</div>
			</div>
		`;
	}

	function patchPosItemDetails() {
		if (!erpnext?.PointOfSale?.ItemDetails) return false;
		const klass = erpnext.PointOfSale.ItemDetails;
		if (klass[PATCH_FLAG]) return true;

		const originalRenderForm = klass.prototype.render_form;

		klass.prototype.render_form = function (item) {
			originalRenderForm.call(this, item);
			this.render_shelf_info(item);
			this.bind_shelf_info_refresh();
		};

		klass.prototype.bind_shelf_info_refresh = function () {
			if (!this.warehouse_control || !this.warehouse_control.$input) return;
			this.warehouse_control.$input.off("change.barriofarmaShelfInfo");
			this.warehouse_control.$input.on("change.barriofarmaShelfInfo", () => {
				this.render_shelf_info(this.current_item || this.item_row || {});
			});
		};

		klass.prototype.render_shelf_info = async function (item) {
			const item_code = item?.item_code;
			const warehouse = this.warehouse_control?.get_value?.() || item?.warehouse;
			if (!item_code || !warehouse || !this.$form_container) return;

			this.$form_container.find(".shelf-info-control").remove();
			const $control = $(`<div class="shelf-info-control"></div>`);
			$control.html(buildShelfInfoHtml(__("Consultando estantes...")));

			const $actualQty = this.$form_container.find(".actual_qty-control");
			if ($actualQty.length) {
				$control.insertAfter($actualQty);
			} else {
				this.$form_container.append($control);
			}

			try {
				const r = await frappe.call({
					method: "barriofarma_app.barriofarma_app.api.pos_shelf.get_item_shelf_summary",
					args: { item_code, warehouse },
				});
				const summary = r?.message?.summary || "";
				$control.html(buildShelfInfoHtml(summary));
			} catch (e) {
				console.error("POS shelf info error", e);
				$control.html(buildShelfInfoHtml(__("No fue posible cargar estantes")));
			}
		};

		klass[PATCH_FLAG] = true;
		return true;
	}

	// point-of-sale.bundle.js se carga dinámicamente; intentamos parchear hasta que exista.
	const timer = setInterval(() => {
		const ok = patchPosItemDetails();
		if (ok) clearInterval(timer);
	}, 500);
})();

