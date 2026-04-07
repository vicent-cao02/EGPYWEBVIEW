from typing import Dict, Any, Optional
from .db import get_connection
from .logs import registrar_log


def get_client(cliente_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene un cliente por ID"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nombre, telefono, ci, chapa, direccion, deuda_total FROM clientes WHERE id = ?",
            (cliente_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def add_client(nombre, telefono, ci, direccion, chapa, usuario=None):
    """
    Agrega un nuevo cliente a la base de datos.
    Si se pasa 'usuario', se registra quién realizó la acción en la auditoría.
    """
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO clientes (nombre, telefono, ci, direccion, chapa)
                VALUES (?, ?, ?, ?, ?)
            """, (
                nombre.strip(),
                telefono.strip() if telefono else None,
                ci.strip() if ci else None,
                direccion.strip() if direccion else None,
                chapa.strip() if chapa else None
            ))
            conn.commit()

            # Validar tipo de usuario antes de registrar el log
            if usuario and isinstance(usuario, (str, int)):
                registrar_log(
                    usuario=str(usuario),
                    accion="crear_cliente",
                    detalles={
                        "nombre": nombre,
                        "telefono": telefono,
                        "ci": ci,
                        "direccion": direccion,
                        "chapa": chapa
                    }
                )

            # Obtener el cliente recién insertado
            cursor.execute("SELECT * FROM clientes ORDER BY id DESC LIMIT 1")
            nuevo = cursor.fetchone()
            return dict(nuevo) if nuevo else None
        finally:
            conn.close()

    except Exception as e:
        print(f"❌ Error al crear cliente: {e}")
        raise ValueError("Error al registrar el cliente. Verifica los datos e inténtalo nuevamente.")


def update_client(cliente_id: str, nombre=None, telefono=None, ci=None, chapa=None, direccion=None, usuario=None):
    """
    Actualiza los datos de un cliente existente en la base de datos.
    Parámetros opcionales: nombre, telefono, ci, chapa, direccion
    """
    cliente = get_client(cliente_id)
    if not cliente:
        raise ValueError(f"No existe el cliente con ID {cliente_id}")

    # Preparar los valores nuevos, manteniendo los anteriores si no se pasan
    nombre = nombre or cliente.get("nombre")
    telefono = telefono or cliente.get("telefono", "")
    ci = ci or cliente.get("ci", "")
    chapa = chapa or cliente.get("chapa", "")
    direccion = direccion or cliente.get("direccion", "")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE clientes
            SET nombre = ?, telefono = ?, ci = ?, chapa = ?, direccion = ?
            WHERE id = ?
        """, (nombre, telefono, ci, chapa, direccion, cliente_id))
        conn.commit()
    finally:
        conn.close()

    registrar_log(usuario or "sistema", "update_client", {"id": cliente_id})
    return get_client(cliente_id)


def delete_client(cliente_id: str, usuario: str = "sistema") -> bool:
    """Elimina un cliente"""
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
            conn.commit()
        finally:
            conn.close()
        
        registrar_log(usuario, "delete_client", {"id": cliente_id})
        return True
    except Exception as e:
        registrar_log(usuario, "error_delete_client", {"id": cliente_id, "error": str(e)})
        raise


def update_debt(cliente_id: str, monto: float, usuario: str = "sistema") -> Dict[str, Any]:
    """Actualiza la deuda del cliente de manera segura"""
    try:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            # En SQLite, usar MAX en lugar de GREATEST
            cursor.execute("""
                UPDATE clientes
                SET deuda_total = MAX(deuda_total + ?, 0)
                WHERE id = ?
            """, (monto, cliente_id))
            conn.commit()
        finally:
            conn.close()
        
        registrar_log(usuario, "update_debt", {"id": cliente_id, "monto": monto})
        return get_client(cliente_id)
    except Exception as e:
        registrar_log(usuario, "error_update_debt", {"id": cliente_id, "monto": monto, "error": str(e)})
        raise


def list_clients() -> list[Dict[str, Any]]:
    """Lista todos los clientes con campos esenciales"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nombre, telefono, ci, chapa, direccion, deuda_total FROM clientes ORDER BY nombre"
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def edit_client(cliente_id: str, nombre: Optional[str] = None, telefono: Optional[str] = None,
                ci: Optional[str] = None, chapa: Optional[str] = None, direccion: Optional[str] = None,
                usuario: str = "sistema") -> Dict[str, Any]:
    """Edita un cliente existente"""
    return update_client(cliente_id, nombre=nombre, telefono=telefono, ci=ci, chapa=chapa, direccion=direccion, usuario=usuario)