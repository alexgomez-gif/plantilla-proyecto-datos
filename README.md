# Nombre del proyecto

> Una frase que explique qué problema resuelve este proyecto y para quién.

## Objetivo

Describe la pregunta de negocio o de investigación, el alcance y los criterios de éxito.

## Estructura del repositorio

```
.
├── data/
│   ├── raw/          # Datos originales, inmutables (no versionados)
│   ├── interim/      # Datos intermedios en transformación
│   └── processed/    # Datos finales listos para modelar o analizar
├── notebooks/        # Exploración y análisis (prefijo numérico: 01_exploracion.ipynb)
├── src/
│   └── proyecto/     # Código reutilizable importable desde notebooks y scripts
├── sql/              # Consultas SQL (extracción, vistas, transformaciones)
├── reports/
│   └── figures/      # Gráficos e informes generados
├── tests/            # Pruebas unitarias (pytest)
├── pyproject.toml    # Metadatos del paquete y configuración de ruff/pytest
├── requirements.txt  # Dependencias
└── README.md
```

## Requisitos

- Python 3.11 o superior

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .                 # Instala src/proyecto en modo editable
```

## Uso

```bash
# Abrir los notebooks
jupyter lab
```

Desde un notebook o script, importa el código del paquete:

```python
from proyecto.config import RAW_DIR, leer_sql
```

## Calidad de código

El estilo se controla con [ruff](https://docs.astral.sh/ruff/) (configurado en `pyproject.toml`).

```bash
ruff check .            # Linter
ruff check . --fix      # Corrige automáticamente lo posible
ruff format .           # Formatea el código
pytest                  # Ejecuta las pruebas
```

## Datos

| Fuente | Descripción | Ubicación | Actualización |
|--------|-------------|-----------|---------------|
| _ejemplo_ | _Ventas diarias_ | `data/raw/ventas.csv` | _Diaria_ |

Los datos **no se versionan** en git. Documenta aquí cómo obtenerlos o regenerarlos.

## Resultados

Resume los hallazgos principales y enlaza a los informes en `reports/`.

## Convenciones

- Los notebooks se nombran `NN_descripcion.ipynb` (p. ej. `01_exploracion.ipynb`).
- La lógica reutilizable vive en `src/`, no en los notebooks.
- Los datos en `data/raw/` nunca se modifican.

## Autoría

- Nombre — correo@ejemplo.com

## Licencia

Indica la licencia del proyecto (p. ej. MIT).
