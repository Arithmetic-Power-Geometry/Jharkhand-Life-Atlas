# Core Geography

The foundational JLA module. Every future module should connect to `place_id` rather than joining on fragile place-name text.

The bundled release contains all 24 Jharkhand districts as a Census-2011 baseline. It intentionally does not invent village/block/panchayat rows. Use the ingestion template in `ingest_template.py` to map an authoritative official hierarchy file into `data/curated/core_geography/places.csv`, then run validation.

Quality class **A** denotes directly transcribed authoritative baseline fields; the JLA-generated `place_id` is marked as a derived identifier in the variable registry.
