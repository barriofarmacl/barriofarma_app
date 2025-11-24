# Análisis de Cobertura: Flujo Completo de Compra → Recepción → Asignación → Venta

## Flujo Descrito

1. **Administrador carga items** que puede vender la farmacia
2. **Químico genera orden de compra** basada en stock necesario para la semana
3. **Se da curso a la orden** y se hace solicitud al proveedor
4. **Se generan documentos asociados** hasta la recepción en bodega
5. **Se guarda en bodega** (Warehouse)
6. **Se asignan a estantes físicos** (Shelf)
7. **En POS se ve reflejada** la mercadería nueva

## Análisis Paso a Paso

### Paso 1: Administrador carga items ✅ PARCIALMENTE CUBIERTO
**Escenario:** Crear nuevos productos que la farmacia puede vender

**Tests Existentes:**
- ✅ `test_item_farmaceutico_ddd.py` - Validaciones de tipo de producto (Venta Libre, Receta Retenida)
- ✅ Validaciones de campos obligatorios (registro sanitario, nivel de control, etc.)

**Gaps Identificados:**
- ❌ No hay test E2E del flujo completo de creación de item nuevo


**Cobertura:** 70% - Tenemos validaciones DDD pero falta flujo E2E completo

---

### Paso 2: Químico genera orden de compra ❌ NO CUBIERTO
**Escenario:** Crear Purchase Order basado en stock necesario

**Tests Existentes:**
- ❌ No hay tests de Purchase Order
- ❌ No hay tests de cálculo de stock necesario
- ❌ No hay tests de generación automática de PO

**Gaps Identificados:**
- ❌ Falta test de creación de Purchase Order
- ❌ Falta test de cálculo de stock necesario vs stock actual
- ❌ Falta test de asignación de items a Purchase Order

**Cobertura:** 0% - No hay tests para este paso

---

### Paso 3: Se da curso a la orden y solicitud al proveedor ❌ NO CUBIERTO
**Escenario:** Aprobar y enviar Purchase Order al proveedor

**Tests Existentes:**
- ❌ No hay tests de workflow de Purchase Order
- ❌ No hay tests de envío/notificación al proveedor

**Gaps Identificados:**
- ❌ Falta test de submit de Purchase Order
- ❌ Falta test de estados de Purchase Order

**Cobertura:** 0% - No hay tests para este paso

---

### Paso 4: Se generan documentos hasta recepción en bodega ✅ PARCIALMENTE CUBIERTO
**Escenario:** Purchase Receipt desde Purchase Order

**Tests Existentes:**
- ✅ `test_purchase_receipt_ddd.py` - Validaciones DDD de Purchase Receipt
- ✅ `test_purchase_receipt_expiry_threshold_ddd.py` - Validaciones de umbral de vencimiento
- ✅ `test_purchase_receipt_invoice_ddd.py` - Validaciones de facturación

**Gaps Identificados:**
- ❌ No hay test E2E de creación de Purchase Receipt desde Purchase Order
- ❌ No hay test que valide que el stock se actualiza correctamente en Warehouse

**Cobertura:** 60% - Tenemos validaciones DDD pero falta flujo E2E completo

---

### Paso 5: Se guarda en bodega ✅ CUBIERTO
**Escenario:** Stock se actualiza en Warehouse después de Purchase Receipt

**Tests Existentes:**
- ✅ `test_shelf_ddd.py::test_invariante_sincronizacion_stock_warehouse` - Valida sincronización
- ✅ `test_shelf_ddd.py::test_invariante_calcular_current_occupancy_desde_stock_real` - Valida cálculo desde Bin

**Cobertura:** 100% - Está cubierto

---

### Paso 6: Se asignan a estantes físicos ✅ PARCIALMENTE CUBIERTO
**Escenario:** Asignar productos recibidos a estantes específicos

**Tests Existentes:**
- ✅ `test_item_shelf_ddd.py` - Tests de relación Item-Shelf
- ✅ `test_shelf_stock_entry_e2e.py::test_e2e_stock_entry_recepcion_en_estante` - Recepción con estante

**Gaps Identificados:**
- ❌ No hay test E2E que valide: Purchase Receipt → Stock Entry → Asignación a Shelf
- ❌ No hay test que valide asignación automática basada en ubicación preferida del item
- ❌ No hay test que valide que después de asignar, el current_occupancy se actualiza

**Cobertura:** 70% - Tenemos tests de asignación pero falta flujo completo desde Purchase Receipt

---

### Paso 7: En POS se ve reflejada la mercadería nueva ❌ NO CUBIERTO
**Escenario:** Productos asignados a estantes aparecen disponibles en POS

**Tests Existentes:**
- ❌ No hay tests de integración POS con Shelf
- ❌ No hay tests que validen que productos en estantes están disponibles para venta
- ❌ No hay tests de consulta de stock por estante en POS

**Gaps Identificados:**
- ❌ Falta test E2E: Item asignado a Shelf → Disponible en POS
- ❌ Falta test de consulta de disponibilidad por estante
- ❌ Falta test de venta desde estante específico

**Cobertura:** 0% - No hay tests para este paso

---

## Resumen de Cobertura

| Paso | Escenario | Cobertura | Estado |
|------|-----------|-----------|--------|
| 1 | Carga de items | 70% | ⚠️ Parcial |
| 2 | Generación orden compra | 0% | ❌ No cubierto |
| 3 | Aprobación y envío PO | 0% | ❌ No cubierto |
| 4 | Recepción en bodega | 60% | ⚠️ Parcial |
| 5 | Guardado en bodega | 100% | ✅ Cubierto |
| 6 | Asignación a estantes | 70% | ⚠️ Parcial |
| 7 | Disponibilidad en POS | 0% | ❌ No cubierto |

**Cobertura Total del Flujo:** ~43%

## Tests Recomendados para Completar el Flujo

### Test E2E 1: Flujo Completo de Compra → Recepción → Asignación
```python
def test_e2e_flujo_completo_compra_recepcion_asignacion():
    """
    Test E2E: Flujo completo desde Purchase Order hasta asignación en estante
    1. Crear Purchase Order con items
    2. Enviar Purchase Order
    3. Crear Purchase Receipt desde PO
    4. Crear Stock Entry de recepción con estante destino
    5. Verificar que items están asignados a estantes
    6. Verificar que current_occupancy se actualiza
    """
```

### Test E2E 2: Asignación Automática Basada en Ubicación Preferida
```python
def test_e2e_asignacion_automatica_ubicacion_preferida():
    """
    Test E2E: Al recibir productos, asignar automáticamente a ubicación preferida
    1. Item tiene ubicación preferida definida
    2. Al recibir en Purchase Receipt, crear Stock Entry con estante preferido
    3. Verificar asignación automática
    """
```

### Test E2E 3: Disponibilidad en POS después de Asignación
```python
def test_e2e_disponibilidad_pos_despues_asignacion():
    """
    Test E2E: Productos asignados a estantes están disponibles en POS
    1. Recibir productos y asignar a estantes
    2. Verificar que productos aparecen disponibles en POS
    3. Verificar que se puede consultar stock por estante
    """
```

### Test E2E 4: Flujo Completo con Validaciones
```python
def test_e2e_flujo_completo_con_validaciones():
    """
    Test E2E: Flujo completo con todas las validaciones
    1. Producto refrigerado → debe ir a estante refrigerado
    2. Producto controlado → debe ir a estante controlado
    3. Validar capacidad antes de asignar
    4. Verificar historial de movimientos
    """
```

## Próximos Pasos Sugeridos

1. **Prioridad Alta:** Crear tests E2E del flujo completo Purchase Receipt → Stock Entry → Shelf
2. **Prioridad Media:** Crear tests de Purchase Order (si es parte del scope)
3. **Prioridad Media:** Crear tests de integración POS-Shelf
4. **Prioridad Baja:** Optimizar tests existentes para mejor cobertura

