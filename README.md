# Jharkhand Life Atlas (JLA) v1.0.0

**Evidence about people, places and access — connected at village level.**

Copyright (C) 2026 Mohammad Amir Khusru Akhtar

Licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)** for original JLA code, documentation, schemas, and original data products. Third-party source data retain their original licences and attribution requirements; see `NOTICE.md` and the source registry.

## What this package is

JLA is a modular, provenance-first public-interest data platform. Version 1.0.0 ships with the production repository skeleton and the first module, **Core Geography**, including a Jharkhand district baseline, a place model, source registry, dynamic module discovery, downloads, evidence metadata, PDF/HTML reporting, validation, tests, and an admin module builder.

The project deliberately does **not fabricate village-level records**. The bundled district baseline lets the application run immediately. Official village/block/panchayat crosswalks can be ingested into the same schema as authoritative files are verified. The architecture is already village-ready.

## Streamlit deployment

1. In Streamlit Community Cloud choose this repository and set **Main file path** to `streamlit_app.py`.
2. Deploy. Public mode works immediately.
3. Configure private secrets separately if you want to enable Admin mode.

## Dynamic modules

Drop a valid module folder under:

```text
modules/<module_id>/
```

At minimum it needs `module.yaml`. On the next Streamlit restart/rerun JLA discovers it automatically and shows it in the Modules page. If the module includes `data/indicators.csv`, those records become browsable and downloadable through the generic module renderer.

Admin mode contains a **Module Builder** that produces a ready-to-commit module ZIP with schema, source, indicator, README and test templates.

## Local run

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Architecture

- Canonical production data: Parquet / GeoParquet
- Portable source/seed data: CSV
- Analytics: DuckDB
- Transformation: Polars
- App: Streamlit 1.63+
- Charts/maps: Plotly 7+
- Reports: Python-native HTML/PDF for zero-extra-runtime deployment
- Citations: structured source registry + BibTeX export
- Module contract: `module.yaml` + optional standardized data files

## Public-interest principles

JLA reports conditions and evidence, not political blame. It separates observed, derived and modelled values; exposes source year and quality; never interprets missing data as zero; and keeps third-party licensing/provenance visible.

## Repository status

`v1.0.0` is a foundation release. The **software layer is complete and runnable**; the bundled Core Geography dataset is a verified district-level baseline and must be expanded with authoritative village/block/panchayat source files rather than invented values.
