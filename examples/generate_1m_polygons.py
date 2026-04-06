"""Generate 1M polygon test data and save as .npz for fast loading."""

import numpy as np
import time

COUNT = 1_000_000
SEED = 42
N_VERTS = 5
VERTS_PER_POLY = N_VERTS + 1  # closed ring

print(f"Generating {COUNT:,} polygons...")
t0 = time.perf_counter()

rng = np.random.default_rng(SEED)

cols = int(np.ceil(np.sqrt(COUNT)))
rows = int(np.ceil(COUNT / cols))
total_cells = cols * rows

lon_range, lat_range = 320.0, 110.0
cell_w, cell_h = lon_range / cols, lat_range / rows
radius = min(cell_w, cell_h) * 0.3

col_idx = np.arange(total_cells) % cols
row_idx = np.arange(total_cells) // cols
cx = -160.0 + (col_idx + 0.5) * cell_w + rng.uniform(-cell_w * 0.1, cell_w * 0.1, total_cells)
cy = -55.0 + (row_idx + 0.5) * cell_h + rng.uniform(-cell_h * 0.1, cell_h * 0.1, total_cells)
cx, cy = cx[:COUNT], cy[:COUNT]

angles = rng.uniform(0, 2 * np.pi, (COUNT, N_VERTS))
angles.sort(axis=1)
radii = radius + rng.uniform(-radius * 0.5, radius * 0.5, (COUNT, N_VERTS))

vx = cx[:, None] + radii * np.cos(angles)
vy = cy[:, None] + radii * np.sin(angles)

colors_rgb = rng.integers(30, 256, (COUNT, 3), dtype=np.uint8)

# Build arrays in the format pack_polygon_binary expects
total_verts = COUNT * VERTS_PER_POLY

coords = np.empty((total_verts, 2), dtype=np.float32)
for v in range(N_VERTS):
    coords[v::VERTS_PER_POLY, 0] = vx[:, v].astype(np.float32)
    coords[v::VERTS_PER_POLY, 1] = vy[:, v].astype(np.float32)
coords[N_VERTS::VERTS_PER_POLY, 0] = vx[:, 0].astype(np.float32)
coords[N_VERTS::VERTS_PER_POLY, 1] = vy[:, 0].astype(np.float32)

start_indices = np.arange(COUNT, dtype=np.uint32) * VERTS_PER_POLY

vertex_colors = np.empty((total_verts, 4), dtype=np.uint8)
for v in range(VERTS_PER_POLY):
    vertex_colors[v::VERTS_PER_POLY, 0] = colors_rgb[:, 0]
    vertex_colors[v::VERTS_PER_POLY, 1] = colors_rgb[:, 1]
    vertex_colors[v::VERTS_PER_POLY, 2] = colors_rgb[:, 2]
    vertex_colors[v::VERTS_PER_POLY, 3] = 180

gen_ms = (time.perf_counter() - t0) * 1000

print(f"Generated in {gen_ms:.0f} ms")
print(f"  coords: {coords.shape} ({coords.nbytes / 1024 / 1024:.1f} MB)")
print(f"  start_indices: {start_indices.shape} ({start_indices.nbytes / 1024 / 1024:.1f} MB)")
print(f"  vertex_colors: {vertex_colors.shape} ({vertex_colors.nbytes / 1024 / 1024:.1f} MB)")
total_mb = (coords.nbytes + start_indices.nbytes + vertex_colors.nbytes) / 1024 / 1024
print(f"  total: {total_mb:.1f} MB")

out = "examples/data/polygons_1m.npz"
np.savez_compressed(
    out,
    coords=coords,
    start_indices=start_indices,
    vertex_colors=vertex_colors,
)

import os
file_mb = os.path.getsize(out) / 1024 / 1024
print(f"\nSaved to {out} ({file_mb:.1f} MB compressed)")
