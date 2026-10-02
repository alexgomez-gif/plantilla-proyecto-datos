"""Rutas y configuración compartidas del proyecto."""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

DATA_DIR = RAIZ / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"

SQL_DIR = RAIZ / "sql"
REPORTS_DIR = RAIZ / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"


def leer_sql(nombre: str) -> str:
    """Devuelve el contenido de un archivo de la carpeta sql/."""
    return (SQL_DIR / nombre).read_text(encoding="utf-8")
