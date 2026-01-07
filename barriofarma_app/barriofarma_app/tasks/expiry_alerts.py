# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Story 6.2: Alertas de Productos Próximos a Caducar

Tareas programadas para verificar productos próximos a caducar y generar alertas.
"""

import frappe
from frappe import _
from frappe.utils import getdate, today, add_days, get_datetime
from datetime import datetime


def check_expiring_products():
    """
    Verificar productos próximos a caducar y generar alertas
    
    Esta función se ejecuta diariamente como scheduled task para:
    - Identificar productos con fechas de caducidad dentro del umbral configurado
    - Generar notificaciones para usuarios relevantes
    - Actualizar estado de alertas en productos
    """
    frappe.logger().info("Iniciando verificación de productos próximos a caducar")
    
    # Obtener umbral global por defecto (30 días)
    # Por ahora usamos 30 días como default, puede configurarse en Company o Item Group
    default_threshold_days = 30
    
    # Obtener todos los batches con stock disponible y fecha de caducidad
    expiring_batches = get_expiring_batches(default_threshold_days)
    
    if not expiring_batches:
        frappe.logger().info("No se encontraron productos próximos a caducar")
        return
    
    # Procesar cada batch y generar alertas
    alerts_created = 0
    for batch_data in expiring_batches:
        try:
            create_expiry_alert(batch_data, default_threshold_days)
            alerts_created += 1
        except Exception as e:
            frappe.logger().error(
                f"Error al crear alerta para batch {batch_data.get('batch_no')}: {str(e)}"
            )
    
    frappe.logger().info(
        f"Verificación completada: {alerts_created} alertas generadas"
    )


def get_expiring_batches(threshold_days=30):
    """
    Obtener batches próximos a caducar con stock disponible
    
    Args:
        threshold_days: Días hasta caducidad para considerar como "próximo a caducar"
    
    Returns:
        Lista de diccionarios con información de batches próximos a caducar
    """
    current_date = getdate(today())
    threshold_date = add_days(current_date, threshold_days)
    
    # Consulta que obtiene batches con stock disponible y fecha de caducidad próxima
    # Usar Serial and Batch Bundle para obtener stock actual (ERPNext v15)
    results = []
    
    # Verificar si Serial and Batch Bundle está disponible
    if frappe.db.table_exists("Serial and Batch Bundle Entry"):
        try:
            query = """
                SELECT DISTINCT
                    b.name as batch_no,
                    b.item as item_code,
                    i.item_name,
                    b.expiry_date,
                    DATEDIFF(b.expiry_date, %(current_date)s) as days_to_expiry,
                    SUM(sbbe.qty) as available_qty,
                    sbb.warehouse
                FROM `tabBatch` b
                INNER JOIN `tabItem` i ON b.item = i.name
                INNER JOIN `tabSerial and Batch Bundle Entry` sbbe ON sbbe.batch_no = b.name
                INNER JOIN `tabSerial and Batch Bundle` sbb ON sbbe.parent = sbb.name
                WHERE b.expiry_date IS NOT NULL
                    AND b.expiry_date >= %(current_date)s
                    AND b.expiry_date <= %(threshold_date)s
                    AND b.disabled = 0
                    AND sbb.docstatus = 1
                GROUP BY b.name, b.item, i.item_name, b.expiry_date, sbb.warehouse
                HAVING SUM(sbbe.qty) > 0
                ORDER BY b.expiry_date ASC
            """
            
            results = frappe.db.sql(query, {
                "current_date": current_date,
                "threshold_date": threshold_date
            }, as_dict=True)
        except Exception:
            # Si falla, usar fallback
            pass
    
    # Si no hay resultados en Serial and Batch Bundle, usar fallback con Stock Ledger Entry
    if not results:
        query_fallback = """
            SELECT DISTINCT
                b.name as batch_no,
                b.item as item_code,
                i.item_name,
                b.expiry_date,
                DATEDIFF(b.expiry_date, %(current_date)s) as days_to_expiry,
                sle.warehouse,
                (SELECT actual_qty 
                 FROM `tabStock Ledger Entry` 
                 WHERE item_code = b.item 
                   AND batch_no = b.name 
                   AND warehouse = sle.warehouse
                 ORDER BY posting_date DESC, posting_time DESC, creation DESC
                 LIMIT 1) as available_qty
            FROM `tabBatch` b
            INNER JOIN `tabItem` i ON b.item = i.name
            INNER JOIN `tabStock Ledger Entry` sle ON sle.batch_no = b.name
            WHERE b.expiry_date IS NOT NULL
                AND b.expiry_date >= %(current_date)s
                AND b.expiry_date <= %(threshold_date)s
                AND b.disabled = 0
            GROUP BY b.name, b.item, i.item_name, b.expiry_date, sle.warehouse
            HAVING available_qty > 0
            ORDER BY b.expiry_date ASC
        """
        
        results = frappe.db.sql(query_fallback, {
            "current_date": current_date,
            "threshold_date": threshold_date
        }, as_dict=True)
    
    return results


def get_expiry_threshold_for_item(item_code):
    """
    Obtener umbral de caducidad para un item específico
    
    Prioridad:
    1. Item.custom_expiry_alert_days (si existe)
    2. Item Group.custom_minimum_expiry_months (convertido a días)
    3. Company.custom_minimum_expiry_months (convertido a días)
    4. Default global (30 días)
    
    Args:
        item_code: Código del producto
    
    Returns:
        Días de umbral para alerta de caducidad
    """
    # Verificar si el item tiene umbral específico
    item_threshold = frappe.db.get_value("Item", item_code, "custom_expiry_alert_days")
    if item_threshold:
        return int(item_threshold)
    
    # Verificar Item Group
    item_group = frappe.db.get_value("Item", item_code, "item_group")
    if item_group:
        item_group_threshold = frappe.db.get_value(
            "Item Group", 
            item_group, 
            "custom_minimum_expiry_months"
        )
        if item_group_threshold:
            # Convertir meses a días (aproximado: 1 mes = 30 días)
            return int(item_group_threshold) * 30
    
    # Verificar Company (usar primera company disponible)
    companies = frappe.get_all("Company", limit=1)
    if companies:
        company_threshold = frappe.db.get_value(
            "Company",
            companies[0].name,
            "custom_minimum_expiry_months"
        )
        if company_threshold:
            return int(company_threshold) * 30
    
    # Default: 30 días
    return 30


def create_expiry_alert(batch_data, default_threshold_days):
    """
    Crear o actualizar alerta de caducidad para un batch
    
    Por ahora solo loguea las alertas. En el futuro se puede crear un DocType
    "Expiry Alert" para gestionar alertas de forma más estructurada.
    
    Args:
        batch_data: Diccionario con información del batch
        default_threshold_days: Umbral por defecto en días
    """
    batch_no = batch_data.get("batch_no")
    item_code = batch_data.get("item_code")
    item_name = batch_data.get("item_name", "")
    days_to_expiry = batch_data.get("days_to_expiry", 0)
    available_qty = batch_data.get("available_qty", 0)
    warehouse = batch_data.get("warehouse", "")
    
    # Obtener umbral específico para este item
    threshold_days = get_expiry_threshold_for_item(item_code)
    
    # Solo crear alerta si está dentro del umbral
    if days_to_expiry > threshold_days:
        return
    
    # Determinar criticidad
    if days_to_expiry < 7:
        severity = "CRÍTICO"
    elif days_to_expiry < 30:
        severity = "ADVERTENCIA"
    else:
        severity = "INFO"
    
    # Loguear la alerta
    frappe.logger().info(
        f"[{severity}] Alerta de caducidad: {item_code} ({item_name}), "
        f"Batch: {batch_no}, Caduca en {days_to_expiry} días, "
        f"Stock: {available_qty} en {warehouse}"
    )
    
    # En el futuro, aquí se podría:
    # - Crear notificaciones para usuarios relevantes
    # - Crear registros en un DocType "Expiry Alert"
    # - Enviar emails automáticos
    # - Actualizar dashboard widgets


def get_expiring_products_summary(threshold_days=30):
    """
    Obtener resumen de productos próximos a caducar para dashboard
    
    Args:
        threshold_days: Días hasta caducidad para filtrar
    
    Returns:
        Diccionario con resumen de productos próximos a caducar
    """
    expiring_batches = get_expiring_batches(threshold_days)
    
    summary = {
        "total_items": 0,
        "total_batches": len(expiring_batches),
        "critical_items": [],  # Items que caducan en < 7 días
        "warning_items": [],   # Items que caducan en 7-30 días
        "info_items": []       # Items que caducan en > 30 días pero dentro del umbral
    }
    
    items_seen = set()
    
    for batch in expiring_batches:
        item_code = batch.get("item_code")
        days_to_expiry = batch.get("days_to_expiry", 0)
        
        if item_code not in items_seen:
            items_seen.add(item_code)
            summary["total_items"] += 1
            
            item_summary = {
                "item_code": item_code,
                "item_name": batch.get("item_name"),
                "days_to_expiry": days_to_expiry,
                "expiry_date": batch.get("expiry_date"),
                "available_qty": batch.get("available_qty", 0)
            }
            
            if days_to_expiry < 7:
                summary["critical_items"].append(item_summary)
            elif days_to_expiry < 30:
                summary["warning_items"].append(item_summary)
            else:
                summary["info_items"].append(item_summary)
    
    return summary

