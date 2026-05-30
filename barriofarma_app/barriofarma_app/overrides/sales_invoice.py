# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Override del DocType Sales Invoice para:
1. Validar disponibilidad de stock en tiempo real (FR22)
2. Validar datos mínimos de cliente/paciente según normativa (FR26)
3. Validar límites de descuento por rol (FR27)
4. Validar que no se vendan productos vencidos (FR12)
5. Validar trazabilidad completa (lote y caducidad) para productos que lo requieren (FR37)
6. Validar y registrar cambios en control level con auditoría (FR25, FR40)
7. Registrar automáticamente Shelf Movement al realizar ventas
"""

import frappe
from frappe import _
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice as ERPNextSalesInvoice
from datetime import datetime
from barriofarma_app.barriofarma_app.validations.expired_products import validate_expired_products_in_invoice
from barriofarma_app.barriofarma_app.validations.traceability import validate_batch_required_for_sale
from barriofarma_app.barriofarma_app.validations.stock_availability import validate_stock_availability
from barriofarma_app.barriofarma_app.validations.patient_data import validate_patient_data_required
from barriofarma_app.barriofarma_app.validations.discount_limits import validate_discount_limits
from barriofarma_app.barriofarma_app.validations.returns import (
	validate_return_requirements,
	validate_return_permissions
)
from barriofarma_app.barriofarma_app.validations.receta_medica_validation import (
	validate_receta_medica_validity,
	update_receta_medica_dispensation
)
from barriofarma_app.barriofarma_app.utils.shelf_movement_submit import insert_and_submit_shelf_movement
from barriofarma_app.barriofarma_app.utils.domain.control_level_audit import (
	validate_control_level_change_reason,
	detect_and_log_control_level_changes
)


class SalesInvoice(ERPNextSalesInvoice):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from erpnext.accounts.doctype.payment_schedule.payment_schedule import PaymentSchedule
		from erpnext.accounts.doctype.pricing_rule_detail.pricing_rule_detail import PricingRuleDetail
		from erpnext.accounts.doctype.sales_invoice_advance.sales_invoice_advance import SalesInvoiceAdvance
		from erpnext.accounts.doctype.sales_invoice_item.sales_invoice_item import SalesInvoiceItem
		from erpnext.accounts.doctype.sales_invoice_payment.sales_invoice_payment import SalesInvoicePayment
		from erpnext.accounts.doctype.sales_invoice_timesheet.sales_invoice_timesheet import SalesInvoiceTimesheet
		from erpnext.accounts.doctype.sales_taxes_and_charges.sales_taxes_and_charges import SalesTaxesandCharges
		from erpnext.selling.doctype.sales_team.sales_team import SalesTeam
		from erpnext.stock.doctype.packed_item.packed_item import PackedItem
		from frappe.types import DF

		account_for_change_amount: DF.Link | None
		additional_discount_account: DF.Link | None
		additional_discount_percentage: DF.Float
		address_display: DF.SmallText | None
		advances: DF.Table[SalesInvoiceAdvance]
		against_income_account: DF.SmallText | None
		allocate_advances_automatically: DF.Check
		amended_from: DF.Link | None
		amount_eligible_for_commission: DF.Currency
		apply_discount_on: DF.Literal["", "Grand Total", "Net Total"]
		auto_repeat: DF.Link | None
		base_change_amount: DF.Currency
		base_discount_amount: DF.Currency
		base_grand_total: DF.Currency
		base_in_words: DF.SmallText | None
		base_net_total: DF.Currency
		base_paid_amount: DF.Currency
		base_rounded_total: DF.Currency
		base_rounding_adjustment: DF.Currency
		base_total: DF.Currency
		base_total_taxes_and_charges: DF.Currency
		base_write_off_amount: DF.Currency
		campaign: DF.Link | None
		cash_bank_account: DF.Link | None
		change_amount: DF.Currency
		commission_rate: DF.Float
		company: DF.Link
		company_address: DF.Link | None
		company_address_display: DF.SmallText | None
		company_contact_person: DF.Link | None
		company_tax_id: DF.Data | None
		contact_display: DF.SmallText | None
		contact_email: DF.Data | None
		contact_mobile: DF.SmallText | None
		contact_person: DF.Link | None
		conversion_rate: DF.Float
		cost_center: DF.Link | None
		currency: DF.Link
		customer: DF.Link | None
		customer_address: DF.Link | None
		customer_group: DF.Link | None
		customer_name: DF.SmallText | None
		debit_to: DF.Link
		disable_rounded_total: DF.Check
		discount_amount: DF.Currency
		dispatch_address: DF.SmallText | None
		dispatch_address_name: DF.Link | None
		due_date: DF.Date | None
		from_date: DF.Date | None
		grand_total: DF.Currency
		group_same_items: DF.Check
		ignore_default_payment_terms_template: DF.Check
		ignore_pricing_rule: DF.Check
		in_words: DF.SmallText | None
		incoterm: DF.Link | None
		inter_company_invoice_reference: DF.Link | None
		is_cash_or_non_trade_discount: DF.Check
		is_consolidated: DF.Check
		is_debit_note: DF.Check
		is_discounted: DF.Check
		is_internal_customer: DF.Check
		is_opening: DF.Literal["No", "Yes"]
		is_pos: DF.Check
		is_return: DF.Check
		items: DF.Table[SalesInvoiceItem]
		language: DF.Data | None
		letter_head: DF.Link | None
		loyalty_amount: DF.Currency
		loyalty_points: DF.Int
		loyalty_program: DF.Link | None
		loyalty_redemption_account: DF.Link | None
		loyalty_redemption_cost_center: DF.Link | None
		named_place: DF.Data | None
		naming_series: DF.Literal["ACC-SINV-.YYYY.-", "ACC-SINV-RET-.YYYY.-"]
		net_total: DF.Currency
		only_include_allocated_payments: DF.Check
		other_charges_calculation: DF.TextEditor | None
		outstanding_amount: DF.Currency
		packed_items: DF.Table[PackedItem]
		paid_amount: DF.Currency
		party_account_currency: DF.Link | None
		payment_schedule: DF.Table[PaymentSchedule]
		payment_terms_template: DF.Link | None
		payments: DF.Table[SalesInvoicePayment]
		plc_conversion_rate: DF.Float
		po_date: DF.Date | None
		po_no: DF.Data | None
		pos_profile: DF.Link | None
		posting_date: DF.Date
		posting_time: DF.Time | None
		price_list_currency: DF.Link
		pricing_rules: DF.Table[PricingRuleDetail]
		project: DF.Link | None
		redeem_loyalty_points: DF.Check
		remarks: DF.SmallText | None
		represents_company: DF.Link | None
		return_against: DF.Link | None
		rounded_total: DF.Currency
		rounding_adjustment: DF.Currency
		sales_partner: DF.Link | None
		sales_team: DF.Table[SalesTeam]
		scan_barcode: DF.Data | None
		select_print_heading: DF.Link | None
		selling_price_list: DF.Link
		set_posting_time: DF.Check
		set_target_warehouse: DF.Link | None
		set_warehouse: DF.Link | None
		shipping_address: DF.SmallText | None
		shipping_address_name: DF.Link | None
		shipping_rule: DF.Link | None
		source: DF.Link | None
		status: DF.Literal["", "Draft", "Return", "Credit Note Issued", "Submitted", "Paid", "Partly Paid", "Unpaid", "Unpaid and Discounted", "Partly Paid and Discounted", "Overdue and Discounted", "Overdue", "Cancelled", "Internal Transfer"]
		subscription: DF.Link | None
		tax_category: DF.Link | None
		tax_id: DF.Data | None
		taxes: DF.Table[SalesTaxesandCharges]
		taxes_and_charges: DF.Link | None
		tc_name: DF.Link | None
		terms: DF.TextEditor | None
		territory: DF.Link | None
		timesheets: DF.Table[SalesInvoiceTimesheet]
		title: DF.Data | None
		to_date: DF.Date | None
		total: DF.Currency
		total_advance: DF.Currency
		total_billing_amount: DF.Currency
		total_billing_hours: DF.Float
		total_commission: DF.Currency
		total_net_weight: DF.Float
		total_qty: DF.Float
		total_taxes_and_charges: DF.Currency
		unrealized_profit_loss_account: DF.Link | None
		update_billed_amount_in_delivery_note: DF.Check
		update_billed_amount_in_sales_order: DF.Check
		update_outstanding_for_self: DF.Check
		update_stock: DF.Check
		use_company_roundoff_cost_center: DF.Check
		write_off_account: DF.Link | None
		write_off_amount: DF.Currency
		write_off_cost_center: DF.Link | None
		write_off_outstanding_amount_automatically: DF.Check
	# end: auto-generated types
	"""
	Extensión de la clase Sales Invoice de ERPNext para:
	- Validar disponibilidad de stock en tiempo real (FR22)
	- Validar datos mínimos de cliente/paciente según normativa (FR26)
	- Validar límites de descuento por rol (FR27)
	- Validar que no se vendan productos vencidos (FR12)
	- Validar trazabilidad completa (lote y caducidad) para productos que lo requieren (FR37)
	- Validar y registrar cambios en control level con auditoría (FR25, FR40)
	- Validar devoluciones de productos vendidos (Story 4.5)
	- Validar vigencia de receta médica y que todos los items de receta estén incluidos (Story 5.2, 5.3)
	- Registrar automáticamente movimientos de tipo "Venta" en Shelf Movement
	"""

	def before_validate(self):
		if self.company:
			company_currency = frappe.db.get_value("Company", self.company, "default_currency")
			if company_currency:
				self.currency = company_currency
				self.conversion_rate = 1
		if not self.get("is_return"):
			validate_batch_required_for_sale(self)
	
	def validate(self):
		"""
		Validar invariantes del dominio farmacéutico antes de guardar
		"""
		if not self.get("is_return"):
			validate_batch_required_for_sale(self)
		super().validate()
		
		# Story 4.5: Validar devoluciones (solo si is_return = 1)
		if self.get("is_return"):
			validate_return_permissions(self)
			validate_return_requirements(self)
		else:
			# Validaciones para ventas normales (no devoluciones)
			# Story 5.2: Validar vigencia de receta médica
			validate_receta_medica_validity(self)
			# FR22: Validar disponibilidad de stock en tiempo real
			validate_stock_availability(self)
			# FR26: Validar datos mínimos de cliente/paciente según normativa
			validate_patient_data_required(self)
			# FR27: Validar límites de descuento por rol
			validate_discount_limits(self)
			# FR12: Validar que no se vendan productos vencidos
			validate_expired_products_in_invoice(self)
			# FR37: Validar trazabilidad completa (lote y caducidad)
			validate_batch_required_for_sale(self)
			# FR25, FR40: Validar que cambios en control level tengan motivo
			validate_control_level_change_reason(self)
	
	def on_submit(self):
		"""
		Registrar Shelf Movement automáticamente y auditoría de cambios en control level
		cuando se envía Sales Invoice
		"""
		super().on_submit()
		# Story 5.2: Actualizar dispensación de receta
		update_receta_medica_dispensation(self)
		# FR25, FR40: Registrar cambios en control level con auditoría
		detect_and_log_control_level_changes(self)
		# Registrar Shelf Movement automáticamente
		# Nota: Se ejecuta después de super().on_submit() para que el stock ya esté actualizado
		frappe.db.commit()  # Asegurar que el stock esté persistido antes de crear Shelf Movement
		self.create_shelf_movements_from_sale()
	
	def create_shelf_movements_from_sale(self):
		"""
		Crear registros de Shelf Movement tipo "Venta" basados en los items vendidos
		"""
		if not self.items:
			return
		
		for item in self.items:
			item_code = item.item_code
			warehouse = item.warehouse or self.set_warehouse
			quantity = item.qty
			
			if not item_code or not warehouse:
				continue
			
			# Obtener shelves del item en el warehouse de la venta
			shelves = self._get_item_shelves_in_warehouse(item_code, warehouse)
			
			# Si el item tiene shelves asignados, crear movimiento de venta para cada shelf
			# Distribuir la cantidad proporcionalmente o usar el primer shelf
			if shelves:
				# Por ahora, usar el primer shelf disponible para simplificar
				# En el futuro se podría implementar lógica más sofisticada
				primary_shelf = shelves[0]
				self._create_shelf_movement_venta(
					shelf=primary_shelf,
					item_code=item_code,
					quantity=quantity
				)
	
	def _get_item_shelves_in_warehouse(self, item_code, warehouse):
		"""
		Obtener lista de shelves donde está asignado el item en el warehouse especificado
		
		Args:
			item_code: Código del item
			warehouse: Nombre del warehouse
		
		Returns:
			Lista de nombres de shelves
		"""
		if not frappe.db.exists("Item", item_code):
			return []
		
		item_doc = frappe.get_doc("Item", item_code)
		
		# Verificar si el item tiene custom_shelf_locations
		if not hasattr(item_doc, "custom_shelf_locations") or not item_doc.custom_shelf_locations:
			return []
		
		shelves = []
		for shelf_location in item_doc.custom_shelf_locations:
			shelf_name = shelf_location.get("shelf")
			if shelf_name and frappe.db.exists("Shelf", shelf_name):
				# Verificar que el shelf pertenece al warehouse de la venta
				shelf_doc = frappe.get_doc("Shelf", shelf_name)
				if shelf_doc.warehouse == warehouse:
					shelves.append(shelf_name)
		
		return shelves
	
	def _create_shelf_movement_venta(self, shelf, item_code, quantity):
		"""
		Crear registro de Shelf Movement tipo "Venta"
		
		Args:
			shelf: Nombre del shelf
			item_code: Código del item
			quantity: Cantidad vendida
		"""
		try:
			movement = frappe.get_doc({
				"doctype": "Shelf Movement",
				"movement_type": "Venta",
				"shelf": shelf,
				"item": item_code,
				"quantity": quantity,
				"movement_date": self.posting_date or datetime.now(),
				"reference_doctype": "Sales Invoice",
				"reference_name": self.name,
				"notes": f"Movimiento automático desde Sales Invoice {self.name}"
			})
			
			insert_and_submit_shelf_movement(movement)
		except Exception as e:
			frappe.log_error(
				message=f"Error al crear Shelf Movement desde Sales Invoice {self.name}: {str(e)}",
				title="Error en Shelf Movement"
			)
			# No lanzar excepción para no bloquear el submit del Sales Invoice
			# pero registrar el error para debugging

