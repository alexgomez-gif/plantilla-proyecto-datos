"""Conexión a DuckDB y ejecución de consultas de la carpeta sql/."""

import duckdb

from proyecto.config import DATA_DIR, leer_sql

DB_PATH = DATA_DIR / "proyecto.duckdb"


def conectar(ruta=DB_PATH) -> duckdb.DuckDBPyConnection:
    """Abre (o crea) la base de datos DuckDB del proyecto."""
    return duckdb.connect(str(ruta))


def consultar(con: duckdb.DuckDBPyConnection, archivo_sql: str):
    """Ejecuta un archivo de sql/ y devuelve el resultado como DataFrame."""
    return con.sql(leer_sql(archivo_sql)).df()
