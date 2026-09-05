# Jharkhand Life Atlas (JLA)

> **Evidence about people, places and access — connected at village level.**

**v1.0.0 · Provenance-first**  
Copyright (C) 2026 Mohammad Amir Khusru Akhtar · CC BY 4.0

## About

**Jharkhand Life Atlas (JLA)** connects geography, public-interest data and source evidence in one modular research platform. It is designed as a long-term, extensible evidence infrastructure for Jharkhand: begin with a verified geographic backbone, then connect independent thematic modules without rebuilding the core application.

JLA is intended for researchers, students, planners, public-interest organisations and citizens who need data that can be explored, downloaded, cited and traced back to its evidence.

## Core idea

JLA follows one simple chain:

**Place → Variable → Observation → Time → Source → Method → Quality**

Every published factual value should be traceable. Missing information remains missing; it is never silently converted to zero or replaced by an invented value.

## Modular by design

The geographic backbone provides stable place identities. Independent modules can then add evidence about health, water, education, agriculture, livelihoods, environment, climate, accessibility, human-wildlife conflict and other public-interest themes.

A valid module lives under:

```text
modules/<module_id>/
```

The application discovers modules from the repository, allowing the platform to expand without redesigning its core navigation or evidence model.

## Module 1 — Core Geography & Census Baseline

Core Geography establishes the geographic spine used by all later JLA modules. Its target hierarchy is:

**State → District → Sub-district → Block → Panchayat → Village/Town**

The module preserves official identifiers, administrative relationships, temporal context, source provenance and Census baseline observations where authoritative source material has been successfully ingested and validated.

Census 2011 geography and current administrative/LGD geography are treated as distinct temporal views and must not be silently mixed. Coverage published by JLA reflects only records that have passed the project's source and validation rules.

## Evidence and provenance rules

JLA is provenance-first:

- no source = no published factual value;
- missing data ≠ zero;
- observed, derived and modelled values are distinguished;
- source year and geographic resolution remain visible;
- transformations should be reproducible;
- third-party licensing and attribution remain attached to source material;
- unsupported or ambiguous records are rejected rather than guessed;
- public outputs should not expose person-level identifiable information.

## Public-interest and non-partisan use

JLA measures publicly observable conditions, accessibility, exposure and service environments. It does not rank political parties, elected representatives or governments, and derived indicators should not be interpreted as attribution of political responsibility.

## Research and application features

The repository supports:

- geographic exploration and place profiles;
- modular data discovery;
- source and methodology inspection;
- evidence-preserving CSV/research-bundle downloads;
- PDF/HTML evidence reports;
- validation and automated tests;
- reproducible source ingestion workflows;
- dynamic module discovery; and
- an Admin Module Builder for preparing future modules.

## Technology

- **Application:** Streamlit 1.63+
- **Analytics:** DuckDB
- **Transformation:** Polars / PyArrow
- **Canonical tabular storage:** Parquet
- **Spatial storage:** GeoParquet where verified geometry is available
- **Portable exchange:** CSV / GeoJSON where appropriate
- **Visualisation:** Plotly 7+ / MapLibre-compatible mapping
- **Metadata:** YAML / JSON / structured source registries
- **Reports:** Python-native HTML/PDF
- **Automation:** GitHub Actions

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Streamlit deployment

In Streamlit Community Cloud, select this repository, use branch `main`, and set the main file path to:

```text
streamlit_app.py
```

Public functionality does not require an admin secret. Admin credentials must be configured privately through Streamlit secrets and must never be committed to this repository.

## Data licensing

Original JLA material is released under the **Creative Commons Attribution 4.0 International (CC BY 4.0)** licence as stated in this repository. Third-party datasets, government source files and externally produced material retain their own applicable terms, licences and attribution requirements. Inclusion of provenance metadata does not relicense third-party material. See `NOTICE.md` and the source registry for source-specific information.

## Repository status

JLA is under evidence-driven expansion. Software capabilities and data coverage are deliberately reported separately: a working module does not imply that every potentially available dataset has been ingested. Each module should be considered complete only after its intended authoritative sources, validation rules, provenance records and published outputs have been checked.

---

**Jharkhand Life Atlas (JLA)**  
**v1.0.0 · Provenance-first**  
**Copyright (C) 2026 Mohammad Amir Khusru Akhtar · CC BY 4.0**
