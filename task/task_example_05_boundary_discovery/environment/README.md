# Agent environment

This task environment contains the source-linked data, task-relevant tools, and pinned Python dependencies. The Dockerfile copies only `environment/`; it never copies `solution/`, `tests/`, or `authoring/`.

The raw-source bootstrap runs during image construction when `network_mode = "public"`. Data provenance, licence notes, file names, units, and checksums are recorded in `data/README.md` and `authoring/provenance/source_manifest.json`.
