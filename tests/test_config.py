from proyecto.config import RAIZ, leer_sql


def test_raiz_contiene_pyproject():
    assert (RAIZ / "pyproject.toml").exists()


def test_leer_sql():
    assert "SELECT" in leer_sql("ejemplo.sql").upper()
