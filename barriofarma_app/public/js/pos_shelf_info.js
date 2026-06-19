(() => {
	const PATCH_FLAG = "__barriofarma_shelf_info_v2";
	const SHELF_FIELD = "barriofarma_shelf_info";

	function shelf_field_meta() {
		return {
			fieldname: SHELF_FIELD,
			fieldtype: "Data",
			label: __("Estantes"),
			read_only: 1,
		};
	}

	function ensure_shelf_field_meta(item_details) {
		if (!item_details?.item_meta?.fields) return;
		if (item_details.item_meta.fields.some((df) => df.fieldname === SHELF_FIELD)) return;
		item_details.item_meta.fields.push(shelf_field_meta());
	}

	function patchPosItemDetails() {
		if (!erpnext?.PointOfSale?.ItemDetails) return false;
		const klass = erpnext.PointOfSale.ItemDetails;
		if (klass[PATCH_FLAG]) return true;

		const originalGetFormFields = klass.prototype.get_form_fields;
		const originalRenderForm = klass.prototype.render_form;

		klass.prototype.get_form_fields = function (item) {
			const fields = originalGetFormFields.call(this, item);
			if (fields.includes(SHELF_FIELD)) return fields;
			const next = [...fields];
			const idx = next.indexOf("actual_qty");
			if (idx >= 0) {
				next.splice(idx + 1, 0, SHELF_FIELD);
			} else {
				next.push(SHELF_FIELD);
			}
			return next;
		};

		klass.prototype.render_form = function (item) {
			ensure_shelf_field_meta(this);
			originalRenderForm.call(this, item);
			this.bind_shelf_info_refresh();
			this.load_shelf_info(item);
		};

		klass.prototype.bind_shelf_info_refresh = function () {
			if (!this.warehouse_control?.$input) return;
			const me = this;
			this.warehouse_control.$input.off("change.barriofarmaShelfInfo");
			this.warehouse_control.$input.on("change.barriofarmaShelfInfo", () => {
				me.load_shelf_info(me.current_item || me.item_row || {});
			});
		};

		klass.prototype.load_shelf_info = async function (item) {
			const control = this[`${SHELF_FIELD}_control`];
			if (!control) return;

			const item_code = item?.item_code;
			const warehouse = this.warehouse_control?.get_value?.() || item?.warehouse;
			if (!item_code || !warehouse) {
				control.set_value("");
				return;
			}

			control.set_value(__("Consultando estantes..."));

			try {
				const r = await frappe.call({
					method: "barriofarma_app.barriofarma_app.api.pos_shelf.get_item_shelf_summary",
					args: { item_code, warehouse },
				});
				control.set_value(r?.message?.summary || __("Sin estantes configurados"));
			} catch (e) {
				console.error("POS shelf info error", e);
				control.set_value(__("No fue posible cargar estantes"));
			}
		};

		klass[PATCH_FLAG] = true;
		return true;
	}

	const timer = setInterval(() => {
		if (patchPosItemDetails()) clearInterval(timer);
	}, 500);
})();
