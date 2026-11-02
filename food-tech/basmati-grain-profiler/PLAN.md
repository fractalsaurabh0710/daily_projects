# Basmati Grain Profiler — build plan

Rice traders lose money when aged basmati is blended with cheaper long-grain, and
mills lose it when chalky or fissured kernels shatter. The goal: take a photo of
kernels on a dark mat and report per-kernel length, breadth, chalkiness and a
blend estimate. Standard library only, so it runs anywhere.

One part per day, each committed finished and tested.

| Part | What | Status |
| ---- | ---- | ------ |
| 1 | PNG read/write on zlib, plus a synthetic-sample generator with exact ground truth | done |
| 2 | Segmentation: Otsu threshold and connected-component labelling into separate kernels | planned |
| 3 | Geometry: principal-axis length and breadth in mm from the pixel scale, tested against ground truth | planned |
| 4 | Chalkiness: opaque-belly area fraction per kernel and per sample | planned |
| 5 | Stress fissures: thin dark lines inside a kernel via a ridge filter | planned |
| 6 | Grading: length/breadth classes, adulteration estimate from a two-population mixture fit | planned |
| 7 | CLI report (table and JSON), end-to-end test from image to verdict | planned |
