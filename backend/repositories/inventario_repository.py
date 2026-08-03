"""
Repositorio de inventario.
Acceso a datos para movimientos, entradas, salidas, ajustes y alertas.
"""

from typing import Dict, List, Optional
from datetime import datetime

from backend.database import db


class InventarioRepository:
    """
    Repositorio de inventario profesional.
    Maneja Kardex, movimientos, entradas, salidas y ajustes.
    """

    # =====================================================
    # MOVIMIENTOS (KARDEX)
    # =====================================================

    def crear_movimiento(
        self,
        producto_id: int,
        tipo: str,
        cantidad: float,
        stock_anterior: float,
        stock_posterior: float,
        referencia: Optional[str] = None,
        usuario: Optional[str] = None,
        observaciones: Optional[str] = None
    ) -> int:
        """Crea un movimiento en el Kardex."""
        ahora = datetime.now().isoformat()
        resultado = db.execute(
            """
            INSERT INTO inventario_movimientos
            (producto_id, tipo, cantidad, stock_anterior, stock_posterior,
             referencia, usuario, fecha, observaciones, fecha_registro)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (producto_id, tipo, cantidad, stock_anterior, stock_posterior,
             referencia, usuario, ahora, observaciones, ahora)
        )
        return resultado

    def obtener_movimientos(self, producto_id: int, limite: int = 100) -> List[Dict]:
        """Obtiene el Kardex de un producto."""
        return db.fetchall(
            """
            SELECT * FROM inventario_movimientos
            WHERE producto_id = ?
            ORDER BY fecha DESC
            LIMIT ?
            """,
            (producto_id, limite)
        )

    def obtener_movimiento(self, movimiento_id: int) -> Optional[Dict]:
        """Obtiene un movimiento específico."""
        return db.fetchone(
            "SELECT * FROM inventario_movimientos WHERE id = ?",
            (movimiento_id,)
        )

    def obtener_kardex_completo(self) -> List[Dict]:
        """Obtiene el Kardex completo ordenado por fecha."""
        return db.fetchall(
            """
            SELECT im.*, p.nombre, p.cantidad as stock_actual
            FROM inventario_movimientos im
            JOIN productos p ON im.producto_id = p.id
            ORDER BY im.fecha DESC
            """
        )

    # =====================================================
    # ENTRADAS
    # =====================================================

    def crear_entrada(
        self,
        producto_id: int,
        cantidad: float,
        precio_unitario: Optional[float] = None,
        proveedor: Optional[str] = None,
        numero_compra: Optional[str] = None,
        usuario: Optional[str] = None,
        observaciones: Optional[str] = None,
        movimiento_id: Optional[int] = None
    ) -> int:
        """Registra una entrada de inventario."""
        ahora = datetime.now().isoformat()
        return db.execute(
            """
            INSERT INTO inventario_entradas
            (producto_id, cantidad, precio_unitario, proveedor, numero_compra,
             usuario, fecha, observaciones, movimiento_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (producto_id, cantidad, precio_unitario, proveedor, numero_compra,
             usuario, ahora, observaciones, movimiento_id)
        )

    def obtener_entradas(self, producto_id: Optional[int] = None, limite: int = 100) -> List[Dict]:
        """Obtiene entradas de un producto o todas."""
        if producto_id:
            return db.fetchall(
                """
                SELECT ie.*, p.nombre, p.quantidade
                FROM inventario_entradas ie
                JOIN productos p ON ie.producto_id = p.id
                WHERE ie.producto_id = ?
                ORDER BY ie.fecha DESC
                LIMIT ?
                """,
                (producto_id, limite)
            )
        else:
            return db.fetchall(
                """
                SELECT ie.*, p.nombre
                FROM inventario_entradas ie
                JOIN productos p ON ie.producto_id = p.id
                ORDER BY ie.fecha DESC
                LIMIT ?
                """,
                (limite,)
            )

    # =====================================================
    # SALIDAS
    # =====================================================

    def crear_salida(
        self,
        producto_id: int,
        cantidad: float,
        motivo: Optional[str] = None,
        numero_documento: Optional[str] = None,
        usuario: Optional[str] = None,
        observaciones: Optional[str] = None,
        movimiento_id: Optional[int] = None
    ) -> int:
        """Registra una salida de inventario."""
        ahora = datetime.now().isoformat()
        return db.execute(
            """
            INSERT INTO inventario_salidas
            (producto_id, cantidad, motivo, numero_documento, usuario, fecha, observaciones, movimiento_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (producto_id, cantidad, motivo, numero_documento, usuario, ahora, observaciones, movimiento_id)
        )

    def obtener_salidas(self, producto_id: Optional[int] = None, limite: int = 100) -> List[Dict]:
        """Obtiene salidas de un producto o todas."""
        if producto_id:
            return db.fetchall(
                """
                SELECT isa.*, p.nombre
                FROM inventario_salidas isa
                JOIN productos p ON isa.producto_id = p.id
                WHERE isa.producto_id = ?
                ORDER BY isa.fecha DESC
                LIMIT ?
                """,
                (producto_id, limite)
            )
        else:
            return db.fetchall(
                """
                SELECT isa.*, p.nombre
                FROM inventario_salidas isa
                JOIN productos p ON isa.producto_id = p.id
                ORDER BY isa.fecha DESC
                LIMIT ?
                """,
                (limite,)
            )

    # =====================================================
    # AJUSTES
    # =====================================================

    def crear_ajuste(
        self,
        producto_id: int,
        cantidad_anterior: float,
        cantidad_nueva: float,
        razon: Optional[str] = None,
        usuario: Optional[str] = None,
        observaciones: Optional[str] = None,
        movimiento_id: Optional[int] = None
    ) -> int:
        """Registra un ajuste de inventario."""
        cantidad_ajuste = cantidad_nueva - cantidad_anterior
        ahora = datetime.now().isoformat()
        return db.execute(
            """
            INSERT INTO inventario_ajustes
            (producto_id, cantidad_anterior, cantidad_nueva, cantidad_ajuste,
             razon, usuario, fecha, observaciones, movimiento_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (producto_id, cantidad_anterior, cantidad_nueva, cantidad_ajuste,
             razon, usuario, ahora, observaciones, movimiento_id)
        )

    def obtener_ajustes(self, producto_id: Optional[int] = None, limite: int = 100) -> List[Dict]:
        """Obtiene ajustes de un producto o todos."""
        if producto_id:
            return db.fetchall(
                """
                SELECT ia.*, p.nombre
                FROM inventario_ajustes ia
                JOIN productos p ON ia.producto_id = p.id
                WHERE ia.producto_id = ?
                ORDER BY ia.fecha DESC
                LIMIT ?
                """,
                (producto_id, limite)
            )
        else:
            return db.fetchall(
                """
                SELECT ia.*, p.nombre
                FROM inventario_ajustes ia
                JOIN productos p ON ia.producto_id = p.id
                ORDER BY ia.fecha DESC
                LIMIT ?
                """,
                (limite,)
            )

    # =====================================================
    # CONFIGURACIÓN DE STOCK
    # =====================================================

    def obtener_config_inventario(self, producto_id: int) -> Optional[Dict]:
        """Obtiene la configuración de inventario de un producto."""
        return db.fetchone(
            "SELECT * FROM inventario_config WHERE producto_id = ?",
            (producto_id,)
        )

    def actualizar_stock_minimo(self, producto_id: int, stock_minimo: float, stock_maximo: float) -> bool:
        """Actualiza el stock mínimo de un producto."""
        ahora = datetime.now().isoformat()
        resultado = db.execute(
            """
            UPDATE inventario_config
            SET stock_minimo = ?, stock_maximo = ?, fecha_actualizacion = ?
            WHERE producto_id = ?
            """,
            (stock_minimo, stock_maximo, ahora, producto_id)
        )
        return resultado > 0

    def crear_config_inventario(self, producto_id: int, stock_minimo: float = 5, stock_maximo: float = 999999) -> int:
        """Crea configuración de inventario para un producto."""
        ahora = datetime.now().isoformat()
        return db.execute(
            """
            INSERT INTO inventario_config
            (producto_id, stock_minimo, stock_maximo, fecha_actualizacion)
            VALUES (?, ?, ?, ?)
            """,
            (producto_id, stock_minimo, stock_maximo, ahora)
        )

    # =====================================================
    # ALERTAS
    # =====================================================

    def crear_alerta(
        self,
        producto_id: int,
        tipo: str,
        mensaje: str,
        stock_actual: float,
        stock_minimo: float
    ) -> int:
        """Crea una alerta de inventario."""
        ahora = datetime.now().isoformat()
        return db.execute(
            """
            INSERT INTO inventario_alertas
            (producto_id, tipo, mensaje, stock_actual, stock_minimo, fecha_creacion)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (producto_id, tipo, mensaje, stock_actual, stock_minimo, ahora)
        )

    def obtener_alertas_activas(self) -> List[Dict]:
        """Obtiene solo las alertas no resueltas."""
        return db.fetchall(
            """
            SELECT ia.*, p.nombre
            FROM inventario_alertas ia
            JOIN productos p ON ia.producto_id = p.id
            WHERE ia.resuelta = 0
            ORDER BY ia.fecha_creacion DESC
            """
        )

    def obtener_alertas_producto(self, producto_id: int) -> List[Dict]:
        """Obtiene alertas de un producto."""
        return db.fetchall(
            """
            SELECT * FROM inventario_alertas
            WHERE producto_id = ?
            ORDER BY fecha_creacion DESC
            """,
            (producto_id,)
        )

    def resolver_alerta(self, alerta_id: int, usuario: Optional[str] = None) -> bool:
        """Marca una alerta como resuelta."""
        ahora = datetime.now().isoformat()
        resultado = db.execute(
            """
            UPDATE inventario_alertas
            SET resuelta = 1, fecha_resolucion = ?, usuario_resolucion = ?
            WHERE id = ?
            """,
            (ahora, usuario, alerta_id)
        )
        return resultado > 0

    def eliminar_alertas_duplicadas(self, producto_id: int, tipo: str) -> bool:
        """Elimina alertas duplicadas del mismo tipo para un producto."""
        resultado = db.execute(
            """
            DELETE FROM inventario_alertas
            WHERE producto_id = ? AND tipo = ? AND resuelta = 0
            AND id NOT IN (
                SELECT id FROM inventario_alertas
                WHERE producto_id = ? AND tipo = ? AND resuelta = 0
                ORDER BY fecha_creacion DESC
                LIMIT 1
            )
            """,
            (producto_id, tipo, producto_id, tipo)
        )
        return resultado > 0
