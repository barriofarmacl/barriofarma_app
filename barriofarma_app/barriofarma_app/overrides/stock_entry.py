# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Override del DocType Stock Entry para registrar automáticamente Shelf Movement
"""

import frappe
from frappe import _
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry as ERPNextStockEntry
from barriofarma_app.barriofarma_app.utils.shelf_movement_submit import insert_and_submit_shelf_movement
from barriofarma_app.barriofarma_app.utils.shelf_validations import validate_stock_entry_item_shelves
from barriofarma_app.barriofarma_app.utils.shelf_item_location import link_item_to_shelf
from datetime import datetime


class StockEntry(ERPNextStockEntry):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from erpnext.stock.doctype.landed_cost_taxes_and_charges.landed_cost_taxes_and_charges import LandedCostTaxesandCharges
		from erpnext.stock.doctype.stock_entry_detail.stock_entry_detail import StockEntryDetail
		from frappe.types import DF

		add_to_transit: DF.Check
		additional_costs: DF.Table[LandedCostTaxesandCharges]
		address_display: DF.SmallText | None
		amended_from: DF.Link | None
		apply_putaway_rule: DF.Check
		asset_repair: DF.Link | None
		bom_no: DF.Link | None
		company: DF.Link
		credit_note: DF.Link | None
		delivery_note_no: DF.Link | None
		fg_completed_qty: DF.Float
		from_bom: DF.Check
		from_warehouse: DF.Link | None
		inspection_required: DF.Check
		is_opening: DF.Literal["No", "Yes"]
		is_return: DF.Check
		items: DF.Table[StockEntryDetail]
		job_card: DF.Link | None
		letter_head: DF.Link | None
		naming_series: DF.Literal["MAT-STE-.YYYY.-"]
		outgoing_stock_entry: DF.Link | None
		per_transferred: DF.Percent
		pick_list: DF.Link | None
		posting_date: DF.Date | None
		posting_time: DF.Time | None
		process_loss_percentage: DF.Percent
		process_loss_qty: DF.Float
		project: DF.Link | None
		purchase_order: DF.Link | None
		purchase_receipt_no: DF.Link | None
		purpose: DF.Literal["Material Issue", "Material Receipt", "Material Transfer", "Material Transfer for Manufacture", "Material Consumption for Manufacture", "Manufacture", "Repack", "Send to Subcontractor", "Disassemble"]
		remarks: DF.Text | None
		sales_invoice_no: DF.Link | None
		scan_barcode: DF.Data | None
		select_print_heading: DF.Link | None
		set_posting_time: DF.Check
		source_address_display: DF.SmallText | None
		source_warehouse_address: DF.Link | None
		stock_entry_type: DF.Link
		subcontracting_order: DF.Link | None
		supplier: DF.Link | None
		supplier_address: DF.Link | None
		supplier_name: DF.Data | None
		target_address_display: DF.SmallText | None
		target_warehouse_address: DF.Link | None
		to_warehouse: DF.Link | None
		total_additional_costs: DF.Currency
		total_amount: DF.Currency
		total_incoming_value: DF.Currency
		total_outgoing_value: DF.Currency
		use_multi_level_bom: DF.Check
		value_difference: DF.Currency
		work_order: DF.Link | None
	# end: auto-generated types
	"""
	Extensión de la clase Stock Entry de ERPNext para registrar
	automáticamente movimientos en Shelf Movement y validar capacidad/tipo de estante
	"""
	
	def validate(self):
		"""
		Validar capacidad y tipo de estante antes de guardar/enviar
		"""
		super().validate()
		# Solo validar si el documento está siendo enviado (docstatus == 0 y tiene items con shelves)
		if self.docstatus == 0 and self.items:
			self.validate_shelf_mandatory()
			self.validate_shelf_capacity_and_type()

	def validate_shelf_mandatory(self):
		"""Issue #58: toda línea con movimiento de stock exige estante origen/destino."""
		if not self.items:
			return
		for item in self.items:
			validate_stock_entry_item_shelves(item, item.idx)
	
	def on_submit(self):
		"""
		Registrar Shelf Movement automáticamente cuando se envía Stock Entry
		"""
		super().on_submit()
		self.create_shelf_movements()
		self.ensure_item_shelf_locations()
		self.sync_item_shelf_quantities()

	def ensure_item_shelf_locations(self):
		"""Vincula el item a estantes origen/destino usados en el movimiento."""
		if not self.items:
			return
		for row in self.items:
			item_code = row.get("item_code")
			if not item_code:
				continue
			qty = row.get("qty")
			for shelf in (row.get("custom_from_shelf"), row.get("custom_to_shelf")):
				if shelf:
					try:
						link_item_to_shelf(item_code, shelf, qty)
					except Exception as e:
						frappe.log_error(
							message=f"Error al vincular item {item_code} al estante {shelf}: {e}",
							title="Stock Entry — Item Shelf Location",
						)
	
	def validate_shelf_capacity_and_type(self):
		"""
		Validar capacidad y tipo de estante para cada item
		"""
		if not self.items:
			return
		
		for item in self.items:
			from_shelf = item.get("custom_from_shelf")
			to_shelf = item.get("custom_to_shelf")
			
			# Validar shelf destino si existe (debe pertenecer a t_warehouse)
			if to_shelf:
				to_warehouse = item.get("t_warehouse") or self.to_warehouse
				self._validate_shelf_capacity(to_shelf, item.item_code, item.qty)
				self._validate_shelf_item_compatibility(to_shelf, item.item_code)
				if to_warehouse:
					self._validate_shelf_warehouse_match(to_shelf, to_warehouse, "destino")
			
			# Validar shelf origen si existe (debe pertenecer a s_warehouse)
			if from_shelf:
				from_warehouse = item.get("s_warehouse") or self.from_warehouse
				self._validate_shelf_item_compatibility(from_shelf, item.item_code)
				if from_warehouse:
					self._validate_shelf_warehouse_match(from_shelf, from_warehouse, "origen")
					# Validar disponibilidad de stock en estante origen antes de transferir
					if self.stock_entry_type in ("Material Transfer", "Material Issue") and from_shelf:
						self._validate_shelf_stock_availability(from_shelf, item.item_code, item.qty, from_warehouse)
	
	def _validate_shelf_capacity(self, shelf_name, item_code, quantity):
		"""
		Validar que el shelf tiene capacidad suficiente
		"""
		if not frappe.db.exists("Shelf", shelf_name):
			return
		
		shelf_doc = frappe.get_doc("Shelf", shelf_name)
		
		if shelf_doc.max_capacity:
			current_occupancy = shelf_doc.calculate_current_occupancy()
			available_capacity = shelf_doc.max_capacity - current_occupancy
			
			if quantity > available_capacity:
				frappe.throw(
					_("No se puede agregar {0} unidades del producto {1} al estante {2}: "
					  "el stock del producto ({3}) excede la capacidad disponible ({4}) "
					  "del estante (capacidad máxima: {5}, ocupación actual: {6})").format(
						quantity,
						frappe.bold(item_code),
						frappe.bold(shelf_doc.shelf_name),
						quantity,
						available_capacity,
						shelf_doc.max_capacity,
						current_occupancy
					),
					title=_("Capacidad del Estante Excedida")
				)
	
	def _validate_shelf_item_compatibility(self, shelf_name, item_code):
		"""
		Validar que el tipo de estante es compatible con el producto
		"""
		if not frappe.db.exists("Shelf", shelf_name) or not frappe.db.exists("Item", item_code):
			return
		
		shelf_doc = frappe.get_doc("Shelf", shelf_name)
		item_doc = frappe.get_doc("Item", item_code)
		
		shelf_type = shelf_doc.get("shelf_type")
		
		# Validar estante Refrigerado
		if shelf_type == "Refrigerado":
			requires_refrigeration = item_doc.get("custom_requires_refrigeration")
			if not requires_refrigeration:
				frappe.throw(
					_("El estante {0} es de tipo Refrigerado y solo puede contener productos que requieren refrigeración. "
					  "El producto {1} no requiere refrigeración.").format(
						frappe.bold(shelf_doc.shelf_name),
						frappe.bold(item_code)
					),
					title=_("Incompatibilidad Tipo Estante-Producto")
				)
		
		# Validar estante Controlado
		if shelf_type == "Controlado":
			control_level = item_doc.get("custom_control_level")
			if not control_level or control_level == "None":
				frappe.throw(
					_("El estante {0} es de tipo Controlado y solo puede contener productos con nivel de control "
					  "(Psicotrópico o Estupefaciente). El producto {1} no tiene nivel de control.").format(
						frappe.bold(shelf_doc.shelf_name),
						frappe.bold(item_code)
					),
					title=_("Incompatibilidad Tipo Estante-Producto")
				)
	
	def _validate_shelf_warehouse_match(self, shelf_name, warehouse, shelf_role="origen"):
		"""
		Validar que el estante pertenece al warehouse correcto
		
		Args:
			shelf_name: Nombre del estante
			warehouse: Warehouse del Stock Entry
			shelf_role: "origen" o "destino" para mensaje de error
		"""
		if not shelf_name or not warehouse:
			return
		
		if not frappe.db.exists("Shelf", shelf_name):
			return
		
		shelf_doc = frappe.get_doc("Shelf", shelf_name)
		
		if shelf_doc.warehouse != warehouse:
			frappe.throw(
				_("El estante {0} pertenece al almacén {1}, pero el Stock Entry está usando el almacén {2}. "
				  "El estante {3} debe pertenecer al mismo almacén que el Stock Entry.").format(
					frappe.bold(shelf_doc.shelf_name),
					frappe.bold(shelf_doc.warehouse),
					frappe.bold(warehouse),
					shelf_role
				),
				title=_("Incompatibilidad Estante-Almacén")
			)
	
	def _validate_shelf_stock_availability(self, shelf_name, item_code, quantity, warehouse):
		"""
		Validar que hay stock disponible en el estante origen antes de transferir
		
		Story 6.3: Optimización de Movimientos de Stock entre Almacenes
		
		Args:
			shelf_name: Nombre del estante origen
			item_code: Código del producto
			quantity: Cantidad a transferir
			warehouse: Warehouse del estante
		"""
		if not shelf_name or not item_code or not warehouse:
			return
		
		# Obtener stock disponible en el estante usando Shelf Movement
		# Sumar movimientos de tipo Recepción y Transferencia (entrada)
		# Restar movimientos de tipo Venta y Ajuste (salida)
		stock_query = """
			SELECT 
				SUM(
					CASE 
						WHEN sm.movement_type IN ('Recepción', 'Transferencia') THEN sm.quantity
						WHEN sm.movement_type IN ('Venta', 'Ajuste') THEN -sm.quantity
						ELSE 0
					END
				) as available_qty
			FROM `tabShelf Movement` sm
			INNER JOIN `tabShelf` s ON sm.shelf = s.name
			WHERE sm.shelf = %(shelf_name)s
				AND sm.item = %(item_code)s
				AND s.warehouse = %(warehouse)s
				AND sm.docstatus = 1
		"""
		
		result = frappe.db.sql(stock_query, {
			"shelf_name": shelf_name,
			"item_code": item_code,
			"warehouse": warehouse
		}, as_dict=True)
		
		available_qty = result[0].get("available_qty") if result and result[0] else None
		if available_qty is None:
			available_qty = 0
		
		# Si no hay stock en Shelf Movement, verificar stock en Bin (fallback)
		if available_qty <= 0:
			bin_stock = frappe.db.get_value(
				"Bin",
				{"item_code": item_code, "warehouse": warehouse},
				"actual_qty"
			) or 0
			
			# Si hay stock en Bin pero no en Shelf Movement, usar stock de Bin
			# pero advertir que el estante puede no tener stock específico
			if bin_stock > 0:
				available_qty = bin_stock
			else:
				available_qty = 0
		
		# Validar que hay stock suficiente
		if available_qty < quantity:
			shelf_doc = frappe.get_doc("Shelf", shelf_name)
			frappe.throw(
				_("No hay stock suficiente en el estante {0} para transferir {1} unidades del producto {2}. "
				  "Stock disponible en el estante: {3} unidades.").format(
					frappe.bold(shelf_doc.shelf_name),
					frappe.bold(quantity),
					frappe.bold(item_code),
					frappe.bold(available_qty)
				),
				title=_("Stock Insuficiente en Estante Origen")
			)
	
	def create_shelf_movements(self):
		"""
		Crear registros de Shelf Movement basados en los items del Stock Entry
		"""
		if not self.items:
			return
		
		for item in self.items:
			# Determinar tipo de movimiento según stock_entry_type
			movement_type = self._get_movement_type()
			
			# Obtener shelves desde campos custom
			from_shelf = item.get("custom_from_shelf")
			to_shelf = item.get("custom_to_shelf")
			
			# Solo crear movimiento si hay al menos un shelf especificado
			if not from_shelf and not to_shelf:
				continue
			
			# Determinar shelf principal según tipo de movimiento
			if movement_type == "Transferencia":
				# Transferencia requiere ambos shelves
				if from_shelf and to_shelf:
					self._create_shelf_movement(
						movement_type=movement_type,
						shelf=from_shelf,
						to_shelf=to_shelf,
						item=item.item_code,
						quantity=item.qty
					)
			elif movement_type == "Recepción":
				# Recepción solo requiere shelf destino
				if to_shelf:
					self._create_shelf_movement(
						movement_type=movement_type,
						shelf=to_shelf,
						item=item.item_code,
						quantity=item.qty
					)
			elif movement_type == "Venta":
				# Venta requiere shelf origen
				if from_shelf:
					self._create_shelf_movement(
						movement_type=movement_type,
						shelf=from_shelf,
						item=item.item_code,
						quantity=item.qty
					)
			elif movement_type == "Ajuste":
				# Ajuste puede tener shelf origen o destino
				shelf = from_shelf or to_shelf
				if shelf:
					self._create_shelf_movement(
						movement_type=movement_type,
						shelf=shelf,
						item=item.item_code,
						quantity=item.qty
					)
	
	def _get_movement_type(self):
		"""
		Determinar tipo de movimiento según stock_entry_type
		"""
		stock_entry_type = self.stock_entry_type
		
		type_mapping = {
			"Material Transfer": "Transferencia",
			"Material Receipt": "Recepción",
			"Material Issue": "Venta",
			"Material Transfer for Manufacture": "Transferencia",
			"Manufacture": "Ajuste",
			"Repack": "Ajuste",
			"Send to Subcontractor": "Transferencia",
			"Send to Warehouse": "Transferencia",
			"Receive at Warehouse": "Recepción"
		}
		
		return type_mapping.get(stock_entry_type, "Ajuste")
	
	def _create_shelf_movement(self, movement_type, shelf, item, quantity, to_shelf=None):
		"""
		Crear registro de Shelf Movement
		"""
		try:
			movement = frappe.get_doc({
				"doctype": "Shelf Movement",
				"movement_type": movement_type,
				"shelf": shelf,
				"to_shelf": to_shelf,
				"item": item,
				"quantity": quantity,
				"movement_date": self.posting_date or datetime.now(),
				"reference_doctype": "Stock Entry",
				"reference_name": self.name,
				"notes": f"Movimiento automático desde Stock Entry {self.name}"
			})
			
			insert_and_submit_shelf_movement(movement)
		except Exception as e:
			frappe.log_error(
				message=f"Error al crear Shelf Movement desde Stock Entry {self.name}: {str(e)}",
				title="Error en Shelf Movement"
			)
			# No lanzar excepción para no bloquear el submit del Stock Entry
			# pero registrar el error para debugging

	def sync_item_shelf_quantities(self):
		"""
		Sincroniza `Item Shelf Location.quantity` desde Shelf Movement al enviar el Stock Entry.

		Política conservadora:
		- Solo actualiza filas con quantity <= 0 (no pisa ajustes manuales positivos).
		- Asegura que ingresos nuevos (Material Receipt/Transfer) propaguen distribución
		  por estante sin depender de edición manual del Item.
		"""
		if not self.items:
			return

		for row in self.items:
			item_code = row.get("item_code")
			if not item_code or not frappe.db.exists("Item", item_code):
				continue
			try:
				item_doc = frappe.get_doc("Item", item_code)
			except Exception:
				continue

			if not hasattr(item_doc, "custom_shelf_locations") or not item_doc.custom_shelf_locations:
				continue

			movement_rows = frappe.db.sql(
				"""
				SELECT t.shelf, SUM(t.delta_qty) AS qty
				FROM (
					SELECT
						sm.shelf AS shelf,
						CASE
							WHEN sm.movement_type = 'Recepción' THEN sm.quantity
							WHEN sm.movement_type = 'Transferencia' THEN -sm.quantity
							WHEN sm.movement_type IN ('Venta', 'Ajuste') THEN -sm.quantity
							ELSE 0
						END AS delta_qty
					FROM `tabShelf Movement` sm
					WHERE sm.item = %(item_code)s
						AND sm.docstatus = 1

					UNION ALL

					SELECT
						sm.to_shelf AS shelf,
						sm.quantity AS delta_qty
					FROM `tabShelf Movement` sm
					WHERE sm.item = %(item_code)s
						AND sm.movement_type = 'Transferencia'
						AND sm.to_shelf IS NOT NULL
						AND sm.docstatus = 1
				) t
				WHERE t.shelf IS NOT NULL
				GROUP BY t.shelf
				""",
				{"item_code": item_code},
				as_dict=True,
			)
			if not movement_rows:
				continue

			qty_by_shelf = {r.get("shelf"): float(r.get("qty") or 0) for r in movement_rows}
			changed = False
			for shelf_row in item_doc.custom_shelf_locations:
				shelf = shelf_row.get("shelf")
				if not shelf:
					continue
				current_qty = float(shelf_row.get("quantity") or 0)
				if current_qty > 0:
					continue
				new_qty = qty_by_shelf.get(shelf)
				if new_qty is None:
					continue
				if new_qty >= 0 and current_qty != new_qty:
					shelf_row.quantity = new_qty
					changed = True

			if changed:
				try:
					item_doc.save(ignore_permissions=True)
				except Exception as e:
					frappe.log_error(
						message=f"Error al sincronizar quantity por estante para item {item_code}: {str(e)}",
						title="Error sync Item Shelf Location.quantity",
					)

			# Regla de consistencia: si en un warehouse hay un único shelf del item,
			# su quantity debe reflejar exactamente el Bin del warehouse.
			self._force_single_shelf_qty_from_bin(item_doc)

	def _force_single_shelf_qty_from_bin(self, item_doc):
		if not hasattr(item_doc, "custom_shelf_locations") or not item_doc.custom_shelf_locations:
			return
		by_warehouse = {}
		for r in item_doc.custom_shelf_locations:
			shelf = r.get("shelf")
			if not shelf or not frappe.db.exists("Shelf", shelf):
				continue
			wh = frappe.db.get_value("Shelf", shelf, "warehouse")
			if not wh:
				continue
			by_warehouse.setdefault(wh, []).append(r)

		changed = False
		for wh, rows in by_warehouse.items():
			if len(rows) != 1:
				continue
			bin_qty = (
				frappe.db.get_value(
					"Bin",
					{"item_code": item_doc.name, "warehouse": wh},
					"actual_qty",
				)
				or 0
			)
			row = rows[0]
			if float(row.get("quantity") or 0) != float(bin_qty):
				row.quantity = float(bin_qty)
				changed = True

		if changed:
			try:
				item_doc.save(ignore_permissions=True)
			except Exception as e:
				frappe.log_error(
					message=f"Error al forzar quantity por estante único para item {item_doc.name}: {str(e)}",
					title="Error force single shelf quantity",
				)

