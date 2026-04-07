# backend/usuarios.py
from datetime import datetime, timedelta
import bcrypt
from .db import get_connection
from .logs import registrar_log

# ============================================
# 🚀 Funciones de Usuarios (SQLite)
# ============================================

def crear_usuario(username, password, rol="empleado", actor=None):
    """Crea un usuario con password encriptado."""
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO usuarios (username, password, rol)
            VALUES (?, ?, ?)
        """, (username, hashed, rol))
        conn.commit()

        registrar_log(usuario=actor or username, accion="crear_usuario", detalles={"username": username, "rol": rol})
        return {"username": username, "rol": rol}
    except Exception as e:
        conn.rollback()
        raise ValueError(f"Error al crear usuario ({username}): {e}")
    finally:
        conn.close()

# --------------------------------------------
def autenticar_usuario(username, password, max_intentos=5, bloqueo_min=15):
    """Autentica usuario, maneja intentos fallidos y bloqueo temporal."""
    now = datetime.now()

    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Obtener datos del usuario
        cursor.execute("""
            SELECT password, activo, intentos_fallidos, bloqueado_hasta, rol
            FROM usuarios WHERE username=?
        """, (username,))
        row = cursor.fetchone()

        if not row or not row["activo"]:
            return None  # Usuario no existe o está desactivado

        # Si está bloqueado
        bloqueado_hasta = row["bloqueado_hasta"]
        if bloqueado_hasta and datetime.fromisoformat(bloqueado_hasta) > now:
            return {"bloqueado": True, "bloqueado_hasta": bloqueado_hasta}

        # Contraseña correcta
        if bcrypt.checkpw(password.encode(), row["password"].encode()):
            if row["intentos_fallidos"] or bloqueado_hasta:
                cursor.execute("""
                    UPDATE usuarios
                    SET intentos_fallidos=0, bloqueado_hasta=NULL
                    WHERE username=?
                """, (username,))
                conn.commit()
            return {"username": username, "rol": row["rol"]}

        # Contraseña incorrecta → aumentar intentos
        intentos = (row["intentos_fallidos"] or 0) + 1
        bloqueado = None
        if intentos >= max_intentos:
            bloqueado = (now + timedelta(minutes=bloqueo_min)).isoformat()
            registrar_log(usuario=username, accion="bloqueo_usuario",
                          detalles={"motivo": "intentos fallidos", "bloqueado_hasta": bloqueado})

        cursor.execute("""
            UPDATE usuarios
            SET intentos_fallidos=?, bloqueado_hasta=?
            WHERE username=?
        """, (intentos, bloqueado, username))
        conn.commit()

    finally:
        conn.close()

    return None

# --------------------------------------------
def cambiar_password(username, new_password, actor=None):
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE usuarios SET password=?, requiere_cambio_password=FALSE WHERE username=?
        """, (hashed, username))
        conn.commit()

        registrar_log(usuario=actor or username, accion="cambiar_password", detalles={"username": username})
        return True
    finally:
        conn.close()

# --------------------------------------------
def cambiar_rol(username, nuevo_rol, actor=None):
    old_rol = get_rol(username)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET rol=? WHERE username=?", (nuevo_rol, username))
        conn.commit()

        registrar_log(usuario=actor or username, accion="cambiar_rol",
                      detalles={"username": username, "rol_anterior": old_rol, "rol_nuevo": nuevo_rol})
        return True
    finally:
        conn.close()

# --------------------------------------------
def set_estado_usuario(username, activo: bool, actor=None):
    """Activa o desactiva usuario (uso unificado)."""

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET activo=? WHERE username=?", (activo, username))
        conn.commit()

        accion = "activar_usuario" if activo else "desactivar_usuario"
        registrar_log(usuario=actor or username, accion=accion, detalles={"username": username})
        return True
    finally:
        conn.close()

# --------------------------------------------
def listar_usuarios():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT username, rol, activo, created_at, requiere_cambio_password
            FROM usuarios ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()

        return [
            {
                "username": r["username"],
                "rol": r["rol"],
                "activo": r["activo"],
                "created_at": r["created_at"],
                "requiere_cambio_password": r["requiere_cambio_password"]
            }
            for r in rows
        ]
    finally:
        conn.close()

# --------------------------------------------
def requiere_cambio_password(username):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT requiere_cambio_password FROM usuarios WHERE username=?", (username,))
        row = cursor.fetchone()
        return bool(row["requiere_cambio_password"]) if row else False
    finally:
        conn.close()

# --------------------------------------------
def get_rol(username):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT rol FROM usuarios WHERE username=?", (username,))
        row = cursor.fetchone()
        return row["rol"] if row else None
    finally:
        conn.close()

# --------------------------------------------
def obtener_logs_usuario(username):
    from .logs import obtener_logs_usuario as fetch_logs
    return fetch_logs(username)

def activar_usuario(username, actor=None):
    return set_estado_usuario(username, True, actor)

def desactivar_usuario(username, actor=None):
    return set_estado_usuario(username, False, actor)

# --------------------------------------------
def eliminar_usuario(username, actor=None):
    """Elimina un usuario de la base de datos."""

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM usuarios WHERE username=?", (username,))
        conn.commit()

        registrar_log(usuario=actor or username, accion="eliminar_usuario", detalles={"username": username})
    finally:
        conn.close()
    return True 