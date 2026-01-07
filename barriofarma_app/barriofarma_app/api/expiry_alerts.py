# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
API Endpoints para Alertas de Productos Próximos a Caducar

Story 6.2: Alertas de Productos Próximos a Caducar
"""

import frappe
from frappe import _
from frappe.utils import getdate, today
from barriofarma_app.barriofarma_app.tasks.expiry_alerts import get_expiring_products_summary


@frappe.whitelist()
def get_expiry_alerts_summary(threshold_days=30):
    """
    Obtener resumen de productos próximos a caducar para dashboard
    
    Args:
        threshold_days: Días hasta caducidad para filtrar (default: 30)
    
    Returns:
        Diccionario con resumen de productos próximos a caducar
    """
    try:
        threshold = int(threshold_days) if threshold_days else 30
        summary = get_expiring_products_summary(threshold)
        
        return {
            "success": True,
            "data": summary
        }
    except Exception as e:
        frappe.log_error(
            title=_("Error al obtener resumen de alertas de caducidad"),
            message=str(e)
        )
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_item_expiry_status(item_code):
    """
    Obtener estado de caducidad para un item específico
    
    Args:
        item_code: Código del producto
    
    Returns:
        Diccionario con información de caducidad del item
    """
    try:
        from barriofarma_app.barriofarma_app.tasks.expiry_alerts import (
            get_expiry_threshold_for_item,
            get_expiring_batches
        )
        
        # Verificar si el item usa batches
        has_batch_no = frappe.db.get_value("Item", item_code, "has_batch_no")
        
        if not has_batch_no:
            return {
                "success": True,
                "data": {
                    "has_batch_no": False,
                    "expiring_batches": [],
                    "status": "no_batch"
                }
            }
        
        # Obtener umbral para este item
        threshold_days = get_expiry_threshold_for_item(item_code)
        
        # Obtener batches próximos a caducar para este item
        all_batches = get_expiring_batches(threshold_days)
        item_batches = [b for b in all_batches if b.get("item_code") == item_code]
        
        # Determinar estado
        status = "ok"
        min_days = None
        
        if item_batches:
            min_days = min([b.get("days_to_expiry", 999) for b in item_batches])
            
            if min_days < 7:
                status = "critical"
            elif min_days < 30:
                status = "warning"
            else:
                status = "info"
        
        return {
            "success": True,
            "data": {
                "has_batch_no": True,
                "expiring_batches": item_batches,
                "status": status,
                "min_days_to_expiry": min_days,
                "threshold_days": threshold_days
            }
        }
    except Exception as e:
        frappe.log_error(
            title=_("Error al obtener estado de caducidad del item"),
            message=str(e)
        )
        return {
            "success": False,
            "error": str(e)
        }

