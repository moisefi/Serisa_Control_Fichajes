class ErrorAplicacion(Exception):
    """Error base de la aplicación."""


class ErrorConfiguracion(ErrorAplicacion):
    """Error relacionado con la configuración."""


class ErrorBaseDeDatos(ErrorAplicacion):
    """Error relacionado con el acceso a la base de datos."""


class ErrorConexionBaseDeDatos(ErrorBaseDeDatos):
    """Error al conectar con la base de datos."""
