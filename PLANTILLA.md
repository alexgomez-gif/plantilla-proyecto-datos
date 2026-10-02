# Cómo usar esta plantilla

Plantilla para proyectos de análisis de datos con Python 3.12, DuckDB, ruff y pytest.
El `README.md` es el modelo que cada proyecto completa.

## Opción 1: desde GitHub

Botón **Use this template** → crea el repositorio y clónalo. Después:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Borra `PLANTILLA.md` y `scripts/` del proyecto nuevo.

## Opción 2: en local con `nuevo-proyecto`

```bash
git clone https://github.com/alexgomez-gif/plantilla-proyecto-datos ~/plantilla-proyecto-datos
ln -s ~/plantilla-proyecto-datos/scripts/nuevo-proyecto ~/.local/bin/nuevo-proyecto

nuevo-proyecto ventas            # crea ~/proyectos/ventas con .venv, dependencias y git
code ~/proyectos/ventas
```

El script copia solo los archivos del proyecto (sin `PLANTILLA.md` ni `scripts/`).

## Qué cambiar en cada proyecto

- `name` y `description` en `pyproject.toml`.
- Las secciones del `README.md`.
- `sql/ejemplo.sql` y las pruebas de ejemplo.
