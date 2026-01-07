// Copyright (c) 2026, Barrio Farma and Contributors
// For license information, please see license.txt

frappe.query_reports["Stock Availability Report"] = {
	"filters": [
		{
			"fieldname": "item_code",
			"label": __("Producto"),
			"fieldtype": "Link",
			"options": "Item",
			"get_query": function() {
				return {
					"filters": {
						"is_stock_item": 1
					}
				};
			}
		},
		{
			"fieldname": "warehouse",
			"label": __("Almacén"),
			"fieldtype": "Link",
			"options": "Warehouse"
		},
		{
			"fieldname": "shelf",
			"label": __("Estante"),
			"fieldtype": "Link",
			"options": "Shelf",
			"get_query": function() {
				return {
					"filters": {
						"warehouse": frappe.query_report.get_filter_value("warehouse")
					}
				};
			}
		},
		{
			"fieldname": "batch_no",
			"label": __("Lote"),
			"fieldtype": "Link",
			"options": "Batch",
			"get_query": function() {
				return {
					"filters": {
						"item": frappe.query_report.get_filter_value("item_code")
					}
				};
			}
		},
		{
			"fieldname": "show_expiring_soon",
			"label": __("Solo Próximos a Caducar"),
			"fieldtype": "Check",
			"default": 0
		},
		{
			"fieldname": "days_to_expiry",
			"label": __("Días hasta Caducidad"),
			"fieldtype": "Int",
			"default": 30,
			"depends_on": "show_expiring_soon"
		},
		{
			"fieldname": "show_low_stock",
			"label": __("Solo Stock Bajo"),
			"fieldtype": "Check",
			"default": 0
		}
	]
};

