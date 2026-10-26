# Legacy Data Migration and Quality Platform

An end-to-end portfolio project that simulates migrating inconsistent legacy customer, product, and order data into a validated analytical SQLite model.

## What it demonstrates

- Schema mapping from legacy CSV and JSON sources
- Type normalization and deterministic transformations
- Duplicate and referential-integrity checks
- Data-quality reporting with accepted/rejected record counts
- Loading validated data into a relational warehouse
- Reproducible synthetic data generation
- Automated tests using Python's standard library

## Run

```powershell
python -m src.generate_data
python -m src.pipeline
python -m unittest discover -s tests -v
```

The pipeline writes:

- `data/raw/` - generated legacy source files
- `data/processed/` - normalized records and `quality_report.json`
- `data/warehouse.db` - validated SQLite warehouse

## Design

```text
legacy CSV/JSON
      |
      v
source loaders -> normalization -> validation -> SQLite warehouse
                                      |
                                      +-> quality_report.json
```

The project intentionally rejects invalid records instead of silently coercing them. In a production migration, the rejected-record report would be reviewed with the source-system owner before a final cutover.

## Example quality checks

- Required identifiers are present
- Emails have a valid basic shape
- Dates use ISO `YYYY-MM-DD`
- Amounts are non-negative
- Orders reference known customers and products
- Duplicate customer IDs are detected

## Next improvements

- Replace SQLite with DuckDB or PostgreSQL
- Add JSON/CSV/Parquet adapters
- Add a formal data-contract layer
- Add CI with coverage and schema-drift checks
- Add a lineage view and a small Streamlit dashboard
