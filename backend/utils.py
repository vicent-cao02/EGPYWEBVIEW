# backend/utils.py
"""
Utilidades para manejo de archivos JSON como "base de datos".
Incluye lectura/escritura atómica, bloqueo de archivo (FileLock), generación de IDs y validaciones básicas.
"""


from pathlib import Path
import json
from filelock import FileLock, Timeout
import tempfile
from typing import Any, List, Dict
import datetime
from .logs import registrar_log

# Ruta base de datos (data/)
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)  # crear si no existe

LOCK_TIMEOUT = 5  # segundos para esperar lock

def _file_lock_path(path: Path) -> Path:
    return Path(str(path) + ".lock")

def read_json(filename: str, actor=None) -> List[Dict[str, Any]]:
    """
    Lee un archivo JSON y devuelve la lista de registros.
    Si no existe, devuelve lista vacía.
    """
    path = DATA_DIR / filename
    if not path.exists():
        registrar_log(
            usuario=actor or "sistema",
            accion="read_json",
            detalles={"archivo": filename, "existe": False}
        )
        return []
    lock = FileLock(str(_file_lock_path(path)))
    try:
        with lock.acquire(timeout=LOCK_TIMEOUT):
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            registrar_log(
                usuario=actor or "sistema",
                accion="read_json",
                detalles={"archivo": filename, "registros": len(data)}
            )
            return data
    except Timeout:
        raise RuntimeError(f"No se pudo adquirir bloqueo para leer {filename}")

def write_json_atomic(filename: str, data: List[Dict[str, Any]], actor=None) -> None:
    """
    Escribe de forma atómica en el archivo JSON (escribe en temp + reemplaza).
    Usa lock para evitar concurrencia.
    """
    path = DATA_DIR / filename
    lock = FileLock(str(_file_lock_path(path)))
    try:
        with lock.acquire(timeout=LOCK_TIMEOUT):
            # escribir en archivo temporal y mover
            with tempfile.NamedTemporaryFile("w", delete=False, dir=str(DATA_DIR), encoding="utf-8") as tmp:
                json.dump(data, tmp, indent=4, ensure_ascii=False)
                tmp_path = Path(tmp.name)
            tmp_path.replace(path)
        registrar_log(
            usuario=actor or "sistema",
            accion="write_json_atomic",
            detalles={"archivo": filename, "registros": len(data)}
        )
    except Timeout:
        raise RuntimeError(f"No se pudo adquirir bloqueo para escribir {filename}")

def generate_id(prefix: str, current_items: List[Dict[str, Any]], field: str = "id") -> str:
    """
    Generador de ID simple: prefix + número secuencial con 3 dígitos.
    Busca el máximo numerico ya usado (si IDs siguen patrón prefixNNN) y devuelve next.
    """
    max_n = 0
    for it in current_items:
        val = it.get(field, "")
        if isinstance(val, str) and val.startswith(prefix):
            try:
                n = int(val[len(prefix):])
                if n > max_n:
                    max_n = n
            except ValueError:
                continue
    return f"{prefix}{max_n+1:03d}"

def iso_today() -> str:
    return datetime.date.today().isoformat()

# Validaciones simples (puedes extender según reglas contables)
def validate_product(obj: Dict[str, Any]) -> bool:
    required = {"id", "nombre", "precio", "cantidad", "categoria"}
    return required.issubset(set(obj.keys()))

def validate_client(obj: Dict[str, Any]) -> bool:
    required = {"id", "nombre", "telefono", "deuda_total"}
    return required.issubset(set(obj.keys()))

def validate_debt(obj: Dict[str, Any]) -> bool:
    required = {"id", "cliente_id", "monto", "estado", "fecha"}
    return required.issubset(set(obj.keys()))

def validate_sale(sale: dict) -> bool:
    """
    Valida que la venta tenga la estructura correcta.
    """
    required_fields = {"id", "fecha", "cliente_id", "productos_vendidos", "total", "pagado"}
    # Ahora permitimos también 'tipo_pago'
    optional_fields = {"tipo_pago"}

    if not isinstance(sale, dict):
        return False

    # Debe contener todos los obligatorios
    if not required_fields.issubset(sale.keys()):
        return False

    # No debe contener claves raras
    allowed_fields = required_fields | optional_fields
    if not set(sale.keys()).issubset(allowed_fields):
        return False

    # Validaciones simples de tipos
    if not isinstance(sale["id"], str):
        return False
    if not isinstance(sale["cliente_id"], str):
        return False
    if not isinstance(sale["productos_vendidos"], list):
        return False
    if not isinstance(sale["total"], (int, float)):
        return False
    if not isinstance(sale["pagado"], (int, float)):
        return False

    # tipo_pago es opcional, pero si existe debe ser str o None
    if "tipo_pago" in sale and sale["tipo_pago"] is not None:
        if not isinstance(sale["tipo_pago"], str):
            return False

    return True
