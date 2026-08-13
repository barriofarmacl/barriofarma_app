(() => {
	frappe.provide("barriofarma_app.pos");

	const PATCH = {
		cart: "__barriofarma_receta_cart_v6",
		payment: "__barriofarma_receta_payment_v2",
		selector: "__barriofarma_receta_selector_v4",
		controller: "__barriofarma_receta_controller_v5",
	};

	const RECETA_FIELDS = [
		{
			fieldname: "custom_patient",
			label: __("Paciente"),
			fieldtype: "Link",
			options: "Patient",
		},
		{
			fieldname: "custom_receta_medica",
			label: __("Receta Medica"),
			fieldtype: "Link",
			options: "Receta Medica",
		},
	];

	barriofarma_app.pos.item_flags = barriofarma_app.pos.item_flags || {};

	function cache_item_flags(item) {
		if (!item?.item_code) return;
		barriofarma_app.pos.item_flags[item.item_code] = !!(
			item.requires_receta_retenida ||
			item.custom_dispensing_type === "Venta con Receta Retenida" ||
			item.custom_requires_prescription_retention
		);
	}

	async function cache_item_flag_for_code(item_code) {
		if (!item_code || barriofarma_app.pos.item_flags[item_code] !== undefined) {
			return;
		}
		try {
			const { message } = await frappe.db.get_value("Item", item_code, [
				"custom_dispensing_type",
				"custom_requires_prescription_retention",
			]);
			cache_item_flags({
				item_code,
				custom_dispensing_type: message?.custom_dispensing_type,
				custom_requires_prescription_retention: message?.custom_requires_prescription_retention,
				requires_receta_retenida:
					message?.custom_dispensing_type === "Venta con Receta Retenida" ||
					message?.custom_requires_prescription_retention,
			});
		} catch (e) {
			barriofarma_app.pos.item_flags[item_code] = false;
		}
	}

	function item_requires_receta(item_code) {
		return !!barriofarma_app.pos.item_flags[item_code];
	}

	function item_data_requires_receta(item) {
		if (!item) return false;
		if (typeof item === "string") {
			return item_requires_receta(item);
		}
		return !!(
			item.requires_receta_retenida ||
			item.custom_dispensing_type === "Venta con Receta Retenida" ||
			item.custom_requires_prescription_retention
		);
	}

	function decorate_grid_receta_badges(item_selector) {
		const $container = item_selector?.$items_container;
		if (!$container?.length) return;

		$container.find(".item-wrapper").each(function () {
			const $wrapper = $(this);
			const item_code = $wrapper.attr("data-item-code");
			if (!item_code || !item_data_requires_receta(item_code)) {
				return;
			}
			if ($wrapper.children(".bf-pos-receta-badge").length) {
				return;
			}
			$wrapper.prepend(receta_badge_html());
		});
	}

	async function ensure_item_flags_for_grid(item_selector) {
		const codes = [];
		item_selector?.$items_container?.find(".item-wrapper").each(function () {
			const code = $(this).attr("data-item-code");
			if (code && barriofarma_app.pos.item_flags[code] === undefined) {
				codes.push(code);
			}
		});

		if (!codes.length) {
			return;
		}

		try {
			const rows = await frappe.db.get_list("Item", {
				filters: { name: ["in", codes] },
				fields: ["name", "custom_dispensing_type", "custom_requires_prescription_retention"],
				limit_page_length: 0,
			});
			const seen = new Set();
			(rows || []).forEach((row) => {
				seen.add(row.name);
				cache_item_flags({
					item_code: row.name,
					custom_dispensing_type: row.custom_dispensing_type,
					custom_requires_prescription_retention: row.custom_requires_prescription_retention,
					requires_receta_retenida:
						row.custom_dispensing_type === "Venta con Receta Retenida" ||
						row.custom_requires_prescription_retention,
				});
			});
			codes.forEach((code) => {
				if (!seen.has(code)) {
					barriofarma_app.pos.item_flags[code] = false;
				}
			});
		} catch (e) {
			console.error("BarrioFarma POS: item flags batch load failed", e);
		}
	}

	async function refresh_grid_receta_badges(item_selector) {
		if (!item_selector?.$items_container?.length) {
			return;
		}
		await ensure_item_flags_for_grid(item_selector);
		decorate_grid_receta_badges(item_selector);
	}

	function get_cart_frm(cart) {
		const frm = cart?.events?.get_frm?.();
		return frm?.doc ? frm : null;
	}

	function active_receta_filters(patient) {
		const filters = {
			status: ["in", ["Nueva", "Parcialmente Dispensada"]],
			valid_till: [">=", frappe.datetime.get_today()],
		};
		if (patient) {
			filters.patient = patient;
		}
		return filters;
	}

	function set_frm_value(cart, fieldname, value) {
		const frm = get_cart_frm(cart);
		if (!frm) {
			return Promise.resolve();
		}
		return frappe.model.set_value(frm.doc.doctype, frm.doc.name, fieldname, value || "");
	}

	function trigger_receta_handler(cart) {
		const frm = get_cart_frm(cart);
		if (!frm || frm.doc.__islocal || !frm.doc.custom_receta_medica) {
			return;
		}
		frm.script_manager.trigger("custom_receta_medica", frm.doc.doctype, frm.doc.name);
	}

	function receta_badge_html() {
		return `<div class="bf-pos-receta-badge">${__("Receta retenida")}</div>`;
	}

	function get_receta_mount_parent(cart) {
		if (!cart.$customer_section?.length) return null;
		const $details = cart.$customer_section.find(".customer-details");
		if ($details.length) return $details;
		return cart.$customer_section;
	}

	function patchItemSelector() {
		const klass = erpnext?.PointOfSale?.ItemSelector;
		if (!klass || klass[PATCH.selector]) return !!klass;

		const originalRenderList = klass.prototype.render_item_list;
		klass.prototype.render_item_list = function (items) {
			(items || []).forEach(cache_item_flags);
			originalRenderList.call(this, items);
			decorate_grid_receta_badges(this);
		};

		const originalGetHtml = klass.prototype.get_item_html;
		klass.prototype.get_item_html = function (item) {
			cache_item_flags(item);
			const html = originalGetHtml.call(this, item);
			if (!item_data_requires_receta(item)) {
				return html;
			}
			return html.replace(
				/<div class="item-wrapper"([^>]*)>/,
				`<div class="item-wrapper"$1>${receta_badge_html()}`
			);
		};

		// ERPNext load_items_data no espera get_items; eso desincroniza freeze_count con el
		// onchange de cliente (freeze + get_items(freeze:true) + unfreeze prematuro).
		const originalLoadItems = klass.prototype.load_items_data;
		klass.prototype.load_items_data = async function (...args) {
			await this.item_ready_group;

			this.start_item_loading_animation();

			if (!this.price_list) {
				const res = await frappe.db.get_value(
					"POS Profile",
					this.pos_profile,
					"selling_price_list"
				);
				this.price_list = res.message.selling_price_list;
			}

			try {
				const { message } = await this.get_items({});
				this.render_item_list(message.items);
			} finally {
				this.stop_item_loading_animation();
			}
		};

		klass[PATCH.selector] = true;
		return true;
	}

	function patchItemCart() {
		const klass = erpnext?.PointOfSale?.ItemCart;
		if (!klass || klass[PATCH.cart]) return !!klass;

		klass.prototype.ensure_receta_mount = function () {
			const $parent = get_receta_mount_parent(this);
			if (!$parent?.length) return null;

			let $mount = $parent.find(".bf-receta-mount");
			if (!$mount.length) {
				$parent.append(`
					<div class="bf-receta-mount">
						<div class="bf-receta-fields-label">${__("Receta y paciente")}</div>
						<div class="bf-receta-banner hidden"></div>
						<div class="bf-receta-field custom_patient-field"></div>
						<div class="bf-receta-field custom_receta_medica-field"></div>
						<div class="bf-receta-summary hidden"></div>
					</div>
				`);
				$mount = $parent.find(".bf-receta-mount");
			}
			this.$receta_mount = $mount;
			return $mount;
		};

		klass.prototype.make_receta_fields_section = function () {
			if (!get_cart_frm(this)) {
				return;
			}

			const $mount = this.ensure_receta_mount();
			if (!$mount?.length) return;

			if (!this.receta_controls) {
				const me = this;
				this.receta_controls = {};

				RECETA_FIELDS.forEach((df) => {
					const get_query =
						df.fieldname === "custom_receta_medica"
							? function () {
									const frm = get_cart_frm(me);
									const patient =
										me.receta_controls.custom_patient?.get_value?.() ||
										frm?.doc?.custom_patient;
									return { filters: active_receta_filters(patient) };
							  }
							: undefined;

					me.receta_controls[df.fieldname] = frappe.ui.form.make_control({
						df: {
							...df,
							get_query,
							onchange: function () {
								const value = this.value || "";
								set_frm_value(me, df.fieldname, value).then(() => {
									const frm = get_cart_frm(me);
									if (!frm) return;
									if (df.fieldname === "custom_patient") {
										return frm.script_manager
											.trigger("custom_patient", frm.doc.doctype, frm.doc.name)
											.then(() => {
												me.sync_receta_controls_from_frm();
												me.clear_receta_summary();
												me.update_receta_banner();
											});
									}
									if (df.fieldname === "custom_receta_medica") {
										trigger_receta_handler(me);
										me.load_receta_summary(value);
										me.update_receta_banner();
									}
								});
							},
						},
						parent: $mount.find(`.${df.fieldname}-field`),
						render_input: true,
					});
					me.receta_controls[df.fieldname].toggle_label(true);
				});

				if (!barriofarma_app.pos._receta_form_listeners) {
					barriofarma_app.pos._receta_form_listeners = true;
					frappe.ui.form.on("POS Invoice", "custom_patient", () => {
						window.cur_pos?.cart?.sync_receta_controls_from_frm?.();
						window.cur_pos?.cart?.update_receta_banner?.();
					});
					frappe.ui.form.on("POS Invoice", "custom_receta_medica", () => {
						window.cur_pos?.cart?.sync_receta_controls_from_frm?.();
						const receta = window.cur_pos?.frm?.doc?.custom_receta_medica;
						window.cur_pos?.cart?.load_receta_summary?.(receta);
						window.cur_pos?.cart?.update_receta_banner?.();
					});
					frappe.ui.form.on("POS Invoice", "items", () => {
						window.cur_pos?.cart?.update_receta_banner?.();
					});
				}
			}

			this.sync_receta_controls_from_frm();
			const frm = get_cart_frm(this);
			if (frm?.doc?.custom_receta_medica) {
				this.load_receta_summary(frm.doc.custom_receta_medica);
			}
		};

		klass.prototype.sync_receta_controls_from_frm = function () {
			if (!this.receta_controls) return;
			const frm = get_cart_frm(this);
			if (!frm) return;
			RECETA_FIELDS.forEach((df) => {
				const control = this.receta_controls[df.fieldname];
				if (!control) return;
				const doc_value = frm.doc[df.fieldname] || "";
				if (control.get_value() !== doc_value) {
					control.set_value(doc_value);
				}
			});
		};

		klass.prototype.cart_has_receta_retenida_items = async function () {
			const frm = get_cart_frm(this);
			if (!frm) return false;
			for (const row of frm.doc.items || []) {
				await cache_item_flag_for_code(row.item_code);
				if (item_requires_receta(row.item_code)) {
					return true;
				}
			}
			return false;
		};

		klass.prototype.update_receta_banner = function () {
			if (!this.$receta_mount?.length) {
				this.make_receta_fields_section();
			}

			const $banner = this.$receta_mount?.find(".bf-receta-banner");
			if (!$banner?.length) return;

			const frm = get_cart_frm(this);
			if (!frm) return;

			const needs_receta = (frm.doc.items || []).some((row) =>
				item_requires_receta(row.item_code)
			);
			const has_receta = !!frm.doc.custom_receta_medica;

			if (needs_receta && !has_receta) {
				$banner
					.removeClass("hidden")
					.html(
						__(
							"Hay productos de receta retenida en el carrito. Complete Paciente y Receta Medica."
						)
					);
			} else {
				$banner.addClass("hidden").html("");
			}
		};

		klass.prototype.clear_receta_summary = function () {
			const $summary = this.$receta_mount?.find(".bf-receta-summary");
			if ($summary?.length) {
				$summary.addClass("hidden").empty();
			}
		};

		klass.prototype.render_receta_summary = function (data) {
			const $summary = this.ensure_receta_mount()?.find(".bf-receta-summary");
			if (!$summary?.length || !data) {
				return;
			}

			const rows = (data.items || [])
				.map(
					(row) => `
				<tr>
					<td class="bf-receta-item-name" title="${frappe.utils.escape_html(row.item_name || row.item || "")}">
						<span class="bf-receta-item-code">${frappe.utils.escape_html(row.item || "")}</span>
						${frappe.utils.escape_html(row.item_name || "")}
					</td>
					<td class="text-right">${row.quantity ?? ""}</td>
					<td class="text-right">${row.dispensed_qty ?? ""}</td>
					<td class="text-right">${row.pending_qty ?? ""}</td>
				</tr>`
				)
				.join("");

			$summary
				.removeClass("hidden")
				.html(`
				<div class="bf-receta-summary-meta">
					<div><span class="bf-receta-meta-label">${__("Valida hasta")}:</span> ${frappe.utils.escape_html(data.valid_till_display || data.valid_till || "")}</div>
					<div><span class="bf-receta-meta-label">${__("Dispensaciones")}:</span> ${data.dispensation_count ?? 0} / ${data.max_dispensations ?? 0}</div>
				</div>
				<div class="bf-receta-summary-table-wrap">
					<table class="bf-receta-summary-table">
						<thead>
							<tr>
								<th>${__("Medicamento")}</th>
								<th class="text-right">${__("Prescrito")}</th>
								<th class="text-right">${__("Entregado")}</th>
								<th class="text-right">${__("Pendiente")}</th>
							</tr>
						</thead>
						<tbody>${rows || `<tr><td colspan="4">${__("Sin medicamentos")}</td></tr>`}</tbody>
					</table>
				</div>
			`);
		};

		klass.prototype.load_receta_summary = async function (receta_name) {
			if (!receta_name) {
				this.clear_receta_summary();
				return;
			}
			try {
				const { message } = await frappe.call({
					method:
						"barriofarma_app.barriofarma_app.api.receta_medica.get_receta_medica_pos_summary_api",
					args: { receta_name },
				});
				this.render_receta_summary(message);
			} catch (e) {
				console.error("BarrioFarma POS: receta summary", e);
				this.clear_receta_summary();
			}
		};

		klass.prototype.ensure_receta_before_checkout = async function () {
			this.make_receta_fields_section();
			const frm = get_cart_frm(this);
			if (!frm) return true;
			if (!(await this.cart_has_receta_retenida_items())) {
				return true;
			}
			if (frm.doc.custom_receta_medica) {
				return true;
			}

			this.update_receta_banner();
			frappe.msgprint({
				title: __("Receta Requerida"),
				indicator: "red",
				message: __(
					"Complete Paciente y Receta Medica en el panel superior del carrito antes de Pedido."
				),
			});
			this.receta_controls?.custom_receta_medica?.set_focus?.();
			return false;
		};

		const originalMakeCustomer = klass.prototype.make_customer_selector;
		klass.prototype.make_customer_selector = function () {
			originalMakeCustomer.call(this);
			this.make_receta_fields_section();
		};

		const originalUpdateCustomer = klass.prototype.update_customer_section;
		klass.prototype.update_customer_section = function () {
			originalUpdateCustomer.call(this);
			this.receta_controls = null;
			this.$receta_mount = null;
			this.make_receta_fields_section();
			clear_stale_pos_freeze();
		};

		const originalLoadInvoice = klass.prototype.load_invoice;
		klass.prototype.load_invoice = function () {
			originalLoadInvoice.call(this);
			this.receta_controls = null;
			this.$receta_mount = null;
			this.make_receta_fields_section();
		};

		const originalRenderCartItem = klass.prototype.render_cart_item;
		klass.prototype.render_cart_item = function (item_data, $item_to_update) {
			originalRenderCartItem.call(this, item_data, $item_to_update);
			cache_item_flag_for_code(item_data.item_code).then(() => {
				const $item = this.get_cart_item(item_data);
				$item.find(".bf-pos-receta-badge").remove();
				if (item_requires_receta(item_data.item_code)) {
					const $image = $item.find(".item-image").first();
					if ($image.length) {
						$image.css("position", "relative");
						$image.prepend(receta_badge_html());
					} else {
						$item.find(".item-name").append(receta_badge_html());
					}
				}
				this.update_receta_banner();
			});
		};

		const originalResetCustomer = klass.prototype.reset_customer_selector;
		klass.prototype.reset_customer_selector = function () {
			originalResetCustomer.call(this);
			set_frm_value(this, "custom_patient", "").then(() => {
				set_frm_value(this, "custom_receta_medica", "").then(() => {
					this.sync_receta_controls_from_frm();
					this.update_receta_banner();
				});
			});
		};

		klass[PATCH.cart] = true;
		return true;
	}

	function patchPayment() {
		const klass = erpnext?.PointOfSale?.Payment;
		if (!klass || klass[PATCH.payment]) return !!klass;

		const originalRender = klass.prototype.render_payment_section;
		klass.prototype.render_payment_section = async function () {
			if (!this.invoice_fields?.length) {
				try {
					const pos_settings = await frappe.db.get_doc("POS Settings", undefined);
					this.invoice_fields = (pos_settings.invoice_fields || []).map((field) => ({
						fieldname: field.fieldname,
						label: field.label,
						fieldtype: field.fieldtype,
						reqd: field.reqd,
						options: field.options,
						default_value: field.default_value,
						read_only: field.read_only,
					}));
				} catch (e) {
					console.error("POS receta fields: invoice_fields", e);
				}
			}
			return originalRender.call(this);
		};

		klass[PATCH.payment] = true;
		return true;
	}

	function clear_stale_pos_freeze() {
		if (frappe.dom.freeze_count > 0) {
			frappe.dom.freeze_count = 0;
			$("#freeze").removeClass("in").remove();
		}
	}

	function patchController() {
		const klass = erpnext?.PointOfSale?.Controller;
		if (!klass || klass[PATCH.controller]) return !!klass;

		const originalMakeApp = klass.prototype.make_app;
		klass.prototype.make_app = function () {
			originalMakeApp.call(this);
			setTimeout(() => {
				refreshPosRecetaUi();
			}, 0);
		};

		const originalOnCartUpdate = klass.prototype.on_cart_update;
		klass.prototype.on_cart_update = async function (...args) {
			if (!this.frm?.doc) {
				return;
			}
			try {
				return await originalOnCartUpdate.apply(this, args);
			} finally {
				setTimeout(clear_stale_pos_freeze, 0);
			}
		};

		const originalInitItemCart = klass.prototype.init_item_cart;
		klass.prototype.init_item_cart = function () {
			originalInitItemCart.call(this);
			const controller = this;
			const cart = this.cart;
			if (!cart?.events) {
				return;
			}
			cart.events.customer_details_updated = async function (details) {
				await controller.item_selector.load_items_data();
				controller.customer_details = details;
				controller.payment.render_loyalty_points_payment_mode();
			};
		};

		const originalSaveCheckout = klass.prototype.save_and_checkout;
		klass.prototype.save_and_checkout = async function () {
			if (
				this.cart?.ensure_receta_before_checkout &&
				!(await this.cart.ensure_receta_before_checkout())
			) {
				this.cart.toggle_checkout_btn(true);
				return;
			}
			return originalSaveCheckout.call(this);
		};

		const originalUpdateItem = klass.prototype.update_cart_html;
		if (originalUpdateItem) {
			klass.prototype.update_cart_html = function (item_row, remove_item) {
				const result = originalUpdateItem.call(this, item_row, remove_item);
				if (this.frm?.doc) {
					this.cart?.update_receta_banner?.();
				}
				return result;
			};
		}

		klass[PATCH.controller] = true;
		return true;
	}

	function applyPatches() {
		try {
			patchItemSelector();
			patchItemCart();
			patchPayment();
			patchController();
		} catch (e) {
			console.error("BarrioFarma POS receta UI patch failed", e);
		}
	}

	function refreshPosRecetaUi() {
		const item_selector = window.cur_pos?.item_selector;
		if (item_selector) {
			refresh_grid_receta_badges(item_selector);
		}
		if (window.cur_pos?.frm?.doc) {
			window.cur_pos?.cart?.make_receta_fields_section?.();
		}
	}

	function bootPosRecetaUi() {
		applyPatches();
		refreshPosRecetaUi();
		setTimeout(refreshPosRecetaUi, 0);
		setTimeout(refreshPosRecetaUi, 300);
	}

	if (frappe.require) {
		frappe.require("point-of-sale.bundle.js", bootPosRecetaUi);
	} else {
		bootPosRecetaUi();
	}

	const page = frappe.pages["point-of-sale"];
	if (page && !page._bf_receta_wrapped) {
		page._bf_receta_wrapped = true;
		const previous_on_page_load = page.on_page_load;
		page.on_page_load = function (wrapper) {
			if (previous_on_page_load) {
				previous_on_page_load(wrapper);
			}
			setTimeout(bootPosRecetaUi, 0);
			setTimeout(bootPosRecetaUi, 500);
		};
	}
})();
