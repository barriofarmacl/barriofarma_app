# Escenarios de Uso - Cobertura de Tests

## Resumen de Tests Existentes

### Tests DDD de Shelf (13 tests)
1. ✅ Shelf debe pertenecer a warehouse válido y activo
2. ✅ location_code único dentro del mismo warehouse
3. ✅ Validación de capacidad cuando estante está lleno
4. ✅ Tipos de estante: Refrigerado, Controlado, Mostrador
5. ✅ Estante deshabilitado no puede usarse
6. ✅ Company obligatorio
7. ✅ Modo de capacidad Dinámica
8. ✅ Modo de capacidad Fija
9. ✅ Cálculo de current_occupancy desde stock real (Bin)
10. ✅ Validación de capacidad antes de agregar productos
11. ✅ Sincronización stock warehouse vs shelves

### Tests DDD de Item-Shelf (6 tests)
1. ✅ Item puede estar en múltiples shelves
2. ✅ Shelf puede contener múltiples items
3. ✅ Estante Refrigerado solo productos refrigerados
4. ✅ Estante Controlado solo productos controlados
5. ✅ Solo una ubicación preferida por item
6. ✅ Shelf debe existir al asignar item

### Tests DDD de Shelf Movement (8 tests)
1. ✅ Tipo de movimiento válido (Transferencia, Recepción, Venta, Ajuste)
2. ✅ Shelf válido y no deshabilitado
3. ✅ Item válido
4. ✅ Cantidad positiva
5. ✅ Registro automático de usuario
6. ✅ Registro automático de fecha
7. ✅ Transferencia requiere shelf destino
8. ✅ Consulta de historial por shelf

### Tests E2E Stock Entry (4 tests)
1. ✅ Transferencia entre estantes crea Shelf Movement automáticamente
2. ✅ Recepción en estante crea Shelf Movement automáticamente
3. ✅ Validación de capacidad antes de transferir
4. ✅ Validación de tipo de estante compatible con producto

## Escenarios de Uso Comunes en Farmacia

### Escenarios de Gestión de Estantes
- [ ] Crear nuevo estante con código único
- [ ] Marcar estante como lleno (modo dinámico)
- [ ] Consultar ocupación actual de un estante
- [ ] Deshabilitar estante temporalmente
- [ ] Reorganizar productos entre estantes

### Escenarios de Asignación de Productos
- [ ] Asignar producto nuevo a estante
- [ ] Cambiar ubicación preferida de un producto
- [ ] Mover producto de un estante a otro
- [ ] Validar que producto refrigerado va a estante refrigerado
- [ ] Validar que producto controlado va a estante controlado

### Escenarios de Movimientos de Stock
- [ ] Recepción de mercadería nueva en estante específico
- [ ] Transferencia de productos entre estantes
- [ ] Venta de productos desde estante específico
- [ ] Ajuste de inventario en estante
- [ ] Consultar historial de movimientos de un estante
- [ ] Consultar historial de movimientos de un producto

### Escenarios de Capacidad
- [ ] Estante alcanza capacidad máxima
- [ ] Intentar agregar más productos de los que caben
- [ ] Liberar espacio al vender productos
- [ ] Reorganizar para optimizar espacio

### Escenarios de Validación
- [ ] Producto no refrigerado en estante refrigerado (debe fallar)
- [ ] Producto sin control en estante controlado (debe fallar)
- [ ] Transferencia a estante deshabilitado (debe fallar)
- [ ] Transferencia excediendo capacidad (debe fallar)

## Escenarios Pendientes de Validar

Por favor, comparte los escenarios específicos que quieres revisar y validaremos si están cubiertos o si necesitamos agregar tests adicionales.

