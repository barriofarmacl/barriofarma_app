# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Script para cargar datos de prueba para UAT
Plan de UAT - Barriofarma

Uso:
    bench --site uat.barriofarma.cl execute \
        barriofarma_app.barriofarma_app.utils.setup.load_uat_data.load_test_data
"""

import frappe
from frappe import _
from frappe.utils import today, add_days, add_months, getdate, flt
import logging
from datetime import datetime

from barriofarma_app.barriofarma_app.test_setup import (
    ensure_minimum_masters,
    create_test_item,
    create_test_supplier,
    create_test_warehouse,
    create_test_shelf,
    create_test_batch,
    create_test_doctor,
    create_test_patient,
    get_test_company,
)

logger = logging.getLogger(__name__)


def create_uat_items():
    """
    Crear 20 productos/items con diferentes características para UAT
    
    Returns:
        Lista de items creados
    """
    logger.info("Creando productos/items para UAT...")
    frappe.set_user("Administrator")
    ensure_minimum_masters()
    
    items = []
    
    # Productos de Venta Libre (5 items)
    for i in range(1, 6):
        item_code = f"UAT-VL-{i:02d}"
        if frappe.db.exists("Item", item_code):
            logger.info(f"  ⚠️  Item '{item_code}' ya existe, omitiendo...")
            item = frappe.get_doc("Item", item_code)
        else:
            item = create_test_item(
                item_code=item_code,
                item_name=f"Producto Venta Libre {i}",
                custom_dispensing_type="Venta Libre",
                has_batch_no=0,
                has_expiry_date=0,
                custom_control_level="",
                stock_uom="Unidad"
            )
            logger.info(f"  ✓ Creado: {item.item_code} - {item.item_name}")
        items.append(item)
    
    # Productos con Receta Retenida (5 items)
    for i in range(1, 6):
        item_code = f"UAT-RR-{i:02d}"
        if frappe.db.exists("Item", item_code):
            logger.info(f"  ⚠️  Item '{item_code}' ya existe, omitiendo...")
            item = frappe.get_doc("Item", item_code)
        else:
            item = create_test_item(
                item_code=item_code,
                item_name=f"Producto Receta Retenida {i}",
                custom_dispensing_type="Venta con Receta Retenida",
                has_batch_no=1,
                has_expiry_date=1,
                custom_prescription_storage_required=1,
                custom_sanitary_registration=f"UAT-REG-{i:02d}",
                custom_control_level="",
                stock_uom="Unidad"
            )
            logger.info(f"  ✓ Creado: {item.item_code} - {item.item_name}")
        items.append(item)
    
    # Productos Controlados - Psicotrópico (5 items)
    for i in range(1, 6):
        item_code = f"UAT-PSI-{i:02d}"
        if frappe.db.exists("Item", item_code):
            logger.info(f"  ⚠️  Item '{item_code}' ya existe, omitiendo...")
            item = frappe.get_doc("Item", item_code)
        else:
            item = create_test_item(
                item_code=item_code,
                item_name=f"Producto Psicotrópico {i}",
                custom_dispensing_type="Venta con Receta Retenida",
                has_batch_no=1,
                has_expiry_date=1,
                custom_prescription_storage_required=1,
                custom_requires_prescription_retention=1,  # Requerido para productos controlados
                custom_sanitary_registration=f"UAT-REG-PSI-{i:02d}",
                custom_control_level="Psicotrópico",
                stock_uom="Unidad"
            )
            logger.info(f"  ✓ Creado: {item.item_code} - {item.item_name}")
        items.append(item)
    
    # Productos Controlados - Estupefaciente (5 items)
    for i in range(1, 6):
        item_code = f"UAT-EST-{i:02d}"
        if frappe.db.exists("Item", item_code):
            logger.info(f"  ⚠️  Item '{item_code}' ya existe, omitiendo...")
            item = frappe.get_doc("Item", item_code)
        else:
            item = create_test_item(
                item_code=item_code,
                item_name=f"Producto Estupefaciente {i}",
                custom_dispensing_type="Venta con Receta Retenida",
                has_batch_no=1,
                has_expiry_date=1,
                custom_prescription_storage_required=1,
                custom_requires_prescription_retention=1,  # Requerido para productos controlados
                custom_sanitary_registration=f"UAT-REG-EST-{i:02d}",
                custom_control_level="Estupefaciente",
                stock_uom="Unidad"
            )
            logger.info(f"  ✓ Creado: {item.item_code} - {item.item_name}")
        items.append(item)
    
    frappe.db.commit()
    logger.info(f"Total items creados: {len(items)}")
    
    return items


def create_uat_suppliers():
    """
    Crear 5 proveedores para UAT
    
    Returns:
        Lista de proveedores creados
    """
    logger.info("Creando proveedores para UAT...")
    frappe.set_user("Administrator")
    
    suppliers = []
    supplier_names = [
        "UAT-Proveedor Farmacéutico A",
        "UAT-Proveedor Farmacéutico B",
        "UAT-Proveedor Distribuidor C",
        "UAT-Proveedor Mayorista D",
        "UAT-Proveedor Importador E"
    ]
    
    for supplier_name in supplier_names:
        supplier = create_test_supplier(supplier_name)
        suppliers.append(supplier)
        logger.info(f"  ✓ Proveedor listo: {supplier.supplier_name} ({supplier.name})")
    
    frappe.db.commit()
    logger.info(f"Total proveedores creados: {len(suppliers)}")
    
    return suppliers


def create_uat_warehouses():
    """
    Crear 3 almacenes para UAT
    
    Returns:
        Lista de almacenes creados
    """
    logger.info("Creando almacenes para UAT...")
    frappe.set_user("Administrator")
    company = get_test_company()
    
    warehouses = []
    warehouse_data = [
        {"name": "UAT-Almacén Principal", "abbr": "UAT-AP"},
        {"name": "UAT-Almacén Secundario", "abbr": "UAT-AS"},
        {"name": "UAT-Almacén Refrigerado", "abbr": "UAT-AR"}
    ]
    
    for wh_data in warehouse_data:
        warehouse = create_test_warehouse(wh_data["name"], company=company)
        warehouses.append(warehouse)
        logger.info(f"  ✓ Almacén listo: {warehouse.warehouse_name} ({warehouse.name})")
    
    frappe.db.commit()
    logger.info(f"Total almacenes creados: {len(warehouses)}")
    
    return warehouses


def create_uat_shelves(warehouses):
    """
    Crear 10 estantes distribuidos en los almacenes para UAT
    
    Args:
        warehouses: Lista de warehouses donde crear estantes
    
    Returns:
        Lista de estantes creados
    """
    logger.info("Creando estantes para UAT...")
    frappe.set_user("Administrator")
    
    shelves = []
    
    # Distribuir estantes en los almacenes
    # Almacén Principal: 4 estantes
    for i in range(1, 5):
        shelf = create_test_shelf(
            shelf_name=f"Estante {i} - Almacén Principal",
            warehouse=warehouses[0].name,
            location_code=f"AP-{i:02d}",
            shelf_type="Normal",
            capacity_mode="Dinámica"
        )
        shelves.append(shelf)
        logger.info(f"  ✓ Creado: {shelf.shelf_name} ({shelf.location_code})")
    
    # Almacén Secundario: 3 estantes
    for i in range(1, 4):
        shelf = create_test_shelf(
            shelf_name=f"Estante {i} - Almacén Secundario",
            warehouse=warehouses[1].name,
            location_code=f"AS-{i:02d}",
            shelf_type="Normal",
            capacity_mode="Dinámica"
        )
        shelves.append(shelf)
        logger.info(f"  ✓ Creado: {shelf.shelf_name} ({shelf.location_code})")
    
    # Almacén Refrigerado: 3 estantes (refrigerados)
    for i in range(1, 4):
        shelf = create_test_shelf(
            shelf_name=f"Estante Refrigerado {i}",
            warehouse=warehouses[2].name,
            location_code=f"AR-{i:02d}",
            shelf_type="Refrigerado",
            capacity_mode="Dinámica"
        )
        shelves.append(shelf)
        logger.info(f"  ✓ Creado: {shelf.shelf_name} ({shelf.location_code})")
    
    frappe.db.commit()
    logger.info(f"Total estantes creados: {len(shelves)}")
    
    return shelves


def create_uat_batches(items):
    """
    Crear 10 lotes con diferentes fechas de caducidad para UAT
    
    Args:
        items: Lista de items que requieren lote
    
    Returns:
        Lista de lotes creados
    """
    logger.info("Creando lotes para UAT...")
    frappe.set_user("Administrator")
    
    batches = []
    
    # Filtrar items que requieren lote
    items_with_batch = [item for item in items if item.has_batch_no == 1]
    
    if not items_with_batch:
        logger.warning("No hay items que requieran lote")
        return batches
    
    # Crear lotes con diferentes fechas de caducidad
    batch_count = 0
    for item in items_with_batch[:10]:  # Máximo 10 lotes
        batch_count += 1
        
        # Fechas de caducidad variadas (algunos próximos a vencer, otros lejanos)
        if batch_count <= 3:
            # Lotes próximos a vencer (1-3 meses)
            expiry_date = add_months(today(), batch_count)
        elif batch_count <= 6:
            # Lotes con caducidad media (6-12 meses)
            expiry_date = add_months(today(), batch_count * 2)
        else:
            # Lotes con caducidad lejana (18-24 meses)
            expiry_date = add_months(today(), 18 + (batch_count - 6))
        
        batch_id = f"UAT-BATCH-{item.item_code}-{batch_count:02d}"
        
        try:
            batch = create_test_batch(
                item_code=item.name,
                batch_id=batch_id,
                expiry_date=expiry_date
            )
            batches.append(batch)
            logger.info(f"  ✓ Creado: {batch.batch_id} (vencimiento: {expiry_date})")
        except Exception as e:
            logger.warning(f"  ✗ Error creando lote {batch_id}: {str(e)}")
    
    frappe.db.commit()
    logger.info(f"Total lotes creados: {len(batches)}")
    
    return batches


def create_uat_doctors():
    """
    Crear 5 médicos para UAT
    
    Returns:
        Lista de médicos creados
    """
    logger.info("Creando médicos para UAT...")
    frappe.set_user("Administrator")
    
    doctors = []
    doctor_data = [
        {"name": "Dr. Juan Pérez González", "license": "UAT-LIC-001", "specialty": "Medicina General"},
        {"name": "Dr. María López Martínez", "license": "UAT-LIC-002", "specialty": "Pediatría"},
        {"name": "Dr. Carlos Rodríguez Silva", "license": "UAT-LIC-003", "specialty": "Cardiología"},
        {"name": "Dra. Ana Fernández Torres", "license": "UAT-LIC-004", "specialty": "Dermatología"},
        {"name": "Dr. Pedro Sánchez Díaz", "license": "UAT-LIC-005", "specialty": "Medicina Interna"}
    ]
    
    for doc_data in doctor_data:
        doctor = create_test_doctor(
            doctor_name=doc_data["name"],
            license_number=doc_data["license"],
            specialty=doc_data["specialty"]
        )
        doctors.append(doctor)
        logger.info(f"  ✓ Creado: {doctor.doctor_name} (licencia: {doctor.license_number})")
    
    frappe.db.commit()
    logger.info(f"Total médicos creados: {len(doctors)}")
    
    return doctors


def create_uat_patients():
    """
    Crear 10 pacientes para UAT
    
    Returns:
        Lista de pacientes creados
    """
    logger.info("Creando pacientes para UAT...")
    frappe.set_user("Administrator")
    
    patients = []
    patient_data = [
        {"name": "Paciente UAT 001", "rut": "UAT-RUT-001"},
        {"name": "Paciente UAT 002", "rut": "UAT-RUT-002"},
        {"name": "Paciente UAT 003", "rut": "UAT-RUT-003"},
        {"name": "Paciente UAT 004", "rut": "UAT-RUT-004"},
        {"name": "Paciente UAT 005", "rut": "UAT-RUT-005"},
        {"name": "Paciente UAT 006", "rut": "UAT-RUT-006"},
        {"name": "Paciente UAT 007", "rut": "UAT-RUT-007"},
        {"name": "Paciente UAT 008", "rut": "UAT-RUT-008"},
        {"name": "Paciente UAT 009", "rut": "UAT-RUT-009"},
        {"name": "Paciente UAT 010", "rut": "UAT-RUT-010"}
    ]
    
    for pat_data in patient_data:
        patient = create_test_patient(
            patient_name=pat_data["name"],
            rut_dni=pat_data["rut"]
        )
        patients.append(patient)
        logger.info(f"  ✓ Creado: {patient.patient_name} (RUT: {patient.rut_dni})")
    
    frappe.db.commit()
    logger.info(f"Total pacientes creados: {len(patients)}")
    
    return patients


def create_initial_stock(items, warehouses, batches):
    """
    Crear stock inicial en almacenes usando Stock Entry
    
    Args:
        items: Lista de items
        warehouses: Lista de warehouses
        batches: Lista de lotes disponibles
    """
    logger.info("Creando stock inicial en almacenes...")
    frappe.set_user("Administrator")
    
    company = get_test_company()
    
    # Crear Stock Entry para cada warehouse
    stock_entries = []
    
    for warehouse in warehouses:
        logger.info(f"  Creando stock en {warehouse.warehouse_name}...")
        
        # Seleccionar algunos items para este almacén
        items_for_warehouse = items[:10]  # 10 items por almacén

        # Re-seed: si ya hay cantidad en Bin para el primer ítem UAT, no duplicar Material Receipt
        probe_item = items_for_warehouse[0].name if items_for_warehouse else None
        if probe_item:
            existing_qty = frappe.db.get_value(
                "Bin",
                {"warehouse": warehouse.name, "item_code": probe_item},
                "actual_qty",
            )
            if flt(existing_qty) > 0:
                logger.info(
                    f"    Omitido Stock Entry: {warehouse.warehouse_name} ya tiene stock "
                    f"({probe_item} qty={flt(existing_qty)})"
                )
                continue

        items_list = []
        for item in items_for_warehouse:
            item_detail = {
                "item_code": item.name,
                "qty": 100,  # Cantidad inicial
                "uom": item.stock_uom,
                "allow_zero_valuation_rate": 1,
                "valuation_rate": 1000  # Precio de costo
            }
            
            # Si el item requiere lote, buscar un lote disponible
            if item.has_batch_no == 1:
                batch_for_item = next((b for b in batches if b.item == item.name), None)
                if batch_for_item:
                    item_detail["batch_no"] = batch_for_item.batch_id
                    item_detail["expiry_date"] = batch_for_item.expiry_date
            
            items_list.append(item_detail)
        
        # Crear Stock Entry tipo "Material Receipt"
        try:
            se = frappe.get_doc({
                "doctype": "Stock Entry",
                "stock_entry_type": "Material Receipt",
                "company": company,
                "to_warehouse": warehouse.name,
                "posting_date": today(),
                "posting_time": "10:00:00",
                "items": items_list
            })
            se.insert(ignore_permissions=True)
            se.submit()
            stock_entries.append(se.name)
            logger.info(f"    ✓ Stock Entry {se.name} creado y enviado")
        except Exception as e:
            logger.error(f"    ✗ Error creando Stock Entry para {warehouse.warehouse_name}: {str(e)}")
    
    frappe.db.commit()
    logger.info(f"Total Stock Entries creados: {len(stock_entries)}")
    
    return stock_entries


def load_test_data():
    """
    Cargar todos los datos de prueba para UAT
    
    Returns:
        Diccionario con resumen de datos creados
    """
    logger.info("=" * 70)
    logger.info("CARGA DE DATOS DE PRUEBA PARA UAT")
    logger.info("=" * 70)
    
    frappe.set_user("Administrator")
    
    try:
        # 1. Crear items
        items = create_uat_items()
        
        # 2. Crear proveedores
        suppliers = create_uat_suppliers()
        
        # 3. Crear almacenes
        warehouses = create_uat_warehouses()
        
        # 4. Crear estantes
        shelves = create_uat_shelves(warehouses)
        
        # 5. Crear lotes
        batches = create_uat_batches(items)
        
        # 6. Crear médicos
        doctors = create_uat_doctors()
        
        # 7. Crear pacientes
        patients = create_uat_patients()
        
        # 8. Crear stock inicial
        stock_entries = create_initial_stock(items, warehouses, batches)
        
        # Resumen
        logger.info("\n" + "=" * 70)
        logger.info("RESUMEN DE DATOS CREADOS")
        logger.info("=" * 70)
        logger.info(f"Items: {len(items)}")
        logger.info(f"Proveedores: {len(suppliers)}")
        logger.info(f"Almacenes: {len(warehouses)}")
        logger.info(f"Estantes: {len(shelves)}")
        logger.info(f"Lotes: {len(batches)}")
        logger.info(f"Médicos: {len(doctors)}")
        logger.info(f"Pacientes: {len(patients)}")
        logger.info(f"Stock Entries: {len(stock_entries)}")
        logger.info("=" * 70)
        logger.info("✓ Carga de datos completada exitosamente")
        logger.info("=" * 70)
        
        return {
            "items": len(items),
            "suppliers": len(suppliers),
            "warehouses": len(warehouses),
            "shelves": len(shelves),
            "batches": len(batches),
            "doctors": len(doctors),
            "patients": len(patients),
            "stock_entries": len(stock_entries)
        }
        
    except Exception as e:
        logger.error(f"Error durante la carga de datos: {str(e)}")
        frappe.db.rollback()
        raise


if __name__ == "__main__":
    import sys
    site = sys.argv[1] if len(sys.argv) > 1 else "barriofarma.localhost"
    
    frappe.init(site=site)
    frappe.connect()
    
    load_test_data()
    
    frappe.db.close()
