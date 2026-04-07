import os
import shutil
from datetime import datetime
from pathlib import Path

def backup_data_folder(dest_folder=None):
    """
    Realiza un backup completo de la carpeta 'data' en una subcarpeta 'backups' con timestamp.
    Si el backup ya existe, lo sobrescribe.
    """
    base_dir = Path(__file__).resolve().parents[1]
    data_dir = base_dir / "data"
    backups_dir = base_dir / "backups"
    backups_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}"
    backup_path = backups_dir / backup_name
    if backup_path.exists():
        shutil.rmtree(backup_path)
    shutil.copytree(data_dir, backup_path)
    return str(backup_path)

def restore_backup(backup_folder):
    """
    Restaura el backup seleccionado sobreescribiendo la carpeta 'data' con el contenido del backup.
    """
    base_dir = Path(__file__).resolve().parents[1]
    data_dir = base_dir / "data"
    backup_path = Path(backup_folder)
    if not backup_path.exists() or not backup_path.is_dir():
        raise FileNotFoundError(f"Backup no encontrado: {backup_folder}")
    # Eliminar data actual
    if data_dir.exists():
        shutil.rmtree(data_dir)
    # Copiar backup a data
    shutil.copytree(backup_path, data_dir)
    return str(data_dir)
import os
import shutil
from datetime import datetime
from pathlib import Path

def backup_data_folder(dest_folder=None):
    """
    Realiza un backup completo de la carpeta 'data' en una subcarpeta 'backups' con timestamp.
    Si el backup ya existe, lo sobrescribe.
    """
    base_dir = Path(__file__).resolve().parents[1]
    data_dir = base_dir / "data"
    backups_dir = base_dir / "backups"
    backups_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}"
    backup_path = backups_dir / backup_name
    if backup_path.exists():
        shutil.rmtree(backup_path)
    shutil.copytree(data_dir, backup_path)
    return str(backup_path)
