from proyecto.db import conectar, consultar


def test_consultar_en_memoria():
    con = conectar(":memory:")
    df = consultar(con, "ejemplo.sql")
    assert df.loc[0, "descripcion"] == "ejemplo"
