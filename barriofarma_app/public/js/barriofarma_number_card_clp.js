// BarrioFarma: fix Number Card CLP (#.###) — cache-bust v2
window.__barriofarma_clp_format_patch = "pending";

(function () {
	function is_abbrev_part(v) {
		return /^\d+\.\d{1,2}$/.test(String(v == null ? "" : v).trim());
	}

	function apply_global_patches() {
		if (typeof window.format_currency !== "function") {
			return false;
		}

		if (!window.__barriofarma_fc_patched) {
			var _format_currency = window.format_currency;
			window.format_currency = function (v, currency, decimals) {
				if (typeof v === "string" && is_abbrev_part(v)) {
					v = flt(v);
				}
				if (currency === "CLP" && typeof v === "number" && v > 0 && v < 1000) {
					v = Math.round(v);
				}
				return _format_currency(v, currency, decimals);
			};
			window.__barriofarma_fc_patched = true;
		}

		if (
			typeof window.convert_old_to_new_number_format === "function" &&
			!window.__barriofarma_convert_patched
		) {
			var _convert = window.convert_old_to_new_number_format;
			window.convert_old_to_new_number_format = function (
				v,
				old_number_format,
				new_number_format
			) {
				if (is_abbrev_part(v)) {
					return String(v).trim();
				}
				return _convert.apply(this, arguments);
			};
			window.__barriofarma_convert_patched = true;
		}

		return true;
	}

	function patch_number_card_widget() {
		if (
			!window.frappe ||
			!frappe.widget ||
			!frappe.widget.widget_factory ||
			!frappe.widget.widget_factory.number_card
		) {
			return false;
		}

		var Widget = frappe.widget.widget_factory.number_card;
		if (!Widget.prototype || Widget.prototype.__barriofarma_nc_patched) {
			return true;
		}

		Widget.prototype.set_formatted_number = function (df) {
			var country = (frappe.sys_defaults && frappe.sys_defaults.country) || "Chile";
			var card = this.card_doc || {};
			var currency = card.currency || frappe.defaults.get_default("currency");
			var parts;
			if (card.show_full_number) {
				parts = [flt(this.number), ""];
			} else {
				parts = String(
					frappe.utils.shorten_number(this.number, country, 5)
				).split(" ");
			}
			var suffix = parts[1] || "";
			var n = flt(parts[0]);
			if ((currency === "CLP" || country === "Chile") && suffix === "K") {
				n = Math.round(n);
			}
			if (currency) {
				this.formatted_number =
					format_currency(n, currency) + (suffix ? " " + __(suffix) : "");
				return;
			}
			if (df && df.fieldtype === "Currency") {
				this.formatted_number =
					format_currency(n, frappe.defaults.get_default("currency")) +
					(suffix ? " " + __(suffix) : "");
				return;
			}
			this.formatted_number =
				format_number(n, get_number_format(), 2) + (suffix ? " " + __(suffix) : "");
		};
		Widget.prototype.__barriofarma_nc_patched = true;
		return true;
	}

	function boot() {
		if (!apply_global_patches()) {
			return false;
		}
		patch_number_card_widget();
		window.__barriofarma_clp_format_patch = true;
		return true;
	}

	if (boot()) {
		return;
	}

	var attempts = 0;
	var timer = setInterval(function () {
		attempts += 1;
		if (boot() || attempts > 100) {
			clearInterval(timer);
		}
	}, 100);

	if (typeof window.jQuery !== "undefined") {
		jQuery(document).on("app_ready startup", boot);
	}
})();
