frappe.require("item-dashboard.bundle.js", function () {
	erpnext.stock.move_item = function (item, source, target, actual_qty, rate, stock_uom, callback) {
		const is_receipt = !source;
		let dialog;

		const clear_to_shelf = () => dialog.set_value("custom_to_shelf", "");
		const clear_from_shelf = () => dialog.set_value("custom_from_shelf", "");

		dialog = new frappe.ui.Dialog({
			title: target ? __("Add Item") : __("Move Item"),
			fields: [
				{
					fieldname: "item_code",
					label: __("Item"),
					fieldtype: "Link",
					options: "Item",
					read_only: 1,
				},
				{
					fieldname: "source",
					label: __("Source Warehouse"),
					fieldtype: "Link",
					options: "Warehouse",
					read_only: 1,
				},
				{
					fieldname: "custom_from_shelf",
					label: __("Estante origen"),
					fieldtype: "Link",
					options: "Shelf",
					reqd: !is_receipt,
					hidden: is_receipt ? 1 : 0,
					get_query() {
						const wh = dialog.get_value("source");
						return {
							filters: {
								disabled: 0,
								...(wh ? { warehouse: wh } : {}),
							},
						};
					},
				},
				{
					fieldname: "target",
					label: __("Almacén de envío"),
					fieldtype: "Link",
					options: "Warehouse",
					reqd: 1,
					onchange: clear_to_shelf,
					get_query() {
						return {
							filters: {
								is_group: 0,
							},
						};
					},
				},
				{
					fieldname: "custom_to_shelf",
					label: __("Estante destino"),
					fieldtype: "Link",
					options: "Shelf",
					reqd: 1,
					get_query() {
						const wh = dialog.get_value("target");
						return {
							filters: {
								disabled: 0,
								...(wh ? { warehouse: wh } : {}),
							},
						};
					},
				},
				{
					fieldname: "qty",
					label: __("Quantity"),
					reqd: 1,
					fieldtype: "Float",
					description: __("Available {0}", [actual_qty]),
				},
				{
					fieldname: "rate",
					label: __("Rate"),
					fieldtype: "Currency",
					hidden: 1,
				},
			],
		});

		dialog.show();
		dialog.get_field("item_code").set_input(item);

		if (source) {
			dialog.get_field("source").set_input(source);
		} else {
			dialog.get_field("source").df.hidden = 1;
			dialog.get_field("source").refresh();
		}

		if (rate) {
			dialog.get_field("rate").set_value(rate);
			dialog.get_field("rate").df.hidden = 0;
			dialog.get_field("rate").refresh();
		}

		if (target) {
			dialog.get_field("target").df.read_only = 1;
			dialog.get_field("target").value = target;
			dialog.get_field("target").refresh();
		}

		dialog.set_primary_action(__("Create Stock Entry"), function (values) {
			const qty = flt(values.qty);
			const available_qty = flt(actual_qty);

			if (source && (qty <= 0 || qty > available_qty)) {
				frappe.msgprint(
					__("Quantity must be greater than zero, and less or equal to {0}", [available_qty])
				);
				return;
			}

			if (values.source === values.target) {
				frappe.msgprint(__("Source and target warehouse must be different"));
				return;
			}

			if (!values.custom_to_shelf) {
				frappe.msgprint(__("Debe indicar el estante destino en el almacén de envío."));
				return;
			}

			if (source && !values.custom_from_shelf) {
				frappe.msgprint(__("Debe indicar el estante origen en el almacén de salida."));
				return;
			}

			frappe.model.with_doctype("Stock Entry", function () {
				const doc = frappe.model.get_new_doc("Stock Entry");
				doc.from_warehouse = values.source;
				doc.to_warehouse = values.target;
				doc.stock_entry_type = doc.from_warehouse ? "Material Transfer" : "Material Receipt";
				const row = frappe.model.add_child(doc, "items");
				row.item_code = values.item_code;
				row.s_warehouse = values.source;
				row.stock_uom = stock_uom;
				row.uom = stock_uom;
				row.t_warehouse = values.target;
				row.qty = qty;
				row.conversion_factor = 1;
				row.transfer_qty = qty;
				row.basic_rate = values.rate;
				row.custom_from_shelf = values.custom_from_shelf;
				row.custom_to_shelf = values.custom_to_shelf;
				dialog.hide();
				frappe.set_route("Form", doc.doctype, doc.name);
				if (typeof callback === "function") {
					callback();
				}
			});
		});
	};
});
