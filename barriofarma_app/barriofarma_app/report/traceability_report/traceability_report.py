# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Reporte de Trazabilidad de Medicamento

Story 2.2: Reporte de Trazabilidad de Medicamento

Este reporte muestra la trazabilidad completa de un medicamento desde
su recepción hasta su venta, cumpliendo con normativa farmacéutica chilena.

FR38: Rastrear medicamento desde recepción hasta venta
FR41: Generar reportes de trazabilidad para auditorías
"""

from __future__ import unicode_literals
import frappe
from frappe import _


def execute(filters=None):
    """
    Función principal del reporte de trazabilidad
    
    Args:
        filters: Diccionario con filtros del usuario:
            - item_code: Código del producto (opcional)
            - batch_no: Número de lote (opcional)
            - from_date: Fecha desde (opcional)
            - to_date: Fecha hasta (opcional)
    
    Returns:
        columns: Lista de diccionarios con definición de columnas
        data: Lista de diccionarios con los datos del reporte
    """
    columns = get_columns()
    data = get_traceability_data(filters or {})
    
    return columns, data


def get_columns():
    """
    Definir columnas del reporte
    
    Returns:
        Lista de diccionarios con definición de columnas
    """
    return [
        {
            "fieldname": "transaction_type",
            "label": _("Tipo de Transacción"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "document_name",
            "label": _("Documento"),
            "fieldtype": "Dynamic Link",
            "options": "reference_doctype",
            "width": 150
        },
        {
            "fieldname": "reference_doctype",
            "label": _("Tipo Doc"),
            "fieldtype": "Data",
            "hidden": 1
        },
        {
            "fieldname": "posting_date",
            "label": _("Fecha"),
            "fieldtype": "Date",
            "width": 100
        },
        {
            "fieldname": "item_code",
            "label": _("Código Producto"),
            "fieldtype": "Link",
            "options": "Item",
            "width": 150
        },
        {
            "fieldname": "item_name",
            "label": _("Nombre Producto"),
            "fieldtype": "Data",
            "width": 200
        },
        {
            "fieldname": "batch_no",
            "label": _("Lote"),
            "fieldtype": "Link",
            "options": "Batch",
            "width": 120
        },
        {
            "fieldname": "expiry_date",
            "label": _("Fecha Caducidad"),
            "fieldtype": "Date",
            "width": 120
        },
        {
            "fieldname": "quantity",
            "label": _("Cantidad"),
            "fieldtype": "Float",
            "width": 100,
            "precision": 2
        },
        {
            "fieldname": "warehouse",
            "label": _("Almacén"),
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 150
        },
        {
            "fieldname": "supplier",
            "label": _("Proveedor"),
            "fieldtype": "Link",
            "options": "Supplier",
            "width": 150
        },
        {
            "fieldname": "customer",
            "label": _("Cliente"),
            "fieldtype": "Link",
            "options": "Customer",
            "width": 150
        },
        {
            "fieldname": "from_warehouse",
            "label": _("Almacén Origen"),
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 150
        },
        {
            "fieldname": "to_warehouse",
            "label": _("Almacén Destino"),
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 150
        },
        {
            "fieldname": "current_stock",
            "label": _("Stock Actual"),
            "fieldtype": "Float",
            "width": 100,
            "precision": 2
        }
    ]


def get_traceability_data(filters):
    """
    Obtener datos de trazabilidad desde múltiples DocTypes
    
    Args:
        filters: Diccionario con filtros del usuario
    
    Returns:
        Lista de diccionarios con datos de trazabilidad ordenados cronológicamente
    """
    data = []
    
    # Obtener información del producto y lote (si se especifican)
    item_code = filters.get("item_code")
    batch_no = filters.get("batch_no")
    
    # Si no se especifica item_code ni batch_no, no podemos generar reporte
    if not item_code and not batch_no:
        frappe.msgprint(
            _("Debe especificar al menos un Producto o un Lote para generar el reporte de trazabilidad."),
            title=_("Filtro Requerido")
        )
        return []
    
    # 1. Información del producto (si se especifica)
    if item_code:
        item_info = get_item_info(item_code)
        if item_info:
            data.append(item_info)
    
    # 2. Información del lote (si se especifica)
    if batch_no:
        batch_info = get_batch_info(batch_no, item_code)
        if batch_info:
            data.append(batch_info)
    
    # 3. Recepciones iniciales (Purchase Receipt)
    purchase_receipts = get_purchase_receipts(filters)
    data.extend(purchase_receipts)
    
    # 4. Movimientos de stock (Stock Entry)
    stock_entries = get_stock_entries(filters)
    data.extend(stock_entries)
    
    # 5. Ventas (Sales Invoice)
    sales_invoices = get_sales_invoices(filters)
    data.extend(sales_invoices)
    
    # 6. Ventas POS (POS Invoice)
    pos_invoices = get_pos_invoices(filters)
    data.extend(pos_invoices)
    
    # 7. Stock actual
    current_stock = get_current_stock(filters)
    if current_stock:
        data.append(current_stock)
    
    # Ordenar por fecha
    data.sort(key=lambda x: x.get("posting_date") or "", reverse=False)
    
    return data


def get_item_info(item_code):
    """
    Obtener información básica del producto
    
    Returns:
        Diccionario con información del producto
    """
    if not frappe.db.exists("Item", item_code):
        return None
    
    item = frappe.get_doc("Item", item_code)
    
    return {
        "transaction_type": _("Información del Producto"),
        "document_name": item_code,
        "reference_doctype": "Item",
        "posting_date": None,
        "item_code": item_code,
        "item_name": item.item_name,
        "batch_no": None,
        "expiry_date": None,
        "quantity": None,
        "warehouse": None,
        "supplier": None,
        "customer": None,
        "from_warehouse": None,
        "to_warehouse": None,
        "current_stock": None
    }


def get_batch_info(batch_no, item_code=None):
    """
    Obtener información del lote
    
    Returns:
        Diccionario con información del lote
    """
    if not frappe.db.exists("Batch", batch_no):
        return None
    
    batch = frappe.get_doc("Batch", batch_no)
    
    # Si se especifica item_code, validar que el batch pertenece al item
    if item_code and batch.item != item_code:
        return None
    
    return {
        "transaction_type": _("Información del Lote"),
        "document_name": batch_no,
        "reference_doctype": "Batch",
        "posting_date": None,
        "item_code": batch.item,
        "item_name": frappe.db.get_value("Item", batch.item, "item_name") if batch.item else None,
        "batch_no": batch_no,
        "expiry_date": batch.expiry_date,
        "quantity": None,
        "warehouse": None,
        "supplier": None,
        "customer": None,
        "from_warehouse": None,
        "to_warehouse": None,
        "current_stock": None
    }


def get_purchase_receipts(filters):
    """
    Obtener recepciones iniciales (Purchase Receipt)
    
    Returns:
        Lista de diccionarios con datos de recepciones
    """
    conditions = []
    params = {}
    
    if filters.get("item_code"):
        conditions.append("pri.item_code = %(item_code)s")
        params["item_code"] = filters["item_code"]
    
    if filters.get("batch_no"):
        conditions.append("pri.batch_no = %(batch_no)s")
        params["batch_no"] = filters["batch_no"]
    
    if filters.get("from_date"):
        conditions.append("pr.posting_date >= %(from_date)s")
        params["from_date"] = filters["from_date"]
    
    if filters.get("to_date"):
        conditions.append("pr.posting_date <= %(to_date)s")
        params["to_date"] = filters["to_date"]
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = f"""
        SELECT 
            pr.name as document_name,
            pr.posting_date,
            pr.supplier,
            pri.item_code,
            i.item_name,
            pri.batch_no,
            b.expiry_date,
            pri.qty as quantity,
            pri.warehouse
        FROM `tabPurchase Receipt` pr
        INNER JOIN `tabPurchase Receipt Item` pri ON pr.name = pri.parent
        LEFT JOIN `tabItem` i ON pri.item_code = i.name
        LEFT JOIN `tabBatch` b ON pri.batch_no = b.name
        WHERE {where_clause}
            AND pr.docstatus = 1
            AND pri.batch_no IS NOT NULL
        ORDER BY pr.posting_date DESC
    """
    
    results = frappe.db.sql(query, params, as_dict=True)
    
    data = []
    for row in results:
        data.append({
            "transaction_type": _("Recepción"),
            "document_name": row.document_name,
            "reference_doctype": "Purchase Receipt",
            "posting_date": row.posting_date,
            "item_code": row.item_code,
            "item_name": row.item_name,
            "batch_no": row.batch_no,
            "expiry_date": row.expiry_date,
            "quantity": row.quantity,
            "warehouse": row.warehouse,
            "supplier": row.supplier,
            "customer": None,
            "from_warehouse": None,
            "to_warehouse": None,
            "current_stock": None
        })
    
    return data


def get_stock_entries(filters):
    """
    Obtener movimientos de stock (Stock Entry)
    
    Returns:
        Lista de diccionarios con datos de movimientos de stock
    """
    conditions = []
    params = {}
    
    if filters.get("item_code"):
        conditions.append("sei.item_code = %(item_code)s")
        params["item_code"] = filters["item_code"]
    
    if filters.get("batch_no"):
        conditions.append("sei.batch_no = %(batch_no)s")
        params["batch_no"] = filters["batch_no"]
    
    if filters.get("from_date"):
        conditions.append("se.posting_date >= %(from_date)s")
        params["from_date"] = filters["from_date"]
    
    if filters.get("to_date"):
        conditions.append("se.posting_date <= %(to_date)s")
        params["to_date"] = filters["to_date"]
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = f"""
        SELECT 
            se.name as document_name,
            se.posting_date,
            sei.item_code,
            i.item_name,
            sei.batch_no,
            b.expiry_date,
            sei.qty as quantity,
            sei.s_warehouse as from_warehouse,
            sei.t_warehouse as to_warehouse
        FROM `tabStock Entry` se
        INNER JOIN `tabStock Entry Detail` sei ON se.name = sei.parent
        LEFT JOIN `tabItem` i ON sei.item_code = i.name
        LEFT JOIN `tabBatch` b ON sei.batch_no = b.name
        WHERE {where_clause}
            AND se.docstatus = 1
            AND sei.batch_no IS NOT NULL
        ORDER BY se.posting_date DESC
    """
    
    results = frappe.db.sql(query, params, as_dict=True)
    
    data = []
    for row in results:
        data.append({
            "transaction_type": _("Movimiento de Stock"),
            "document_name": row.document_name,
            "reference_doctype": "Stock Entry",
            "posting_date": row.posting_date,
            "item_code": row.item_code,
            "item_name": row.item_name,
            "batch_no": row.batch_no,
            "expiry_date": row.expiry_date,
            "quantity": row.quantity,
            "warehouse": row.to_warehouse or row.from_warehouse,
            "supplier": None,
            "customer": None,
            "from_warehouse": row.from_warehouse,
            "to_warehouse": row.to_warehouse,
            "current_stock": None
        })
    
    return data


def get_sales_invoices(filters):
    """
    Obtener ventas (Sales Invoice)
    
    Returns:
        Lista de diccionarios con datos de ventas
    """
    conditions = []
    params = {}
    
    if filters.get("item_code"):
        conditions.append("sii.item_code = %(item_code)s")
        params["item_code"] = filters["item_code"]
    
    if filters.get("batch_no"):
        conditions.append("sii.batch_no = %(batch_no)s")
        params["batch_no"] = filters["batch_no"]
    
    if filters.get("from_date"):
        conditions.append("si.posting_date >= %(from_date)s")
        params["from_date"] = filters["from_date"]
    
    if filters.get("to_date"):
        conditions.append("si.posting_date <= %(to_date)s")
        params["to_date"] = filters["to_date"]
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = f"""
        SELECT 
            si.name as document_name,
            si.posting_date,
            si.customer,
            sii.item_code,
            i.item_name,
            sii.batch_no,
            b.expiry_date,
            sii.qty as quantity,
            sii.warehouse
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
        LEFT JOIN `tabItem` i ON sii.item_code = i.name
        LEFT JOIN `tabBatch` b ON sii.batch_no = b.name
        WHERE {where_clause}
            AND si.docstatus = 1
            AND sii.batch_no IS NOT NULL
        ORDER BY si.posting_date DESC
    """
    
    results = frappe.db.sql(query, params, as_dict=True)
    
    data = []
    for row in results:
        data.append({
            "transaction_type": _("Venta"),
            "document_name": row.document_name,
            "reference_doctype": "Sales Invoice",
            "posting_date": row.posting_date,
            "item_code": row.item_code,
            "item_name": row.item_name,
            "batch_no": row.batch_no,
            "expiry_date": row.expiry_date,
            "quantity": -row.quantity,  # Negativo porque es salida
            "warehouse": row.warehouse,
            "supplier": None,
            "customer": row.customer,
            "from_warehouse": None,
            "to_warehouse": None,
            "current_stock": None
        })
    
    return data


def get_pos_invoices(filters):
    """
    Obtener ventas POS (POS Invoice)
    
    Returns:
        Lista de diccionarios con datos de ventas POS
    """
    conditions = []
    params = {}
    
    if filters.get("item_code"):
        conditions.append("pii.item_code = %(item_code)s")
        params["item_code"] = filters["item_code"]
    
    if filters.get("batch_no"):
        conditions.append("pii.batch_no = %(batch_no)s")
        params["batch_no"] = filters["batch_no"]
    
    if filters.get("from_date"):
        conditions.append("pi.posting_date >= %(from_date)s")
        params["from_date"] = filters["from_date"]
    
    if filters.get("to_date"):
        conditions.append("pi.posting_date <= %(to_date)s")
        params["to_date"] = filters["to_date"]
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = f"""
        SELECT 
            pi.name as document_name,
            pi.posting_date,
            pi.customer,
            pii.item_code,
            i.item_name,
            pii.batch_no,
            b.expiry_date,
            pii.qty as quantity,
            pii.warehouse
        FROM `tabPOS Invoice` pi
        INNER JOIN `tabPOS Invoice Item` pii ON pi.name = pii.parent
        LEFT JOIN `tabItem` i ON pii.item_code = i.name
        LEFT JOIN `tabBatch` b ON pii.batch_no = b.name
        WHERE {where_clause}
            AND pi.docstatus = 1
            AND pii.batch_no IS NOT NULL
        ORDER BY pi.posting_date DESC
    """
    
    results = frappe.db.sql(query, params, as_dict=True)
    
    data = []
    for row in results:
        data.append({
            "transaction_type": _("Venta POS"),
            "document_name": row.document_name,
            "reference_doctype": "POS Invoice",
            "posting_date": row.posting_date,
            "item_code": row.item_code,
            "item_name": row.item_name,
            "batch_no": row.batch_no,
            "expiry_date": row.expiry_date,
            "quantity": -row.quantity,  # Negativo porque es salida
            "warehouse": row.warehouse,
            "supplier": None,
            "customer": row.customer,
            "from_warehouse": None,
            "to_warehouse": None,
            "current_stock": None
        })
    
    return data


def get_current_stock(filters):
    """
    Obtener stock actual del producto/lote
    
    Returns:
        Diccionario con información de stock actual
    """
    conditions = []
    params = {}
    
    if filters.get("item_code"):
        conditions.append("bin.item_code = %(item_code)s")
        params["item_code"] = filters["item_code"]
    
    if filters.get("batch_no"):
        # Para stock por lote, necesitamos consultar Serial and Batch Bundle
        # Por simplicidad, mostramos stock total del item
        pass
    
    if not conditions:
        return None
    
    where_clause = " AND ".join(conditions)
    
    query = f"""
        SELECT 
            bin.item_code,
            i.item_name,
            bin.warehouse,
            SUM(bin.actual_qty) as total_stock
        FROM `tabBin` bin
        LEFT JOIN `tabItem` i ON bin.item_code = i.name
        WHERE {where_clause}
        GROUP BY bin.item_code, bin.warehouse
        HAVING SUM(bin.actual_qty) > 0
    """
    
    results = frappe.db.sql(query, params, as_dict=True)
    
    if not results:
        return None
    
    # Sumar stock de todos los warehouses
    total_stock = sum(row.total_stock for row in results)
    
    return {
        "transaction_type": _("Stock Actual"),
        "document_name": _("Stock Actual"),
        "reference_doctype": "Bin",
        "posting_date": None,
        "item_code": results[0].item_code if results else None,
        "item_name": results[0].item_name if results else None,
        "batch_no": filters.get("batch_no"),
        "expiry_date": None,
        "quantity": None,
        "warehouse": ", ".join([row.warehouse for row in results]),
        "supplier": None,
        "customer": None,
        "from_warehouse": None,
        "to_warehouse": None,
        "current_stock": total_stock
    }

