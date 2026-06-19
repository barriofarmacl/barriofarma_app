// BarrioFarma: User.time_zone limitado a America/* (Autocomplete).
frappe.provide("barriofarma_app.user_timezone");

const AMERICA_PREFIX = "America/";

function barriofarma_americas_timezones(all) {
	return (all || []).filter((tz) => tz.startsWith(AMERICA_PREFIX)).sort();
}

function barriofarma_apply_user_timezone_options(frm) {
	if (!frm.fields_dict.time_zone) {
		return;
	}
	const apply = () => {
		const america = barriofarma_americas_timezones(frappe.all_timezones);
		if (america.length) {
			frm.fields_dict.time_zone.set_data(america);
		}
	};
	if (frappe.all_timezones) {
		apply();
		return;
	}
	frappe.call({
		method: "frappe.core.doctype.user.user.get_timezones",
		callback(r) {
			frappe.all_timezones = r.message.timezones;
			apply();
		},
	});
}

frappe.ui.form.on("User", {
	onload(frm) {
		barriofarma_apply_user_timezone_options(frm);
	},
	refresh(frm) {
		barriofarma_apply_user_timezone_options(frm);
	},
});
