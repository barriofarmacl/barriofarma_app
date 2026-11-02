// BarrioFarma: llamar al siguiente turno desde el POS (whiteboard #90).
// No modifica erpnext/selling/page/point_of_sale/*: se inyecta via page_js.
//
// Importante: `page.inner_toolbar` es el mismo nodo que `page.custom_actions`.
// POS llama `prepare_menu()` y luego `prepare_btns()`, y este ultimo hace
// `clear_custom_actions()`. El boton visible MUST agregarse en prepare_btns,
// despues del clear; si se agrega en prepare_menu, desaparece.
(() => {
	const PATCH_FLAG = "__barriofarma_pos_turnos_v3";
	const API_LLAMAR = "barriofarma_app.barriofarma_app.api.turnos.llamar_siguiente";
	const API_AUSENTE = "barriofarma_app.barriofarma_app.api.turnos.marcar_ausente";

	let llamadaEnVuelo = false;
	let ausenteEnVuelo = false;

	function mostrarResultadoLlamada(message) {
		const payload = message || {};
		if (payload.cola_vacia) {
			frappe.show_alert({
				message: __("No hay turnos en espera"),
				indicator: "orange",
			});
			return;
		}
		frappe.show_alert({
			message: __("Turno {0}", [payload.numero]),
			indicator: "green",
		});
	}

	function llamarSiguiente() {
		if (llamadaEnVuelo) {
			return;
		}
		llamadaEnVuelo = true;
		frappe.call({
			method: API_LLAMAR,
			freeze: false,
			callback: (response) => mostrarResultadoLlamada(response.message),
			always: () => {
				llamadaEnVuelo = false;
			},
		});
	}

	function marcarAusente() {
		if (ausenteEnVuelo) {
			return;
		}
		ausenteEnVuelo = true;
		frappe.call({
			method: API_AUSENTE,
			freeze: false,
			callback: (response) => {
				const payload = response.message || {};
				if (!payload.ok) {
					frappe.show_alert({
						message: __("No hay un turno en atencion"),
						indicator: "orange",
					});
					return;
				}
				frappe.show_alert({
					message: __("Turno {0} ausente", [payload.numero]),
					indicator: "blue",
				});
			},
			always: () => {
				ausenteEnVuelo = false;
			},
		});
	}

	function patchController() {
		const proto = erpnext?.PointOfSale?.Controller?.prototype;
		if (!proto || proto[PATCH_FLAG]) {
			return Boolean(proto);
		}

		const originalPrepareMenu = proto.prepare_menu;
		proto.prepare_menu = function prepare_menu_with_turnos() {
			originalPrepareMenu.call(this);
			this.page.add_menu_item(__("Cliente ausente"), marcarAusente, false);
			this.page.add_menu_item(__("Llamar siguiente"), llamarSiguiente, false);
		};

		const originalPrepareBtns = proto.prepare_btns;
		proto.prepare_btns = function prepare_btns_with_turnos() {
			originalPrepareBtns.call(this);
			// Despues de clear_custom_actions(): boton visible junto a Recent Orders.
			this.page.add_inner_button(__("Llamar siguiente"), llamarSiguiente);
		};

		proto[PATCH_FLAG] = true;
		return true;
	}

	function applyPosTurnosPatch() {
		return patchController();
	}

	function wrapPointOfSalePageLoad() {
		const page = frappe.pages["point-of-sale"];
		if (!page || page[PATCH_FLAG]) {
			return;
		}

		const originalOnPageLoad = page.on_page_load;
		page.on_page_load = function on_page_load_with_turnos(wrapper) {
			const boot = () => {
				applyPosTurnosPatch();
				originalOnPageLoad(wrapper);
			};

			if (erpnext?.PointOfSale?.Controller) {
				boot();
			} else {
				frappe.require("point-of-sale.bundle.js", boot);
			}
		};

		page[PATCH_FLAG] = true;
	}

	wrapPointOfSalePageLoad();
	frappe.require("point-of-sale.bundle.js", applyPosTurnosPatch);
})();
