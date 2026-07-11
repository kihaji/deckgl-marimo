# Benchmarks

Performance harnesses — not usage examples.

| File | Purpose |
|------|---------|
| [binary_benchmark.py](binary_benchmark.py) | Parametrized JSON-vs-binary transport comparison: pick a layer type (Scatterplot/Arc/Line/Column/PointCloud/Path/Polygon) and row count, measure serialization time + payload size, view the binary result. Replaces the seven former `*_binary_compare.py` notebooks. |
| [polygon_perf.py](polygon_perf.py) | Polygon rendering performance exploration |
| [polygon_stress.py](polygon_stress.py) | Polygon count stress test |
| [polygon_1m_stress.py](polygon_1m_stress.py) | 1M-polygon stress test (uses generated .npz data) |
| [generate_1m_polygons.py](generate_1m_polygons.py) | Generator for the 1M-polygon dataset |

```bash
uv run marimo edit benchmarks/binary_benchmark.py
```
