# Módulo de Ventas Mejorado - Documentación Completa

## 📋 Características Implementadas

### ✅ 1. Facturación Profesional
- Generación automática de números de factura secuenciales
- Formato: `FAC-000001`, `CRE-000001`, `DEV-000001`
- Prefijos configurables por tipo de venta
- Control de secuencial en base de datos

### ✅ 2. Número Consecutivo Automático
- Secuencial para facturas de contado
- Secuencial para facturas de crédito
- Secuencial para devoluciones
- Facilidad para resetear (con auditoría)

### ✅ 3. Control de Stock
- Validación de stock antes de crear venta
- Descuento automático de stock al registrar venta
- Restauración de stock al cancelar venta
- Restauración de stock al procesar devolución

### ✅ 4. Validación de Productos
- Validación de existencia de productos
- Validación de stock disponible
- Validación de cantidades y precios
- Prevención de operaciones inválidas

### ✅ 5. Descuentos
- Descuentos porcentuales por factura
- Cálculo correcto de descuentos
- Aplicación antes del cálculo de impuestos

### ✅ 6. Impuestos Configurables
- Tabla de configuración de impuestos
- Impuesto IVA por defecto (configurable)
- Posibilidad de crear nuevos impuestos
- Activar/desactivar impuestos

### ✅ 7. Múltiples Métodos de Pago
- Efectivo
- Tarjeta de débito
- Tarjeta de crédito
- Transferencia bancaria
- Cheque
- Métodos personalizados extensibles

### ✅ 8. Ventas a Crédito
- Registro automático de deudas
- Control de vencimientos
- Seguimiento de pagos pendientes
- Estado de venta: CREDITO

### ✅ 9. Devoluciones
- Creación de devoluciones vinculadas a venta
- Número de devolución secuencial
- Gestión de productos devueltos
- Estados: PENDIENTE, APROBADA, PROCESADA, RECHAZADA

### ✅ 10. Cancelación con Auditoría
- Cancelación de ventas
- Registro completo en tabla de auditoría
- Datos originales guardados
- Usuario y motivo de cancelación registrados
- Restauración de stock automática

---

## 🚀 Uso del Módulo

### Importar el módulo

```python
from backend import ventas
```

### Crear una Venta Completa

```python
venta = ventas.crear_venta(
    cliente_id=1,
    usuario='admin',
    productos=[
        {
            'id_producto': 1,
            'cantidad': 2,
            'precio_unitario': 100.00
        },
        {
            'id_producto': 2,
            'cantidad': 1,
            'precio_unitario': 50.00
        }
    ],
    tipo_venta='CONTADO',
    metodo_pago='EFECTIVO',
    pagado=250.00,
    descuento_porcentaje=5.0,
    observaciones='Venta por encargo',
    vendedor='Juan Pérez',
    telefono_vendedor='+58-412-1234567'
)

print(venta)
# Retorna:
# {
#     'id': 1,
#     'numero_factura': 'FAC-000001',
#     'cliente_id': 1,
#     'tipo_venta': 'CONTADO',
#     'subtotal': 250.00,
#     'descuento_total': 12.50,
#     'impuesto_total': 11.88,
#     'total': 249.38,
#     'pagado': 250.00,
#     'saldo': 0.0,
#     'estado': 'PAGADA',
#     'productos': [...]
# }
```

### Crear una Venta a Crédito

```python
venta_credito = ventas.crear_venta(
    cliente_id=2,
    usuario='vendedor',
    productos=[
        {'id_producto': 3, 'cantidad': 5, 'precio_unitario': 75.00}
    ],
    metodo_pago='TARJETA_CREDITO',
    pagado=100.00,  # Pago parcial
    referencia_pago='4532123456789012'  # Número de tarjeta
)

# Estado se determina automáticamente como CREDITO
# Se registra deuda pendiente
```

### Crear una Devolución

```python
devolucion = ventas.crear_devolucion(
    venta_id=1,
    usuario='admin',
    productos=[
        {
            'id_producto': 1,
            'cantidad': 1,
            'precio_unitario': 100.00,
            'nombre': 'Producto Original'
        }
    ],
    motivo='Producto defectuoso',
    observaciones='Contacto del cliente: 412-123-4567'
)

print(devolucion)
# {
#     'id': 1,
#     'numero_devolucion': 'DEV-000001',
#     'venta_id': 1,
#     'cliente_id': 1,
#     'motivo': 'Producto defectuoso',
#     'total_devolucion': 100.00,
#     'productos': [...]
# }
```

### Cancelar una Venta

```python
# Solo administradores pueden cancelar
resultado = ventas.cancelar_venta(
    venta_id=1,
    usuario='admin',
    motivo='Cancelada por solicitud del cliente - reembolso total'
)

# Automáticamente:
# - Cambia estado a CANCELADA
# - Registra en auditoría
# - Restaura stock de productos
# - Registra en logs
```

### Obtener Venta Completa

```python
venta = ventas.obtener_venta_completa(venta_id=1)

# Retorna venta con:
# - Datos básicos
# - Detalles de productos
# - Devoluciones vinculadas
```

### Configurar Impuestos

```python
# Obtener impuesto actual
iva = ventas.obtener_impuesto('IVA')
print(iva)
# {'id': 1, 'nombre': 'IVA', 'porcentaje': 5.0, 'activo': True}

# Actualizar porcentaje de IVA
ventas.actualizar_impuesto('IVA', porcentaje=10.0, activo=True)

# Crear nuevo impuesto
impuesto_id = ventas.crear_impuesto('IMPUESTO_MUNICIPAL', 2.5)
```

### Gestionar Métodos de Pago

```python
# Obtener métodos disponibles
metodos = ventas.obtener_metodos_pago(solo_activos=True)

# Crear nuevo método de pago
nuevo_metodo = ventas.crear_metodo_pago(
    nombre='BILLETERA_DIGITAL',
    descripcion='Pago por billetera digital',
    requiere_referencia=True
)
```

### Generar Reportes

```python
# Resumen de ventas en un período
resumen = ventas.obtener_resumen_ventas(
    fecha_inicio='2026-08-01',
    fecha_fin='2026-08-31'
)

print(resumen)
# {
#     'periodo': '2026-08-01 a 2026-08-31',
#     'totales': {
#         'cantidad_ventas': 15,
#         'total_ventas': 5000.00,
#         'total_pagado': 4500.00,
#         'total_saldo': 500.00,
#         'total_descuentos': 150.00,
#         'total_impuestos': 225.00
#     },
#     'por_metodo_pago': [
#         {'tipo_pago': 'EFECTIVO', 'cantidad': 10, 'total': 3000.00},
#         {'tipo_pago': 'TARJETA', 'cantidad': 5, 'total': 2000.00}
#     ]
# }

# Ventas sin cobrar
pendientes = ventas.obtener_ventas_sin_cobrar()

# Ventas por estado
pagadas = ventas.obtener_ventas_por_estado('PAGADA')
credito = ventas.obtener_ventas_por_estado('CREDITO')

# Ventas por rango de fechas
del_mes = ventas.obtener_ventas_por_rango_fechas(
    fecha_inicio='2026-08-01',
    fecha_fin='2026-08-31'
)

# Historial de cancelaciones (auditoría)
cancelaciones = ventas.obtener_historial_cancelaciones()
```

---

## 🧪 Pruebas Automáticas

Ejecutar las pruebas:

```bash
# Desde el directorio raíz del proyecto
python -m pytest backend/test_ventas_advanced.py -v

# O con unittest
python -m unittest backend.test_ventas_advanced -v

# O ejecutar directamente
python backend/test_ventas_advanced.py
```

### Suites de pruebas incluidas:

1. **TestProductoVenta** - Tests para estructura de producto
2. **TestFactura** - Tests para factura completa
3. **TestDevolucion** - Tests para devoluciones
4. **TestValidacionesVentas** - Tests de validación
5. **TestCalculosFactura** - Tests de cálculos
6. **TestRepositorioAvanzado** - Tests de acceso a datos
7. **TestIntegracion** - Tests end-to-end
8. **TestSecuencial** - Tests de números secuenciales

---

## 📊 Estructura de Base de Datos

### Nuevas tablas creadas:

#### `configuracion_impuestos`
```sql
CREATE TABLE configuracion_impuestos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    porcentaje REAL NOT NULL DEFAULT 0,
    activo BOOLEAN DEFAULT 1,
    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TEXT
)
```

#### `secuencial_facturas`
```sql
CREATE TABLE secuencial_facturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_venta TEXT NOT NULL UNIQUE,
    numero_actual INTEGER NOT NULL DEFAULT 0,
    prefijo TEXT DEFAULT '',
    fecha_modificacion TEXT DEFAULT CURRENT_TIMESTAMP
)
```

#### `metodos_pago`
```sql
CREATE TABLE metodos_pago (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    descripcion TEXT,
    requiere_referencia BOOLEAN DEFAULT 0,
    activo BOOLEAN DEFAULT 1,
    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
)
```

#### `devoluciones`
```sql
CREATE TABLE devoluciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id INTEGER NOT NULL,
    numero_devolucion TEXT NOT NULL UNIQUE,
    fecha TEXT NOT NULL,
    cliente_id INTEGER NOT NULL,
    usuario TEXT NOT NULL,
    motivo TEXT,
    estado TEXT DEFAULT 'PENDIENTE',
    observaciones TEXT,
    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (venta_id) REFERENCES ventas(id),
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
)
```

#### `devolucion_detalle`
```sql
CREATE TABLE devolucion_detalle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    devolucion_id INTEGER NOT NULL,
    producto_id INTEGER NOT NULL,
    cantidad REAL NOT NULL,
    precio_unitario REAL NOT NULL,
    subtotal REAL NOT NULL,
    razon TEXT,
    FOREIGN KEY (devolucion_id) REFERENCES devoluciones(id) ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES productos(id)
)
```

#### `ventas_canceladas`
```sql
CREATE TABLE ventas_canceladas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id INTEGER NOT NULL,
    fecha_cancelacion TEXT NOT NULL,
    usuario_cancelacion TEXT NOT NULL,
    motivo TEXT,
    datos_originales TEXT,
    fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP
)
```

### Campos agregados a tablas existentes:

#### `ventas`
- `numero_factura TEXT UNIQUE` - Número de factura
- `estado TEXT DEFAULT 'ACTIVA'` - Estado actual
- `fecha_cancelacion TEXT` - Fecha de cancelación
- `tipo_cliente TEXT DEFAULT 'CONTADO'` - Tipo de venta
- `descuento_total REAL DEFAULT 0` - Total de descuentos
- `impuesto_total REAL DEFAULT 0` - Total de impuestos
- `referencia_pago TEXT` - Referencia del pago

---

## 🔄 Flujos de Negocio Soportados

### Flujo 1: Venta de Contado Simple
1. Cliente elige productos
2. Sistema calcula subtotal, descuentos e impuestos
3. Se paga el total completo
4. Venta se marca como PAGADA
5. Stock se descuenta automáticamente
6. Se genera número de factura FAC-000001

### Flujo 2: Venta a Crédito
1. Cliente elige productos
2. Se registra venta con tipo CREDITO
3. Se crea registro de deuda
4. Cliente puede hacer pagos parciales
5. Al pagar total, venta se marca como PAGADA
6. Si queda saldo, permanece en CREDITO

### Flujo 3: Devolución de Producto
1. Cliente regresa producto de venta anterior
2. Se crea número de devolución DEV-000001
3. Stock se restaura automáticamente
4. Se registra motivo de devolución
5. Se puede aplicar reembolso al cliente
6. Devolución se puede aprobar o rechazar

### Flujo 4: Cancelación de Venta (Auditoría)
1. Administrador solicita cancelación
2. Se valida que venta sea cancelable
3. Se cambia estado a CANCELADA
4. Datos originales se guardan en auditoría
5. Stock se restaura
6. Se registra usuario y motivo en logs
7. Historial es inmutable para trazabilidad

---

## 📚 Tipos de Datos

### EstadoVenta
- `ACTIVA` - Venta activa sin pagar
- `PAGADA` - Venta pagada completamente
- `PARCIALMENTE_PAGADA` - Venta con pago parcial
- `CREDITO` - Venta a crédito
- `CANCELADA` - Venta cancelada
- `ANULADA` - Venta anulada

### TipoVenta
- `CONTADO` - Venta de contado
- `CREDITO` - Venta a crédito
- `DEVOLUCION` - Devolución de producto

### EstadoDevolucion
- `PENDIENTE` - Devolución registrada, pendiente de aprobación
- `APROBADA` - Devolución aprobada
- `PROCESADA` - Devolución procesada
- `RECHAZADA` - Devolución rechazada

### MetodoPago
- `EFECTIVO` - Pago en efectivo
- `TARJETA_DEBITO` - Tarjeta de débito
- `TARJETA_CREDITO` - Tarjeta de crédito
- `TRANSFERENCIA` - Transferencia bancaria
- `CHEQUE` - Pago con cheque

---

## 🔐 Validaciones

El módulo incluye validaciones automáticas para:

- ✅ Cliente existe en base de datos
- ✅ Producto existe y tiene stock
- ✅ Cantidades son positivas
- ✅ Precios no son negativos
- ✅ Método de pago es válido
- ✅ Referencia de pago cuando se requiere
- ✅ Descuentos están entre 0-100%
- ✅ Pago no excede total de venta
- ✅ Motivo de cancelación no está vacío

---

## 📝 Logging y Auditoría

Todas las operaciones se registran automáticamente:

```python
# Logs registrados para:
- crear_venta
- crear_devolucion
- cancelar_venta
- ajustes de stock
- cambios de impuestos
- cambios de métodos de pago
```

Los datos se guardan en tabla `logs` con:
- Usuario que realizó la acción
- Acción realizada
- Detalles en JSON
- Fecha y hora

---

## 🎯 Próximas Mejoras Posibles

1. Auto-liquidación de facturas
2. Reportes PDF profesionales
3. Integración con sistema de inventario en tiempo real
4. Notificaciones de deudas vencidas
5. Descuentos por volumen
6. Planes de pago a plazos
7. Integración con pasarelas de pago
8. Exportación de datos a contabilidad

---

## 📞 Soporte

Para reportar bugs o sugerencias:
1. Revisar logs en `backend/logs` 
2. Ejecutar pruebas con `test_ventas_advanced.py`
3. Contactar al equipo de desarrollo

---

**Módulo creado:** Agosto 2026
**Versión:** 2.0 - Completamente rediseñado
**Estado:** Producción
