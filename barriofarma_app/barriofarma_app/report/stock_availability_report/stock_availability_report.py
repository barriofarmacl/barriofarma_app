# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Reporte de Disponibilidad de Stock en Tiempo Real

Story 6.1: Mejora de Visualización de Stock en Tiempo Real

Este reporte muestra disponibilidad de stock por almacén, estante, lote y fechas de caducidad,
permitiendo gestión eficiente de inventario.

FR6: Visualizar stock disponible por almacén y ubicación
FR7: Consultar stock por estante físico (Shelf)
FR8: Consultar stock por lote (Batch)
FR9: Visualizar fechas de caducidad próximas
FR11: Alertas de stock bajo o productos próximos a vencer
"""

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, today, add_days, flt


def execute(filters=None):
    """
    Función principal del reporte de disponibilidad de stock
    
    Args:
        filters: Diccionario con filtros del usuario:
            - item_code: Código del producto (opcional)
            - warehouse: Almacén (opcional)
            - shelf: Estante (opcional)
            - batch_no: Número de lote (opcional)
            - show_expiring_soon: Mostrar solo productos próximos a caducar (opcional)
            - days_to_expiry: Días hasta caducidad para filtrar (opcional, default: 30)
            - show_low_stock: Mostrar solo productos con stock bajo (opcional)
    
    Returns:
        columns: Lista de diccionarios con definición de columnas
        data: Lista de diccionarios con los datos del reporte
    """
    columns = get_columns()
    data = get_stock_data(filters or {})
    
    return columns, data


def get_columns():
    """
    Definir columnas del reporte
    
    Returns:
        Lista de diccionarios con definición de columnas
    """
    return [
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
            "width": 250
        },
        {
            "fieldname": "warehouse",
            "label": _("Almacén"),
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 150
        },
        {
            "fieldname": "shelf",
            "label": _("Estante"),
            "fieldtype": "Link",
            "options": "Shelf",
            "width": 150
        },
        {
            "fieldname": "shelf_name",
            "label": _("Nombre Estante"),
            "fieldtype": "Data",
            "width": 150
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
            "fieldname": "days_to_expiry",
            "label": _("Días hasta Caducar"),
            "fieldtype": "Int",
            "width": 120
        },
        {
            "fieldname": "available_qty",
            "label": _("Stock Disponible"),
            "fieldtype": "Float",
            "width": 120,
            "precision": 2
        },
        {
            "fieldname": "stock_minimum",
            "label": _("Stock Mínimo"),
            "fieldtype": "Float",
            "width": 120,
            "precision": 2
        },
        {
            "fieldname": "stock_status",
            "label": _("Estado"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "alert",
            "label": _("Alerta"),
            "fieldtype": "Data",
            "width": 200
        }
    ]


def get_stock_data(filters):
    """
    Obtener datos de stock disponible con filtros
    
    Args:
        filters: Diccionario con filtros del usuario
    
    Returns:
        Lista de diccionarios con datos de stock
    """
    conditions = []
    params = {}
    
    # Filtros básicos
    if filters.get("item_code"):
        conditions.append("bin.item_code = %(item_code)s")
        params["item_code"] = filters["item_code"]
    
    if filters.get("warehouse"):
        conditions.append("bin.warehouse = %(warehouse)s")
        params["warehouse"] = filters["warehouse"]
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    # Consulta base: Stock por warehouse desde Bin
    query = f"""
        SELECT 
            bin.item_code,
            i.item_name,
            bin.warehouse,
            bin.actual_qty as available_qty,
            COALESCE(i.safety_stock, 0) as stock_minimum,
            CASE 
                WHEN bin.actual_qty <= 0 THEN 'Sin Stock'
                WHEN COALESCE(i.safety_stock, 0) > 0 AND bin.actual_qty < i.safety_stock THEN 'Stock Bajo'
                ELSE 'Disponible'
            END as stock_status
        FROM `tabBin` bin
        INNER JOIN `tabItem` i ON bin.item_code = i.name
        WHERE {where_clause}
            AND bin.actual_qty > 0
        ORDER BY bin.item_code, bin.warehouse
    """
    
    results = frappe.db.sql(query, params, as_dict=True)
    
    # Expandir datos con información de Shelf y Batch
    data = []
    current_date = getdate(today())
    days_to_expiry_threshold = int(filters.get("days_to_expiry", 30))
    show_expiring_soon = filters.get("show_expiring_soon", False)
    show_low_stock = filters.get("show_low_stock", False)
    shelf_filter = filters.get("shelf")
    batch_filter = filters.get("batch_no")
    
    for row in results:
        # Obtener información de Shelf Movement para este item y warehouse
        shelf_data = get_shelf_stock(row.item_code, row.warehouse, shelf_filter)
        
        # Si hay filtro de shelf y no hay stock en ese shelf, omitir
        if shelf_filter and not shelf_data:
            continue
        
        # Si no hay datos de shelf, mostrar stock general del warehouse
        if not shelf_data:
            shelf_data = [{
                "shelf": None,
                "shelf_name": None,
                "qty": row.available_qty
            }]
        
        # Para cada shelf, obtener información de batches
        # Nota: Shelf Movement no tiene batch_no directamente,
        # por lo que obtenemos batches del warehouse completo
        for shelf_row in shelf_data:
                # Obtener batches del warehouse (no filtrado por shelf específico)
                batch_data = get_batch_stock(
                    row.item_code, 
                    row.warehouse, 
                    None,  # No podemos filtrar por shelf específico para batches
                    batch_filter
                )
                
                # Si hay filtro de batch y no hay stock en ese batch, omitir
                if batch_filter and not batch_data:
                    continue
                
                # Si no hay datos de batch, mostrar stock general del shelf
                if not batch_data:
                    batch_data = [{
                        "batch_no": None,
                        "expiry_date": None,
                        "qty": shelf_row.get("qty", row.available_qty)
                    }]
                
                # Para cada batch, crear fila en el reporte
                # Nota: La cantidad mostrada es del shelf, pero los batches son del warehouse completo
                for batch_row in batch_data:
                    expiry_date = batch_row.get("expiry_date")
                    days_to_expiry = None
                    alert = []
                    
                    # Calcular días hasta caducidad
                    if expiry_date:
                        expiry = getdate(expiry_date)
                        days_to_expiry = (expiry - current_date).days
                        
                        # Alertas de caducidad
                        if days_to_expiry < 0:
                            alert.append(_("Producto Vencido"))
                        elif days_to_expiry <= days_to_expiry_threshold:
                            alert.append(_("Próximo a Caducar ({0} días)").format(days_to_expiry))
                    
                    # Alertas de stock bajo
                    if row.stock_status == "Stock Bajo":
                        alert.append(_("Stock Bajo"))
                    elif row.stock_status == "Sin Stock":
                        alert.append(_("Sin Stock"))
                    
                    # Filtrar por expiring soon si está activado
                    if show_expiring_soon:
                        if not expiry_date or days_to_expiry is None or days_to_expiry > days_to_expiry_threshold:
                            continue
                    
                    # Filtrar por stock bajo si está activado
                    if show_low_stock:
                        if row.stock_status != "Stock Bajo":
                            continue
                    
                    data.append({
                        "item_code": row.item_code,
                        "item_name": row.item_name,
                        "warehouse": row.warehouse,
                        "shelf": shelf_row.get("shelf"),
                        "shelf_name": shelf_row.get("shelf_name"),
                        "batch_no": batch_row.get("batch_no"),
                        "expiry_date": expiry_date,
                        "days_to_expiry": days_to_expiry,
                        "available_qty": flt(batch_row.get("qty", shelf_row.get("qty", row.available_qty))),
                        "stock_minimum": flt(row.stock_minimum or 0),
                        "stock_status": row.stock_status,
                        "alert": " | ".join(alert) if alert else None
                    })
    
    return data


def get_shelf_stock(item_code, warehouse, shelf_filter=None):
    """
    Obtener stock por estante (Shelf) usando Shelf Movement y custom_shelf_locations
    
    Estrategia:
    1. Primero intenta obtener estantes desde Shelf Movement (stock real por transacciones)
    2. Si no hay Shelf Movements, consulta estantes desde custom_shelf_locations (configuración estática)
    3. Para cada estante, muestra stock real desde Bin
    
    Args:
        item_code: Código del producto
        warehouse: Almacén
        shelf_filter: Filtro opcional de estante específico
    
    Returns:
        Lista de diccionarios con stock por estante
    """
    shelf_data = []
    
    # 1. Intentar obtener estantes desde Shelf Movement (stock por transacciones)
    conditions = [
        "sm.item = %(item_code)s",
        "s.warehouse = %(warehouse)s",
        "sm.docstatus = 1"
    ]
    params = {
        "item_code": item_code,
        "warehouse": warehouse
    }
    
    if shelf_filter:
        conditions.append("sm.shelf = %(shelf)s")
        params["shelf"] = shelf_filter
    
    where_clause = " AND ".join(conditions)
    
    # Consulta que suma movimientos por estante
    query = f"""
        SELECT 
            sm.shelf,
            s.shelf_name,
            SUM(
                CASE 
                    WHEN sm.movement_type IN ('Recepción', 'Transferencia') THEN sm.quantity
                    WHEN sm.movement_type IN ('Venta', 'Ajuste') THEN -sm.quantity
                    ELSE 0
                END
            ) as qty
        FROM `tabShelf Movement` sm
        INNER JOIN `tabShelf` s ON sm.shelf = s.name
        WHERE {where_clause}
        GROUP BY sm.shelf, s.shelf_name
        HAVING SUM(
            CASE 
                WHEN sm.movement_type IN ('Recepción', 'Transferencia') THEN sm.quantity
                WHEN sm.movement_type IN ('Venta', 'Ajuste') THEN -sm.quantity
                ELSE 0
            END
        ) > 0
    """
    
    results = frappe.db.sql(query, params, as_dict=True)
    
    if results:
        # Si hay Shelf Movements, usar esos datos
        shelf_data = results
    else:
        # 2. Si no hay Shelf Movements, consultar estantes desde custom_shelf_locations
        shelf_locations = get_shelf_locations_from_item(item_code, warehouse, shelf_filter)
        
        if shelf_locations:
            # Para cada estante configurado, obtener stock real desde Bin
            for shelf_info in shelf_locations:
                shelf_name = shelf_info.get("shelf_name")
                shelf_code = shelf_info.get("shelf")
                
                # Obtener stock real desde Bin para este item en este warehouse
                # Nota: El stock en Bin es por warehouse, no por shelf específico
                # Por ahora mostramos el stock del warehouse completo
                bin_stock = frappe.db.get_value(
                    "Bin",
                    {"item_code": item_code, "warehouse": warehouse},
                    "actual_qty"
                ) or 0
                
                shelf_data.append({
                    "shelf": shelf_code,
                    "shelf_name": shelf_name,
                    "qty": bin_stock
                })
    
    return shelf_data


def get_shelf_locations_from_item(item_code, warehouse, shelf_filter=None):
    """
    Obtener estantes configurados en custom_shelf_locations del Item
    
    Args:
        item_code: Código del producto
        warehouse: Almacén para filtrar estantes
        shelf_filter: Filtro opcional de estante específico
    
    Returns:
        Lista de diccionarios con información de estantes
    """
    conditions = [
        "isl.parent = %(item_code)s",
        "s.warehouse = %(warehouse)s",
        "s.disabled = 0"
    ]
    params = {
        "item_code": item_code,
        "warehouse": warehouse
    }
    
    if shelf_filter:
        conditions.append("isl.shelf = %(shelf)s")
        params["shelf"] = shelf_filter
    
    where_clause = " AND ".join(conditions)
    
    query = f"""
        SELECT DISTINCT
            isl.shelf,
            s.shelf_name
        FROM `tabItem Shelf Location` isl
        INNER JOIN `tabShelf` s ON isl.shelf = s.name
        WHERE {where_clause}
    """
    
    results = frappe.db.sql(query, params, as_dict=True)
    
    return results if results else []


def get_batch_stock(item_code, warehouse, shelf=None, batch_filter=None):
    """
    Obtener stock por lote (Batch) con fechas de caducidad
    
    Usa la función estándar de ERPNext para obtener stock por batch.
    En ERPNext v15, el stock por batch se obtiene desde Serial and Batch Bundle.
    
    Args:
        item_code: Código del producto
        warehouse: Almacén
        shelf: Estante opcional (no implementado - Shelf Movement no tiene batch_no)
        batch_filter: Filtro opcional de lote específico
    
    Returns:
        Lista de diccionarios con stock por lote
    """
    # Verificar si el item tiene has_batch_no=1
    has_batch_no = frappe.db.get_value("Item", item_code, "has_batch_no")
    
    if not has_batch_no:
        # Si el item no usa batches, retornar lista vacía
        return []
    
    params = {
        "item_code": item_code,
        "warehouse": warehouse
    }
    
    results = []  # Inicializar results
    
    # En ERPNext v15, usar Serial and Batch Bundle para obtener stock por batch
    # Verificar si la tabla existe antes de usarla
    if frappe.db.table_exists("Serial and Batch Bundle Entry"):
        try:
            query = """
                SELECT 
                    sbbe.batch_no,
                    b.expiry_date,
                    SUM(sbbe.qty) as qty
                FROM `tabSerial and Batch Bundle Entry` sbbe
                INNER JOIN `tabSerial and Batch Bundle` sbb ON sbbe.parent = sbb.name
                INNER JOIN `tabBatch` b ON sbbe.batch_no = b.name
                WHERE sbb.item_code = %(item_code)s
                    AND sbb.warehouse = %(warehouse)s
                    AND sbbe.batch_no IS NOT NULL
                    AND sbb.docstatus = 1
            """
            
            if batch_filter:
                query += " AND sbbe.batch_no = %(batch_no)s"
                params["batch_no"] = batch_filter
            
            query += """
                GROUP BY sbbe.batch_no, b.expiry_date
                HAVING SUM(sbbe.qty) > 0
                ORDER BY b.expiry_date ASC
            """
            
            results = frappe.db.sql(query, params, as_dict=True)
            
            if results:
                return results
        except Exception:
            # Si falla, usar fallback
            pass
    
    # Si no hay resultados en Serial and Batch Bundle o la tabla no existe,
    # usar fallback desde Stock Ledger Entry y Bin
    # (para compatibilidad con datos antiguos o si Serial and Batch Bundle no está en uso)
    if not results:
        query_fallback = """
            SELECT 
                sle.batch_no,
                b.expiry_date,
                sle.actual_qty as qty
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabBatch` b ON sle.batch_no = b.name
            WHERE sle.item_code = %(item_code)s
                AND sle.warehouse = %(warehouse)s
                AND sle.batch_no IS NOT NULL
        """
        
        if batch_filter:
            query_fallback += " AND sle.batch_no = %(batch_no)s"
        
        query_fallback += """
            AND sle.actual_qty > 0
            GROUP BY sle.batch_no, b.expiry_date
            ORDER BY b.expiry_date ASC
        """
        
        # Obtener último saldo por batch (más reciente)
        results_fallback = frappe.db.sql(query_fallback, params, as_dict=True)
        
        if results_fallback:
            # Para cada batch, obtener el último saldo
            batch_stocks = {}
            for row in results_fallback:
                batch_no = row.get("batch_no")
                if batch_no not in batch_stocks:
                    batch_stocks[batch_no] = {
                        "batch_no": batch_no,
                        "expiry_date": row.get("expiry_date"),
                        "qty": 0
                    }
            
            # Obtener último saldo de cada batch
            for batch_no in batch_stocks.keys():
                last_qty = frappe.db.sql("""
                    SELECT actual_qty
                    FROM `tabStock Ledger Entry`
                    WHERE item_code = %(item_code)s
                        AND warehouse = %(warehouse)s
                        AND batch_no = %(batch_no)s
                    ORDER BY posting_date DESC, posting_time DESC, creation DESC
                    LIMIT 1
                """, {
                    "item_code": item_code,
                    "warehouse": warehouse,
                    "batch_no": batch_no
                }, as_dict=True)
                
                if last_qty and last_qty[0].get("actual_qty", 0) > 0:
                    batch_stocks[batch_no]["qty"] = last_qty[0].get("actual_qty", 0)
            
            results = [v for v in batch_stocks.values() if v["qty"] > 0]
    
    return results if results else []

