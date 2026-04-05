class AppError(Exception):
    """Error base de la aplicación"""
    pass


class DatabaseConnectionError(AppError):
    """No hay conexión con la base de datos"""
    pass


class DatabaseQueryError(AppError):
    """Error al ejecutar una consulta"""
    pass


class NotFoundError(AppError):
    """Registro no encontrado"""
    pass
