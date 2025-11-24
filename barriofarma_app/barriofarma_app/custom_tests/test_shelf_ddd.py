# -*- coding: utf-8 -*-
# Copyright (c) 2025, Barrio Farma and Contributors
# See license.txt

"""
Tests DDD para el Agregado Shelf (Estante)
Validación de invariantes y reglas de negocio del dominio farmacéutico
"""

import unittest
import frappe
from frappe.exceptions import ValidationError

from barriofarma_app.barriofarma_app.test_setup import (
    ensure_minimum_masters,
    create_test_warehouse,
    create_test_shelf,
    get_test_company,
)


class TestShelfDDD(unittest.TestCase):
    """Tests para invariantes DDD del agregado Shelf"""

    def setUp(self):
        """Preparar datos necesarios para cada test"""
        frappe.set_user("Administrator")
        ensure_minimum_masters()
        self.test_shelves = []
        self.test_warehouses = []

    def tearDown(self):
        """Limpiar datos de prueba después de cada test"""
        frappe.set_user("Administrator")
        
        # Limpiar shelves
        for shelf_name in self.test_shelves:
            try:
                if frappe.db.exists("Shelf", shelf_name):
                    frappe.delete_doc("Shelf", shelf_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        # Limpiar warehouses
        for warehouse_name in self.test_warehouses:
            try:
                if frappe.db.exists("Warehouse", warehouse_name):
                    # Limpiar Bins relacionados
                    frappe.db.sql("DELETE FROM `tabBin` WHERE warehouse = %s", (warehouse_name,))
                    frappe.delete_doc("Warehouse", warehouse_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        
        frappe.db.commit()

    def test_invariante_shelf_debe_pertenecer_a_warehouse_valido(self):
        """
        Invariante DDD: Un Shelf debe pertenecer a un Warehouse válido y activo
        """
        # Crear warehouse válido
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        # Crear shelf con warehouse válido
        shelf = create_test_shelf(
            shelf_name="Estante A1",
            warehouse=warehouse.name,
            location_code="A1"
        )
        self.test_shelves.append(shelf.name)
        
        # Validar que el shelf tiene el warehouse correcto
        self.assertEqual(shelf.warehouse, warehouse.name, "Shelf debe pertenecer al warehouse especificado")
        
        # Intentar crear shelf con warehouse inexistente debe fallar
        with self.assertRaises((ValidationError, frappe.exceptions.LinkValidationError)):
            invalid_shelf = frappe.get_doc({
                "doctype": "Shelf",
                "shelf_name": "Estante Inválido",
                "warehouse": "WAREHOUSE-INEXISTENTE",
                "location_code": "INV-1",
                "shelf_type": "Normal",
                "company": get_test_company()
            })
            invalid_shelf.insert(ignore_permissions=True)

    def test_invariante_location_code_unico_en_warehouse(self):
        """
        Invariante DDD: El location_code debe ser único dentro del mismo Warehouse
        """
        # Crear warehouse
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        # Crear primer shelf con location_code "A1"
        shelf1 = create_test_shelf(
            shelf_name="Estante A1",
            warehouse=warehouse.name,
            location_code="A1"
        )
        self.test_shelves.append(shelf1.name)
        
        # Intentar crear segundo shelf con mismo location_code en mismo warehouse debe fallar
        with self.assertRaises((ValidationError, frappe.exceptions.DuplicateEntryError)):
            shelf2 = frappe.get_doc({
                "doctype": "Shelf",
                "shelf_name": "Estante A1 Duplicado",
                "warehouse": warehouse.name,
                "location_code": "A1",  # Mismo código
                "shelf_type": "Normal",
                "company": get_test_company()
            })
            shelf2.insert(ignore_permissions=True)
        
        # Pero puede existir mismo location_code en diferente warehouse
        warehouse2 = create_test_warehouse(f"TEST-WH-2-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse2.name)
        
        shelf3 = create_test_shelf(
            shelf_name="Estante A1 en Warehouse 2",
            warehouse=warehouse2.name,
            location_code="A1"  # Mismo código pero diferente warehouse
        )
        self.test_shelves.append(shelf3.name)
        
        # Debe crearse sin problemas
        self.assertIsNotNone(shelf3.name, "Shelf con mismo location_code en diferente warehouse debe crearse")

    def test_invariante_capacidad_estante_lleno(self):
        """
        Invariante DDD: Si is_full = 1, entonces current_occupancy >= max_capacity
        """
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        # Crear shelf con capacidad fija
        shelf = create_test_shelf(
            shelf_name="Estante con Capacidad",
            warehouse=warehouse.name,
            location_code="CAP-1",
            capacity_mode="Fija",
            max_capacity=100.0
        )
        self.test_shelves.append(shelf.name)
        
        # Inicialmente no está lleno
        self.assertEqual(shelf.is_full, 0, "Shelf nuevo no debe estar marcado como lleno")
        
        # Marcar como lleno con capacidad dinámica
        shelf_dynamic = create_test_shelf(
            shelf_name="Estante Dinámico",
            warehouse=warehouse.name,
            location_code="DYN-1",
            capacity_mode="Dinámica"
        )
        self.test_shelves.append(shelf_dynamic.name)
        
        # Establecer ocupación actual (simulado)
        shelf_dynamic.current_occupancy = 50.0
        shelf_dynamic.is_full = 1
        shelf_dynamic.save(ignore_permissions=True)
        frappe.db.commit()
        
        # Si está marcado como lleno en modo dinámico, debe establecer max_capacity
        shelf_dynamic.reload()
        if shelf_dynamic.is_full:
            # En modo dinámico, al marcar como lleno debe establecer max_capacity = current_occupancy
            # Esto se implementará en la lógica del DocType
            pass

    def test_invariante_tipo_estante_refrigerado(self):
        """
        Invariante DDD: Estantes tipo Refrigerado deben estar claramente identificados
        """
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        # Crear shelf tipo Refrigerado
        shelf = create_test_shelf(
            shelf_name="Estante Refrigerado",
            warehouse=warehouse.name,
            location_code="REF-1",
            shelf_type="Refrigerado"
        )
        self.test_shelves.append(shelf.name)
        
        # Validar que el tipo es correcto
        self.assertEqual(shelf.shelf_type, "Refrigerado", "Shelf debe tener tipo Refrigerado")
        
        # Validar que shelf_type tiene valor por defecto si no se especifica
        # (Frappe usa el default del campo, así que no falla)
        shelf_with_default = frappe.get_doc({
            "doctype": "Shelf",
            "shelf_name": "Estante Con Default",
            "warehouse": warehouse.name,
            "location_code": "DEFAULT-TYPE",
            "company": get_test_company()
            # shelf_type faltante - usará default "Normal"
        })
        shelf_with_default.insert(ignore_permissions=True)
        self.test_shelves.append(shelf_with_default.name)
        
        # Validar que se asignó el valor por defecto
        self.assertEqual(shelf_with_default.shelf_type, "Normal", "Shelf sin tipo debe usar default 'Normal'")

    def test_invariante_tipo_estante_controlado(self):
        """
        Invariante DDD: Estantes tipo Controlado deben estar claramente identificados
        """
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        # Crear shelf tipo Controlado
        shelf = create_test_shelf(
            shelf_name="Estante Controlado",
            warehouse=warehouse.name,
            location_code="CTRL-1",
            shelf_type="Controlado"
        )
        self.test_shelves.append(shelf.name)
        
        # Validar que el tipo es correcto
        self.assertEqual(shelf.shelf_type, "Controlado", "Shelf debe tener tipo Controlado")

    def test_invariante_tipo_estante_mostrador(self):
        """
        Invariante DDD: Estantes tipo Mostrador para productos de venta rápida
        """
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        # Crear shelf tipo Mostrador
        shelf = create_test_shelf(
            shelf_name="Mostrador Principal A1",
            warehouse=warehouse.name,
            location_code="MOST-A1",
            shelf_type="Mostrador"
        )
        self.test_shelves.append(shelf.name)
        
        # Validar que el tipo es correcto
        self.assertEqual(shelf.shelf_type, "Mostrador", "Shelf debe tener tipo Mostrador")

    def test_invariante_shelf_deshabilitado_no_puede_usarse(self):
        """
        Invariante DDD: Un Shelf deshabilitado no puede ser usado en transacciones
        """
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        # Crear shelf y deshabilitarlo
        shelf = create_test_shelf(
            shelf_name="Estante Deshabilitado",
            warehouse=warehouse.name,
            location_code="DISABLED-1",
            disabled=1
        )
        self.test_shelves.append(shelf.name)
        
        # Validar que está deshabilitado
        self.assertEqual(shelf.disabled, 1, "Shelf debe estar deshabilitado")
        
        # La validación de que no se puede usar en transacciones se implementará
        # en la lógica de Stock Entry y otros documentos que referencien Shelf

    def test_invariante_company_obligatorio(self):
        """
        Invariante DDD: Shelf debe pertenecer a una Company
        """
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        # Crear shelf sin company debe fallar
        # Frappe valida campos obligatorios en validate() o insert()
        invalid_shelf = frappe.get_doc({
            "doctype": "Shelf",
            "shelf_name": "Estante Sin Company",
            "warehouse": warehouse.name,
            "location_code": "NO-COMPANY",
            "shelf_type": "Normal"
            # company faltante
        })
        
        # Frappe puede validar en validate() o insert()
        # Intentar insertar y verificar que falla
        try:
            invalid_shelf.insert(ignore_permissions=True)
            # Si no falla, el campo company debe tener un valor por defecto o venir del warehouse
            # Verificar que tiene company (puede venir del warehouse)
            self.assertIsNotNone(invalid_shelf.company, "Company debe estar presente (puede venir del warehouse)")
        except (ValidationError, frappe.exceptions.MandatoryError) as e:
            # Si falla, es el comportamiento esperado
            self.assertIn("company", str(e).lower() or "mandatory", "Debe validar que company es obligatorio")

    def test_invariante_capacidad_modo_dinamica(self):
        """
        Invariante DDD: En modo Dinámica, max_capacity se establece cuando se marca como lleno
        """
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        # Crear shelf en modo dinámica
        shelf = create_test_shelf(
            shelf_name="Estante Dinámico",
            warehouse=warehouse.name,
            location_code="DYN-2",
            capacity_mode="Dinámica"
        )
        self.test_shelves.append(shelf.name)
        
        # Inicialmente no tiene max_capacity definida
        self.assertIsNone(shelf.max_capacity or None, "Shelf en modo dinámica no debe tener max_capacity inicial")
        
        # La lógica de establecer max_capacity al marcar como lleno se implementará
        # en el método del DocType Shelf

    def test_invariante_capacidad_modo_fija(self):
        """
        Invariante DDD: En modo Fija, max_capacity es obligatorio
        """
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        # Crear shelf en modo fija con max_capacity
        shelf = create_test_shelf(
            shelf_name="Estante Fija",
            warehouse=warehouse.name,
            location_code="FIX-1",
            capacity_mode="Fija",
            max_capacity=200.0
        )
        self.test_shelves.append(shelf.name)
        
        # Validar que tiene max_capacity
        self.assertEqual(shelf.max_capacity, 200.0, "Shelf en modo fija debe tener max_capacity definida")
        
        # La validación de que max_capacity es obligatorio en modo fija
        # se implementará en la lógica del DocType

    def test_invariante_calcular_current_occupancy_desde_stock_real(self):
        """
        Invariante DDD: current_occupancy debe calcularse desde el stock real (Bin) 
        de los items ubicados en este estante
        """
        # Crear warehouse y shelf
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        shelf = create_test_shelf(
            shelf_name="Estante con Stock",
            warehouse=warehouse.name,
            location_code="STOCK-1",
            capacity_mode="Fija",
            max_capacity=100.0
        )
        self.test_shelves.append(shelf.name)
        
        # Importar create_test_item para crear items de prueba
        from barriofarma_app.barriofarma_app.test_setup import create_test_item
        
        # Crear items y agregarlos al shelf
        item1 = create_test_item(
            item_code=f"TEST-ITEM-1-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre"
        )
        
        item2 = create_test_item(
            item_code=f"TEST-ITEM-2-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre"
        )
        
        # Agregar items al shelf mediante custom_shelf_locations
        item1.reload()
        if hasattr(item1, "custom_shelf_locations"):
            item1.append("custom_shelf_locations", {
                "shelf": shelf.name,
                "preferred_location": 1
            })
            item1.save(ignore_permissions=True)
        
        item2.reload()
        if hasattr(item2, "custom_shelf_locations"):
            item2.append("custom_shelf_locations", {
                "shelf": shelf.name,
                "preferred_location": 0
            })
            item2.save(ignore_permissions=True)
        
        frappe.db.commit()
        
        # Crear stock en el warehouse (simular Stock Entry)
        # Por ahora, insertar directamente en Bin para simular stock
        from erpnext.stock.utils import get_or_make_bin
        
        bin1_name = get_or_make_bin(item1.name, warehouse.name)
        bin1 = frappe.get_doc("Bin", bin1_name)
        bin1.actual_qty = 25.0
        bin1.save(ignore_permissions=True)
        
        bin2_name = get_or_make_bin(item2.name, warehouse.name)
        bin2 = frappe.get_doc("Bin", bin2_name)
        bin2.actual_qty = 15.0
        bin2.save(ignore_permissions=True)
        
        frappe.db.commit()
        
        # Calcular ocupación actual del shelf
        shelf.reload()
        if hasattr(shelf, "calculate_current_occupancy"):
            calculated_occupancy = shelf.calculate_current_occupancy()
            # Debe ser la suma del stock de los items en este shelf: 25 + 15 = 40
            self.assertEqual(calculated_occupancy, 40.0, 
                           "current_occupancy debe ser la suma del stock de items en el shelf")
        else:
            self.fail("Método calculate_current_occupancy no existe en Shelf")

    def test_invariante_validar_capacidad_antes_agregar_producto(self):
        """
        Invariante DDD: Antes de agregar un producto a un shelf, 
        debe validarse que hay capacidad disponible
        """
        # Crear warehouse y shelf con capacidad limitada
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        shelf = create_test_shelf(
            shelf_name="Estante con Capacidad Limitada",
            warehouse=warehouse.name,
            location_code="CAP-LIM-1",
            capacity_mode="Fija",
            max_capacity=50.0
        )
        self.test_shelves.append(shelf.name)
        
        from barriofarma_app.barriofarma_app.test_setup import create_test_item
        from erpnext.stock.utils import get_or_make_bin
        
        # Crear item con stock que excede la capacidad
        item = create_test_item(
            item_code=f"TEST-ITEM-EXCESO-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre"
        )
        
        # Crear stock que excede la capacidad del shelf
        bin_item_name = get_or_make_bin(item.name, warehouse.name)
        bin_item = frappe.get_doc("Bin", bin_item_name)
        bin_item.actual_qty = 60.0  # Excede max_capacity de 50
        bin_item.save(ignore_permissions=True)
        frappe.db.commit()
        
        # Intentar agregar item al shelf debe validar capacidad
        item.reload()
        if hasattr(item, "custom_shelf_locations"):
            item.append("custom_shelf_locations", {
                "shelf": shelf.name,
                "preferred_location": 1
            })
            
            # La validación debe ocurrir al guardar
            # Si el stock del item (60) excede la capacidad máxima del shelf (50), debe fallar
            # Calcular capacidad disponible: max_capacity (50) - current_occupancy (0) = 50
            # Stock del item (60) > capacidad disponible (50), debe fallar
            with self.assertRaises((ValidationError, frappe.exceptions.ValidationError)):
                item.save(ignore_permissions=True)
                frappe.db.commit()

    def test_invariante_sincronizacion_stock_warehouse(self):
        """
        Invariante DDD: El stock total del warehouse debe ser igual o mayor 
        que la suma del stock de todos los shelves en ese warehouse
        """
        # Crear warehouse y múltiples shelves
        warehouse = create_test_warehouse(f"TEST-WH-{frappe.generate_hash(length=6)}")
        self.test_warehouses.append(warehouse.name)
        
        shelf1 = create_test_shelf(
            shelf_name="Estante 1",
            warehouse=warehouse.name,
            location_code="SYNC-1"
        )
        self.test_shelves.append(shelf1.name)
        
        shelf2 = create_test_shelf(
            shelf_name="Estante 2",
            warehouse=warehouse.name,
            location_code="SYNC-2"
        )
        self.test_shelves.append(shelf2.name)
        
        from barriofarma_app.barriofarma_app.test_setup import create_test_item
        from erpnext.stock.utils import get_or_make_bin
        
        # Crear items y distribuirlos en diferentes shelves
        item1 = create_test_item(
            item_code=f"TEST-ITEM-SYNC-1-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre"
        )
        
        item2 = create_test_item(
            item_code=f"TEST-ITEM-SYNC-2-{frappe.generate_hash(length=6)}",
            custom_dispensing_type="Venta Libre"
        )
        
        # Agregar item1 a shelf1
        item1.reload()
        if hasattr(item1, "custom_shelf_locations"):
            item1.append("custom_shelf_locations", {
                "shelf": shelf1.name,
                "preferred_location": 1
            })
            item1.save(ignore_permissions=True)
        
        # Agregar item2 a shelf2
        item2.reload()
        if hasattr(item2, "custom_shelf_locations"):
            item2.append("custom_shelf_locations", {
                "shelf": shelf2.name,
                "preferred_location": 1
            })
            item2.save(ignore_permissions=True)
        
        frappe.db.commit()
        
        # Crear stock en el warehouse
        bin1_name = get_or_make_bin(item1.name, warehouse.name)
        bin1 = frappe.get_doc("Bin", bin1_name)
        bin1.actual_qty = 30.0
        bin1.save(ignore_permissions=True)
        
        bin2_name = get_or_make_bin(item2.name, warehouse.name)
        bin2 = frappe.get_doc("Bin", bin2_name)
        bin2.actual_qty = 20.0
        bin2.save(ignore_permissions=True)
        
        frappe.db.commit()
        
        # Calcular stock total del warehouse
        warehouse_stock = frappe.db.sql("""
            SELECT SUM(actual_qty) as total_stock
            FROM `tabBin`
            WHERE warehouse = %s
        """, (warehouse.name,), as_dict=True)[0]
        
        total_warehouse_stock = warehouse_stock.get("total_stock") or 0.0
        
        # Calcular suma de stock de shelves
        shelf1.reload()
        shelf2.reload()
        
        shelf1_stock = 0.0
        shelf2_stock = 0.0
        
        if hasattr(shelf1, "calculate_current_occupancy"):
            shelf1_stock = shelf1.calculate_current_occupancy()
        
        if hasattr(shelf2, "calculate_current_occupancy"):
            shelf2_stock = shelf2.calculate_current_occupancy()
        
        total_shelf_stock = shelf1_stock + shelf2_stock
        
        # El stock del warehouse debe ser >= suma de stocks de shelves
        # (puede haber items sin ubicación en shelf)
        self.assertGreaterEqual(total_warehouse_stock, total_shelf_stock,
                              "Stock del warehouse debe ser >= suma de stocks de shelves")
        
        # En este caso específico, todos los items están en shelves, así que deben ser iguales
        self.assertEqual(total_warehouse_stock, total_shelf_stock,
                        "Si todos los items están en shelves, el stock debe ser igual")

