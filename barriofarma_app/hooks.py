app_name = "barriofarma_app"
app_title = "Barriofarma App"
app_publisher = "eaa"
app_description = "frontend para farmacias barriofarma"
app_email = "eduardo.araya@barriofarma.cl"
app_license = "mit"
# required_apps = []

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/barriofarma_app/css/barriofarma_app.css"
app_include_js = [
	"/assets/barriofarma_app/js/pos_shelf_info.js",
	"/assets/barriofarma_app/js/barriofarma_number_card_clp.js",
]

# include js, css files in header of web template
# web_include_css = "/assets/barriofarma_app/css/barriofarma_app.css"
# web_include_js = "/assets/barriofarma_app/js/barriofarma_app.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "barriofarma_app/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
page_js = {
	"stock-balance": "public/js/stock_balance_move_item.js",
}

# include js in doctype views
doctype_js = {
	"Stock Reconciliation": "public/js/stock_reconciliation_shelf.js",
	"Purchase Receipt": "public/js/purchase_receipt_shelf.js",
	"Stock Entry": "public/js/stock_entry_shelf.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "barriofarma_app/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# (Print Format boleta SII vive en la app ``pagosbf`` cuando esta instalada.)

# Installation
# ------------

# before_install = "barriofarma_app.install.before_install"
# after_install = "barriofarma_app.install.after_install"

# Story 8.1: Refinamiento de Gestión de Usuarios y Roles
# Configurar roles y permisos personalizados después de cada migración
after_migrate = "barriofarma_app.barriofarma_app.install.after_migrate"

# Fixtures
# --------
# Fixtures are documents or records that are automatically created/imported
# when installing the app or when running `bench --site [sitename] migrate`
# Custom Fields para DocType Item (DDD)
# Los fixtures ya están exportados en fixtures/custom_field.json
# Se importan automáticamente durante bench migrate
# Client Scripts para funcionalidades de UI (ej: auto-fill de barcode)
fixtures = ["Custom Field", "Client Script", "Report", "Property Setter"]

# Uninstallation
# ------------

# before_uninstall = "barriofarma_app.uninstall.before_uninstall"
# after_uninstall = "barriofarma_app.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "barriofarma_app.utils.before_app_install"
# after_app_install = "barriofarma_app.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "barriofarma_app.utils.before_app_uninstall"
# after_app_uninstall = "barriofarma_app.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "barriofarma_app.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Item": "barriofarma_app.barriofarma_app.overrides.item.Item",
	"Purchase Receipt": "barriofarma_app.barriofarma_app.overrides.purchase_receipt.PurchaseReceipt",
	"Stock Entry": "barriofarma_app.barriofarma_app.overrides.stock_entry.StockEntry",
	"Sales Invoice": "barriofarma_app.barriofarma_app.overrides.sales_invoice.SalesInvoice",
	"POS Invoice": "barriofarma_app.barriofarma_app.overrides.pos_invoice.POSInvoice",
	"Stock Reconciliation": "barriofarma_app.barriofarma_app.overrides.stock_reconciliation.StockReconciliation",
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"POS Invoice": {
		"validate": [
			"barriofarma_app.barriofarma_app.validations.receta_medica_validation.validate_receta_medica_validity",
			"barriofarma_app.barriofarma_app.validations.stock_availability.validate_stock_availability",
			"barriofarma_app.barriofarma_app.validations.patient_data.validate_patient_data_required",
			"barriofarma_app.barriofarma_app.validations.discount_limits.validate_discount_limits",
			"barriofarma_app.barriofarma_app.validations.expired_products.validate_expired_products_in_invoice",
			"barriofarma_app.barriofarma_app.validations.traceability.validate_batch_required_for_sale",
			"barriofarma_app.barriofarma_app.utils.domain.control_level_audit.validate_control_level_change_reason_doc_event",
		],
		"on_submit": [
			"barriofarma_app.barriofarma_app.validations.receta_medica_validation.update_receta_medica_dispensation",
			"barriofarma_app.barriofarma_app.utils.domain.control_level_audit.detect_and_log_control_level_changes_doc_event",
		],
	}
}

# Scheduled Tasks
# ---------------
# Story 6.2: Alertas de Productos Próximos a Caducar

scheduler_events = {
	"daily": [
		"barriofarma_app.barriofarma_app.tasks.expiry_alerts.check_expiring_products"
	]
}

# Testing
# -------

before_tests = "barriofarma_app.barriofarma_app.install.before_tests"

# Overriding Methods
# ------------------------------
override_whitelisted_methods = {
	"erpnext.stock.doctype.purchase_receipt.purchase_receipt.make_purchase_invoice": "barriofarma_app.barriofarma_app.overrides.purchase_receipt.make_purchase_invoice"
}

# API Whitelist
# -------------
# Story 6.2: Alertas de Productos Próximos a Caducar
whitelisted_methods = {
	"barriofarma_app.barriofarma_app.api.expiry_alerts.get_expiry_alerts_summary": ["System Manager", "Stock Manager", "Stock User"],
	"barriofarma_app.barriofarma_app.api.expiry_alerts.get_item_expiry_status": ["System Manager", "Stock Manager", "Stock User"]
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "barriofarma_app.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["barriofarma_app.utils.before_request"]
# after_request = ["barriofarma_app.utils.after_request"]

# Job Events
# ----------
# before_job = ["barriofarma_app.utils.before_job"]
# after_job = ["barriofarma_app.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"barriofarma_app.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }


website_route_rules = [{'from_route': '/inicio/<path:app_path>', 'to_route': 'inicio'},]