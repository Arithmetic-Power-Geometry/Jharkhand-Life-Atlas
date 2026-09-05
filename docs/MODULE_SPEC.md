# JLA Module Contract v1

A dynamically discoverable module is a folder under `modules/` containing `module.yaml` with: `id`, `name`, `version`, `status`, `description`.

Recommended files:

- `module.yaml` — identity and features
- `sources.yaml` — source IDs/metadata
- `schema.yaml` — input/indicator contract
- `data/indicators.csv` — optional generic indicator feed
- `README.md` — human documentation
- `tests/` — module tests

## Generic indicator columns

`place_id, indicator_id, period, value_numeric, value_text, unit, source_id, quality_class, observation_type`

`observation_type` should distinguish `observed`, `derived`, and `modelled`.

A module added to GitHub becomes visible automatically because the app scans `modules/*/module.yaml` at runtime.
