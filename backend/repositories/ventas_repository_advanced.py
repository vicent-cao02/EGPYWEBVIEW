"""
Repositorio mejorado para ventas con todas las funcionalidades avanzadas.
Incluye números de factura secuenciales, devoluciones, impuestos y auditoría.
"""

from typing import Dict, List, Optional, Any
import json
from datetime import datetime

from backend.database import db


class VentasRepositoryAvanced:
    """
    Repositorio avanzado para operaciones de ventas.
    Maneja:
    - Números de factura secuenciales
    - Devoluciones
    - Configuración de impuestos
    - Métodos de pago
    - Auditoría de cancellaciones
    """

    def __init__(self, conn=None):
        self.conn = conn

    # =====================================================
    # HELPERS
    # =====================================================

    def _execute(self, query, params=()):
        if self.conn:
            cursor = self.conn.execute(query, params)
            return cursor
        with db.transaction() as conn:
            cursor = conn.execute(query, params)
            return cursor

    def _fetchall(self, query, params=()):
        if self.conn:
            cursor = self.conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        return db.fetchall(query, params)

    def _fetchone(self, query, params=()):
        if self.conn:
            cursor = self.conn.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
        return db.fetchone(query, params)

    # =====================================================
    # SECUENCIAL DE FACTURAS
    # =====================================================

    def obtener_siguiente_numero_factura(self, tipo_venta: str = "CONTADO") -> str:
        """
        Obtiene el siguiente número de factura disponible.
        Incrementa el contador automáticamente.
        """
        cursor = self._execute("""
            UPDATE secuencial_facturas
            SET numero_actual = numero_actual + 1,
                fecha_modificacion = CURRENT_TIMESTAMP
            WHERE tipo_venta = ?
        """, (tipo_venta,))

        if cursor.rowcount == 0:
            # Crear entrada si no existe
            self._execute("""
                INSERT INTO secuencial_facturas (tipo_venta, numero_actual, prefijo)
                VALUES (?, 1, ?)
            """, (tipo_venta, tipo_venta[:3]))

            numero = 1
            prefijo = tipo_venta[:3]
        else:
            # Obtener el nuevo número
            resultado = self._fetchone("""
                SELECT numero_actual, prefijo
                FROM secuencial_facturas
                WHERE tipo_venta = ?
            """, (tipo_venta,))
            numero = resultado["numero_actual"]
            prefijo = resultado["prefijo"]

        return f"{prefijo}-{numero:06d}"

    def obtener_secuencial_actual(self, tipo_venta: str = "CONTADO") -> Dict[str, Any]:
        """Obtiene la configuración actual del secuencial"""
        return self._fetchone("""
            SELECT id, tipo_venta, numero_actual, prefijo, fecha_modificacion
            FROM secuencial_facturas
            WHERE tipo_venta = ?
        """, (tipo_venta,))

    def resetear_secuencial(self, tipo_venta: str) -> bool:
        """Resetea el secuencial a 0 (requiere auditoría)"""
        cursor = self._execute("""
            UPDATE secuencial_facturas
            SET numero_actual = 0, fecha_modificacion = CURRENT_TIMESTAMP
            WHERE tipo_venta = ?
        """, (tipo_venta,))
        return cursor.rowcount > 0

    # =====================================================
    # CONFIGURACIÓN DE IMPUESTOS
    # =====================================================

    def obtener_impuestos(self) -> List[Dict[str, Any]]:
        """Obtiene todos los impuestos configurados"""
        return self._fetchall("""
            SELECT id, nombre, porcentaje, activo, fecha_creacion, fecha_modificacion
            FROM configuracion_impuestos
            ORDER BY nombre
        """)

    def obtener_impuesto(self, nombre: str) -> Optional[Dict[str, Any]]:
        """Obtiene un impuesto específico"""
        return self._fetchone("""
            SELECT id, nombre, porcentaje, activo
            FROM configuracion_impuestos
            WHERE nombre = ?
        """, (nombre,))

    def crear_impuesto(self, nombre: str, porcentaje: float) -> int:
        """Crea un nuevo impuesto"""
        cursor = self._execute("""
            INSERT INTO configuracion_impuestos (nombre, porcentaje, activo)
            VALUES (?, ?, 1)
        """, (nombre, porcentaje))
        return cursor.lastrowid

    def actualizar_impuesto(self, nombre: str, porcentaje: float, activo: bool = True) -> bool:
        """Actualiza la configuración de un impuesto"""
        cursor = self._execute("""
            UPDATE configuracion_impuestos
            SET porcentaje = ?, activo = ?, fecha_modificacion = CURRENT_TIMESTAMP
            WHERE nombre = ?
        """, (porcentaje, 1 if activo else 0, nombre))
        return cursor.rowcount > 0

    # =====================================================
    # MÉTODOS DE PAGO
    # =====================================================

    def obtener_metodos_pago(self, solo_activos: bool = True) -> List[Dict[str, Any]]:
        """Obtiene todos los métodos de pago configurados"""
        query = "SELECT id, nombre, descripcion, requiere_referencia, activo FROM metodos_pago"
        if solo_activos:
            query += " WHERE activo = 1"
        query += " ORDER BY nombre"
        return self._fetchall(query)

    def obtener_metodo_pago(self, nombre: str) -> Optional[Dict[str, Any]]:
        """Obtiene un método de pago específico"""
        return self._fetchone("""
            SELECT id, nombre, descripcion, requiere_referencia, activo
            FROM metodos_pago
            WHERE nombre = ?
        """, (nombre,))

    def crear_metodo_pago(
        self,
        nombre: str,
        descripcion: str = "",
        requiere_referencia: bool = False
    ) -> int:
        """Crea un nuevo método de pago"""
        cursor = self._execute("""
            INSERT INTO metodos_pago (nombre, descripcion, requiere_referencia, activo)
            VALUES (?, ?, ?, 1)
        """, (nombre, descripcion, 1 if requiere_referencia else 0))
        return cursor.lastrowid

    # =====================================================
    # FACTURA
    # =====================================================

    def crear_venta_completa(
        self,
        cliente_id: int,
        usuario: str,
        tipo_venta: str,
        metodo_pago: str,
        productos: List[Dict],
        pagado: float,
        observaciones: Optional[str] = None,
        vendedor: Optional[str] = None,
        telefono_vendedor: Optional[str] = None,
        chofer: Optional[str] = None,
        chapa: Optional[str] = None,
        referencia_pago: Optional[str] = None,
        descuento_total: float = 0.0,
        impuesto_total: float = 0.0,
    ) -> int:
        """
        Crea una venta completa con todos los detalles.
        Retorna el ID de la venta creada.
        """
        # Obtener número de factura
        numero_factura = self.obtener_siguiente_numero_factura(tipo_venta)

        # Calcular montos
        subtotal = sum(p["subtotal"] for p in productos)
        total = subtotal - descuento_total + impuesto_total
        saldo = round(total - pagado, 2)

        # Determinar estado
        estado = "PAGADA" if saldo <= 0 else ("CREDITO" if tipo_venta == "CREDITO" else "ACTIVA")

        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Insertar venta
        cursor = self._execute("""
            INSERT INTO ventas (
                cliente_id, numero_factura, fecha, estado, tipo_venta, 
                subtotal, descuento_total, impuesto_total,
                pagado, saldo, total, tipo_pago, usuario,
                observaciones, vendedor, telefono_vendedor, chofer, chapa, referencia_pago
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cliente_id, numero_factura, fecha, estado, tipo_venta,
            subtotal, descuento_total, impuesto_total,
            pagado, saldo, total, metodo_pago, usuario,
            observaciones, vendedor, telefono_vendedor, chofer, chapa, referencia_pago
        ))

        venta_id = cursor.lastrowid

        # Crear detalles de venta
        for producto in productos:
            self._execute("""
                INSERT INTO venta_detalle (
                    venta_id, producto_id, cantidad, precio_unitario,
                    descuento, subtotal
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                venta_id,
                producto["id_producto"],
                producto["cantidad"],
                producto["precio_unitario"],
                producto.get("descuento", 0),
                producto["subtotal"]
            ))

        return venta_id

    def actualizar_estado_venta(
        self,
        venta_id: int,
        nuevo_estado: str
    ) -> bool:
        """Actualiza el estado de una venta"""
        cursor = self._execute("""
            UPDATE ventas
            SET estado = ?
            WHERE id = ?
        """, (nuevo_estado, venta_id))
        return cursor.rowcount > 0

    def obtener_venta_completa(self, venta_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene una venta con todos sus detalles"""
        venta = self._fetchone("SELECT * FROM ventas WHERE id = ?", (venta_id,))
        if not venta:
            return None

        # Obtener detalles
        detalles = self._fetchall(
            "SELECT * FROM venta_detalle WHERE venta_id = ?",
            (venta_id,)
        )
        venta["detalles"] = detalles

        # Obtener devoluciones asociadas
        devoluciones = self._fetchall(
            "SELECT * FROM devoluciones WHERE venta_id = ?",
            (venta_id,)
        )
        venta["devoluciones"] = devoluciones

        return venta

    # =====================================================
    # DEVOLUCIONES
    # =====================================================

    def crear_devolucion(
        self,
        venta_id: int,
        cliente_id: int,
        usuario: str,
        productos: List[Dict],
        motivo: str,
        observaciones: Optional[str] = None,
    ) -> int:
        """Crea una devolución de venta"""
        # Obtener número de devolucion
        numero_devolucion = self.obtener_siguiente_numero_factura("DEVOLUCION")

        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor = self._execute("""
            INSERT INTO devoluciones (
                venta_id, numero_devolucion, fecha, cliente_id,
                usuario, motivo, estado, observaciones
            ) VALUES (?, ?, ?, ?, ?, ?, 'PENDIENTE', ?)
        """, (
            venta_id, numero_devolucion, fecha, cliente_id,
            usuario, motivo, observaciones
        ))

        devolucion_id = cursor.lastrowid

        # Crear detalles de devolución
        for producto in productos:
            self._execute("""
                INSERT INTO devolucion_detalle (
                    devolucion_id, producto_id, cantidad,
                    precio_unitario, subtotal, razon
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                devolucion_id,
                producto["id_producto"],
                producto["cantidad"],
                producto["precio_unitario"],
                producto["subtotal"],
                producto.get("razon", "")
            ))

        return devolucion_id

    def obtener_devolucion(self, devolucion_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene una devolución con sus detalles"""
        devolucion = self._fetchone(
            "SELECT * FROM devoluciones WHERE id = ?",
            (devolucion_id,)
        )
        if not devolucion:
            return None

        # Obtener detalles
        detalles = self._fetchall(
            "SELECT * FROM devolucion_detalle WHERE devolucion_id = ?",
            (devolucion_id,)
        )
        devolucion["detalles"] = detalles

        return devolucion

    def obtener_devoluciones_venta(self, venta_id: int) -> List[Dict[str, Any]]:
        """Obtiene todas las devoluciones de una venta"""
        return self._fetchall(
            "SELECT * FROM devoluciones WHERE venta_id = ? ORDER BY fecha DESC",
            (venta_id,)
        )

    def actualizar_estado_devolucion(
        self,
        devolucion_id: int,
        nuevo_estado: str
    ) -> bool:
        """Actualiza el estado de una devolución"""
        cursor = self._execute("""
            UPDATE devoluciones
            SET estado = ?
            WHERE id = ?
        """, (nuevo_estado, devolucion_id))
        return cursor.rowcount > 0

    # =====================================================
    # CANCELACIÓN CON AUDITORÍA
    # =====================================================

    def cancelar_venta(
        self,
        venta_id: int,
        usuario: str,
        motivo: str
    ) -> bool:
        """
        Cancela una venta y registra en auditoría.
        Requiere permisos de administrador.
        """
        # Obtener datos originales
        venta = self._fetchone("SELECT * FROM ventas WHERE id = ?", (venta_id,))
        if not venta:
            return False

        datos_originales = json.dumps(dict(venta), default=str, ensure_ascii=False)
        fecha_cancelacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Actualizar venta
        cursor = self._execute("""
            UPDATE ventas
            SET estado = 'CANCELADA', fecha_cancelacion = ?
            WHERE id = ?
        """, (fecha_cancelacion, venta_id))

        if cursor.rowcount == 0:
            return False

        # Registrar en auditoría
        self._execute("""
            INSERT INTO ventas_canceladas (
                venta_id, fecha_cancelacion, usuario_cancelacion,
                motivo, datos_originales
            ) VALUES (?, ?, ?, ?, ?)
        """, (venta_id, fecha_cancelacion, usuario, motivo, datos_originales))

        return True

    def obtener_venta_cancelada(self, venta_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene el registro de cancelación de una venta"""
        return self._fetchone(
            "SELECT * FROM ventas_canceladas WHERE venta_id = ?",
            (venta_id,)
        )

    def obtener_historial_cancelaciones(self) -> List[Dict[str, Any]]:
        """Obtiene el historial completo de cancelaciones"""
        return self._fetchall("""
            SELECT vc.*, v.cliente_id, c.nombre as cliente_nombre
            FROM ventas_canceladas vc
            JOIN ventas v ON vc.venta_id = v.id
            JOIN clientes c ON v.cliente_id = c.id
            ORDER BY vc.fecha_cancelacion DESC
        """)

    # =====================================================
    # REPORTES Y BÚSQUEDAS
    # =====================================================

    def obtener_ventas_por_estado(self, estado: str) -> List[Dict[str, Any]]:
        """Obtiene todas las ventas con un estado específico"""
        return self._fetchall("""
            SELECT * FROM ventas
            WHERE estado = ?
            ORDER BY fecha DESC
        """, (estado,))

    def obtener_ventas_por_rango_fechas(
        self,
        fecha_inicio: str,
        fecha_fin: str
    ) -> List[Dict[str, Any]]:
        """Obtiene ventas dentro de un rango de fechas"""
        return self._fetchall("""
            SELECT * FROM ventas
            WHERE DATE(fecha) BETWEEN ? AND ?
            ORDER BY fecha DESC
        """, (fecha_inicio, fecha_fin))

    def obtener_ventas_sin_cobrar(self) -> List[Dict[str, Any]]:
        """Obtiene todas las ventas con saldo pendiente"""
        return self._fetchall("""
            SELECT v.*, c.nombre as cliente_nombre, c.telefono
            FROM ventas v
            JOIN clientes c ON v.cliente_id = c.id
            WHERE v.saldo > 0 AND v.estado != 'CANCELADA'
            ORDER BY v.fecha DESC
        """)

    def obtener_total_ventas_por_periodo(
        self,
        fecha_inicio: str,
        fecha_fin: str
    ) -> Dict[str, float]:
        """Calcula totales de ventas en un período"""
        resultado = self._fetchone("""
            SELECT
                COUNT(*) as cantidad_ventas,
                SUM(total) as total_ventas,
                SUM(pagado) as total_pagado,
                SUM(saldo) as total_saldo,
                SUM(descuento_total) as total_descuentos,
                SUM(impuesto_total) as total_impuestos
            FROM ventas
            WHERE DATE(fecha) BETWEEN ? AND ? AND estado != 'CANCELADA'
        """, (fecha_inicio, fecha_fin))

        return resultado or {
            "cantidad_ventas": 0,
            "total_ventas": 0,
            "total_pagado": 0,
            "total_saldo": 0,
            "total_descuentos": 0,
            "total_impuestos": 0,
        }

    def obtener_ventas_por_metodo_pago(
        self,
        fecha_inicio: str = None,
        fecha_fin: str = None
    ) -> List[Dict[str, Any]]:
        """Agrupa ventas por método de pago"""
        query = """
            SELECT tipo_pago, COUNT(*) as cantidad, SUM(total) as total
            FROM ventas
            WHERE estado != 'CANCELADA'
        """
        params = []

        if fecha_inicio and fecha_fin:
            query += " AND DATE(fecha) BETWEEN ? AND ?"
            params = [fecha_inicio, fecha_fin]

        query += " GROUP BY tipo_pago ORDER BY total DESC"

        return self._fetchall(query, params)
