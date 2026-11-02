# Basmati Grain Profiler

Measures rice kernels from a photo: length and breadth to 0.1 mm, chalky bellies,
stress fissures, and an estimate of how much cheaper long-grain has been blended in.
Built in seven parts, one per day. See [PLAN.md](PLAN.md).

## Part 1 — image plumbing and test data

- `pngio.py` reads and writes PNG using only `zlib` and `struct`, including all five
  scanline filters.
- `synth.py` renders mats of kernels with known length, breadth, angle and chalk
  fraction, and writes the truth next to the image as JSON.

```
python3 pngio.py     # round-trip and filter tests
python3 synth.py     # checks the generator against its own ground truth
```

Real calibration photos are scarce, so every later stage is measured against images
whose true answers are known exactly.
