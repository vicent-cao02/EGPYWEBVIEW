# utils/export_utils.py

import platform
import subprocess
import os
from pathlib import Path
import pandas as pd


def exportar_excel(dataframe, nombre_archivo="inventario.xlsx"):
    """
    Guarda un DataFrame en disco y devuelve la ruta del archivo.
    """

    export_dir = Path("exports")
    export_dir.mkdir(exist_ok=True)

    file_path = export_dir / nombre_archivo

    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
        dataframe.to_excel(writer, index=False, sheet_name="Inventario")

    return str(file_path)


def abrir_archivo(path: str):
    """
    Abre el archivo con la aplicación predeterminada del sistema.
    """

    system = platform.system()

    try:
        if system == "Darwin":  # macOS
            subprocess.call(["open", path])

        elif system == "Windows":
            os.startfile(path)

        else:  # Linux
            subprocess.call(["xdg-open", path])

    except Exception as e:
        print(f"No se pudo abrir el archivo: {e}")