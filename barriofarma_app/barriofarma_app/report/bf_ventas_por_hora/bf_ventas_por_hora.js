// Copyright (c) 2026, Barrio Farma and Contributors
// Change: barriofarma-number-cards-platform fase 2

frappe.query_reports["BF Ventas por Hora"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "period",
			label: __("Period"),
			fieldtype: "Select",
			options: ["Today", "Last Week", "Last Month"],
			default: "Last Week",
			reqd: 1,
		},
	],
};
